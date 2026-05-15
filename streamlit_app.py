from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st

from app.config import GROQ_MODEL
from app.groq_extractor import extract_screening_request, groq_is_configured
from app.rules import evaluate_rules
from app.sample_data import build_sample_request
from app.scoring import build_screening_response
from app.schemas import (
    CandidateProfile,
    Evidence,
    ExtractedField,
    JobRequirement,
    MandatoryRule,
    ReviewStatus,
    ScreeningRequest,
    Severity,
    SkillExperience,
)
from app.database import SessionLocal, engine, Base
from app.crud import save_screening_run
from app.normalizer import normalize_candidate_profile

# Ensure tables are created
Base.metadata.create_all(bind=engine)


def _sample_to_session() -> None:
    st.session_state["phase"] = "REVIEW"
    sample = build_sample_request()
    st.session_state["candidate_id"] = sample.candidate.candidate_id
    st.session_state["full_name"] = sample.candidate.full_name or ""
    st.session_state["total_experience_months"] = sample.candidate.total_experience_months
    st.session_state["skills_rows"] = [
        {
            "skill": item.skill,
            "months": item.months,
            "evidence_snippet": item.evidence[0].snippet if item.evidence else "",
            "page": item.evidence[0].page if item.evidence else None,
            "confidence": item.evidence[0].confidence if item.evidence else 0.8,
        }
        for item in sample.candidate.skills
    ]
    st.session_state["review_rows"] = [
        {
            "name": item.name,
            "ai_value": item.ai_value,
            "human_value": item.human_value or "",
            "review_status": item.review_status.value,
            "evidence_snippet": item.evidence[0].snippet if item.evidence else "",
            "page": item.evidence[0].page if item.evidence else None,
            "confidence": item.evidence[0].confidence if item.evidence else 0.8,
        }
        for item in sample.candidate.fields_for_review
    ]
    st.session_state["role_title"] = sample.job.role_title
    st.session_state["min_total_experience_months"] = sample.job.min_total_experience_months
    st.session_state["mandatory_skills"] = ", ".join(sample.job.mandatory_skills)
    st.session_state["preferred_skills"] = ", ".join(sample.job.preferred_skills)
    st.session_state["required_domains"] = ", ".join(sample.job.required_domains)
    st.session_state["rules_rows"] = [
        {
            "id": item.id,
            "type": item.type,
            "severity": item.severity.value,
            "weight": item.weight,
            "skill": item.skill or "",
            "min_months": item.min_months,
            "domain": item.domain or "",
            "expected_value": item.expected_value or "",
        }
        for item in sample.rules
    ]


def _blank_session() -> None:
    st.session_state["phase"] = "INGEST"
    st.session_state["candidate_id"] = "cand-001"
    st.session_state["full_name"] = ""
    st.session_state["total_experience_months"] = 0
    st.session_state["skills_rows"] = [
        {"skill": "", "months": 0, "evidence_snippet": "", "page": 1, "confidence": 0.8}
    ]
    st.session_state["review_rows"] = [
        {
            "name": "",
            "ai_value": "",
            "human_value": "",
            "review_status": ReviewStatus.pending.value,
            "evidence_snippet": "",
            "page": 1,
            "confidence": 0.8,
        }
    ]
    st.session_state["role_title"] = ""
    st.session_state["min_total_experience_months"] = 0
    st.session_state["mandatory_skills"] = ""
    st.session_state["preferred_skills"] = ""
    st.session_state["required_domains"] = ""
    st.session_state["rules_rows"] = [
        {
            "id": "rule-001",
            "type": "skill_min_months",
            "severity": Severity.hard_fail.value,
            "weight": 25,
            "skill": "",
            "min_months": 0,
            "domain": "",
            "expected_value": "",
        }
    ]


def _ensure_session() -> None:
    if "phase" not in st.session_state:
        st.session_state["phase"] = "INGEST"
    if "candidate_id" not in st.session_state:
        _sample_to_session()


def _normalize_text(text: str) -> str:
    cleaned_lines = [line.rstrip() for line in text.splitlines()]
    normalized: List[str] = []
    previous_blank = False

    for line in cleaned_lines:
        is_blank = not line.strip()
        if is_blank and previous_blank:
            continue
        normalized.append(line)
        previous_blank = is_blank

    return "\n".join(normalized).strip()


def _extract_with_docling(file_name: str, file_bytes: bytes) -> str:
    try:
        from docling.datamodel.base_models import DocumentStream
        from docling.document_converter import DocumentConverter
    except ImportError:
        return ""

    try:
        stream = DocumentStream(name=file_name, stream=BytesIO(file_bytes))
        result = DocumentConverter().convert(stream)
        return _normalize_text(result.document.export_to_markdown())
    except Exception as e:
        print(f"Docling extraction failed: {e}")
        return ""


def _extract_pdf_text(file_name: str, file_bytes: bytes) -> str:
    docling_text = _extract_with_docling(file_name, file_bytes)
    if docling_text:
        return docling_text

    from pypdf import PdfReader

    reader = PdfReader(BytesIO(file_bytes))
    parts = [page.extract_text() or "" for page in reader.pages]
    return _normalize_text("\n\n".join(parts))


def _extract_docx_text(file_bytes: bytes) -> str:
    from docx import Document

    document = Document(BytesIO(file_bytes))
    parts = [paragraph.text for paragraph in document.paragraphs if paragraph.text.strip()]
    return _normalize_text("\n".join(parts))


def _extract_uploaded_text(file_name: str, file_bytes: bytes) -> str:
    suffix = Path(file_name).suffix.lower()
    if suffix == ".pdf":
        return _extract_pdf_text(file_name, file_bytes)
    if suffix == ".docx":
        return _extract_docx_text(file_bytes)
    raise ValueError(f"Unsupported file type: {suffix or 'unknown'}")


def _sync_uploaded_text(
    uploaded_file: Any,
    *,
    target_key: str,
    status_key: str,
    label: str,
) -> None:
    if uploaded_file is None:
        st.session_state.pop(status_key, None)
        return

    file_bytes = uploaded_file.getvalue()
    fingerprint = f"{uploaded_file.name}:{len(file_bytes)}"
    current_status = st.session_state.get(status_key, {})
    if current_status.get("fingerprint") == fingerprint:
        return

    try:
        extracted_text = _extract_uploaded_text(uploaded_file.name, file_bytes)
    except Exception as exc:
        st.session_state[status_key] = {
            "fingerprint": fingerprint,
            "level": "error",
            "message": f"{label} upload could not be parsed: {exc}",
        }
        return

    st.session_state[target_key] = extracted_text
    st.session_state[status_key] = {
        "fingerprint": fingerprint,
        "level": "success",
        "message": f"{label} text loaded from {uploaded_file.name}.",
    }


def _split_csv(value: str) -> List[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _request_to_session(payload: ScreeningRequest) -> None:
    st.session_state["candidate_id"] = payload.candidate.candidate_id
    st.session_state["full_name"] = payload.candidate.full_name or ""
    st.session_state["total_experience_months"] = payload.candidate.total_experience_months
    st.session_state["skills_rows"] = [
        {
            "skill": item.skill,
            "months": item.months,
            "evidence_snippet": item.evidence[0].snippet if item.evidence else "",
            "page": item.evidence[0].page if item.evidence else None,
            "confidence": item.evidence[0].confidence if item.evidence else 0.8,
        }
        for item in payload.candidate.skills
    ] or [{"skill": "", "months": 0, "evidence_snippet": "", "page": 1, "confidence": 0.8}]
    st.session_state["review_rows"] = [
        {
            "name": item.name,
            "ai_value": item.ai_value,
            "human_value": item.human_value or "",
            "review_status": item.review_status.value,
            "evidence_snippet": item.evidence[0].snippet if item.evidence else "",
            "page": item.evidence[0].page if item.evidence else None,
            "confidence": item.evidence[0].confidence if item.evidence else 0.8,
        }
        for item in payload.candidate.fields_for_review
    ] or [
        {
            "name": "",
            "ai_value": "",
            "human_value": "",
            "review_status": ReviewStatus.pending.value,
            "evidence_snippet": "",
            "page": 1,
            "confidence": 0.8,
        }
    ]
    st.session_state["role_title"] = payload.job.role_title
    st.session_state["min_total_experience_months"] = payload.job.min_total_experience_months
    st.session_state["mandatory_skills"] = ", ".join(payload.job.mandatory_skills)
    st.session_state["preferred_skills"] = ", ".join(payload.job.preferred_skills)
    st.session_state["required_domains"] = ", ".join(payload.job.required_domains)
    st.session_state["rules_rows"] = [
        {
            "id": item.id,
            "type": item.type,
            "severity": item.severity.value,
            "weight": item.weight,
            "skill": item.skill or "",
            "min_months": item.min_months,
            "domain": item.domain or "",
            "expected_value": item.expected_value or "",
        }
        for item in payload.rules
    ] or [
        {
            "id": "rule-001",
            "type": "skill_min_months",
            "severity": Severity.hard_fail.value,
            "weight": 25,
            "skill": "",
            "min_months": 0,
            "domain": "",
            "expected_value": "",
        }
    ]


def _evidence_from_row(source_document: str, row: Dict[str, Any]) -> List[Evidence]:
    snippet = str(row.get("evidence_snippet", "")).strip()
    if not snippet:
        return []
    page_value = row.get("page")
    page = int(page_value) if page_value not in (None, "") else None
    confidence_value = row.get("confidence", 0.8)
    confidence = float(confidence_value) if confidence_value not in (None, "") else 0.8
    return [
        Evidence(
            source_document=source_document,
            snippet=snippet,
            page=page,
            confidence=confidence,
        )
    ]


def _build_request(
    skills_rows: List[Dict[str, Any]],
    review_rows: List[Dict[str, Any]],
    rules_rows: List[Dict[str, Any]],
) -> ScreeningRequest:
    skills = []
    for row in skills_rows:
        skill = str(row.get("skill", "")).strip()
        if not skill:
            continue
        months_value = row.get("months", 0)
        skills.append(
            SkillExperience(
                skill=skill,
                months=int(months_value or 0),
                evidence=_evidence_from_row("resume", row),
            )
        )

    review_fields = []
    for row in review_rows:
        name = str(row.get("name", "")).strip()
        if not name:
            continue
        status = str(row.get("review_status", ReviewStatus.pending.value))
        review_fields.append(
            ExtractedField(
                name=name,
                ai_value=str(row.get("ai_value", "")),
                human_value=str(row.get("human_value", "")).strip() or None,
                review_status=ReviewStatus(status),
                evidence=_evidence_from_row("resume", row),
            )
        )

    candidate = CandidateProfile(
        candidate_id=st.session_state["candidate_id"],
        full_name=st.session_state["full_name"].strip() or None,
        total_experience_months=int(st.session_state["total_experience_months"] or 0),
        skills=skills,
        fields_for_review=review_fields,
    )

    job = JobRequirement(
        role_title=st.session_state["role_title"].strip(),
        min_total_experience_months=int(st.session_state["min_total_experience_months"] or 0),
        mandatory_skills=_split_csv(st.session_state["mandatory_skills"]),
        preferred_skills=_split_csv(st.session_state["preferred_skills"]),
        required_domains=_split_csv(st.session_state["required_domains"]),
    )

    rules = []
    for row in rules_rows:
        rule_id = str(row.get("id", "")).strip()
        rule_type = str(row.get("type", "")).strip()
        if not rule_id or not rule_type:
            continue
        min_months = row.get("min_months")
        rules.append(
            MandatoryRule(
                id=rule_id,
                type=rule_type,
                severity=Severity(str(row.get("severity", Severity.soft.value))),
                weight=int(row.get("weight", 0) or 0),
                skill=str(row.get("skill", "")).strip() or None,
                min_months=int(min_months) if min_months not in (None, "") else None,
                domain=str(row.get("domain", "")).strip() or None,
                expected_value=str(row.get("expected_value", "")).strip() or None,
            )
        )

    return ScreeningRequest(candidate=candidate, job=job, rules=rules)


def _render_results(payload: ScreeningRequest) -> None:
    # 1. Normalize the candidate profile
    payload.candidate = normalize_candidate_profile(payload.candidate)

    # 2. Evaluate rules and build response
    results = evaluate_rules(payload.candidate, payload.rules)
    response = build_screening_response(payload.candidate, payload.job, results)

    # 3. Save to database
    try:
        with SessionLocal() as db:
            save_screening_run(db, payload, response)
        st.toast("Screening run saved to database successfully!", icon="✅")
    except Exception as e:
        st.error(f"Failed to save to database: {e}")

    st.subheader("Screening Result")
    metric_columns = st.columns(4)
    metric_columns[0].metric("Recommendation", response.recommendation.value.replace("_", " ").title())
    metric_columns[1].metric("Final Score", f"{response.scores.final_score}")
    metric_columns[2].metric("Hard Fail", "Yes" if response.hard_fail else "No")
    metric_columns[3].metric(
        "Evidence Confidence",
        f"{round(response.scores.evidence_confidence * 100, 1)}%",
    )

    st.write(response.explanation)

    st.subheader("Score Breakdown")
    st.dataframe(
        [
            {"component": "mandatory_fit", "value": response.scores.mandatory_fit},
            {"component": "experience_depth", "value": response.scores.experience_depth},
            {"component": "skill_match", "value": response.scores.skill_match},
            {"component": "domain_relevance", "value": response.scores.domain_relevance},
            {"component": "recency", "value": response.scores.recency},
            {"component": "evidence_confidence", "value": response.scores.evidence_confidence},
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Rule Results")
    for item in response.rule_results:
        status_text = "PASS" if item.passed else "FAIL"
        with st.expander(f"{status_text} | {item.rule_id} | {item.severity.value}"):
            st.write(item.message)
            if item.evidence:
                st.write("Evidence")
                for evidence in item.evidence:
                    st.caption(
                        f"Page {evidence.page or '-'} | confidence {evidence.confidence} | {evidence.snippet}"
                    )

    st.subheader("JSON Output")
    st.json(response.model_dump())


st.set_page_config(page_title="HR Screening Workbench", layout="wide")
st.title("HR Screening Workbench")
st.caption("Resume/JD screening with human verification, mandatory rules, and deterministic scoring.")

_ensure_session()
phase = st.session_state["phase"]

with st.sidebar:
    st.header("Session")
    if st.button("Load Sample Case", use_container_width=True):
        _sample_to_session()
        st.rerun()
    if st.button("Reset Blank Form", use_container_width=True):
        _blank_session()
        st.rerun()
    st.markdown(
        "Use the editable tables to simulate extracted resume facts, human review corrections, job requirements, and mandatory checks."
    )

if phase == "INGEST":
    st.header("Phase 1: Ingest Documents")
    st.markdown("Upload or paste the Candidate's Resume and the Job Description, then use AI to extract the data.")
    resume_upload = st.file_uploader("Upload Resume/CV", type=["pdf", "docx"], key="resume_upload")
    jd_upload = st.file_uploader("Upload Job Description", type=["pdf", "docx"], key="jd_upload")
    _sync_uploaded_text(
        resume_upload,
        target_key="resume_text",
        status_key="resume_upload_status",
        label="Resume",
    )
    _sync_uploaded_text(
        jd_upload,
        target_key="jd_text",
        status_key="jd_upload_status",
        label="JD",
    )
    resume_status = st.session_state.get("resume_upload_status")
    if resume_status:
        getattr(st, resume_status["level"])(resume_status["message"])
    jd_status = st.session_state.get("jd_upload_status")
    if jd_status:
        getattr(st, jd_status["level"])(jd_status["message"])
    st.text_area("Resume Text", height=180, key="resume_text")
    st.text_area("JD Text", height=180, key="jd_text")
    st.text_area(
        "Mandatory Rule Notes",
        height=120,
        placeholder="Example: Tableau must be at least 24 months. SQL is mandatory. Healthcare domain preferred.",
        help="Use this as the free-form rule input that a future LLM-to-rules step can convert into structured checks.",
        key="mandatory_rule_notes",
    )
    if groq_is_configured():
        st.success(f"Groq configured. Model: {GROQ_MODEL}")
    else:
        st.warning("Groq is not configured. Add GROQ_API_KEY to your .env file.")
    if st.button("Extract With Groq", use_container_width=True, disabled=not groq_is_configured(), type="primary"):
        if not st.session_state["resume_text"].strip() or not st.session_state["jd_text"].strip():
            st.error("Resume Text and JD Text are required for Groq extraction.")
        else:
            with st.spinner("Extracting candidate, job, and rule data with Groq..."):
                extracted = extract_screening_request(
                    resume_text=st.session_state["resume_text"],
                    jd_text=st.session_state["jd_text"],
                    mandatory_rule_notes=st.session_state["mandatory_rule_notes"],
                )
            _request_to_session(extracted)
            st.session_state["phase"] = "REVIEW"
            st.rerun()

elif phase == "REVIEW":
    st.header("Phase 2: Human-in-the-Loop Review")
    st.markdown("Verify the AI-extracted data. You can directly edit the skill months or provide human overrides in the review queue before running the final screening rules.")
    left_column, right_column = st.columns([1.1, 0.9])

    with left_column:
        st.subheader("Candidate")
        st.text_input("Candidate ID", key="candidate_id")
        st.text_input("Full Name", key="full_name")
        st.number_input("Total Experience (months)", min_value=0, step=1, key="total_experience_months")

        st.subheader("Extracted Skill Evidence")
        skills_rows = st.data_editor(
            st.session_state["skills_rows"],
            key="skills_editor",
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "skill": st.column_config.TextColumn("Skill"),
                "months": st.column_config.NumberColumn("Months", min_value=0, step=1),
                "evidence_snippet": st.column_config.TextColumn("Evidence Snippet", width="large"),
                "page": st.column_config.NumberColumn("Page", min_value=1, step=1),
                "confidence": st.column_config.NumberColumn("Confidence", min_value=0.0, max_value=1.0, step=0.01),
            },
        )

        st.subheader("Human Review Queue")
        review_rows = st.data_editor(
            st.session_state["review_rows"],
            key="review_editor",
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "name": st.column_config.TextColumn("Field Name"),
                "ai_value": st.column_config.TextColumn("AI Value"),
                "human_value": st.column_config.TextColumn("Human Value"),
                "review_status": st.column_config.SelectboxColumn(
                    "Review Status",
                    options=[status.value for status in ReviewStatus],
                ),
                "evidence_snippet": st.column_config.TextColumn("Evidence Snippet", width="large"),
                "page": st.column_config.NumberColumn("Page", min_value=1, step=1),
                "confidence": st.column_config.NumberColumn("Confidence", min_value=0.0, max_value=1.0, step=0.01),
            },
        )

    with right_column:
        st.subheader("Job Description")
        st.text_input("Role Title", key="role_title")
        st.number_input(
            "Minimum Total Experience (months)",
            min_value=0,
            step=1,
            key="min_total_experience_months",
        )
        st.text_area("Mandatory Skills (comma separated)", key="mandatory_skills", height=80)
        st.text_area("Preferred Skills (comma separated)", key="preferred_skills", height=80)
        st.text_area("Required Domains (comma separated)", key="required_domains", height=80)

        st.subheader("Mandatory Rules")
        rules_rows = st.data_editor(
            st.session_state["rules_rows"],
            key="rules_editor",
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "id": st.column_config.TextColumn("Rule ID"),
                "type": st.column_config.SelectboxColumn(
                    "Rule Type",
                    options=["skill_min_months", "skill_required", "total_experience_min_months"],
                ),
                "severity": st.column_config.SelectboxColumn(
                    "Severity",
                    options=[severity.value for severity in Severity],
                ),
                "weight": st.column_config.NumberColumn("Weight", min_value=0, step=1),
                "skill": st.column_config.TextColumn("Skill"),
                "min_months": st.column_config.NumberColumn("Min Months", min_value=0, step=1),
                "domain": st.column_config.TextColumn("Domain"),
                "expected_value": st.column_config.TextColumn("Expected Value"),
            },
        )

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Back to Ingest", use_container_width=True):
            st.session_state["phase"] = "INGEST"
            st.rerun()
    with col2:
        if st.button("Run Final Screening", type="primary", use_container_width=True):
            payload = _build_request(skills_rows, review_rows, rules_rows)
            st.session_state["screening_payload"] = payload
            st.session_state["phase"] = "RESULT"
            st.rerun()

elif phase == "RESULT":
    st.header("Phase 3: Screening Result")
    payload = st.session_state.get("screening_payload")
    if payload:
        _render_results(payload)
    else:
        st.error("No screening data found. Please start over.")
    
    st.markdown("---")
    if st.button("Start New Screening", use_container_width=True):
        _blank_session()
        st.rerun()
