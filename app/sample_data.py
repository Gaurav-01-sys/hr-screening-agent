from __future__ import annotations

from datetime import date

from .schemas import (
    CandidateProfile,
    Evidence,
    ExperienceEntry,
    ExtractedField,
    JobRequirement,
    MandatoryRule,
    ReviewStatus,
    ScreeningRequest,
    Severity,
    SkillExperience,
)


def build_sample_request() -> ScreeningRequest:
    tableau_evidence = Evidence(
        source_document="resume",
        snippet="Created Tableau dashboards during internship from Jan 2024 to Mar 2024.",
        page=2,
        confidence=0.88,
    )

    sql_evidence = Evidence(
        source_document="resume",
        snippet="Worked on SQL-based reporting automation for customer analytics.",
        page=2,
        confidence=0.92,
    )

    candidate = CandidateProfile(
        candidate_id="cand-001",
        full_name="Sample Candidate",
        total_experience_months=30,
        skills=[
            SkillExperience(skill="Tableau", months=3, evidence=[tableau_evidence]),
            SkillExperience(skill="SQL", months=24, evidence=[sql_evidence]),
        ],
        experiences=[
            ExperienceEntry(
                title="Data Analyst Intern",
                company="Example Corp",
                start_date=date(2024, 1, 1),
                end_date=date(2024, 3, 31),
                skills_used=["Tableau", "SQL"],
                evidence=[tableau_evidence, sql_evidence],
            )
        ],
        fields_for_review=[
            ExtractedField(
                name="tableau_experience_months",
                ai_value="3",
                review_status=ReviewStatus.approved,
                evidence=[tableau_evidence],
            ),
            ExtractedField(
                name="sql_experience_months",
                ai_value="24",
                review_status=ReviewStatus.approved,
                evidence=[sql_evidence],
            ),
        ],
    )

    job = JobRequirement(
        role_title="BI Analyst",
        min_total_experience_months=24,
        mandatory_skills=["Tableau", "SQL"],
        preferred_skills=["Python", "Power BI"],
        required_domains=["Retail"],
    )

    rules = [
        MandatoryRule(
            id="tableau_min_exp",
            type="skill_min_months",
            severity=Severity.hard_fail,
            weight=25,
            skill="Tableau",
            min_months=24,
        ),
        MandatoryRule(
            id="sql_required",
            type="skill_required",
            severity=Severity.hard_fail,
            weight=20,
            skill="SQL",
        ),
    ]

    return ScreeningRequest(candidate=candidate, job=job, rules=rules)
