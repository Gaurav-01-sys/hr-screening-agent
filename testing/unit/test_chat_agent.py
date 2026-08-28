import asyncio

from fastapi.testclient import TestClient

from app.chat_agent import HRChatAgent
from app.main import app
from app.schemas import (
    CandidateProfile,
    ChatMessage,
    JobRequirement,
    Recommendation,
    RuleResult,
    ScoreBreakdown,
    ScreeningResponse,
    Severity,
)


def _context() -> tuple[CandidateProfile, JobRequirement, ScreeningResponse]:
    candidate = CandidateProfile(
        candidate_id="chat-candidate",
        full_name="Alex Example",
        total_experience_months=36,
    )
    job = JobRequirement(role_title="BI Analyst")
    response = ScreeningResponse(
        recommendation=Recommendation.borderline,
        hard_fail=False,
        rule_results=[
            RuleResult(
                rule_id="tableau",
                passed=False,
                severity=Severity.soft,
                weight=1,
                message="Tableau experience is below the required 24 months.",
            )
        ],
        scores=ScoreBreakdown(
            mandatory_fit=0.5,
            experience_depth=0.5,
            skill_match=0.5,
            domain_relevance=0.5,
            recency=0.5,
            evidence_confidence=0.8,
            final_score=50,
        ),
        explanation="Review required.",
    )
    return candidate, job, response


def test_chat_answers_from_facts_and_rejects_absent_facts():
    candidate, job, response = _context()
    agent = HRChatAgent(candidate, job, response)

    experience = asyncio.run(
        agent.respond([ChatMessage(role="user", content="What is the candidate's total experience?")])
    )
    absent = asyncio.run(
        agent.respond([ChatMessage(role="user", content="What is the candidate's favorite food?")])
    )

    assert "36 months" in experience.reply.content
    assert experience.sources == ["screening/hall_facts/candidate"]
    assert "not available in the screening memory" in absent.reply.content
    assert absent.sources == []


def test_chat_explains_recorded_rule_result():
    candidate, job, response = _context()
    result = asyncio.run(
        HRChatAgent(candidate, job, response).respond(
            [ChatMessage(role="user", content="Why did the Tableau rule fail?")]
        )
    )

    assert "tableau: failed" in result.reply.content.lower()
    assert result.sources == ["screening/hall_decision/rule:tableau"]


def test_chat_endpoint_returns_chat_response():
    candidate, job, response = _context()
    client = TestClient(app)
    result = client.post(
        "/chat",
        json={
            "messages": [
                {"role": "user", "content": "What is the candidate's total experience?"}
            ],
            "candidate": candidate.model_dump(mode="json"),
            "job": job.model_dump(mode="json"),
            "response": response.model_dump(mode="json"),
        },
    )

    assert result.status_code == 200
    assert result.json()["reply"]["role"] == "assistant"
    assert "36 months" in result.json()["reply"]["content"]
