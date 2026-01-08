"""
core/cleaning.py

This module cleans raw extracted text.

Why cleaning matters:
- PDF extraction is noisy.
- Clean text improves matching accuracy later.
"""

import re


def clean_text(text: str) -> str:
    """
    Clean and normalize text.

    Steps:
    1. Remove null characters.
    2. Replace multiple spaces with one.
    3. Reduce excessive blank lines.
    """
    if not text:
        return ""

    # Remove invisible null characters
    text = text.replace("\x00", " ")

    # Replace multiple spaces or tabs with a single space
    text = re.sub(r"[ \t]+", " ", text)

    # Replace 3 or more newlines with exactly 2
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()
