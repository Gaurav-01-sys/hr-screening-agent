from __future__ import annotations

from datetime import date
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class ReviewStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    corrected = "corrected"
    rejected = "rejected"


class Severity(str, Enum):
    hard_fail = "hard_fail"
    soft = "soft"


class Recommendation(str, Enum):
    strong_fit = "strong_fit"
    borderline = "borderline"
    reject = "reject"
    needs_review = "needs_review"


class Evidence(BaseModel):
    source_document: str = Field(..., description="resume or jd")
    snippet: str
    page: Optional[int] = None
    bbox: Optional[List[float]] = Field(
        default=None,
        description="Optional [x1, y1, x2, y2] bounding box from parser output",
    )
    confidence: float = 0.0


class ExtractedField(BaseModel):
    name: str
    ai_value: str
    human_value: Optional[str] = None
    review_status: ReviewStatus = ReviewStatus.pending
    evidence: List[Evidence] = Field(default_factory=list)

    @property
    def effective_value(self) -> str:
        return self.human_value if self.human_value else self.ai_value


class SkillExperience(BaseModel):
    skill: str
    months: int
    evidence: List[Evidence] = Field(default_factory=list)


class ExperienceEntry(BaseModel):
    title: str
    company: str
    start_date: date
    end_date: Optional[date] = None
    skills_used: List[str] = Field(default_factory=list)
    evidence: List[Evidence] = Field(default_factory=list)


class CandidateProfile(BaseModel):
    candidate_id: str
    full_name: Optional[str] = None
    total_experience_months: int = 0
    skills: List[SkillExperience] = Field(default_factory=list)
    experiences: List[ExperienceEntry] = Field(default_factory=list)
    fields_for_review: List[ExtractedField] = Field(default_factory=list)


class JobRequirement(BaseModel):
    role_title: str
    min_total_experience_months: int = 0
    mandatory_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    required_domains: List[str] = Field(default_factory=list)


class MandatoryRule(BaseModel):
    id: str
    type: str
    severity: Severity
    weight: int = 0
    skill: Optional[str] = None
    min_months: Optional[int] = None
    domain: Optional[str] = None
    expected_value: Optional[str] = None


class ScreeningRequest(BaseModel):
    candidate: CandidateProfile
    job: JobRequirement
    rules: List[MandatoryRule] = Field(default_factory=list)


class RuleResult(BaseModel):
    rule_id: str
    passed: bool
    severity: Severity
    weight: int
    message: str
    evidence: List[Evidence] = Field(default_factory=list)


class ScoreBreakdown(BaseModel):
    mandatory_fit: float
    experience_depth: float
    skill_match: float
    domain_relevance: float
    recency: float
    evidence_confidence: float
    final_score: float


class ScreeningResponse(BaseModel):
    recommendation: Recommendation
    hard_fail: bool
    rule_results: List[RuleResult]
    scores: ScoreBreakdown
    explanation: str
