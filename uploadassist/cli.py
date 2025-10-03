import argparse
import sys

from .deps import collect
from .latexmk import (
    get_latexmk,
    get_latexmk_engine_opts,
    get_latexmk_version,
    LatexmkException,
)
from .utils import sizeof_fmt


class AppendList(argparse.Action):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, nargs=0, **kwargs)
        self.values = []

    def __call__(self, parser, namespace, values, option_string=None):
        items = getattr(namespace, self.dest, None)
        if items is None:
            items = []
        items.append(values)
        setattr(namespace, self.dest, items)


def parse_args():
    parser = argparse.ArgumentParser(
        description="UploadAssist: Package LaTeX sources for journal/journal repository submission."
    )
    parser.add_argument(
        "texfile",
        nargs="?",
        help="Main .tex file to process (default: auto-detect in current directory)",
    )
    parser.add_argument(
        "--noflatten",
        action="store_true",
        help="Do NOT flatten files; preserve directory structure (default: flatten enabled)",
    )
    parser.add_argument(
        "--latexmk",
        type=str,
        default="latexmk",
        help="Path to latexmk executable (default: latexmk on PATH)",
    )
    parser.add_argument(
        "--engine",
        choices=["pdflatex", "xelatex", "lualatex"],
        default="pdflatex",
        help="TeX engine to use (default: pdflatex)",
    )
    parser.add_argument(
        "--no-strip-comments",
        action="store_true",
        help="Do not strip comments from .tex files",
    )
    parser.add_argument(
        "--include-packages",
        action=AppendList,
        help="Additional directories or packages to include",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="UploadAssist (dynamic versioning via setuptools_scm)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    try:
        latexmk_path = args.latexmk
        engine = args.engine
        texfile = args.texfile
        flatten = not args.noflatten
        strip_comments = not args.no_strip_comments
        include_packages = getattr(args, "include_packages", [])

        print(f"Using latexmk: {latexmk_path}")
        print(f"TeX engine: {engine}")
        print(f"Main .tex file: {texfile if texfile else '(auto-detect)'}")
        if flatten:
            print("Flattening output for journal submission (default).")
        else:
            print("Preserving directory structure (no flatten).")
        if not strip_comments:
            print("Comments will NOT be stripped from .tex files.")
        if include_packages:
            print(f"Including additional packages/directories: {include_packages}")

        # Collect and package files
        collect(
            texfile=texfile,
            latexmk_path=latexmk_path,
            engine=engine,
            flatten=flatten,
            strip_comments=strip_comments,
            include_packages=include_packages,
        )
        print("Packaging complete.")

    except LatexmkException as e:
        print(f"Latexmk error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
