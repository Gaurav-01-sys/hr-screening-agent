from __future__ import annotations

from datetime import date
from typing import List

from .communications import build_communication_draft
from .interview import generate_interview_questions
from .normalizer import comparison_key, skill_matches
from .schemas import (
    CandidateProfile,
    ExtractedField,
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


def _matching_skill_count(candidate: CandidateProfile, requested: List[str]) -> int:
    return sum(
        1
        for skill in requested
        if any(skill_matches(item.skill, skill) for item in candidate.skills)
    )


def _average_evidence_confidence(candidate: CandidateProfile) -> float:
    confidences = []
    for item in candidate.skills:
        confidences.extend(evidence.confidence for evidence in item.evidence)
    for item in candidate.experiences:
        confidences.extend(evidence.confidence for evidence in item.evidence)
    for item in candidate.education:
        confidences.extend(evidence.confidence for evidence in item.evidence)
    for field in candidate.fields_for_review:
        confidences.extend(evidence.confidence for evidence in field.evidence)
    if not confidences:
        return 0.5
    return max(0.0, min(sum(confidences) / len(confidences), 1.0))


def _domain_relevance(candidate: CandidateProfile, job: JobRequirement) -> float:
    required = [comparison_key(value) for value in job.required_domains if value.strip()]
    if not required:
        return 0.5
    available = [comparison_key(value) for value in candidate.domains]
    for experience in candidate.experiences:
        available.extend(comparison_key(value) for value in experience.domains)
    if not available:
        return 0.0
    hits = sum(1 for item in required if any(item == value or item in value or value in item for value in available))
    return hits / len(required)


def _recency(candidate: CandidateProfile) -> float:
    """Estimate recency from dated experience without rewarding missing dates."""
    if not candidate.experiences:
        return 0.5
    today = date.today()
    scores = []
    for experience in candidate.experiences:
        end = experience.end_date or today
        months_since = max(0, (today.year - end.year) * 12 + today.month - end.month)
        scores.append(max(0.0, 1.0 - months_since / 60.0))
    return sum(scores) / len(scores)


def _field_needs_review(field: ExtractedField) -> bool:
    if field.review_status.value in {"pending", "rejected"}:
        return True
    if field.review_status.value == "corrected" and not field.human_value:
        return True
    if field.review_status.value == "approved" and not (field.human_value or field.ai_value):
        return True
    return False


def build_screening_response(
    candidate: CandidateProfile,
    job: JobRequirement,
    rule_results: List[RuleResult],
) -> ScreeningResponse:
    hard_fail = any(not item.passed and item.severity == Severity.hard_fail for item in rule_results)
    review_required = any(_field_needs_review(field) for field in candidate.fields_for_review)

    mandatory_skills = list(dict.fromkeys(job.mandatory_skills))
    preferred_skills = list(dict.fromkeys(job.preferred_skills))
    mandatory_hits = _matching_skill_count(candidate, mandatory_skills)
    preferred_hits = _matching_skill_count(candidate, preferred_skills)

    mandatory_fit = mandatory_hits / len(mandatory_skills) if mandatory_skills else 1.0
    experience_depth = _bounded_ratio(candidate.total_experience_months, job.min_total_experience_months)
    skill_match = preferred_hits / len(preferred_skills) if preferred_skills else 1.0
    domain_relevance = _domain_relevance(candidate, job)
    recency = _recency(candidate)
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
    final_score = max(0.0, min(100.0, weighted_score - soft_penalty))

    if hard_fail:
        final_score = min(final_score, 35.0)
        recommendation = Recommendation.reject
    elif review_required:
        recommendation = Recommendation.needs_review
    elif final_score >= 80:
        recommendation = Recommendation.strong_fit
    elif final_score >= 55:
        recommendation = Recommendation.borderline
    else:
        recommendation = Recommendation.reject

    if recommendation == Recommendation.needs_review:
        grade = "PENDING"
    elif final_score >= 90:
        grade = "A"
    elif final_score >= 80:
        grade = "B"
    elif final_score >= 70:
        grade = "C"
    elif final_score >= 60:
        grade = "D"
    else:
        grade = "F"

    passed_rules = [item for item in rule_results if item.passed]
    failed_rules = [item for item in rule_results if not item.passed]
    strengths = []
    if mandatory_hits:
        strengths.append(f"Meets {mandatory_hits}/{len(mandatory_skills)} mandatory skill criteria")
    if candidate.total_experience_months and candidate.total_experience_months >= job.min_total_experience_months:
        strengths.append(f"Has {candidate.total_experience_months} months of total experience")
    if preferred_hits:
        strengths.append(f"Matches {preferred_hits}/{len(preferred_skills)} preferred skills")
    strengths.extend(item.message for item in passed_rules[:2])

    concerns = [item.message for item in failed_rules]
    if review_required:
        concerns.insert(0, "One or more extracted fields still require human verification")
    red_flags = list(dict.fromkeys(candidate.red_flags))

    if recommendation == Recommendation.strong_fit:
        next_action = "invite_to_interview"
    elif recommendation == Recommendation.reject:
        next_action = "reject_with_human_review"
    else:
        next_action = "manual_review"

    if mandatory_skills:
        explanation_lines = [
            f"The candidate matches {mandatory_hits} of {len(mandatory_skills)} mandatory skills "
            f"and brings {candidate.total_experience_months} months of experience."
        ]
    else:
        explanation_lines = [
            f"No mandatory skills were specified; the candidate brings {candidate.total_experience_months} months of experience."
        ]
    if soft_penalty:
        explanation_lines.append(
            f"The review applied {soft_penalty} points for unmet secondary requirements."
        )
    else:
        explanation_lines.append("No secondary requirements reduced the score.")
    if hard_fail:
        explanation_lines.append("However, at least one required condition was not met.")
    if review_required:
        explanation_lines.append("A human reviewer still needs to verify one or more extracted fields.")
    if red_flags:
        explanation_lines.append(
            f"The reviewer should also look at {len(red_flags)} flagged item(s) in the resume."
        )

    response = ScreeningResponse(
        recommendation=recommendation,
        grade=grade,
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
        strengths=strengths,
        concerns=concerns,
        red_flags=red_flags,
        next_action=next_action,
    )
    response.interview_questions = generate_interview_questions(candidate, job, rule_results)
    response.communication_draft = build_communication_draft(candidate, job, response)
    return response
