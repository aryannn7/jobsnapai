"""
core/parsing.py

Convert resume files into plain text.

Contract:
- No exceptions leak to app.py.
- parse_resume returns: (file_type, extracted_text, error_message)
"""

from __future__ import annotations

import io
from typing import Optional, Tuple

import fitz  # PyMuPDF
from docx import Document


def extract_text_from_pdf(file_bytes: bytes) -> Tuple[Optional[str], Optional[str]]:
    try:
        pdf_document = fitz.open(stream=file_bytes, filetype="pdf")
        text_blocks = []
        for page in pdf_document:
            text_blocks.append(page.get_text("text"))
        return "\n".join(text_blocks).strip(), None
    except Exception as e:
        return None, f"Failed to read PDF: {type(e).__name__}: {e}"


def extract_text_from_docx(file_bytes: bytes) -> Tuple[Optional[str], Optional[str]]:
    try:
        buffer = io.BytesIO(file_bytes)
        document = Document(buffer)
        paragraphs = [p.text.strip() for p in document.paragraphs if p.text and p.text.strip()]
        return "\n".join(paragraphs).strip(), None
    except Exception as e:
        return None, f"Failed to read DOCX: {type(e).__name__}: {e}"


def parse_resume(filename: str, file_bytes: bytes) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Returns:
        (file_type, extracted_text, error_message)
    """
    try:
        name = (filename or "").lower().strip()

        if name.endswith(".pdf"):
            text, err = extract_text_from_pdf(file_bytes)
            return "pdf", text, err

        if name.endswith(".docx"):
            text, err = extract_text_from_docx(file_bytes)
            return "docx", text, err

        return None, None, "Unsupported file format. Please upload PDF or DOCX."
    except Exception as e:
        return None, None, f"Resume parsing failed: {type(e).__name__}: {e}"
