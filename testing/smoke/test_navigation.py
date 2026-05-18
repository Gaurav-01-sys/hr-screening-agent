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
    app.wait_for_phase("Phase 2")


def test_back_to_ingest_returns_to_phase1(app_with_sample: AppPage) -> None:
    """'Back to Ingest' button navigates back to Phase 1."""
    app_with_sample.click_back_to_ingest()
    app_with_sample.wait_for_phase("Phase 1")


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
    app_with_sample.wait_for_phase("Phase 3")


def test_phase3_start_new_returns_to_phase1(app_with_sample: AppPage) -> None:
    """'Start New Screening' on Phase 3 returns to Phase 1."""
    app_with_sample.click_run_final_screening()
    app_with_sample.wait_for_phase("Phase 3")
    app_with_sample.click_start_new_screening()
    app_with_sample.wait_for_phase("Phase 1")
