from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime

class EducationItem(BaseModel):
    degree: str = Field(..., description="Degree or qualification name (e.g. B.S. in Computer Science)")
    institution: str = Field(..., description="University, college, or school name")
    year: Optional[str] = Field(None, description="Graduation year or date range")
    field: Optional[str] = Field(None, description="Field of study or major")

class ExperienceItem(BaseModel):
    title: str = Field(..., description="Job role or title")
    company: str = Field(..., description="Company or organization name")
    duration: Optional[str] = Field(None, description="Employment dates or duration")
    description: Optional[str] = Field(None, description="Core responsibilities and achievements")

class ProjectItem(BaseModel):
    name: str = Field(..., description="Project name")
    description: Optional[str] = Field(None, description="Summary of the project")
    technologies: List[str] = Field(default_factory=list, description="Technologies and tools used")

class StructuredResumeProfile(BaseModel):
    """Strict structured schema extracted by the Resume Analyzer Agent."""
    candidate_name: Optional[str] = Field(None, description="Candidate's full name")
    email: Optional[str] = Field(None, description="Candidate's email address")
    phone: Optional[str] = Field(None, description="Candidate's phone number")
    location: Optional[str] = Field(None, description="Candidate's location or address")
    professional_summary: Optional[str] = Field(None, description="Summary of professional background and expertise")
    technical_skills: List[str] = Field(default_factory=list, description="Extracted hard technical skills, languages, tools")
    soft_skills: List[str] = Field(default_factory=list, description="Extracted interpersonal and soft skills")
    education: List[EducationItem] = Field(default_factory=list, description="List of educational qualifications")
    experience: List[ExperienceItem] = Field(default_factory=list, description="List of work experiences")
    projects: List[ProjectItem] = Field(default_factory=list, description="List of relevant personal or academic projects")
    certifications: List[str] = Field(default_factory=list, description="List of professional certifications")
    languages: List[str] = Field(default_factory=list, description="Languages spoken")
    strengths: List[str] = Field(default_factory=list, description="Key candidate strengths identified from the resume")
    weaknesses: List[str] = Field(default_factory=list, description="Identified resume weaknesses or presentation gaps")
    missing_areas: List[str] = Field(default_factory=list, description="Missing sections, details, or metrics")
    recommended_improvements: List[str] = Field(default_factory=list, description="Concrete resume improvement suggestions")

class ResumeAnalysisResponse(BaseModel):
    id: int
    resume_id: int
    user_id: int
    candidate_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    professional_summary: Optional[str] = None
    technical_skills: List[str] = []
    soft_skills: List[str] = []
    education: List[Dict[str, Any]] = []
    experience: List[Dict[str, Any]] = []
    projects: List[Dict[str, Any]] = []
    certifications: List[str] = []
    languages: List[str] = []
    strengths: List[str] = []
    weaknesses: List[str] = []
    missing_areas: List[str] = []
    recommended_improvements: List[str] = []
    ai_provider_used: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
