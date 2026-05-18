"""
Smoke Test 2: Navigation between phases via the Load Sample shortcut
and the Back to Ingest button.
"""
import pytest
from playwright.sync_api import expect
from testing.conftest import AppPage


def test_load_sample_goes_to_phase2(app: AppPage) -> None:
    """Clicking 'Load Sample Case' navigates to Phase 2."""
    app.click_load_sample()
    assert app.is_phase("phase 2"), f"Expected Phase 2, got: {app.current_phase_header()}"


def test_back_to_ingest_returns_to_phase1(app_with_sample: AppPage) -> None:
    """'Back to Ingest' button navigates back to Phase 1."""
    app_with_sample.click_back_to_ingest()
    assert app_with_sample.is_phase("phase 1"), (
        f"Expected Phase 1, got: {app_with_sample.current_phase_header()}"
    )


def test_phase2_candidate_section_visible(app_with_sample: AppPage) -> None:
    """Phase 2 shows the Candidate section."""
    header = app_with_sample.page.get_by_text("Candidate", exact=False).first
    expect(header).to_be_visible()


def test_phase2_job_description_section_visible(app_with_sample: AppPage) -> None:
    """Phase 2 shows the Job Description section."""
    header = app_with_sample.page.get_by_text("Job Description", exact=False).first
    expect(header).to_be_visible()


def test_phase2_run_screening_goes_to_phase3(app_with_sample: AppPage) -> None:
    """'Run Final Screening' button navigates to Phase 3."""
    app_with_sample.click_run_final_screening()
    assert app_with_sample.is_phase("phase 3"), (
        f"Expected Phase 3, got: {app_with_sample.current_phase_header()}"
    )


def test_phase3_start_new_returns_to_phase1(app_with_sample: AppPage) -> None:
    """'Start New Screening' on Phase 3 returns to Phase 1."""
    app_with_sample.click_run_final_screening()
    app_with_sample.click_start_new_screening()
    assert app_with_sample.is_phase("phase 1"), (
        f"Expected Phase 1, got: {app_with_sample.current_phase_header()}"
    )
