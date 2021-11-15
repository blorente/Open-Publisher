#!/usr/bin/env python3

from pathlib import Path
import argparse
import logging
import subprocess
import os
import shutil

from layouts.epub import EPUB_LAYOUT
from layouts.paperback import PAPERBACK_LAYOUT

project_dir = Path(__file__).parent.parent

POSSIBLE_FORMATS = ["epub", "paperback"]

log = logging.getLogger("Binder")


def pandoc(cmd, check=False):
    log.debug(f"Running: pandoc {' '.join(cmd)}")
    res = subprocess.run(["pandoc"] + cmd, check=check, capture_output=True)
    if res.returncode != 0:
        log.error(f"Pandoc failed: {res}")
    return res


def stitch_document(manuscript: Path, outdir: Path, layout) -> Path:
    true_layout = []
    for item in layout:
        if item == "manuscript":
            true_layout.append(manuscript)
        else:
            true_layout.append(item)

    stitched = outdir / f"{manuscript.name}.stitched.md"
    content = "\n".join([file.read_text() for file in true_layout])
    stitched.write_text(content)
    log.info(f"Written stiched content to {stitched}")
    log.debug(f"Stitched content: {content}")
    return stitched


def compile_epub(manuscript: Path, book_name: str, outdir: Path):
    stitched = stitch_document(manuscript, outdir, EPUB_LAYOUT)
    output = f"{outdir}/{book_name}.epub"
    cmd = [
        "--top-level-division=chapter",
        "--toc-depth=1",
        "--template=src/pandoc/templates/custom-epub.html",
        "--css=src/pandoc/css/style.css",
        "-f",
        "markdown+smart",
        "-o",
        str(output),
        str(stitched),
    ]
    res = pandoc(cmd)
    if res.returncode == 0:
        log.info(f"=> Compiled with epub at {output}")


def compile_paperback(manuscript: Path, book_name: str, outdir: Path):
    stitched = stitch_document(manuscript, outdir, PAPERBACK_LAYOUT)
    output = f"{outdir}/{book_name}-paperback.pdf"
    cmd = [
        "--top-level-division=chapter",
        "--template=src/pandoc/templates/cs-5x8-pdf.latex",
        "--pdf-engine=xelatex",
        '--pdf-engine-opt=-output-driver="xdvipdfmx -V 3 -z 0"',
        "-f",
        "markdown+backtick_code_blocks",
        "-o",
        str(output),
        str(stitched),
    ]
    res = pandoc(cmd)
    if res.returncode == 0:
        log.info(f"=> Compiled with paperback at {output}")


def main(args):
    logging.basicConfig(level=args.log_level)
    book_file = Path(args.book_file[0])
    book_name = book_file.name
    log.info(f"=== Binding {book_name} ===")
    log.debug(f"Args are {args}")

    outdir = Path(args.out)
    if outdir.exists():
        log.info(f"=> Outdir exists: {outdir}. Removing.")
        shutil.rmtree(outdir)
    log.info(f"=> Creating outdir: {outdir}.")
    outdir.mkdir(parents=True)

    partialdir = outdir / "partial"

    formats = POSSIBLE_FORMATS if args.format == "all" else [args.format]
    if "epub" in formats:
        compile_epub(book_file, book_name=book_name, outdir=outdir)

    if "paperback" in formats:
        compile_paperback(book_file, book_name=book_name, outdir=outdir)


def parse_args():
    parser = argparse.ArgumentParser("Borja's Amazing Book Binder")
    parser.add_argument(
        "--format", "-f", choices=["all"] + POSSIBLE_FORMATS, default="all"
    )
    parser.add_argument(
        "--template",
        "-t",
        type=str,
        default=None,
        help="Optional template file. Oherwise, default will be applied.",
    )
    parser.add_argument("--out", "-o", type=str, default=f"{project_dir}/.out")
    parser.add_argument("--log-level", "-l", default=logging.INFO, type=int)
    parser.add_argument("book_file", nargs=1, type=str)
    return parser.parse_args()


if __name__ == "__main__":
    os.chdir(project_dir)
    main(parse_args())
