"""
Dependency tracking and file collection logic for uploadassist.

Includes logic to flatten project structure for journal submission,
updating LaTeX source paths to match the flattened layout.

This module provides functions to analyze LaTeX projects, determine file dependencies,
and collect all necessary files for packaging and submission.

Functions:
    get_deps: Analyze a LaTeX project and return a list of required files.
    collect: Collect all files needed for submission, optionally flattening the structure.
    add: Helper to add files to the collection, handling duplicates and exclusions.
"""

import os
import shutil
from typing import List, Dict, Set, Optional


def get_deps(
    main_tex: str, latexmk_path: str = "latexmk", engine: str = "pdflatex"
) -> Set[str]:
    """
    Recursively analyze the LaTeX project and return a set of all files required for compilation.

    Args:
        main_tex (str): Path to the main .tex file.
        latexmk_path (str): Path to the latexmk executable.
        engine (str): TeX engine to use ("pdflatex", "xelatex", "lualatex").

    Returns:
        Set[str]: Set of file paths required for the project.
    """
    # Recursively parse all .tex files for dependencies
    deps = set()
    visited = set()

    def parse_tex(tex_path):
        if tex_path in visited or not os.path.isfile(tex_path):
            return
        visited.add(tex_path)
        deps.add(tex_path)
        with open(tex_path, "r", encoding="utf-8") as f:
            content = f.read()
        # Find \input, \include, \includegraphics
        input_patterns = [
            r"\\(?:input|include)\{([^\}]+)\}",
            r"\\includegraphics(?:\[[^\]]*\])?\{([^\}]+)\}",
        ]
        for pattern in input_patterns:
            for match in re.findall(pattern, content):
                # Remove any extension for \input/\include if not present
                candidate = match
                # Try .tex for input/include if not present
                if pattern.startswith(
                    r"\\(?:input|include)"
                ) and not candidate.endswith(".tex"):
                    candidate += ".tex"
                # Search for file relative to current tex_path
                candidate_path = os.path.join(os.path.dirname(tex_path), candidate)
                if os.path.isfile(candidate_path):
                    parse_tex(candidate_path)
                    deps.add(candidate_path)
                else:
                    # For graphics, try common extensions
                    if pattern.startswith(r"\\includegraphics"):
                        for ext in [".png", ".jpg", ".jpeg", ".pdf"]:
                            candidate_graphic = (
                                candidate
                                if candidate.lower().endswith(ext)
                                else candidate + ext
                            )
                            candidate_path = os.path.join(
                                os.path.dirname(tex_path), candidate_graphic
                            )
                            if os.path.isfile(candidate_path):
                                deps.add(candidate_path)
                                break

    parse_tex(main_tex)
    # Also add any .bib, .sty, .cls files in the main directory and subdirectories
    main_dir = os.path.dirname(os.path.abspath(main_tex))
    for root, dirs, files in os.walk(main_dir):
        for fname in files:
            if fname.endswith((".bib", ".sty", ".cls")):
                deps.add(os.path.join(root, fname))
    return deps


def add(file_set: Set[str], file_path: str, exclude: Optional[Set[str]] = None) -> None:
    """
    Add a file to the set of collected files, unless it is excluded.

    Args:
        file_set (Set[str]): The set of files being collected.
        file_path (str): The file to add.
        exclude (Optional[Set[str]]): Set of files to exclude.
    """
    if exclude and file_path in exclude:
        return
    file_set.add(file_path)


from pathlib import Path
import re


def flatten_tex_paths(tex_path, output_dir):
    """
    Update LaTeX source file paths for includes and graphics so all referenced files
    are at the same directory level. Writes the updated file to output_dir.
    """
    with open(tex_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Patterns for includegraphics, input, include
    patterns = [
        r"(\\includegraphics(?:\[[^\]]*\])?\{)([^}]+)\}",
        r"(\\input\{)([^}]+)\}",
        r"(\\include\{)([^}]+)\}",
    ]

    def replacer(match):
        prefix, path = match.groups()
        filename = Path(path).name
        return f"{prefix}{filename}" + "}"

    for pattern in patterns:
        content = re.sub(pattern, replacer, content)

    # Overwrite the file in the output directory
    output_path = Path(output_dir) / Path(tex_path).name
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)


def collect(
    main_tex: str,
    output_dir: str,
    flatten: bool = False,
    latexmk_path: str = "latexmk",
    engine: str = "pdflatex",
    exclude: Optional[Set[str]] = None,
) -> List[str]:
    """
    Collect all files needed for submission, copying them to output_dir.
    Optionally flatten the directory structure and update LaTeX source paths.

    Args:
        main_tex (str): Path to the main .tex file.
        output_dir (str): Directory to copy files into.
        flatten (bool): If True, copy all files into a single directory and update paths.
        latexmk_path (str): Path to latexmk executable.
        engine (str): TeX engine to use.
        exclude (Optional[Set[str]]): Set of files to exclude.

    Returns:
        List[str]: List of files copied to output_dir.
    """
    deps = get_deps(main_tex, latexmk_path, engine)
    collected = []

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Map from original path to flattened path
    flatten_map = {}

    for fpath in deps:
        if exclude and fpath in exclude:
            continue
        if flatten:
            dest_path = os.path.join(output_dir, os.path.basename(fpath))
            flatten_map[fpath] = dest_path
        else:
            rel_path = os.path.relpath(fpath, os.path.dirname(main_tex))
            dest_path = os.path.join(output_dir, rel_path)
            dest_dir = os.path.dirname(dest_path)
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)
        shutil.copy2(fpath, dest_path)
        collected.append(dest_path)

    # If flattening, update all .tex files in output_dir to fix paths
    if flatten:
        for orig_path, flat_path in flatten_map.items():
            if orig_path.endswith(".tex"):
                flatten_tex_paths(flat_path, output_dir)
    return collected
    # If flattening, update all .tex files in output_dir to fix paths
    if flatten:
        for fpath in deps:
            if fpath.endswith(".tex"):
                flatten_tex_paths(fpath, output_dir)

    return collected
