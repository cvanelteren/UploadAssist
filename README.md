<table>
  <tr>
    <td><img src="https://raw.githubusercontent.com/cvanelteren/UploadAssist/main/assets/logo.svg" alt="UploadAssist logo" width="128"></td>
    <td>
      <h1>UploadAssist</h1>
      <p><strong>Submission-ready LaTeX project packaging.</strong></p>
    </td>
  </tr>
</table>

UploadAssist packages the local files used by a LaTeX document into a clean submission directory and `.tar.gz` archive. It is designed for journal, conference, and repository submission systems, many of which require a flat source bundle.

Version 1.0 is a modern, dependency-free successor to [arxiv-collector](https://github.com/djsutherland/arxiv-collector). It supports Python 3.9 and newer.

## Highlights

- Recursively discovers `\input`, `\include`, `\subfile`, import-family commands, graphics, bibliographies, and local classes/styles.
- Flattens the bundle by default and rewrites source references accordingly.
- Detects duplicate basenames before flattening instead of silently overwriting files.
- Strips LaTeX comments by default while preserving escaped percent signs.
- Replaces stale output atomically and creates a ready-to-upload archive.
- Requires no Python dependencies and no TeX installation.

## Installation

```console
python -m pip install uploadassist
```

## Usage

Run the command from the directory containing your main document:

```console
uploadassist
```

If there is one `.tex` file, it is selected automatically. If there are several, `main.tex` or `paper.tex` is preferred when unambiguous. You can always specify the document:

```console
uploadassist path/to/main.tex
```

The default output is `output/` next to the main document, plus `output.tar.gz`.

Common options:

```console
uploadassist --noflatten main.tex             # preserve directories
uploadassist --no-strip-comments main.tex     # retain comments
uploadassist --no-archive main.tex            # omit the tar.gz file
uploadassist -o submission main.tex            # choose the output directory
uploadassist --include journal-template.sty main.tex
uploadassist --include extra-files/ main.tex   # repeatable
uploadassist --version
```

To extract only cited BibTeX entries:

```console
uploadassist --extract-bib references.bib main.tex > cited.bib
```

Run `uploadassist --help` for the complete command reference.

## Python API

```python
from uploadassist import collect, get_deps

dependencies = get_deps("main.tex")
files = collect("main.tex", "submission", flatten=True)
```

`collect` returns the generated file paths. Pass `create_archive=False` to omit the archive.

## Discovery and limitations

UploadAssist uses static source discovery so it can run without compiling the document. This covers conventional literal paths in common LaTeX commands. Paths assembled through custom macros, generated during compilation, or selected only through TeX conditionals cannot be inferred; add those files with `--include`.

Flattening changes every dependency to its basename. If two used files have the same basename, UploadAssist stops with an actionable error; rename one file or use `--noflatten`. Always compile and inspect the generated bundle before submitting it.

## Development

```console
python -m pip install -e ".[dev]"
ruff check uploadassist tests examples
ruff format --check uploadassist tests examples
python -m pytest
python -m build
python -m twine check dist/*
```

Bug reports are welcome in the [issue tracker](https://github.com/cvanelteren/UploadAssist/issues).
Maintainers can use the [release checklist](RELEASING.md) for PyPI publishing.

## License

UploadAssist is distributed under the BSD 3-Clause License. See [LICENSE](LICENSE).
