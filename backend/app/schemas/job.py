from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
from datetime import datetime

class JobBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    company: str = Field(..., min_length=2, max_length=255)
    description: str = Field(..., min_length=10)
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    experience_years: float = Field(0.0, ge=0.0, le=50.0)
    education_level: str = Field("Bachelor's", max_length=100)
    location: str = Field("Remote", max_length=255)
    employment_type: str = Field("Full-time", max_length=100)
    salary_range: Optional[str] = None
    contact_email: Optional[EmailStr] = Field(None, description="Contact email for job applications")

class JobCreate(JobBase):
    pass

class JobUpdate(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    description: Optional[str] = None
    required_skills: Optional[List[str]] = None
    preferred_skills: Optional[List[str]] = None
    experience_years: Optional[float] = None
    education_level: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    salary_range: Optional[str] = None
    contact_email: Optional[EmailStr] = None

class JobResponse(JobBase):
    id: int
    created_by_user_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class JobListResponse(BaseModel):
    jobs: List[JobResponse]
    total: int

