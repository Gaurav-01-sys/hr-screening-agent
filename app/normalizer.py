import re
from typing import Optional

from .schemas import CandidateProfile, ReviewStatus, SkillExperience

SKILL_SYNONYMS = {
    "js": "JavaScript",
    "react": "React.js",
    "reactjs": "React.js",
    "node": "Node.js",
    "nodejs": "Node.js",
    "ts": "TypeScript",
    "k8s": "Kubernetes",
    "aws": "Amazon Web Services",
    "gcp": "Google Cloud Platform",
    "ml": "Machine Learning",
    "ai": "Artificial Intelligence",
    "nlp": "Natural Language Processing",
    "postgres": "PostgreSQL",
    "sql server": "Microsoft SQL Server",
    "mssql": "Microsoft SQL Server",
    "c#": "C#",
    "c++": "C++",
    "vue": "Vue.js",
    "vuejs": "Vue.js"
}

# These aliases are intentionally small and transparent. They are used only to
# compare job criteria with extracted evidence; they do not infer experience.
_COMPARISON_ALIASES = {
    "postgres": "postgresql",
    "mssql": "sql server",
    "tsql": "sql",
    "plsql": "sql",
    "pl/sql": "sql",
    "js": "javascript",
    "ts": "typescript",
    "node": "node.js",
    "nodejs": "node.js",
    "reactjs": "react.js",
    "react": "react.js",
    "k8s": "kubernetes",
    "ml": "machine learning",
    "ai": "artificial intelligence",
}

def normalize_skill_name(raw_name: str) -> str:
    name = raw_name.strip()
    lower_name = name.lower()
    return SKILL_SYNONYMS.get(lower_name, name)


def comparison_key(value: str) -> str:
    """Return a stable key for evidence-backed, case-insensitive matching."""
    value = re.sub(r"[^a-z0-9+#./ -]+", " ", str(value).lower()).strip()
    value = re.sub(r"[-_/]+", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    compact = value.replace(" ", "")
    return _COMPARISON_ALIASES.get(compact, _COMPARISON_ALIASES.get(value, value))


def skill_matches(candidate_skill: str, requested_skill: str) -> bool:
    """Match common spelling/variant differences without fuzzy overmatching."""
    candidate_key = comparison_key(candidate_skill)
    requested_key = comparison_key(requested_skill)
    if not candidate_key or not requested_key:
        return False
    if candidate_key == requested_key:
        return True
    if requested_key == "sql" and candidate_key in {
        "sql", "postgresql", "postgres", "mysql", "mssql", "sql server", "oracle", "sqlite"
    }:
        return True
    # Allow qualified labels such as ``Tableau Desktop`` for ``Tableau``.
    return requested_key in candidate_key.split("/") or requested_key in candidate_key.split()


_REVIEW_FIELD_ALIASES = {
    "name": "full_name",
    "full name": "full_name",
    "fullname": "full_name",
    "email": "email",
    "phone": "phone",
    "telephone": "phone",
    "location": "location",
    "current title": "current_title",
    "currenttitle": "current_title",
    "current company": "current_company",
    "currentcompany": "current_company",
    "total experience": "total_experience_months",
    "total experience months": "total_experience_months",
    "totalexperiencemonths": "total_experience_months",
    "experience": "total_experience_months",
    "notice period": "notice_period_days",
    "notice period days": "notice_period_days",
    "noticeperioddays": "notice_period_days",
    "work authorization": "work_authorization",
    "work authorization status": "work_authorization",
    "workauthorization": "work_authorization",
    "domains": "domains",
    "domain": "domains",
    "certifications": "certifications",
    "certification": "certifications",
    "languages": "languages",
    "language": "languages",
    "red flags": "red_flags",
    "red flags to review": "red_flags",
    "redflags": "red_flags",
}


def _review_field_target(field_name: str) -> Optional[str]:
    key = comparison_key(field_name)
    key = key.rsplit(".", 1)[-1]
    return _REVIEW_FIELD_ALIASES.get(key)


def _review_list_value(raw_value: Optional[str]) -> list[str]:
    if not raw_value:
        return []
    return list(dict.fromkeys(item.strip() for item in raw_value.split(",") if item.strip()))


def _review_months_value(raw_value: Optional[str]) -> int:
    if not raw_value:
        return 0
    normalized = raw_value.lower()
    years = re.search(r"(\d+(?:\.\d+)?)\s*(?:years?|yrs?)", normalized)
    months = re.search(r"(\d+(?:\.\d+)?)\s*(?:months?|mos?)", normalized)
    total = 0.0
    if years:
        total += float(years.group(1)) * 12
    if months:
        total += float(months.group(1))
    if total:
        return max(0, round(total))
    number = re.search(r"\d+", normalized)
    return int(number.group(0)) if number else 0


def _review_int_value(raw_value: Optional[str]) -> Optional[int]:
    if not raw_value:
        return None
    number = re.search(r"\d+", raw_value)
    return int(number.group(0)) if number else None


def apply_review_overrides(candidate: CandidateProfile) -> CandidateProfile:
    """Apply human corrections before rules and scoring consume candidate facts."""
    for field in candidate.fields_for_review:
        target = _review_field_target(field.name)
        if not target:
            continue

        rejected = field.review_status == ReviewStatus.rejected
        if not rejected and not field.human_value:
            # CandidateProfile already contains the AI value. Do not overwrite
            # a direct reviewer edit with a stale pending/approved AI value.
            continue
        raw_value = None if rejected else field.human_value.strip()

        if target == "total_experience_months":
            candidate.total_experience_months = _review_months_value(raw_value)
        elif target == "notice_period_days":
            candidate.notice_period_days = _review_int_value(raw_value)
        elif target in {"domains", "certifications", "languages", "red_flags"}:
            setattr(candidate, target, _review_list_value(raw_value))
        else:
            setattr(candidate, target, raw_value or None)

    return candidate

def normalize_candidate_profile(candidate: CandidateProfile) -> CandidateProfile:
    """
    Normalizes candidate data before scoring.
    - Aggregates duplicate skills (e.g. JS + JavaScript -> single JavaScript entry with summed months).
    """
    apply_review_overrides(candidate)
    aggregated_skills = {}
    for skill in candidate.skills:
        normalized_name = normalize_skill_name(skill.skill)
        key = comparison_key(normalized_name)
        if key in aggregated_skills:
            aggregated_skills[key].months += max(0, skill.months)
            aggregated_skills[key].evidence.extend(skill.evidence)
        else:
            aggregated_skills[key] = SkillExperience(
                skill=normalized_name,
                months=max(0, skill.months),
                evidence=list(skill.evidence)
            )

    candidate.skills = list(aggregated_skills.values())
    candidate.domains = list(dict.fromkeys(item.strip() for item in candidate.domains if item.strip()))
    return candidate
