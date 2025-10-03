"""
Example: Using uploadassist to flatten a LaTeX project for journal submission.

This script demonstrates how to use the uploadassist package to collect and flatten
all files required for a LaTeX project, updating paths in the .tex files so that
all dependencies are at the same directory level.

Usage:
    python flatten_example.py

Requirements:
    - uploadassist package must be installed and available in PYTHONPATH.
    - Example assumes a LaTeX project structure in 'sample_project/'.

Creates:
    - 'flattened_output/' directory with all files at the same level and updated .tex paths.
"""

import os
from pathlib import Path
from uploadassist.deps import collect

# Example LaTeX project directory
PROJECT_DIR = Path("sample_project")
MAIN_TEX = PROJECT_DIR / "main.tex"
OUTPUT_DIR = Path("flattened_output")


def main():
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Collect and flatten the project
    collected_files = collect(
        main_tex=str(MAIN_TEX),
        output_dir=str(OUTPUT_DIR),
        flatten=True,  # Flatten is enabled by default in CLI, explicit here for clarity
        latexmk_path="latexmk",
        engine="pdflatex",
        exclude=None,
    )

    print("Flattened files:")
    for f in collected_files:
        print(f"  - {f}")

    print("\nCheck the flattened_output/ directory for your ready-to-upload files.")


if __name__ == "__main__":
    main()
