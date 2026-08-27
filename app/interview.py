"""Structured, evidence-linked interview prompts for shortlisted candidates.

Questions are generated after scoring and are drafts for an interviewer. The
module never changes a recommendation and never evaluates a candidate's
answer, which keeps the high-stakes decision with a trained human reviewer.
"""

from __future__ import annotations

from typing import List

from .normalizer import skill_matches
from .schemas import CandidateProfile, InterviewQuestion, JobRequirement, RuleResult


def _skill_evidence(candidate: CandidateProfile, requested: str) -> str | None:
    for item in candidate.skills:
        if skill_matches(item.skill, requested):
            if item.evidence:
                return item.evidence[0].snippet
            return None
    return None


def generate_interview_questions(
    candidate: CandidateProfile,
    job: JobRequirement,
    rule_results: List[RuleResult],
    max_questions: int = 8,
) -> List[InterviewQuestion]:
    """Create a consistent mix of technical and behavioral questions."""
    questions: List[InterviewQuestion] = []
    mandatory = list(dict.fromkeys(job.mandatory_skills))

    for skill in mandatory[:3]:
        anchor = _skill_evidence(candidate, skill)
        questions.append(
            InterviewQuestion(
                question=f"Walk us through the most production-critical work you have done with {skill}. What was your specific contribution and what changed as a result?",
                type="technical",
                purpose=f"Validate applied {skill} depth behind the resume claim.",
                good_answer_signals="Clear ownership, technical trade-offs, scale or constraints, and measurable outcomes.",
                evidence_anchor=anchor,
            )
        )

    failed = [item for item in rule_results if not item.passed]
    for item in failed[:2]:
        questions.append(
            InterviewQuestion(
                question=f"Please describe a recent example that demonstrates the requirement behind {item.rule_id}. What evidence would you use to show your level of experience?",
                type="verification",
                purpose=f"Resolve the screening concern: {item.message}",
                good_answer_signals="Specific example, accurate timeline, personal ownership, and evidence that directly addresses the requirement.",
            )
        )

    questions.extend(
        [
            InterviewQuestion(
                question="Tell us about a time you had to make a difficult prioritization decision with incomplete information. What did you choose and what did you learn?",
                type="behavioral",
                purpose="Assess judgment, prioritization, and learning agility.",
                good_answer_signals="Structured reasoning, stakeholder awareness, explicit trade-offs, and reflection on the outcome.",
            ),
            InterviewQuestion(
                question="Describe a disagreement with a stakeholder or teammate about an important deliverable. How did you reach a decision?",
                type="behavioral",
                purpose="Assess collaboration, communication, and conflict handling.",
                good_answer_signals="Respectful communication, evidence-based influence, shared decision-making, and accountability.",
            ),
            InterviewQuestion(
                question=f"What would you aim to understand and deliver in your first 30 days as a {job.role_title or 'new team member'}?",
                type="situational",
                purpose="Assess role understanding and practical onboarding approach.",
                good_answer_signals="A realistic learning plan, stakeholder map, early wins, and measurable success criteria.",
            ),
        ]
    )
    return questions[:max_questions]
