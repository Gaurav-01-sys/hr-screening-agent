"""
E2E Test 1: Uploading PDF files (sample_cv.pdf and sample_jd.pdf) and verifying text population.
"""
import pytest
from playwright.sync_api import expect
from testing.conftest import AppPage


def test_pdf_upload_populates_text_areas(app: AppPage) -> None:
    """Uploading sample_cv.pdf and sample_jd.pdf should trigger text extraction and populate text areas."""
    assert app.is_phase("phase 1")

    # Upload CV
    app.upload_resume()
    
    # Wait and verify that the Resume Text area is populated (not empty)
    resume_text_area = app.page.get_by_label("Resume Text")
    expect(resume_text_area).not_to_have_value("")
    
    # Check that extracted text contains key words from our sample CV
    expect(resume_text_area).to_contain_text("Riya Sharma")

    # Upload JD
    app.upload_jd()

    # Wait and verify that the JD Text area is populated
    jd_text_area = app.page.get_by_label("JD Text")
    expect(jd_text_area).not_to_have_value("")
    
    # Check that extracted text contains key words from our sample JD
    expect(jd_text_area).to_contain_text("Business Intelligence Analyst")
