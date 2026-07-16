"""Command-line interface for UploadAssist."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ._version import __version__
from .bib import extract_bib
from .deps import collect


def _detect_texfile(directory: Path) -> Path:
    candidates = sorted(directory.glob("*.tex"))
    if len(candidates) == 1:
        return candidates[0]
    preferred = [path for path in candidates if path.stem.lower() in {"main", "paper"}]
    if len(preferred) == 1:
        return preferred[0]
    names = ", ".join(path.name for path in candidates) or "none"
    raise ValueError(f"Cannot auto-detect the main .tex file (candidates: {names})")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Package a LaTeX project for journal or repository submission."
    )
    parser.add_argument(
        "texfile", nargs="?", help="Main .tex file (default: auto-detect)"
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output directory (default: output, next to the main document)",
    )
    parser.add_argument(
        "--noflatten",
        action="store_true",
        help="Preserve the project directory structure instead of flattening it",
    )
    parser.add_argument(
        "--no-strip-comments",
        action="store_true",
        help="Keep comments in .tex files",
    )
    parser.add_argument(
        "--no-archive",
        action="store_true",
        help="Create only the output directory, without a .tar.gz archive",
    )
    parser.add_argument(
        "--include",
        "--include-packages",
        action="append",
        default=[],
        metavar="PATH",
        help="Include an additional file or directory (repeatable)",
    )
    # Retained as no-op compatibility options for pre-1.0 callers. Static discovery
    # means users do not need a TeX installation merely to package their sources.
    parser.add_argument("--latexmk", default="latexmk", help=argparse.SUPPRESS)
    parser.add_argument(
        "--engine",
        choices=["pdflatex", "xelatex", "lualatex"],
        default="pdflatex",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--extract-bib",
        nargs=2,
        metavar=("BIB_FILE", "TEX_FILE"),
        help="Print only bibliography entries cited by a TeX file",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        if args.extract_bib:
            extract_bib(*args.extract_bib)
            return 0

        texfile = (
            Path(args.texfile).expanduser()
            if args.texfile
            else _detect_texfile(Path.cwd())
        )
        texfile = texfile.resolve()
        flatten = not args.noflatten
        output = (
            Path(args.output).expanduser()
            if args.output
            else texfile.parent / ("output" if flatten else "output_no_flatten")
        )
        collected = collect(
            str(texfile),
            str(output),
            flatten=flatten,
            latexmk_path=args.latexmk,
            engine=args.engine,
            strip_comments=not args.no_strip_comments,
            include_packages=args.include,
            create_archive=not args.no_archive,
        )
        output = output.resolve()
        print(f"Packaged {len(collected)} files in {output}")
        if not args.no_archive:
            print(f"Created archive {output}.tar.gz")
        return 0
    except (OSError, UnicodeError, ValueError) as error:
        print(f"uploadassist: error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
