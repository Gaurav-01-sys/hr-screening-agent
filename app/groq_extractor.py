from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any, Dict, List

try:
    from groq import Groq
except ImportError:  # pragma: no cover
    Groq = None

from .config import GROQ_API_KEY, GROQ_MODEL
from .schemas import (
    CandidateProfile,
    Evidence,
    EducationEntry,
    ExtractedField,
    ExperienceEntry,
    JobRequirement,
    MandatoryRule,
    ReviewStatus,
    ScreeningRequest,
    Severity,
    SkillExperience,
)


SYSTEM_PROMPT = """
You are an expert HR resume screening assistant.
Your job is to READ the provided resume and job description texts and EXTRACT real information from them.
Always return a single valid JSON object. No markdown fences. No extra text.
Extract as much data as possible. Do NOT leave fields empty if the information exists in the text.
Do not infer or extract protected characteristics (such as age, gender, race, religion,
marital status, disability, or pregnancy). Do not make a hiring decision.
"""


def groq_is_configured() -> bool:
    return bool(GROQ_API_KEY) and Groq is not None


# Exposed for debug display in the UI
_last_raw_response: str = ""


def _build_client() -> Groq:
    if Groq is None:
        raise ValueError("groq package is not installed. Run: pip install groq")
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not configured.")
    return Groq(api_key=GROQ_API_KEY)


def _extract_json(content: str) -> Dict[str, Any]:
    content = content.strip()

    # Strip markdown fences if present
    for fence in ("```json", "```"):
        if content.startswith(fence):
            content = content[len(fence):]
            break
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()

    # Find the first JSON object or array in the content
    # (handles models that add prose before/after the JSON)
    start = -1
    start_char = None
    for i, ch in enumerate(content):
        if ch in ("{", "["):
            start = i
            start_char = ch
            break

    if start == -1:
        print(f"[GROQ] No JSON found in response:\n{content[:500]}")
        return {}

    json_str = content[start:]

    try:
        obj, _ = json.JSONDecoder().raw_decode(json_str)
    except json.JSONDecodeError as e:
        print(f"[GROQ] JSONDecodeError: {e}")
        print(f"[GROQ] Content snippet:\n{json_str[:500]}")
        return {}

    # If we got a proper dict, return it directly
    if isinstance(obj, dict):
        return obj

    # Some models return a malformed array like:
    # [{"candidate": {...}}, "job", ":", {...}, "rules", ":", [...]]
    # Reconstruct into a proper dict
    if isinstance(obj, list):
        result: Dict[str, Any] = {}
        i = 0
        while i < len(obj):
            item = obj[i]
            if isinstance(item, dict):
                result.update(item)
                i += 1
            elif isinstance(item, str) and i + 1 < len(obj):
                key = item
                # skip optional ":" string element
                next_i = i + 1
                if next_i < len(obj) and obj[next_i] == ":":
                    next_i += 1
                if next_i < len(obj):
                    result[key] = obj[next_i]
                    i = next_i + 1
                else:
                    i += 1
            else:
                i += 1
        return result

    return {}


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, ""):
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float = 0.8) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_date(value: Any) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        for pattern in ("%B %Y", "%b %Y", "%Y"):
            try:
                return datetime.strptime(str(value).strip(), pattern).date()
            except ValueError:
                continue
        return None


def _as_list(value: Any) -> list:
    return value if isinstance(value, list) else []


def _build_evidence(source_document: str, items: List[Dict[str, Any]]) -> List[Evidence]:
    evidence_items = []
    for item in _as_list(items):
        if not isinstance(item, dict):
            continue
        snippet = str(item.get("snippet", "")).strip()
        if not snippet:
            continue
        evidence_items.append(
            Evidence(
                source_document=source_document,
                snippet=snippet,
                page=_safe_int(item.get("page"), default=1),
                confidence=max(0.0, min(1.0, _safe_float(item.get("confidence"), default=0.8))),
            )
        )
    return evidence_items


def extract_screening_request(
    resume_text: str,
    jd_text: str,
    mandatory_rule_notes: str = "",
) -> ScreeningRequest:
    client = _build_client()
    prompt = f"""
You are given a Resume, a Job Description, and optional Mandatory Rule Notes.
Extract all information from these texts and return it as a JSON object.

INSTRUCTIONS:
1. Read the RESUME TEXT carefully. Extract the candidate's full name, total years/months of experience, and ALL skills mentioned with their estimated durations.
   Also extract contact details, location, current role, dated work history, education,
   certifications, domains, links, notable achievements, work authorization, notice period,
   and any factual resume concerns as red_flags. Keep evidence snippets tied to the resume.
2. Read the JD TEXT carefully. Extract the role title, experience requirements, and required/preferred skills.
   Also extract location, work authorization, maximum notice period, required domains, and explicit red flags.
3. If MANDATORY RULE NOTES are provided, convert them into structured rules. Treat each stated minimum, required item, or must-have as a knockout with severity "hard_fail". Use severity "soft" only when the notes explicitly say preferred, nice-to-have, or soft requirement. Otherwise return an empty rules array.
4. Return ONLY the JSON object below, filled with REAL data from the texts. Replace ALL example values.

IMPORTANT: Convert years to months (e.g. 2 years = 24 months, 1.5 years = 18 months).

Return this exact JSON structure filled with real extracted data:
{{
  "candidate": {{
    "candidate_id": "cand-001",
    "full_name": "REPLACE WITH REAL NAME FROM RESUME",
    "email": null,
    "phone": null,
    "location": null,
    "current_title": null,
    "current_company": null,
    "total_experience_months": 0,
    "skills": [
      {{
        "skill": "REPLACE WITH REAL SKILL",
        "months": 0,
        "evidence": [{{"snippet": "REPLACE WITH QUOTE FROM RESUME", "page": 1, "confidence": 0.9}}]
      }}
    ],
    "experiences": [{{"title": "", "company": "", "start_date": "YYYY-MM-DD", "end_date": null, "skills_used": [], "domains": [], "evidence": []}}],
    "education": [{{"degree": "", "field": "", "school": "", "year": null, "evidence": []}}],
    "certifications": [],
    "languages": [],
    "domains": [],
    "notable_achievements": [],
    "linkedin_url": null,
    "github_url": null,
    "portfolio_url": null,
    "work_authorization": null,
    "notice_period_days": null,
    "red_flags": [],
    "fields_for_review": [
      {{
        "name": "Total Experience",
        "ai_value": "REPLACE WITH VALUE",
        "human_value": "",
        "review_status": "pending",
        "evidence": [{{"snippet": "REPLACE WITH QUOTE", "page": 1, "confidence": 0.9}}]
      }}
    ]
  }},
  "job": {{
    "role_title": "REPLACE WITH ROLE FROM JD",
    "min_total_experience_months": 0,
    "mandatory_skills": [],
    "preferred_skills": [],
    "required_domains": [],
    "location": null,
    "work_authorization_required": null,
    "max_notice_period_days": null,
    "red_flags": []
  }},
  "rules": []
}}

Valid rule types (only use if MANDATORY RULE NOTES are provided):
- "skill_min_months": requires skill + min_months
- "skill_required": requires skill only
- "total_experience_min_months": requires min_months only
- "education_required": requires expected_value (degree/field/school)
- "location_required": requires expected_value
- "notice_period_max_days": requires max_days
- "work_authorization_required": requires expected_value
- "domain_required": requires domain or expected_value

RESUME TEXT:
{resume_text}

JD TEXT:
{jd_text}

MANDATORY RULE NOTES:
{mandatory_rule_notes}
"""

    completion = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT.strip()},
            {"role": "user", "content": prompt.strip()},
        ],
        temperature=0.2,
    )
    global _last_raw_response
    raw_content = completion.choices[0].message.content or "{}"
    _last_raw_response = raw_content
    print(f"[GROQ RAW RESPONSE]:\n{raw_content[:2000]}")
    payload = _extract_json(raw_content)
    if not isinstance(payload, dict):
        payload = {}

    candidate_data = payload.get("candidate", {})
    if not isinstance(candidate_data, dict):
        candidate_data = {}
    skills = []
    for item in _as_list(candidate_data.get("skills")):
        if not isinstance(item, dict):
            continue
        skill_name = str(item.get("skill", "")).strip()
        if not skill_name:
            continue
        skills.append(
            SkillExperience(
                skill=skill_name,
                months=_safe_int(item.get("months"), 0),
                evidence=_build_evidence("resume", item.get("evidence", [])),
            )
        )

    review_fields = []
    for item in _as_list(candidate_data.get("fields_for_review")):
        if not isinstance(item, dict):
            continue
        field_name = str(item.get("name", "")).strip()
        if not field_name:
            continue
        review_status = str(item.get("review_status", ReviewStatus.pending.value))
        if review_status not in {status.value for status in ReviewStatus}:
            review_status = ReviewStatus.pending.value
        review_fields.append(
            ExtractedField(
                name=field_name,
                ai_value=str(item.get("ai_value", "")),
                human_value=str(item.get("human_value", "")).strip() or None,
                review_status=ReviewStatus(review_status),
                evidence=_build_evidence("resume", item.get("evidence", [])),
            )
        )

    experiences = []
    for item in _as_list(candidate_data.get("experiences")):
        if not isinstance(item, dict):
            continue
        start_date = _safe_date(item.get("start_date"))
        if not start_date:
            continue
        experiences.append(
            ExperienceEntry(
                title=str(item.get("title", "")).strip(),
                company=str(item.get("company", "")).strip(),
                start_date=start_date,
                end_date=_safe_date(item.get("end_date")),
                skills_used=[str(value).strip() for value in _as_list(item.get("skills_used")) if str(value).strip()],
                domains=[str(value).strip() for value in _as_list(item.get("domains")) if str(value).strip()],
                evidence=_build_evidence("resume", item.get("evidence", [])),
            )
        )

    education = []
    for item in _as_list(candidate_data.get("education")):
        if not isinstance(item, dict):
            continue
        year = _safe_int(item.get("year"), 0) or None
        education.append(
            EducationEntry(
                degree=str(item.get("degree", "")).strip(),
                field=str(item.get("field", "")).strip(),
                school=str(item.get("school", "")).strip(),
                year=year,
                evidence=_build_evidence("resume", item.get("evidence", [])),
            )
        )

    candidate = CandidateProfile(
        candidate_id=str(candidate_data.get("candidate_id", "cand-001")),
        full_name=str(candidate_data.get("full_name", "")).strip() or None,
        email=str(candidate_data.get("email", "")).strip() or None,
        phone=str(candidate_data.get("phone", "")).strip() or None,
        location=str(candidate_data.get("location", "")).strip() or None,
        current_title=str(candidate_data.get("current_title", "")).strip() or None,
        current_company=str(candidate_data.get("current_company", "")).strip() or None,
        total_experience_months=_safe_int(candidate_data.get("total_experience_months"), 0),
        skills=skills,
        experiences=experiences,
        education=education,
        certifications=[str(value).strip() for value in _as_list(candidate_data.get("certifications")) if str(value).strip()],
        languages=[str(value).strip() for value in _as_list(candidate_data.get("languages")) if str(value).strip()],
        domains=[str(value).strip() for value in _as_list(candidate_data.get("domains")) if str(value).strip()],
        notable_achievements=[str(value).strip() for value in _as_list(candidate_data.get("notable_achievements")) if str(value).strip()],
        linkedin_url=str(candidate_data.get("linkedin_url", "")).strip() or None,
        github_url=str(candidate_data.get("github_url", "")).strip() or None,
        portfolio_url=str(candidate_data.get("portfolio_url", "")).strip() or None,
        work_authorization=str(candidate_data.get("work_authorization", "")).strip() or None,
        notice_period_days=_safe_int(candidate_data.get("notice_period_days"), 0) or None,
        red_flags=[str(value).strip() for value in _as_list(candidate_data.get("red_flags")) if str(value).strip()],
        fields_for_review=review_fields,
    )

    job_data = payload.get("job", {})
    if not isinstance(job_data, dict):
        job_data = {}
    job = JobRequirement(
        role_title=str(job_data.get("role_title", "")).strip(),
        min_total_experience_months=_safe_int(job_data.get("min_total_experience_months"), 0),
        mandatory_skills=[str(item).strip() for item in _as_list(job_data.get("mandatory_skills")) if str(item).strip()],
        preferred_skills=[str(item).strip() for item in _as_list(job_data.get("preferred_skills")) if str(item).strip()],
        required_domains=[str(item).strip() for item in _as_list(job_data.get("required_domains")) if str(item).strip()],
        location=str(job_data.get("location", "")).strip() or None,
        work_authorization_required=str(job_data.get("work_authorization_required", "")).strip() or None,
        max_notice_period_days=_safe_int(job_data.get("max_notice_period_days"), 0) or None,
        red_flags=[str(item).strip() for item in _as_list(job_data.get("red_flags")) if str(item).strip()],
    )

    rules = []
    for item in _as_list(payload.get("rules")):
        if not isinstance(item, dict):
            continue
        severity_value = str(item.get("severity", Severity.hard_fail.value))
        if severity_value not in {severity.value for severity in Severity}:
            severity_value = Severity.hard_fail.value
        rule_id = str(item.get("id", "")).strip()
        rule_type = str(item.get("type", "")).strip()
        if not rule_type:
            continue
        # Auto-generate an id if the model omitted it
        if not rule_id:
            rule_id = f"rule-{len(rules) + 1:03d}"
        rules.append(
            MandatoryRule(
                id=rule_id,
                type=rule_type,
                severity=Severity(severity_value),
                weight=_safe_int(item.get("weight"), 0),
                skill=str(item.get("skill", "")).strip() or None,
                min_months=_safe_int(item.get("min_months"), 0) if item.get("min_months") not in (None, "") else None,
                max_days=_safe_int(item.get("max_days"), 0) if item.get("max_days") not in (None, "") else None,
                domain=str(item.get("domain", "")).strip() or None,
                expected_value=str(item.get("expected_value", "")).strip() or None,
            )
        )

    return ScreeningRequest(candidate=candidate, job=job, rules=rules)
