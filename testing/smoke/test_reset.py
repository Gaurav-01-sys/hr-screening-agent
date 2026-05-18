"""
Smoke Test 3: Wiping data via the Reset Application button.
"""
import pytest
from playwright.sync_api import expect
from testing.conftest import AppPage


def test_reset_button_wipes_inputs(app: AppPage) -> None:
    """Clicking 'Reset Application' wipes text fields and returns to Ingest."""
    # First load some sample case to populate text
    app.click_load_sample()
    app.wait_for_phase("Phase 2")

    # Now click reset
    app.click_reset()

    # Should be back to Ingest
    app.wait_for_phase("Phase 1")

    # Fields should be empty
    expect(app.page.get_by_label("Resume Text")).to_have_value("")
    expect(app.page.get_by_label("JD Text")).to_have_value("")
    expect(app.page.get_by_placeholder("Example: Tableau must be at least 24 months", exact=False)).to_have_value("")
