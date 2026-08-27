from __future__ import annotations

from pathlib import Path

from app.document_parser import extract_uploaded_text


def test_pdfium_extracts_selectable_pdf_text() -> None:
    project_root = Path(__file__).resolve().parents[2]
    sample_pdf = project_root / "sample_cv.pdf"

    text = extract_uploaded_text(sample_pdf.name, sample_pdf.read_bytes())

    assert "Riya Sharma" in text
    assert "Professional Summary" in text


def test_invalid_pdf_returns_no_text() -> None:
    assert extract_uploaded_text("broken.pdf", b"not-a-real-pdf") == ""
