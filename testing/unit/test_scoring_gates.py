from app import scoring
from app.rules import evaluate_rules
from app.schemas import CandidateProfile, JobRequirement, MandatoryRule, Severity, SkillExperience


def test_failed_mandatory_threshold_cannot_be_strong_fit(monkeypatch):
    monkeypatch.setattr(scoring, "build_communication_draft", lambda *args: "draft")

    candidate = CandidateProfile(
        candidate_id="c-threshold-gap",
        total_experience_months=36,
        skills=[
            SkillExperience(skill="Tableau", months=18),
            SkillExperience(skill="SQL", months=48),
        ],
        domains=["Retail"],
    )
    job = JobRequirement(
        role_title="Business Intelligence Analyst",
        min_total_experience_months=36,
        mandatory_skills=["Tableau", "SQL"],
        required_domains=["Retail"],
    )
    rules = [
        MandatoryRule(
            id="rule-001",
            type="skill_min_months",
            severity=Severity.soft,
            skill="Tableau",
            min_months=36,
        ),
        MandatoryRule(
            id="rule-002",
            type="skill_required",
            severity=Severity.soft,
            skill="SQL",
        ),
    ]

    response = scoring.build_screening_response(candidate, job, evaluate_rules(candidate, rules))

    assert response.recommendation.value == "borderline"
    assert response.scores.final_score < 80
    assert response.scores.mandatory_fit == 0.5
    assert "cannot be classified as a Strong Fit" in response.explanation


def test_hard_fail_is_a_reject_gate_and_score_cap(monkeypatch):
    monkeypatch.setattr(scoring, "build_communication_draft", lambda *args: "draft")

    candidate = CandidateProfile(candidate_id="c-hard-fail", total_experience_months=60)
    job = JobRequirement(role_title="Analyst")
    rule = MandatoryRule(
        id="authorization",
        type="work_authorization_required",
        severity=Severity.hard_fail,
        expected_value="Canada",
    )

    response = scoring.build_screening_response(candidate, job, evaluate_rules(candidate, [rule]))

    assert response.recommendation.value == "reject"
    assert response.hard_fail is True
    assert response.scores.final_score <= scoring.HARD_FAIL_SCORE_CAP
