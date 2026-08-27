from __future__ import annotations

import json

from app import document_parser


class _Response:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload

    def __enter__(self) -> "_Response":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.payload


def test_ocrflux_remote_page_extracts_natural_text(monkeypatch) -> None:
    response = {
        "choices": [
            {
                "message": {
                    "content": '{"natural_text": "# Candidate\\n\\nOCRFlux output"}'
                }
            }
        ]
    }
    monkeypatch.setenv("OCRFLUX_URL", "http://localhost:30024")
    monkeypatch.setattr(
        document_parser.urllib_request,
        "urlopen",
        lambda *args, **kwargs: _Response(json.dumps(response).encode("utf-8")),
    )

    assert document_parser._ocrflux_remote_page(b"fake-png") == "# Candidate\n\nOCRFlux output"


def test_pdf_parser_keeps_text_fallback_when_ocrflux_is_unconfigured(monkeypatch) -> None:
    monkeypatch.delenv("OCRFLUX_URL", raising=False)
    monkeypatch.delenv("OCRFLUX_MODEL_PATH", raising=False)

    text = document_parser.extract_uploaded_text("sample_cv.pdf", b"not-a-real-pdf")

    assert text == ""
