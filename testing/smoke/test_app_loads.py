"""
Smoke Test 1: App loads correctly and Phase 1 UI is visible.
"""
import pytest
from playwright.sync_api import expect
from testing.conftest import AppPage


def test_page_title(app: AppPage) -> None:
    """The browser tab title contains the app name."""
    expect(app.page).to_have_title("HR Screening Workbench")


def test_phase1_header_visible(app: AppPage) -> None:
    """Phase 1 header is shown on initial load."""
    assert app.is_phase("phase 1"), f"Expected Phase 1, got: {app.current_phase_header()}"


def test_resume_uploader_visible(app: AppPage) -> None:
    """Resume file uploader widget is present on Phase 1."""
    expect(app.page.get_by_text("Upload Resume/CV")).to_be_visible()


def test_jd_uploader_visible(app: AppPage) -> None:
    """Job Description file uploader widget is present on Phase 1."""
    expect(app.page.get_by_text("Upload Job Description")).to_be_visible()


def test_resume_text_area_visible(app: AppPage) -> None:
    """Resume Text text area is visible on Phase 1."""
    ta = app.page.get_by_label("Resume Text")
    expect(ta).to_be_visible()


def test_jd_text_area_visible(app: AppPage) -> None:
    """JD Text text area is visible on Phase 1."""
    ta = app.page.get_by_label("JD Text")
    expect(ta).to_be_visible()


def test_mandatory_rule_notes_visible(app: AppPage) -> None:
    """Mandatory Rule Notes area is visible on Phase 1."""
    ta = app.page.get_by_placeholder("Example: Tableau must be at least 24 months", exact=False)
    expect(ta).to_be_visible()


def test_extract_button_visible(app: AppPage) -> None:
    """Extract With AI button is present on Phase 1."""
    btn = app.page.get_by_role("button", name="Extract With AI")
    expect(btn).to_be_visible()


def test_load_sample_button_visible(app: AppPage) -> None:
    """Load Sample Case sidebar button is present."""
    btn = app.page.get_by_role("button", name="Load Sample Case")
    expect(btn).to_be_visible()


def test_reset_button_visible(app: AppPage) -> None:
    """Reset Application button is present in the header area."""
    btn = app.page.get_by_role("button", name="Reset Application")
    expect(btn).to_be_visible()


def test_no_error_on_load(app: AppPage) -> None:
    """No Streamlit error alert is shown on initial load."""
    errors = app.page.locator("[data-testid='stAlert'][kind='error']")
    expect(errors).to_have_count(0)
