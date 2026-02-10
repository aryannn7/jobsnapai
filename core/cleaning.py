"""
core/cleaning.py

Cleaning utilities:
- Preserve newlines so evidence snippets remain readable.
- Deterministic, lightweight, no heavy NLP.
"""

from __future__ import annotations

import re


def clean_text(text: str) -> str:
    if not text:
        return ""

    t = text.replace("\r\n", "\n").replace("\r", "\n")

    # normalize bullets into line breaks
    for b in ("•", "●", "▪"):
        t = t.replace(b, f"\n{b} ")

    t = t.replace("–", "-")

    cleaned_lines = []
    for line in t.split("\n"):
        line = re.sub(r"[ \t]+", " ", line.strip())
        if line:
            cleaned_lines.append(line)

    out = "\n".join(cleaned_lines)
    out = re.sub(r"\n{3,}", "\n\n", out).strip()
    return out
