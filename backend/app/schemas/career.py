from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class CareerQuestionRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000)
    resume_id: Optional[int] = Field(None, description="Optional resume ID to personalize advice")
    target_role: Optional[str] = Field(None, description="Optional target role (e.g. Senior Backend Engineer)")

class RetrievedChunkInfo(BaseModel):
    document_title: str
    category: str
    snippet: str
    similarity_score: float

class CareerRoadmapStep(BaseModel):
    step_number: int
    phase: str
    focus_skills: List[str]
    description: str
    recommended_certifications: List[str] = []
    recommended_courses: List[str] = []

class CareerQuestionResponse(BaseModel):
    question: str
    answer: str
    grounded_by_rag: bool
    retrieved_sources: List[RetrievedChunkInfo] = []
    recommended_skills: List[str] = []
    suggested_certifications: List[str] = []
    suggested_resources: List[Dict[str, str]] = []
    career_roadmap: List[CareerRoadmapStep] = []
    ai_provider_used: str

class CareerGuidanceOverview(BaseModel):
    resume_id: int
    candidate_name: Optional[str] = None
    target_recommendations: List[str] = []
    missing_critical_skills: List[str] = []
    learning_roadmap: List[CareerRoadmapStep] = []
    suggested_certifications: List[str] = []
    curated_resources: List[Dict[str, str]] = []
