"""
core/parsing.py

This module is responsible for converting resume files into plain text.

Why this exists:
- Resumes are uploaded as files (PDF or Word).
- Our system works on text, not files.
- So we extract text first, before doing anything else.
"""

import io
from typing import Tuple

import fitz  # PyMuPDF: used to read PDF files
from docx import Document  # python-docx: used to read Word documents


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract text from a PDF file.

    Parameters:
    file_bytes (bytes):
        The raw bytes of the uploaded PDF file.

    Returns:
    str:
        All text extracted from the PDF.
    """
    pdf_document = fitz.open(stream=file_bytes, filetype="pdf")

    text_blocks = []

    # Each PDF can have multiple pages
    for page in pdf_document:
        page_text = page.get_text("text")
        text_blocks.append(page_text)

    return "\n".join(text_blocks).strip()


def extract_text_from_docx(file_bytes: bytes) -> str:
    """
    Extract text from a Microsoft Word (.docx) file.

    Parameters:
    file_bytes (bytes):
    The raw bytes of the Word file.

    Returns:
    str:
    All text extracted from the document.
    
    """
    buffer = io.BytesIO(file_bytes)
    document = Document(buffer)

    paragraphs = []
    for paragraph in document.paragraphs:
        if paragraph.text.strip():
            paragraphs.append(paragraph.text)

    return "\n".join(paragraphs).strip()


def parse_resume(filename: str, file_bytes: bytes) -> Tuple[str, str]:
    """
    Decide which extraction method to use based on file type.
    Returns:
    (file_type, extracted_text)

    """
    filename = filename.lower()

    if filename.endswith(".pdf"):
        return "pdf", extract_text_from_pdf(file_bytes)

    if filename.endswith(".docx"):
        return "docx", extract_text_from_docx(file_bytes)

    raise ValueError("Unsupported file format. Please upload PDF or DOCX.")