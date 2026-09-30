from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default="user", nullable=False)  # "user" or "admin"
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")
    analyses = relationship("ResumeAnalysis", back_populates="user", cascade="all, delete-orphan")
    created_jobs = relationship("Job", back_populates="creator")

class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_type = Column(String(50), nullable=False)  # "pdf" or "docx"
    file_size_bytes = Column(Integer, nullable=False)
    raw_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    # Relationships
    user = relationship("User", back_populates="resumes")
    analysis = relationship("ResumeAnalysis", back_populates="resume", uselist=False, cascade="all, delete-orphan")

class ResumeAnalysis(Base):
    __tablename__ = "resume_analyses"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Profile & Contact
    candidate_name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(100), nullable=True)
    location = Column(String(255), nullable=True)
    
    # Core Analysis Content
    professional_summary = Column(Text, nullable=True)
    technical_skills = Column(JSON, default=list, nullable=False)
    soft_skills = Column(JSON, default=list, nullable=False)
    education = Column(JSON, default=list, nullable=False)      # list of dicts: degree, institution, year, field
    experience = Column(JSON, default=list, nullable=False)     # list of dicts: title, company, duration, description
    projects = Column(JSON, default=list, nullable=False)       # list of dicts: name, description, technologies
    certifications = Column(JSON, default=list, nullable=False) # list of str
    languages = Column(JSON, default=list, nullable=False)      # list of str

    # Evaluative Insights
    strengths = Column(JSON, default=list, nullable=False)
    weaknesses = Column(JSON, default=list, nullable=False)
    missing_areas = Column(JSON, default=list, nullable=False)
    recommended_improvements = Column(JSON, default=list, nullable=False)
    
    ai_provider_used = Column(String(50), default="cascade", nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    # Relationships
    resume = relationship("Resume", back_populates="analysis")
    user = relationship("User", back_populates="analyses")
    recommendations = relationship("Recommendation", back_populates="analysis", cascade="all, delete-orphan")

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), index=True, nullable=False)
    company = Column(String(255), index=True, nullable=False)
    description = Column(Text, nullable=False)
    required_skills = Column(JSON, default=list, nullable=False)
    preferred_skills = Column(JSON, default=list, nullable=False)
    experience_years = Column(Float, default=0.0, nullable=False)
    education_level = Column(String(100), default="Bachelor's", nullable=False)
    location = Column(String(255), default="Remote", nullable=False)
    employment_type = Column(String(100), default="Full-time", nullable=False)
    salary_range = Column(String(100), nullable=True)
    contact_email = Column(String(255), nullable=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    creator = relationship("User", back_populates="created_jobs")
    recommendations = relationship("Recommendation", back_populates="job", cascade="all, delete-orphan")

class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("resume_analyses.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Detailed Multi-dimensional Scores
    match_score = Column(Float, nullable=False)        # 0.0 - 100.0
    skill_score = Column(Float, nullable=False)        # 0.0 - 100.0
    experience_score = Column(Float, nullable=False)   # 0.0 - 100.0
    education_score = Column(Float, nullable=False)    # 0.0 - 100.0
    semantic_score = Column(Float, nullable=False)     # 0.0 - 100.0

    # Detailed Breakdown
    matching_skills = Column(JSON, default=list, nullable=False)
    missing_skills = Column(JSON, default=list, nullable=False)
    relevant_experience = Column(Text, nullable=True)
    match_explanation = Column(Text, nullable=False)
    gaps_identified = Column(JSON, default=list, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    # Relationships
    analysis = relationship("ResumeAnalysis", back_populates="recommendations")
    job = relationship("Job", back_populates="recommendations")

class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    category = Column(String(100), index=True, nullable=False)  # "job_description", "skill_description", "career_roadmap", "learning_resource", "resume_guideline"
    source = Column(String(255), default="curated", nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    # Relationships
    chunks = relationship("KnowledgeChunk", back_populates="document", cascade="all, delete-orphan")

class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(JSON, nullable=True)  # List[float] embedding vector
    token_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    # Relationships
    document = relationship("KnowledgeDocument", back_populates="chunks")
