import re

from .schemas import CandidateProfile, SkillExperience

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

def normalize_candidate_profile(candidate: CandidateProfile) -> CandidateProfile:
    """
    Normalizes candidate data before scoring.
    - Aggregates duplicate skills (e.g. JS + JavaScript -> single JavaScript entry with summed months).
    """
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
