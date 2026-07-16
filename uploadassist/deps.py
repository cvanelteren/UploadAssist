"""Discover and package local dependencies of a LaTeX document."""

from __future__ import annotations

import re
import shutil
import tarfile
import tempfile
from pathlib import Path
from typing import Iterable, List, Optional, Set


_INPUT_RE = re.compile(r"\\(?:input|include|subfile)\s*\{([^}]+)\}")
_IMPORT_RE = re.compile(
    r"\\(?:import|subimport|inputfrom|includefrom)\s*\{([^}]+)\}\s*\{([^}]+)\}"
)
_GRAPHICS_RE = re.compile(r"\\includegraphics\s*(?:\[[^]]*\]\s*)?\{([^}]+)\}")
_GRAPHICSPATH_RE = re.compile(r"\\graphicspath\s*\{((?:\s*\{[^}]*\}\s*)+)\}")
_BIB_RE = re.compile(r"\\bibliography\s*\{([^}]+)\}")
_ADDBIB_RE = re.compile(r"\\addbibresource\s*(?:\[[^]]*\]\s*)?\{([^}]+)\}")
_BIBSTYLE_RE = re.compile(r"\\bibliographystyle\s*\{([^}]+)\}")
_PACKAGE_RE = re.compile(r"\\usepackage\s*(?:\[[^]]*\]\s*)?\{([^}]+)\}")
_CLASS_RE = re.compile(r"\\documentclass\s*(?:\[[^]]*\]\s*)?\{([^}]+)\}")


def strip_comments(content: str) -> str:
    """Remove unescaped LaTeX comments while preserving escaped percent signs."""
    result = []
    verbatim_environment = None
    for line in content.splitlines(keepends=True):
        if verbatim_environment:
            result.append(line)
            if rf"\end{{{verbatim_environment}}}" in line:
                verbatim_environment = None
            continue
        begin = re.search(r"\\begin\{(verbatim\*?|Verbatim|lstlisting|minted)\}", line)
        if begin:
            verbatim_environment = begin.group(1)
            result.append(line)
            if rf"\end{{{verbatim_environment}}}" in line[begin.end() :]:
                verbatim_environment = None
            continue

        protected = []
        for match in re.finditer(r"\\verb\*?(.)", line):
            delimiter = match.group(1)
            end = line.find(delimiter, match.end())
            if end != -1:
                protected.append((match.start(), end + 1))
        for index, char in enumerate(line):
            if char != "%" or any(start <= index < end for start, end in protected):
                continue
            backslashes = 0
            cursor = index - 1
            while cursor >= 0 and line[cursor] == "\\":
                backslashes += 1
                cursor -= 1
            if backslashes % 2 == 0:
                newline = "\n" if line.endswith("\n") else ""
                line = line[:index].rstrip() + newline
                break
        result.append(line)
    return "".join(result)


_strip_comments = strip_comments


def _discovery_content(content: str) -> str:
    content = strip_comments(content)
    content = re.sub(
        r"\\begin\{(verbatim\*?|Verbatim|lstlisting|minted)\}.*?\\end\{\1\}",
        "",
        content,
        flags=re.DOTALL,
    )
    return re.sub(r"\\verb\*?(?P<delimiter>[^\s]).*?(?P=delimiter)", "", content)


def _resolve(
    value: str,
    directories: Iterable[Path],
    extensions: Iterable[str],
) -> Optional[Path]:
    value = value.strip()
    if not value or any(token in value for token in ("\\", "#")):
        return None
    candidate = Path(value).expanduser()
    suffixes = ("",) if candidate.suffix else tuple(extensions)
    for directory in directories:
        base = candidate if candidate.is_absolute() else directory / candidate
        for suffix in suffixes:
            path = Path(f"{base}{suffix}").resolve()
            if path.is_file():
                return path
    return None


def get_deps(
    main_tex: str, latexmk_path: str = "latexmk", engine: str = "pdflatex"
) -> Set[str]:
    """Return local files referenced recursively by *main_tex*.

    ``latexmk_path`` and ``engine`` remain accepted for API compatibility. Discovery is
    intentionally static, so packaging works without a TeX installation and never
    includes unrelated build artifacts.
    """
    del latexmk_path, engine
    main = Path(main_tex).expanduser().resolve()
    if not main.is_file():
        raise FileNotFoundError(f"Main TeX file does not exist: {main_tex}")
    if main.suffix.lower() != ".tex":
        raise ValueError(f"Main document must be a .tex file: {main_tex}")

    project_root = main.parent
    dependencies: Set[Path] = set()
    visited: Set[Path] = set()

    def required(
        value: str, directories: Iterable[Path], extensions: Iterable[str], kind: str
    ) -> Path:
        dependency = _resolve(value, directories, extensions)
        if dependency is None:
            raise FileNotFoundError(f"Referenced {kind} file not found: {value}")
        return dependency

    def parse_tex(tex_path: Path) -> None:
        tex_path = tex_path.resolve()
        if tex_path in visited:
            return
        visited.add(tex_path)
        dependencies.add(tex_path)
        content = _discovery_content(tex_path.read_text(encoding="utf-8"))
        source_dir = tex_path.parent

        graphics_dirs = [source_dir]
        for match in _GRAPHICSPATH_RE.finditer(content):
            for value in re.findall(r"\{([^}]*)\}", match.group(1)):
                graphics_dirs.append((source_dir / value).resolve())

        for value in _INPUT_RE.findall(content):
            dependency = required(value, (source_dir, project_root), (".tex",), "input")
            parse_tex(dependency)

        for directory, value in _IMPORT_RE.findall(content):
            dependency = required(
                value,
                ((source_dir / directory).resolve(),),
                (".tex",),
                "import",
            )
            parse_tex(dependency)

        for value in _GRAPHICS_RE.findall(content):
            dependency = required(
                value,
                (*graphics_dirs, project_root),
                (".pdf", ".png", ".jpg", ".jpeg", ".eps", ".svg", ".mps"),
                "graphics",
            )
            dependencies.add(dependency)

        bib_values = list(_ADDBIB_RE.findall(content))
        bib_values.extend(
            item for group in _BIB_RE.findall(content) for item in group.split(",")
        )
        for value in bib_values:
            dependency = required(
                value, (source_dir, project_root), (".bib",), "bibliography"
            )
            dependencies.add(dependency)
        if bib_values:
            bbl = main.with_suffix(".bbl")
            if bbl.is_file():
                dependencies.add(bbl)
        for value in _BIBSTYLE_RE.findall(content):
            dependency = _resolve(value, (source_dir, project_root), (".bst",))
            if dependency:
                dependencies.add(dependency)

        local_modules = [
            (value, ".sty")
            for group in _PACKAGE_RE.findall(content)
            for value in group.split(",")
        ]
        local_modules.extend((value, ".cls") for value in _CLASS_RE.findall(content))
        for value, extension in local_modules:
            dependency = _resolve(value, (source_dir, project_root), (extension,))
            if dependency:
                parse_tex(dependency)

    parse_tex(main)
    return {str(path) for path in dependencies}


def add(file_set: Set[str], file_path: str, exclude: Optional[Set[str]] = None) -> None:
    """Add *file_path* unless explicitly excluded (legacy public helper)."""
    if not exclude or file_path not in exclude:
        file_set.add(file_path)


def _flatten_content(content: str) -> str:
    def basename(match: re.Match[str]) -> str:
        return f"{match.group(1)}{Path(match.group(2)).name}}}"

    patterns = (
        re.compile(r"(\\includegraphics\s*(?:\[[^]]*\]\s*)?\{)([^}]+)\}"),
        re.compile(r"(\\(?:input|include|subfile)\s*\{)([^}]+)\}"),
        re.compile(r"(\\addbibresource\s*(?:\[[^]]*\]\s*)?\{)([^}]+)\}"),
        re.compile(r"(\\documentclass\s*(?:\[[^]]*\]\s*)?\{)([^}]+)\}"),
        re.compile(r"(\\bibliographystyle\s*\{)([^}]+)\}"),
    )
    for pattern in patterns:
        content = pattern.sub(basename, content)
    content = _PACKAGE_RE.sub(
        lambda match: match.group(0).replace(
            match.group(1),
            ",".join(Path(value.strip()).name for value in match.group(1).split(",")),
        ),
        content,
    )
    content = _BIB_RE.sub(
        lambda match: (
            "\\bibliography{"
            + ",".join(Path(value.strip()).name for value in match.group(1).split(","))
            + "}"
        ),
        content,
    )
    content = _IMPORT_RE.sub(
        lambda match: rf"\input{{{Path(match.group(2)).name}}}", content
    )
    content = _GRAPHICSPATH_RE.sub("", content)
    return content


def flatten_tex_paths(tex_path: str, output_dir: str) -> None:
    """Rewrite a copied TeX file so its references point to flat basenames."""
    path = Path(tex_path)
    output_path = Path(output_dir) / path.name
    output_path.write_text(
        _flatten_content(path.read_text(encoding="utf-8")), encoding="utf-8"
    )


def _additional_files(paths: Optional[List[str]]) -> Set[Path]:
    files: Set[Path] = set()
    for raw_path in paths or []:
        path = Path(raw_path).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"Additional path does not exist: {raw_path}")
        if path.is_dir():
            files.update(item.resolve() for item in path.rglob("*") if item.is_file())
        else:
            files.add(path)
    return files


def collect(
    main_tex: str,
    output_dir: str,
    flatten: bool = False,
    latexmk_path: str = "latexmk",
    engine: str = "pdflatex",
    exclude: Optional[Set[str]] = None,
    strip_comments: bool = True,
    include_packages: Optional[List[str]] = None,
    create_archive: bool = True,
) -> List[str]:
    """Collect a document and its local dependencies into a clean output tree."""
    main = Path(main_tex).expanduser().resolve()
    project_root = main.parent
    output = Path(output_dir).expanduser().absolute()
    archive = Path(f"{output}.tar.gz")
    if output == project_root or output == main or output in main.parents:
        raise ValueError("Output must not replace the source project or main TeX file")

    excluded = {str(Path(path).expanduser().resolve()) for path in (exclude or set())}
    sources = {Path(path) for path in get_deps(str(main), latexmk_path, engine)}
    sources.update(_additional_files(include_packages))
    sources = {path for path in sources if str(path.resolve()) not in excluded}

    destinations = {}
    for source in sorted(sources):
        if flatten:
            relative = Path(source.name)
        else:
            try:
                relative = source.relative_to(project_root)
            except ValueError:
                relative = Path(source.name)
        if relative in destinations and destinations[relative] != source:
            raise ValueError(
                f"Cannot flatten files with the same name: {destinations[relative]} and {source}"
            )
        destinations[relative] = source

    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output.name}-", dir=output.parent))
    try:
        for relative, source in destinations.items():
            destination = staging / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            if source.suffix.lower() in {".tex", ".sty", ".cls"}:
                content = source.read_text(encoding="utf-8")
                if strip_comments and source.suffix.lower() == ".tex":
                    content = _strip_comments(content)
                if flatten:
                    content = _flatten_content(content)
                destination.write_text(content, encoding="utf-8")
                shutil.copystat(source, destination)
            else:
                shutil.copy2(source, destination)

        if output.exists():
            if output.is_symlink():
                raise ValueError(
                    f"Refusing to replace symlinked output directory: {output}"
                )
            if not output.is_dir():
                raise FileExistsError(
                    f"Output path exists and is not a directory: {output}"
                )
            shutil.rmtree(output)
        staging.replace(output)
        staging = None

        if create_archive:
            with tarfile.open(archive, "w:gz") as tar:
                tar.add(output, arcname=output.name)
        elif archive.exists():
            archive.unlink()
    finally:
        if staging is not None:
            shutil.rmtree(staging, ignore_errors=True)

    return [str(output / relative) for relative in sorted(destinations)]
