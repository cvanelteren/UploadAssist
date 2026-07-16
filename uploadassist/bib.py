"""Small, dependency-free helpers for extracting cited BibTeX entries."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Dict

from .deps import _discovery_content


_CITE_RE = re.compile(
    r"\\(?:[A-Za-z]*cite[A-Za-z]*|nocite)\*?(?:\s*\[[^]]*\])*\s*\{([^}]*)\}"
)
_ENTRY_RE = re.compile(r"@[A-Za-z]+\s*([({])\s*([^,\s]+)\s*,", re.MULTILINE)


def _entries(content: str) -> Dict[str, str]:
    entries: Dict[str, str] = {}
    position = 0
    while True:
        match = _ENTRY_RE.search(content, position)
        if not match:
            break
        opening = match.group(1)
        closing = ")" if opening == "(" else "}"
        depth = 1
        brace_depth = 0
        cursor = match.end()
        in_quote = False
        escaped = False
        while cursor < len(content) and depth:
            char = content[cursor]
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_quote = not in_quote
            elif not in_quote:
                if opening == "(" and char == "{":
                    brace_depth += 1
                elif opening == "(" and char == "}" and brace_depth:
                    brace_depth -= 1
                elif char == opening:
                    depth += 1
                elif char == closing and not brace_depth:
                    depth -= 1
            cursor += 1
        if depth:
            raise ValueError(f"Unterminated BibTeX entry: {match.group(2)}")
        entries[match.group(2)] = content[match.start() : cursor].strip() + "\n"
        position = cursor
    return entries


def extract_bib(bib_file: str, tex_file: str) -> None:
    """Write entries cited by *tex_file* from *bib_file* to standard output."""
    tex_content = _discovery_content(Path(tex_file).read_text(encoding="utf-8"))
    citation_keys = {
        key.strip()
        for match in _CITE_RE.finditer(tex_content)
        for key in match.group(1).split(",")
        if key.strip() and key.strip() != "*"
    }
    entries = _entries(Path(bib_file).read_text(encoding="utf-8"))
    missing = sorted(citation_keys - entries.keys())
    if missing:
        print(
            f"Warning: missing bibliography entries: {', '.join(missing)}",
            file=sys.stderr,
        )
    for key in sorted(citation_keys):
        if key in entries:
            sys.stdout.write(entries[key])
