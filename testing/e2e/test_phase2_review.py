"""
E2E Test 2: Interacting with and editing fields in Phase 2.
"""
import pytest
from playwright.sync_api import expect
from testing.conftest import AppPage


def test_edit_candidate_and_jd_fields(app_with_sample: AppPage) -> None:
    """Verify that editing fields on Phase 2 works and values are preserved."""
    app_with_sample.wait_for_phase("Phase 2")

    # Locate and check the initial full name
    full_name_input = app_with_sample.page.get_by_label("Full Name")
    expect(full_name_input).to_have_value("Riya Sharma")

    # Edit the full name
    full_name_input.fill("Riya Sharma Edited")
    app_with_sample.wait_for_streamlit()

    # Verify change is preserved
    expect(full_name_input).to_have_value("Riya Sharma Edited")

    # Locate and check initial Role Title
    role_title_input = app_with_sample.page.get_by_label("Role Title")
    expect(role_title_input).to_have_value("Business Intelligence Analyst")

    # Edit the role title
    role_title_input.fill("Senior BI Analyst")
    app_with_sample.wait_for_streamlit()

    # Verify role title change is preserved
    expect(role_title_input).to_have_value("Senior BI Analyst")


def test_review_tables_are_rendered(app_with_sample: AppPage) -> None:
    """Verify that tables like Extracted Skill Evidence and Mandatory Rules are rendered as data editors."""
    app_with_sample.wait_for_phase("Phase 2")

    # Streamlit data editors render with a div having data-testid="stDataEditor"
    editors = app_with_sample.page.locator("div[data-testid='stDataEditor']")
    # We should have at least 3 editors (Skills, Review Queue, Rules)
    expect(editors).to_have_count(3)
