from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import List


def _normalize_text(text: str) -> str:
    cleaned_lines = [line.rstrip() for line in text.splitlines()]
    normalized: List[str] = []
    previous_blank = False

    for line in cleaned_lines:
        is_blank = not line.strip()
        if is_blank and previous_blank:
            continue
        normalized.append(line)
        previous_blank = is_blank

    return "\n".join(normalized).strip()


def _extract_pdf_text(file_bytes: bytes) -> str:
    """Extract selectable PDF text with PDFium, preserving page order."""
    try:
        import pypdfium2 as pdfium
    except ImportError as exc:
        raise RuntimeError(
            "PDF parsing requires pypdfium2; install the project requirements."
        ) from exc

    try:
        document = pdfium.PdfDocument(file_bytes)
    except Exception as exc:
        print(f"PDFium extraction failed: {exc}")
        return ""
    page_texts: List[str] = []
    try:
        for page_index in range(len(document)):
            page = document[page_index]
            text_page = page.get_textpage()
            try:
                page_texts.append(text_page.get_text_range())
            finally:
                text_page.close()
                page.close()
    finally:
        document.close()

    return _normalize_text("\n\n".join(page_texts))


def _extract_docx_text(file_bytes: bytes) -> str:
    from docx import Document

    document = Document(BytesIO(file_bytes))
    parts = [paragraph.text for paragraph in document.paragraphs if paragraph.text.strip()]
    return _normalize_text("\n".join(parts))


def extract_uploaded_text(file_name: str, file_bytes: bytes) -> str:
    suffix = Path(file_name).suffix.lower()
    if suffix == ".pdf":
        return _extract_pdf_text(file_bytes)
    if suffix == ".docx":
        return _extract_docx_text(file_bytes)
    raise ValueError(f"Unsupported file type: {suffix or 'unknown'}")
