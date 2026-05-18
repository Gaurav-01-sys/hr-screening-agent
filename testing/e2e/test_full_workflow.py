"""
E2E Test 4: Full custom workflow from Phase 1 to Phase 3.
Skipped if AI is not configured (GROQ_API_KEY missing).
"""
import os
import pytest
from playwright.sync_api import expect
from testing.conftest import AppPage
from testing.fixtures.data import SAMPLE_RESUME_TEXT, SAMPLE_JD_TEXT, SAMPLE_RULE_NOTES


@pytest.mark.skipif("GROQ_API_KEY" not in os.environ, reason="GROQ_API_KEY is not set")
def test_full_custom_workflow_with_ai(app: AppPage) -> None:
    """Run a full custom extraction and screening flow using custom texts and live AI."""
    app.wait_for_phase("Phase 1")

    # Fill out the fields manually
    app.fill_resume_text(SAMPLE_RESUME_TEXT)
    app.fill_jd_text(SAMPLE_JD_TEXT)
    app.fill_rule_notes(SAMPLE_RULE_NOTES)

    # Click Extract With AI and wait
    app.click_extract_with_ai()

    # Should now be in Phase 2
    app.wait_for_phase("Phase 2")

    # Verify AI extracted key fields from the custom texts
    expect(app.page.get_by_label("Full Name")).to_have_value("John Doe")
    expect(app.page.get_by_label("Role Title")).to_have_value("Business Intelligence Analyst")

    # Run screening
    app.click_run_final_screening()
    app.wait_for_phase("Phase 3")

    # The custom resume has Tableau = 28 months, and rule asks for Tableau >= 24 months.
    # Total experience is 52 months, and rule asks for >= 36 months.
    # Therefore, John Doe should PASS!
    expect(app.page.locator("[data-testid='stMetricValue']").first).to_have_text("Pass")
