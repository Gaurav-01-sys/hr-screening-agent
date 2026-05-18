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
    expect(full_name_input).to_have_value("Sample Candidate")

    # Edit the full name
    full_name_input.fill("Sample Candidate Edited")
    app_with_sample.wait_for_streamlit()

    # Verify change is preserved
    expect(full_name_input).to_have_value("Sample Candidate Edited")

    # Locate and check initial Role Title
    role_title_input = app_with_sample.page.get_by_label("Role Title")
    expect(role_title_input).to_have_value("BI Analyst")

    # Edit the role title
    role_title_input.fill("Senior BI Analyst")
    app_with_sample.wait_for_streamlit()

    # Verify role title change is preserved
    expect(role_title_input).to_have_value("Senior BI Analyst")


def test_review_tables_are_rendered(app_with_sample: AppPage) -> None:
    """Verify that tables like Extracted Skill Evidence and Mandatory Rules are rendered as data editors."""
    app_with_sample.wait_for_phase("Phase 2")

    # Streamlit data editors render with a div having class stDataFrameGlideDataEditor
    editors = app_with_sample.page.locator(".stDataFrameGlideDataEditor")
    # We should have at least 3 editors (Skills, Review Queue, Rules)
    expect(editors.first).to_be_visible()
    count = editors.count()
    assert count >= 3, f"Expected at least 3 data editors, found {count}"
