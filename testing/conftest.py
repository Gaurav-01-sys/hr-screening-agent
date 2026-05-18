"""
Shared Playwright fixtures for the HR Screening test suite.
"""
from __future__ import annotations

import pytest
from pathlib import Path
from playwright.sync_api import Page, expect

# ---------------------------------------------------------------------------
# Paths to test fixtures
# ---------------------------------------------------------------------------
FIXTURES_DIR = Path(__file__).parent.parent  # project root
SAMPLE_CV_PATH = FIXTURES_DIR / "sample_cv.pdf"
SAMPLE_JD_PATH = FIXTURES_DIR / "sample_jd.pdf"


# ---------------------------------------------------------------------------
# Helpers shared across tests
# ---------------------------------------------------------------------------
class AppPage:
    """Thin wrapper around a Playwright Page with HR-app-specific helpers."""

    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------
    def goto(self) -> None:
        self.page.goto(self.base_url)
        self.wait_for_streamlit()

    def wait_for_streamlit(self, timeout: int = 20_000) -> None:
        """Wait until Streamlit has finished rendering (spinner gone)."""
        self.page.wait_for_load_state("networkidle", timeout=timeout)
        # Streamlit shows a top progress bar while loading; wait for it to go
        self.page.wait_for_selector(
            "div[data-testid='stAppViewContainer']", timeout=timeout
        )

    # ------------------------------------------------------------------
    # Phase detection
    # ------------------------------------------------------------------
    def current_phase_header(self) -> str:
        # Streamlit main body headers are inside section.main
        h2 = self.page.locator("section.main h2").first
        if h2.count() > 0:
            return h2.inner_text()
        return ""

    def is_phase(self, label: str) -> bool:
        header = self.current_phase_header()
        return label.lower() in header.lower()

    # ------------------------------------------------------------------
    # Phase 1 helpers
    # ------------------------------------------------------------------
    def upload_resume(self) -> None:
        locator = self.page.get_by_label("Upload Resume/CV")
        locator.set_input_files(str(SAMPLE_CV_PATH))
        self.wait_for_streamlit()

    def upload_jd(self) -> None:
        locator = self.page.get_by_label("Upload Job Description")
        locator.set_input_files(str(SAMPLE_JD_PATH))
        self.wait_for_streamlit()

    def fill_resume_text(self, text: str) -> None:
        self.page.get_by_label("Resume Text").fill(text)

    def fill_jd_text(self, text: str) -> None:
        self.page.get_by_label("JD Text").fill(text)

    def fill_rule_notes(self, text: str) -> None:
        self.page.get_by_role("textbox", name="Mandatory Rule Notes").fill(text)

    def click_load_sample(self) -> None:
        self.page.get_by_role("button", name="Load Sample Case").click()
        self.wait_for_streamlit()

    def click_extract_with_ai(self) -> None:
        self.page.get_by_role("button", name="Extract With AI").click()
        # AI call can take up to 60 s
        self.wait_for_streamlit(timeout=60_000)

    # ------------------------------------------------------------------
    # Phase 2 helpers
    # ------------------------------------------------------------------
    def click_back_to_ingest(self) -> None:
        self.page.get_by_role("button", name="Back to Ingest").click()
        self.wait_for_streamlit()

    def click_run_final_screening(self) -> None:
        self.page.get_by_role("button", name="Run Final Screening").click()
        self.wait_for_streamlit()

    # ------------------------------------------------------------------
    # Global
    # ------------------------------------------------------------------
    def click_reset(self) -> None:
        self.page.get_by_role("button", name="Reset Application").click()
        self.wait_for_streamlit()

    def click_start_new_screening(self) -> None:
        self.page.get_by_role("button", name="Start New Screening").click()
        self.wait_for_streamlit()


# ---------------------------------------------------------------------------
# Pytest fixtures
# ---------------------------------------------------------------------------
@pytest.fixture()
def app(page: Page, base_url: str) -> AppPage:
    """Return a fresh AppPage already navigated to Phase 1."""
    ap = AppPage(page, base_url)
    ap.goto()
    return ap


@pytest.fixture()
def app_with_sample(app: AppPage) -> AppPage:
    """Navigate to Phase 2 using the Load Sample Case shortcut."""
    app.click_load_sample()
    return app
