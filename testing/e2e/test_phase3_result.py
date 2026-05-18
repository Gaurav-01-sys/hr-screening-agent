"""
E2E Test 3: Running screening and verifying the Phase 3 results display.
"""
import pytest
from playwright.sync_api import expect
from testing.conftest import AppPage


def test_screening_run_and_results_rendering(app_with_sample: AppPage) -> None:
    """Verify that running the screening navigates to Phase 3 and shows evaluation results."""
    app_with_sample.wait_for_phase("Phase 2")

    # Run screening
    app_with_sample.click_run_final_screening()
    app_with_sample.wait_for_phase("Phase 3")

    # Check that score / pass status is shown
    # The default sample has Tableau = 18 months, but the rule requires 24 months. So it should FAIL.
    expect(app_with_sample.page.locator("[data-testid='stMetricValue']").first).to_have_text("Reject")
    
    # Check that score breakdown is visible in Phase 3
    expect(app_with_sample.page.get_by_text("Score Breakdown", exact=False)).to_be_visible()

    # Check that the rule evaluation breakdown is present
    expect(app_with_sample.page.get_by_text("tableau_min_exp", exact=False)).to_be_visible()
    expect(app_with_sample.page.get_by_text("Tableau", exact=False)).to_be_visible()
