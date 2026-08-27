# HR Screening Agentic System

This repository contains a starter architecture for an HR analyst workflow that compares a resume/CV against a job description, applies mandatory check rules, and supports a human-in-the-loop verification step before final scoring.

## Design goals

- Use PDFium for local, selectable-text PDF extraction and `python-docx` for DOCX parsing.
- Keep LLM usage narrow: extraction, normalization suggestions, and explanation generation.
- Keep scoring, date arithmetic, and threshold checks deterministic.
- Make every extracted field reviewable by a human before a recommendation is produced.
- Produce explainable outputs with evidence-backed rule results.

## Workflow

1. Upload a resume, JD, and optional mandatory-rule set.
2. Parse documents into blocks with evidence metadata.
3. Extract candidate and job facts into structured JSON.
4. Present extracted facts for human approval or correction.
5. Normalize skills, titles, and dates.
6. Run deterministic rule checks and weighted scoring.
7. Generate an explainable recommendation for HR.

## Suggested architecture

- `app/main.py`: API entry point
- `app/schemas.py`: request and response contracts
- `app/rules.py`: rule evaluation engine
- `app/scoring.py`: scoring logic and recommendation policy
- `app/sample_data.py`: seed payloads for testing

## Human-in-the-loop principle

Every extracted fact should preserve:

- source document
- source snippet
- page number
- optional bounding box
- extractor confidence

The reviewer sees both the machine-extracted value and the evidence used to support it. The reviewer can then approve, edit, or reject the value.

## Example rule

If the JD requires 24 months of Tableau experience and the extracted resume evidence supports only 3 months, the system should:

- mark the rule as failed
- apply a strong penalty or a hard-fail policy
- explain why the candidate is undesirable for that requirement

## Environment

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-20b
```

`GROQ_MODEL` is optional. If omitted, the app defaults to `openai/gpt-oss-20b`.

PDF parsing uses `pypdfium2` for selectable text and keeps page order. Scanned
PDFs without a text layer return no extracted text and should be converted to
searchable PDF before upload. DOCX files use `python-docx`.

## Run API

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for the API.

The API also exposes `POST /screen/batch`. Send a shared `job` and `rules`
with a `candidates` array containing reviewed `CandidateProfile` objects; the
response returns deterministic rank order and the same evidence-backed result
artifacts as `/screen`.

## Run Streamlit

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run streamlit_app.py
```

The Streamlit app gives HR an interactive workbench to:

- paste resume and JD text for Groq-based extraction
- enter extracted skill evidence
- review and correct AI-extracted fields
- configure mandatory rules
- run scoring and see explainable rule results
- review structured interview questions personalized to the candidate's evidence
- inspect a draft-only interview/rejection communication (never sent automatically)
- screen and rank multiple reviewed candidates through `POST /screen/batch`

Communication drafts use a natural recruiter tone. Their prompt context is
organized with a bounded MemPalace-inspired wing/room/drawer structure while
keeping the source evidence traceable and local.

## Deploy to Render

The root [`render.yaml`](render.yaml) defines three Render services:

- `hr-screening-backend`: FastAPI on the Render-provided `$PORT`, with `/health` as its health check
- `hr-screening-frontend`: the Vite build served as a static site, with an SPA fallback to `index.html`
- `hr-screening-streamlit`: the optional Streamlit workbench on the Render-provided `$PORT`

To deploy, create a new Blueprint in the Render dashboard and select this
repository. During the first sync, provide `GROQ_API_KEY` for the backend and
Streamlit services. After the backend has a public `onrender.com` URL, set the
frontend service's `VITE_API_URL` to that URL and redeploy the frontend.

The Blueprint does not add a managed database. The app's current SQLite file is
therefore ephemeral on Render; use a persistent disk or migrate the persistence
layer before relying on hosted screening history.

## Groq integration

The app now uses Groq for:

- extracting candidate facts from resume text
- extracting job requirements from JD text
- converting free-form mandatory rule notes into structured rules

The app still uses deterministic Python logic for:

- hard-fail checks
- score calculation
- final recommendation policy

When `GROQ_API_KEY` is available, the draft communication is lightly polished
with a natural recruiter-tone prompt grounded in the reviewed facts. If the
model is unavailable, the same response path falls back to the local
plain-language templates.

## HR skills and upstream design notes

See [`docs/hr-skills-integration.md`](docs/hr-skills-integration.md) for the
review of `hr-skills-dev.zip`, the selected assessment/interview/fairness
patterns incorporated here, and the comparison with the referenced
`RareBeacon/ai-hr-screening-agent` repository.
