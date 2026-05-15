from __future__ import annotations

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from .document_parser import extract_uploaded_text

from .groq_extractor import extract_screening_request, groq_is_configured
from .rules import evaluate_rules
from .sample_data import build_sample_request
from .scoring import build_screening_response
from .schemas import ScreeningRequest, ScreeningResponse
from .database import SessionLocal, engine, Base
from .crud import save_screening_run
from .normalizer import normalize_candidate_profile

# Ensure DB tables are created
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="HR Screening Agentic System",
    description="Starter API for evidence-backed resume to JD screening with human verification and deterministic scoring.",
    version="0.1.0",
)

# Allow React frontend to communicate with API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "groq_configured": groq_is_configured()}

@app.post("/parse-document")
async def parse_document(file: UploadFile = File(...)):
    contents = await file.read()
    try:
        text = extract_uploaded_text(file.filename, contents)
        return {"filename": file.filename, "text": text}
    except Exception as e:
        return {"error": str(e)}


@app.get("/sample-request", response_model=ScreeningRequest)
def sample_request() -> ScreeningRequest:
    return build_sample_request()


@app.post("/extract", response_model=ScreeningRequest)
def extract_from_text(payload: dict) -> ScreeningRequest:
    resume_text = str(payload.get("resume_text", "")).strip()
    jd_text = str(payload.get("jd_text", "")).strip()
    mandatory_rule_notes = str(payload.get("mandatory_rule_notes", "")).strip()
    return extract_screening_request(resume_text, jd_text, mandatory_rule_notes)


@app.post("/screen", response_model=ScreeningResponse)
def screen_candidate(payload: ScreeningRequest) -> ScreeningResponse:
    # 1. Normalize the candidate profile
    payload.candidate = normalize_candidate_profile(payload.candidate)

    # 2. Evaluate rules and build response
    rule_results = evaluate_rules(payload.candidate, payload.rules)
    response = build_screening_response(payload.candidate, payload.job, rule_results)

    # 3. Save to database
    try:
        with SessionLocal() as db:
            save_screening_run(db, payload, response)
    except Exception as e:
        print(f"Failed to save screening run: {e}")

    return response
