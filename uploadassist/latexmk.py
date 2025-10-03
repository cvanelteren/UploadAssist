"""
latexmk.py

Functions and classes for interacting with latexmk and TeX engine options.
"""

import subprocess
import re
import os
from urllib.request import urlopen


class LatexmkException(Exception):
    """Custom exception for latexmk-related errors."""

    pass


def get_latexmk_engine_opts(engine: str):
    """
    Returns the latexmk options for the specified TeX engine.
    Supported engines: pdflatex, xelatex, lualatex.
    """
    engine_opts = {
        "pdflatex": ["-pdf"],
        "xelatex": ["-pdfxe"],
        "lualatex": ["-pdflua"],
    }
    if engine not in engine_opts:
        raise ValueError(f"Unsupported engine: {engine}")
    return engine_opts[engine]


def get_latexmk(latexmk_path="latexmk"):
    """
    Returns the path to latexmk, downloading it if necessary.
    """
    if os.path.isfile(latexmk_path) and os.access(latexmk_path, os.X_OK):
        return latexmk_path
    # Try to find latexmk in PATH
    for path in os.environ.get("PATH", "").split(os.pathsep):
        candidate = os.path.join(path, "latexmk")
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    raise LatexmkException("latexmk not found on PATH or at specified location.")


def get_latexmk_version(latexmk_path="latexmk"):
    """
    Returns the version string of latexmk.
    """
    try:
        output = subprocess.check_output([latexmk_path, "-v"], universal_newlines=True)
        match = re.search(r"Latexmk, John Collins, version: ([\d\.a-zA-Z]+)", output)
        if match:
            return match.group(1)
        else:
            raise LatexmkException("Could not parse latexmk version output.")
    except Exception as e:
        raise LatexmkException(f"Error getting latexmk version: {e}")


def download_latexmk(url, dest_path):
    """
    Downloads latexmk from a given URL to the destination path.
    """
    try:
        response = urlopen(url)
        with open(dest_path, "wb") as f:
            f.write(response.read())
    except Exception as e:
        raise LatexmkException(f"Failed to download latexmk: {e}")
