from app import communications
from app.memory import build_screening_memory, render_memory_context
from app.schemas import (
    CandidateProfile,
    Evidence,
    JobRequirement,
    Recommendation,
    ScoreBreakdown,
    ScreeningResponse,
    SkillExperience,
)


def _response(recommendation: Recommendation, concerns: list[str] | None = None) -> ScreeningResponse:
    return ScreeningResponse(
        recommendation=recommendation,
        hard_fail=recommendation == Recommendation.reject,
        rule_results=[],
        scores=ScoreBreakdown(
            mandatory_fit=0.5,
            experience_depth=0.5,
            skill_match=0.5,
            domain_relevance=0.5,
            recency=0.5,
            evidence_confidence=0.8,
            final_score=50,
        ),
        explanation="A human-readable explanation.",
        concerns=concerns or [],
    )


def test_fallback_draft_uses_recruiter_language(monkeypatch):
    monkeypatch.setattr(communications, "GROQ_API_KEY", "")
    candidate = CandidateProfile(
        candidate_id="c-1",
        full_name="Alex Example",
        skills=[SkillExperience(skill="Python", months=12)],
    )
    job = JobRequirement(role_title="Data Analyst", mandatory_skills=["Python"])
    response = _response(
        Recommendation.reject,
        ["Python experience is 12 months, below required 24 months"],
    )

    draft = communications.build_communication_draft(candidate, job, response)

    assert "mandatory skill criteria" not in draft
    assert "the role asks for at least 24 months of Python experience" in draft
    assert "Hi Alex" in draft


def test_memory_context_keeps_evidence_in_labeled_drawers():
    candidate = CandidateProfile(
        candidate_id="c-2",
        full_name="Jordan Example",
        skills=[
            SkillExperience(
                skill="Tableau",
                months=30,
                evidence=[Evidence(source_document="resume", snippet="Built Tableau dashboards for retail teams.")],
            )
        ],
    )
    job = JobRequirement(role_title="BI Analyst", mandatory_skills=["Tableau"])

    context = render_memory_context(build_screening_memory(candidate, job))

    assert "screening/hall_evidence/skill:tableau" in context
    assert "Built Tableau dashboards for retail teams." in context
