from __future__ import annotations

from typing import List, Set

from .schemas import (
    CandidateProfile,
    JobRequirement,
    Recommendation,
    RuleResult,
    ScoreBreakdown,
    ScreeningResponse,
    Severity,
)


def _bounded_ratio(value: float, maximum: float) -> float:
    if maximum <= 0:
        return 1.0
    return max(0.0, min(value / maximum, 1.0))


def _candidate_skill_set(candidate: CandidateProfile) -> Set[str]:
    return {item.skill.lower() for item in candidate.skills}


def _average_evidence_confidence(candidate: CandidateProfile) -> float:
    confidences = []
    for field in candidate.fields_for_review:
        for evidence in field.evidence:
            confidences.append(evidence.confidence)
    if not confidences:
        return 0.5
    return sum(confidences) / len(confidences)


def build_screening_response(
    candidate: CandidateProfile,
    job: JobRequirement,
    rule_results: List[RuleResult],
) -> ScreeningResponse:
    hard_fail = any(not item.passed and item.severity == Severity.hard_fail for item in rule_results)
    pending_review = any(field.review_status == "pending" for field in candidate.fields_for_review)

    mandatory_total = max(len(job.mandatory_skills), 1)
    candidate_skills = _candidate_skill_set(candidate)
    mandatory_hits = sum(1 for skill in job.mandatory_skills if skill.lower() in candidate_skills)
    preferred_hits = sum(1 for skill in job.preferred_skills if skill.lower() in candidate_skills)

    mandatory_fit = mandatory_hits / mandatory_total
    experience_depth = _bounded_ratio(
        candidate.total_experience_months,
        max(job.min_total_experience_months, 1),
    )
    skill_denominator = max(len(job.preferred_skills), 1)
    skill_match = preferred_hits / skill_denominator
    domain_relevance = 0.5
    recency = 0.7
    evidence_confidence = _average_evidence_confidence(candidate)

    weighted_score = (
        0.40 * mandatory_fit
        + 0.25 * experience_depth
        + 0.15 * skill_match
        + 0.10 * domain_relevance
        + 0.05 * recency
        + 0.05 * evidence_confidence
    ) * 100.0

    soft_penalty = sum(item.weight for item in rule_results if not item.passed and item.severity == Severity.soft)
    final_score = max(0.0, weighted_score - soft_penalty)

    if hard_fail:
        final_score = min(final_score, 35.0)
        recommendation = Recommendation.reject
    elif pending_review:
        recommendation = Recommendation.needs_review
    elif final_score >= 80:
        recommendation = Recommendation.strong_fit
    elif final_score >= 55:
        recommendation = Recommendation.borderline
    else:
        recommendation = Recommendation.reject

    explanation_lines = [
        f"Mandatory skill match: {mandatory_hits}/{mandatory_total}",
        f"Total experience: {candidate.total_experience_months} months",
        f"Soft rule penalties applied: {soft_penalty}",
    ]
    if hard_fail:
        explanation_lines.append("One or more hard-fail rules were not satisfied.")
    if pending_review:
        explanation_lines.append("At least one extracted field still requires human verification.")

    return ScreeningResponse(
        recommendation=recommendation,
        hard_fail=hard_fail,
        rule_results=rule_results,
        scores=ScoreBreakdown(
            mandatory_fit=round(mandatory_fit, 3),
            experience_depth=round(experience_depth, 3),
            skill_match=round(skill_match, 3),
            domain_relevance=round(domain_relevance, 3),
            recency=round(recency, 3),
            evidence_confidence=round(evidence_confidence, 3),
            final_score=round(final_score, 2),
        ),
        explanation=" ".join(explanation_lines),
    )
