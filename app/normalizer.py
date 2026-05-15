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

def normalize_skill_name(raw_name: str) -> str:
    name = raw_name.strip()
    lower_name = name.lower()
    return SKILL_SYNONYMS.get(lower_name, name)

def normalize_candidate_profile(candidate: CandidateProfile) -> CandidateProfile:
    """
    Normalizes candidate data before scoring.
    - Aggregates duplicate skills (e.g. JS + JavaScript -> single JavaScript entry with summed months).
    """
    aggregated_skills = {}
    for skill in candidate.skills:
        normalized_name = normalize_skill_name(skill.skill)
        if normalized_name in aggregated_skills:
            aggregated_skills[normalized_name].months += skill.months
            aggregated_skills[normalized_name].evidence.extend(skill.evidence)
        else:
            aggregated_skills[normalized_name] = SkillExperience(
                skill=normalized_name,
                months=skill.months,
                evidence=list(skill.evidence)
            )
            
    candidate.skills = list(aggregated_skills.values())
    return candidate
