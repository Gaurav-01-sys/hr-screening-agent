from app.normalizer import normalize_candidate_profile
from app.rules import evaluate_rules
from app.schemas import (
    CandidateProfile,
    EducationEntry,
    JobRequirement,
    MandatoryRule,
    ReviewStatus,
    Severity,
    SkillExperience,
    ExtractedField,
)
from app.scoring import build_screening_response


def test_skill_variants_are_aggregated_and_sql_rule_matches_variants():
    candidate = CandidateProfile(
        candidate_id="c-1",
        skills=[SkillExperience(skill="js", months=6), SkillExperience(skill="JavaScript", months=12), SkillExperience(skill="PostgreSQL", months=18)],
    )
    normalized = normalize_candidate_profile(candidate)
    assert len(normalized.skills) == 2
    assert next(item.months for item in normalized.skills if item.skill == "JavaScript") == 18
    result = evaluate_rules(normalized, [MandatoryRule(id="sql", type="skill_required", severity=Severity.hard_fail, skill="SQL")])[0]
    assert result.passed is True


def test_job_related_rules_cover_education_location_notice_and_authorization():
    candidate = CandidateProfile(
        candidate_id="c-2",
        location="Toronto, Canada",
        work_authorization="Canada work permit",
        notice_period_days=14,
        education=[EducationEntry(degree="BSc", field="Computer Science", school="Example University")],
    )
    rules = [
        MandatoryRule(id="edu", type="education_required", severity=Severity.hard_fail, expected_value="Computer Science"),
        MandatoryRule(id="loc", type="location_required", severity=Severity.hard_fail, expected_value="Canada"),
        MandatoryRule(id="notice", type="notice_period_max_days", severity=Severity.soft, max_days=30),
        MandatoryRule(id="auth", type="work_authorization_required", severity=Severity.hard_fail, expected_value="Canada"),
    ]
    assert all(item.passed for item in evaluate_rules(candidate, rules))


def test_pending_review_cannot_produce_positive_automatic_recommendation():
    candidate = CandidateProfile(
        candidate_id="c-3",
        total_experience_months=60,
        skills=[SkillExperience(skill="Python", months=60)],
        fields_for_review=[ExtractedField(name="location", ai_value="Remote", review_status=ReviewStatus.pending)],
    )
    job = JobRequirement(role_title="Senior Python Engineer", min_total_experience_months=36, mandatory_skills=["Python"])
    response = build_screening_response(candidate, job, [])
    assert response.recommendation.value == "needs_review"
    assert response.next_action == "manual_review"
    assert response.interview_questions
    assert response.communication_draft.startswith("Internal draft")


def test_response_contains_interview_guide_and_draft_for_rejection():
    candidate = CandidateProfile(candidate_id="c-4", full_name="Alex Example")
    job = JobRequirement(role_title="Data Analyst", mandatory_skills=["Tableau"])
    rules = [MandatoryRule(id="tableau", type="skill_required", severity=Severity.hard_fail, skill="Tableau")]
    response = build_screening_response(candidate, job, evaluate_rules(candidate, rules))
    assert response.recommendation.value == "reject"
    assert response.next_action == "reject_with_human_review"
    assert response.communication_draft and "do not" not in response.communication_draft.lower()
