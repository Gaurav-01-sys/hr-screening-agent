from __future__ import annotations

from typing import List, Optional

from .schemas import CandidateProfile, MandatoryRule, RuleResult, Severity


def _find_skill_months(candidate: CandidateProfile, skill_name: str) -> Optional[int]:
    for item in candidate.skills:
        if item.skill.lower() == skill_name.lower():
            return item.months
    return None


def evaluate_rules(candidate: CandidateProfile, rules: List[MandatoryRule]) -> List[RuleResult]:
    results: List[RuleResult] = []

    for rule in rules:
        if rule.type == "skill_min_months" and rule.skill and rule.min_months is not None:
            actual_months = _find_skill_months(candidate, rule.skill)
            passed = actual_months is not None and actual_months >= rule.min_months
            message = (
                f"{rule.skill} experience requirement met"
                if passed
                else f"{rule.skill} experience is {actual_months or 0} months, below required {rule.min_months} months"
            )
            evidence = []
            for skill in candidate.skills:
                if skill.skill.lower() == rule.skill.lower():
                    evidence = skill.evidence
                    break
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
            matched = _find_skill_months(candidate, rule.skill) is not None
            message = (
                f"Required skill {rule.skill} found"
                if matched
                else f"Required skill {rule.skill} not found"
            )
            evidence = []
            if matched:
                for skill in candidate.skills:
                    if skill.skill.lower() == rule.skill.lower():
                        evidence = skill.evidence
                        break
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
