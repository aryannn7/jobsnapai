# core/parsing.py
from __future__ import annotations

import io
from typing import Optional, Tuple

import fitz  # PyMuPDF
from docx import Document


def extract_text_from_pdf(file_bytes: bytes) -> str:
    pdf_document = fitz.open(stream=file_bytes, filetype="pdf")
    blocks = []
    for page in pdf_document:
        blocks.append(page.get_text("text") or "")
    return "\n".join(blocks).strip()


def extract_text_from_docx(file_bytes: bytes) -> str:
    buffer = io.BytesIO(file_bytes)
    document = Document(buffer)
    paragraphs = [p.text.strip() for p in document.paragraphs if (p.text or "").strip()]
    return "\n".join(paragraphs).strip()


def parse_resume(filename: str, file_bytes: bytes) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Deterministic + failure-proof.
    Returns:
      (file_type, extracted_text, error_message)

    Never raises.
    """
    try:
        name = (filename or "").lower().strip()
        if not name:
            return None, None, "Missing filename."

        if name.endswith(".pdf"):
            try:
                text = extract_text_from_pdf(file_bytes)
                return "pdf", text, None
            except Exception as e:
                return "pdf", None, f"Failed to parse PDF: {type(e).__name__}: {e}"

        if name.endswith(".docx"):
            try:
                text = extract_text_from_docx(file_bytes)
                return "docx", text, None
            except Exception as e:
                return "docx", None, f"Failed to parse DOCX: {type(e).__name__}: {e}"

        return None, None, "Unsupported file format. Please upload PDF or DOCX."

    except Exception as e:
        return None, None, f"Resume parsing failed: {type(e).__name__}: {e}"
