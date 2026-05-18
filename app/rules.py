from __future__ import annotations

from typing import List, Optional

from .schemas import CandidateProfile, MandatoryRule, RuleResult, Severity


def _find_skill_data(candidate: CandidateProfile, skill_name: str) -> tuple[Optional[int], list]:
    target_lower = skill_name.lower()
    sql_variants = ["mysql", "postgresql", "postgres", "mssql", "sql server", "oracle", "pl/sql", "tsql", "sql"]
    is_sql_search = target_lower == "sql"

    total_months = 0
    found = False
    evidence = []
    
    for item in candidate.skills:
        item_lower = item.skill.lower()
        # Semantic matching rules:
        # 1. Exact match
        # 2. Substring match (e.g., target "Tableau" found in "Tableau Desktop")
        # 3. SQL variants (if target is "SQL", accept variants)
        if (
            target_lower == item_lower or
            target_lower in item_lower or
            (is_sql_search and item_lower in sql_variants)
        ):
            total_months += item.months
            found = True
            evidence.extend(item.evidence)
            
    return (total_months, evidence) if found else (None, [])


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
