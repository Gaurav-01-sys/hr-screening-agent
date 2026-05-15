from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .database import Base

class ScreeningRun(Base):
    __tablename__ = "screening_runs"
    
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(String, index=True)
    role_title = Column(String, index=True)
    recommendation = Column(String)
    hard_fail = Column(Boolean)
    explanation = Column(String)
    
    # Score fields
    mandatory_fit = Column(Float)
    experience_depth = Column(Float)
    skill_match = Column(Float)
    domain_relevance = Column(Float)
    recency = Column(Float)
    evidence_confidence = Column(Float)
    final_score = Column(Float)
    
    # Relationships
    candidate = relationship("CandidateModel", back_populates="run", uselist=False, cascade="all, delete-orphan")
    job = relationship("JobModel", back_populates="run", uselist=False, cascade="all, delete-orphan")
    rules = relationship("RuleModel", back_populates="run", cascade="all, delete-orphan")
    rule_results = relationship("RuleResultModel", back_populates="run", cascade="all, delete-orphan")

class CandidateModel(Base):
    __tablename__ = "candidates"
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("screening_runs.id"))
    candidate_id = Column(String)
    full_name = Column(String, nullable=True)
    total_experience_months = Column(Integer)
    
    run = relationship("ScreeningRun", back_populates="candidate")
    skills = relationship("SkillModel", back_populates="candidate", cascade="all, delete-orphan")
    experiences = relationship("ExperienceModel", back_populates="candidate", cascade="all, delete-orphan")
    fields_for_review = relationship("ReviewFieldModel", back_populates="candidate", cascade="all, delete-orphan")

class SkillModel(Base):
    __tablename__ = "candidate_skills"
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"))
    skill = Column(String)
    months = Column(Integer)
    evidence = Column(JSON)
    
    candidate = relationship("CandidateModel", back_populates="skills")

class ExperienceModel(Base):
    __tablename__ = "candidate_experiences"
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"))
    title = Column(String)
    company = Column(String)
    start_date = Column(String)
    end_date = Column(String, nullable=True)
    skills_used = Column(JSON)
    evidence = Column(JSON)
    
    candidate = relationship("CandidateModel", back_populates="experiences")

class ReviewFieldModel(Base):
    __tablename__ = "candidate_review_fields"
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"))
    name = Column(String)
    ai_value = Column(String)
    human_value = Column(String, nullable=True)
    review_status = Column(String)
    evidence = Column(JSON)
    
    candidate = relationship("CandidateModel", back_populates="fields_for_review")

class JobModel(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("screening_runs.id"))
    role_title = Column(String)
    min_total_experience_months = Column(Integer)
    mandatory_skills = Column(JSON)
    preferred_skills = Column(JSON)
    required_domains = Column(JSON)
    
    run = relationship("ScreeningRun", back_populates="job")

class RuleModel(Base):
    __tablename__ = "rules"
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("screening_runs.id"))
    rule_id_str = Column(String)
    type = Column(String)
    severity = Column(String)
    weight = Column(Integer)
    skill = Column(String, nullable=True)
    min_months = Column(Integer, nullable=True)
    domain = Column(String, nullable=True)
    expected_value = Column(String, nullable=True)
    
    run = relationship("ScreeningRun", back_populates="rules")

class RuleResultModel(Base):
    __tablename__ = "rule_results"
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("screening_runs.id"))
    rule_id_str = Column(String)
    passed = Column(Boolean)
    severity = Column(String)
    weight = Column(Integer)
    message = Column(String)
    evidence = Column(JSON)
    
    run = relationship("ScreeningRun", back_populates="rule_results")
