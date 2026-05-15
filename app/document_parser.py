import os
from pathlib import Path
from io import BytesIO
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

def _extract_with_docling(file_name: str, file_bytes: bytes) -> str:
    try:
        from docling.datamodel.base_models import DocumentStream
        from docling.document_converter import DocumentConverter
    except ImportError:
        return ""

    try:
        stream = DocumentStream(name=file_name, stream=BytesIO(file_bytes))
        result = DocumentConverter().convert(stream)
        return _normalize_text(result.document.export_to_markdown())
    except Exception as e:
        print(f"Docling extraction failed: {e}")
        return ""

def _extract_pdf_text(file_name: str, file_bytes: bytes) -> str:
    # Try pypdf first because it is extremely fast
    try:
        from pypdf import PdfReader
        reader = PdfReader(BytesIO(file_bytes))
        parts = [page.extract_text() or "" for page in reader.pages]
        pypdf_text = _normalize_text("\n\n".join(parts))
        
        # If pypdf successfully extracted a reasonable amount of text, return it
        if len(pypdf_text) > 100:
            return pypdf_text
    except Exception as e:
        print(f"pypdf extraction failed: {e}")

    # Fallback to docling for complex or image-based PDFs (slower)
    print("Falling back to Docling for complex PDF extraction...")
    docling_text = _extract_with_docling(file_name, file_bytes)
    if docling_text:
        return docling_text
        
    return ""

def _extract_docx_text(file_bytes: bytes) -> str:
    from docx import Document
    document = Document(BytesIO(file_bytes))
    parts = [paragraph.text for paragraph in document.paragraphs if paragraph.text.strip()]
    return _normalize_text("\n".join(parts))

def extract_uploaded_text(file_name: str, file_bytes: bytes) -> str:
    suffix = Path(file_name).suffix.lower()
    if suffix == ".pdf":
        return _extract_pdf_text(file_name, file_bytes)
    if suffix == ".docx":
        return _extract_docx_text(file_bytes)
    raise ValueError(f"Unsupported file type: {suffix or 'unknown'}")
