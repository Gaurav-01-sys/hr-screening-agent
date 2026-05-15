# HR Screening Agentic System

This repository contains a starter architecture for an HR analyst workflow that compares a resume/CV against a job description, applies mandatory check rules, and supports a human-in-the-loop verification step before final scoring.

## Design goals

- Use `Docling` or an equivalent parser to extract structured text and evidence spans from resumes and JDs.
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

## Run API

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install fastapi uvicorn pydantic groq
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for the API.

## Run Streamlit

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install streamlit fastapi uvicorn pydantic groq
streamlit run streamlit_app.py
```

The Streamlit app gives HR an interactive workbench to:

- paste resume and JD text for Groq-based extraction
- enter extracted skill evidence
- review and correct AI-extracted fields
- configure mandatory rules
- run scoring and see explainable rule results

## Groq integration

The app now uses Groq for:

- extracting candidate facts from resume text
- extracting job requirements from JD text
- converting free-form mandatory rule notes into structured rules

The app still uses deterministic Python logic for:

- hard-fail checks
- score calculation
- final recommendation policy
