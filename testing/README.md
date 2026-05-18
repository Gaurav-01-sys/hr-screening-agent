# HR Screening Agent — Test Suite

## Overview
This directory contains the full automated test suite for the HR Screening System built with **Playwright** (Python) and **pytest**.

## Structure
```
testing/
├── conftest.py                  # Shared fixtures, base URL, browser setup
├── pytest.ini                   # pytest / Playwright config
├── requirements-test.txt        # Test dependencies
├── fixtures/                    # Shared test data helpers
│   └── data.py
├── smoke/                       # Fast sanity checks (no AI calls)
│   ├── test_app_loads.py
│   ├── test_navigation.py
│   └── test_reset.py
└── e2e/                         # Full end-to-end workflows
    ├── test_phase1_upload.py    # File upload + text paste
    ├── test_phase2_review.py    # Review editing + back navigation
    ├── test_phase3_result.py    # Final screening result
    └── test_full_workflow.py    # Complete flow Phase1→2→3
```

## Prerequisites
```bash
pip install -r testing/requirements-test.txt
playwright install chromium
```

## Running Tests
```bash
# Run all tests (app must be running locally on http://localhost:8501)
pytest testing/ -v

# Smoke tests only (fast, ~10s)
pytest testing/smoke/ -v

# E2E only
pytest testing/e2e/ -v

# Point at a different URL (e.g. Streamlit Cloud)
pytest testing/ -v --base-url https://your-app.streamlit.app

# With HTML report
pytest testing/ -v --html=testing/report.html --self-contained-html
```

## Notes
- The E2E `test_phase2_ai_extract` test calls the live AI and requires `GROQ_API_KEY` to be set.  
  All other tests use the **Load Sample Case** button to bypass AI.
- Tests assume the app starts on **Phase 1 (Ingest)**.
