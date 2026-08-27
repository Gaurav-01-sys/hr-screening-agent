from __future__ import annotations

from typing import List, Optional

from .normalizer import comparison_key, skill_matches
from .schemas import CandidateProfile, MandatoryRule, RuleResult, Severity


def _find_skill_data(candidate: CandidateProfile, skill_name: str) -> tuple[Optional[int], list]:
    total_months = 0
    found = False
    evidence = []

    for item in candidate.skills:
        if skill_matches(item.skill, skill_name):
            total_months += item.months
            found = True
            evidence.extend(item.evidence)

    return (total_months, evidence) if found else (None, [])


def _field_evidence(candidate: CandidateProfile, names: set[str]) -> list:
    evidence = []
    for field in candidate.fields_for_review:
        if comparison_key(field.name) in {comparison_key(name) for name in names}:
            evidence.extend(field.evidence)
    return evidence


def _contains_value(actual: Optional[str], expected: Optional[str]) -> bool:
    if not actual or not expected:
        return False
    actual_key = comparison_key(actual)
    expected_key = comparison_key(expected)
    return actual_key == expected_key or expected_key in actual_key or actual_key in expected_key


def _domain_values(candidate: CandidateProfile) -> list[str]:
    values = list(candidate.domains)
    for experience in candidate.experiences:
        values.extend(experience.domains)
    return values


def evaluate_rules(candidate: CandidateProfile, rules: List[MandatoryRule]) -> List[RuleResult]:
    results: List[RuleResult] = []

    for rule in rules:
        if rule.type == "skill_min_months" and rule.skill and rule.min_months is not None:
            actual_months, evidence = _find_skill_data(candidate, rule.skill)
            passed = actual_months is not None and actual_months >= rule.min_months
            message = (
                f"{rule.skill} experience requirement met ({actual_months} months found)"
                if passed
                else f"{rule.skill} experience is {actual_months or 0} months, below required {rule.min_months} months"
            )
            results.append(
                RuleResult(
                    rule_id=rule.id,
                    passed=passed,
                    severity=rule.severity,
                    weight=rule.weight,
                    message=message,
                    evidence=evidence,
                )
            )
            continue

        if rule.type == "skill_required" and rule.skill:
            actual_months, evidence = _find_skill_data(candidate, rule.skill)
            matched = actual_months is not None
            message = (
                f"Required skill {rule.skill} found"
                if matched
                else f"Required skill {rule.skill} not found"
            )
            results.append(
                RuleResult(
                    rule_id=rule.id,
                    passed=matched,
                    severity=rule.severity,
                    weight=rule.weight,
                    message=message,
                    evidence=evidence,
                )
            )
            continue

        if rule.type == "total_experience_min_months" and rule.min_months is not None:
            passed = candidate.total_experience_months >= rule.min_months
            message = (
                f"Total experience requirement met ({candidate.total_experience_months} >= {rule.min_months} months)"
                if passed
                else f"Total experience is {candidate.total_experience_months} months, below required {rule.min_months} months"
            )
            results.append(
                RuleResult(
                    rule_id=rule.id,
                    passed=passed,
                    severity=rule.severity,
                    weight=rule.weight,
                    message=message,
                    evidence=[],
                )
            )
            continue

        if rule.type == "education_required":
            expected = rule.expected_value or rule.skill
            actual = [" ".join(value for value in [item.degree, item.field, item.school] if value) for item in candidate.education]
            passed = any(_contains_value(value, expected) for value in actual)
            message = (
                f"Required education found ({expected})" if passed
                else f"Required education {expected or 'qualification'} not found"
            )
            results.append(RuleResult(rule_id=rule.id, passed=passed, severity=rule.severity,
                                      weight=rule.weight, message=message,
                                      evidence=_field_evidence(candidate, {"education", "degree"})))
            continue

        if rule.type == "location_required":
            expected = rule.expected_value or rule.domain or rule.skill
            passed = _contains_value(candidate.location, expected)
            message = (
                f"Location requirement met ({candidate.location})" if passed
                else f"Location {expected or 'requirement'} not confirmed"
            )
            results.append(RuleResult(rule_id=rule.id, passed=passed, severity=rule.severity,
                                      weight=rule.weight, message=message,
                                      evidence=_field_evidence(candidate, {"location"})))
            continue

        if rule.type == "notice_period_max_days":
            maximum = rule.max_days if rule.max_days is not None else rule.min_months
            actual = candidate.notice_period_days
            passed = actual is not None and maximum is not None and actual <= maximum
            message = (
                f"Notice period requirement met ({actual} days <= {maximum})" if passed
                else f"Notice period is {actual if actual is not None else 'unknown'} days, maximum is {maximum}"
            )
            results.append(RuleResult(rule_id=rule.id, passed=passed, severity=rule.severity,
                                      weight=rule.weight, message=message,
                                      evidence=_field_evidence(candidate, {"notice period", "notice_period_days"})))
            continue

        if rule.type == "work_authorization_required":
            expected = rule.expected_value or "authorized"
            passed = _contains_value(candidate.work_authorization, expected)
            message = (
                "Work authorization requirement confirmed" if passed
                else f"Work authorization {expected} not confirmed"
            )
            results.append(RuleResult(rule_id=rule.id, passed=passed, severity=rule.severity,
                                      weight=rule.weight, message=message,
                                      evidence=_field_evidence(candidate, {"work authorization", "work_authorization"})))
            continue

        if rule.type in {"domain_required", "domain_experience_required"}:
            expected = rule.domain or rule.expected_value
            domains = _domain_values(candidate)
            passed = any(_contains_value(value, expected) for value in domains)
            message = (
                f"Required domain found ({expected})" if passed
                else f"Required domain {expected or 'domain'} not found"
            )
            results.append(RuleResult(rule_id=rule.id, passed=passed, severity=rule.severity,
                                      weight=rule.weight, message=message,
                                      evidence=_field_evidence(candidate, {"domain", "domains"})))
            continue

        results.append(
            RuleResult(
                rule_id=rule.id,
                passed=False,
                severity=Severity.soft,
                weight=0,
                message=f"Unsupported or incomplete rule definition for {rule.id}",
            )
        )

    return results
