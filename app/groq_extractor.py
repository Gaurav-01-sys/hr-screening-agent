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
You are an information extraction engine for HR resume screening.
Return valid JSON only.
Do not add markdown fences.
Use evidence snippets copied from the input text when possible.
Be conservative. If something is missing, leave it blank or use 0.
"""


def groq_is_configured() -> bool:
    return bool(GROQ_API_KEY) and Groq is not None


def _build_client() -> Groq:
    if Groq is None:
        raise ValueError("groq package is not installed. Run: pip install groq")
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not configured.")
    return Groq(api_key=GROQ_API_KEY)


def _extract_json(content: str) -> Dict[str, Any]:
    content = content.strip()
    # Strip markdown if present
    if content.startswith("```json"):
        content = content[7:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()

    # Sometimes the model appends extra text after the valid JSON object.
    # raw_decode reads the first valid JSON object and ignores the rest.
    try:
        obj, _ = json.JSONDecoder().raw_decode(content)
        return obj
    except json.JSONDecodeError as e:
        print(f"JSONDecodeError: {e}")
        print(f"Failed JSON string:\n{content}")
        raise ValueError(f"Failed to decode JSON: {e}")


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
Extract resume screening data from the following inputs.

Return a JSON object with this exact top-level structure:
{{
  "candidate": {{
    "candidate_id": "cand-001",
    "full_name": "",
    "total_experience_months": 0,
    "skills": [
      {{
        "skill": "",
        "months": 0,
        "evidence": [{{"snippet": "", "page": 1, "confidence": 0.8}}]
      }}
    ],
    "fields_for_review": [
      {{
        "name": "",
        "ai_value": "",
        "human_value": "",
        "review_status": "pending",
        "evidence": [{{"snippet": "", "page": 1, "confidence": 0.8}}]
      }}
    ]
  }},
  "job": {{
    "role_title": "",
    "min_total_experience_months": 0,
    "mandatory_skills": [],
    "preferred_skills": [],
    "required_domains": []
  }},
  "rules": [
    // Array of rule objects. Leave this array EMPTY if no mandatory rules are found in the notes.
    // Valid types: "skill_min_months", "skill_required", "total_experience_min_months"
    // Example:
    // {{
    //   "id": "rule-001",
    //   "type": "skill_min_months",
    //   "severity": "hard_fail",
    //   "weight": 25,
    //   "skill": "Python",
    //   "min_months": 24,
    //   "domain": "",
    //   "expected_value": ""
    // }}
  ]
}}

- Infer skill duration conservatively from the resume text.
- If mandatory rule notes specify thresholds like years or months, convert them into structured rules.
- Add review rows for important extracted values such as skill durations and total experience.
- Keep unsupported values empty rather than inventing details.
- Do NOT generate placeholder or blank rules. If no valid rules are found, return an empty "rules" array [].

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
        response_format={"type": "json_object"},
    )
    payload = _extract_json(completion.choices[0].message.content or "{}")
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
        if not rule_id or not rule_type:
            continue
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
