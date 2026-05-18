from __future__ import annotations

import json
from typing import Any, Dict, List

try:
    from groq import Groq
except ImportError:  # pragma: no cover
    Groq = None

from .config import GROQ_API_KEY, GROQ_MODEL
from .schemas import (
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


SYSTEM_PROMPT = """
You are an expert HR resume screening assistant.
Your job is to READ the provided resume and job description texts and EXTRACT real information from them.
Always return a single valid JSON object. No markdown fences. No extra text.
Extract as much data as possible. Do NOT leave fields empty if the information exists in the text.
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


def _build_evidence(source_document: str, items: List[Dict[str, Any]]) -> List[Evidence]:
    evidence_items = []
    for item in items or []:
        snippet = str(item.get("snippet", "")).strip()
        if not snippet:
            continue
        evidence_items.append(
            Evidence(
                source_document=source_document,
                snippet=snippet,
                page=_safe_int(item.get("page"), default=1),
                confidence=_safe_float(item.get("confidence"), default=0.8),
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
2. Read the JD TEXT carefully. Extract the role title, experience requirements, and required/preferred skills.
3. If MANDATORY RULE NOTES are provided, convert them into structured rules. Otherwise return an empty rules array.
4. Return ONLY the JSON object below, filled with REAL data from the texts. Replace ALL example values.

IMPORTANT: Convert years to months (e.g. 2 years = 24 months, 1.5 years = 18 months).

Return this exact JSON structure filled with real extracted data:
{{
  "candidate": {{
    "candidate_id": "cand-001",
    "full_name": "REPLACE WITH REAL NAME FROM RESUME",
    "total_experience_months": 0,
    "skills": [
      {{
        "skill": "REPLACE WITH REAL SKILL",
        "months": 0,
        "evidence": [{{"snippet": "REPLACE WITH QUOTE FROM RESUME", "page": 1, "confidence": 0.9}}]
      }}
    ],
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
    "required_domains": []
  }},
  "rules": []
}}

Valid rule types (only use if MANDATORY RULE NOTES are provided):
- "skill_min_months": requires skill + min_months
- "skill_required": requires skill only
- "total_experience_min_months": requires min_months only

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
    skills = []
    for item in candidate_data.get("skills", []):
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
    for item in candidate_data.get("fields_for_review", []):
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

    candidate = CandidateProfile(
        candidate_id=str(candidate_data.get("candidate_id", "cand-001")),
        full_name=str(candidate_data.get("full_name", "")).strip() or None,
        total_experience_months=_safe_int(candidate_data.get("total_experience_months"), 0),
        skills=skills,
        fields_for_review=review_fields,
    )

    job_data = payload.get("job", {})
    job = JobRequirement(
        role_title=str(job_data.get("role_title", "")).strip(),
        min_total_experience_months=_safe_int(job_data.get("min_total_experience_months"), 0),
        mandatory_skills=[str(item).strip() for item in job_data.get("mandatory_skills", []) if str(item).strip()],
        preferred_skills=[str(item).strip() for item in job_data.get("preferred_skills", []) if str(item).strip()],
        required_domains=[str(item).strip() for item in job_data.get("required_domains", []) if str(item).strip()],
    )

    rules = []
    for item in payload.get("rules", []):
        severity_value = str(item.get("severity", Severity.soft.value))
        if severity_value not in {severity.value for severity in Severity}:
            severity_value = Severity.soft.value
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
                domain=str(item.get("domain", "")).strip() or None,
                expected_value=str(item.get("expected_value", "")).strip() or None,
            )
        )

    return ScreeningRequest(candidate=candidate, job=job, rules=rules)
