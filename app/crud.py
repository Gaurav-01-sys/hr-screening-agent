from sqlalchemy.orm import Session
from . import models, schemas

def save_screening_run(db: Session, request: schemas.ScreeningRequest, response: schemas.ScreeningResponse) -> models.ScreeningRun:
    db_run = models.ScreeningRun(
        candidate_id=request.candidate.candidate_id,
        role_title=request.job.role_title,
        recommendation=response.recommendation.value,
        hard_fail=response.hard_fail,
        explanation=response.explanation,
        mandatory_fit=response.scores.mandatory_fit,
        experience_depth=response.scores.experience_depth,
        skill_match=response.scores.skill_match,
        domain_relevance=response.scores.domain_relevance,
        recency=response.scores.recency,
        evidence_confidence=response.scores.evidence_confidence,
        final_score=response.scores.final_score,
    )
    db.add(db_run)
    db.flush()

    db_candidate = models.CandidateModel(
        run_id=db_run.id,
        candidate_id=request.candidate.candidate_id,
        full_name=request.candidate.full_name,
        email=request.candidate.email,
        phone=request.candidate.phone,
        location=request.candidate.location,
        current_title=request.candidate.current_title,
        current_company=request.candidate.current_company,
        total_experience_months=request.candidate.total_experience_months,
        domains=request.candidate.domains,
        certifications=request.candidate.certifications,
        work_authorization=request.candidate.work_authorization,
        notice_period_days=request.candidate.notice_period_days,
        red_flags=request.candidate.red_flags,
    )
    db.add(db_candidate)
    db.flush()

    for skill in request.candidate.skills:
        db.add(models.SkillModel(
            candidate_id=db_candidate.id,
            skill=skill.skill,
            months=skill.months,
            evidence=[e.model_dump() for e in skill.evidence]
        ))
        
    for exp in request.candidate.experiences:
        db.add(models.ExperienceModel(
            candidate_id=db_candidate.id,
            title=exp.title,
            company=exp.company,
            start_date=str(exp.start_date),
            end_date=str(exp.end_date) if exp.end_date else None,
            skills_used=exp.skills_used,
            domains=exp.domains,
            evidence=[e.model_dump() for e in exp.evidence]
        ))
        
    for field in request.candidate.fields_for_review:
        db.add(models.ReviewFieldModel(
            candidate_id=db_candidate.id,
            name=field.name,
            ai_value=field.ai_value,
            human_value=field.human_value,
            review_status=field.review_status.value,
            evidence=[e.model_dump() for e in field.evidence]
        ))

    db_job = models.JobModel(
        run_id=db_run.id,
        role_title=request.job.role_title,
        min_total_experience_months=request.job.min_total_experience_months,
        mandatory_skills=request.job.mandatory_skills,
        preferred_skills=request.job.preferred_skills,
        required_domains=request.job.required_domains,
        location=request.job.location,
        work_authorization_required=request.job.work_authorization_required,
        max_notice_period_days=request.job.max_notice_period_days,
        red_flags=request.job.red_flags,
    )
    db.add(db_job)

    for rule in request.rules:
        db.add(models.RuleModel(
            run_id=db_run.id,
            rule_id_str=rule.id,
            type=rule.type,
            severity=rule.severity.value,
            weight=rule.weight,
            skill=rule.skill,
            min_months=rule.min_months,
            max_days=rule.max_days,
            domain=rule.domain,
            expected_value=rule.expected_value
        ))

    for rr in response.rule_results:
        db.add(models.RuleResultModel(
            run_id=db_run.id,
            rule_id_str=rr.rule_id,
            passed=rr.passed,
            severity=rr.severity.value,
            weight=rr.weight,
            message=rr.message,
            evidence=[e.model_dump() for e in rr.evidence]
        ))

    db.commit()
    db.refresh(db_run)
    return db_run
