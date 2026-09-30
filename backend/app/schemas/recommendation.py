from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime
from app.schemas.job import JobResponse

class ScoreBreakdown(BaseModel):
    skill_score: float
    experience_score: float
    education_score: float
    semantic_score: float
    formula: str = "(Skill * 0.40) + (Experience * 0.25) + (Education * 0.15) + (Semantic * 0.20)"

class RecommendationResponse(BaseModel):
    id: int
    analysis_id: int
    job_id: int
    match_score: float
    skill_score: float
    experience_score: float
    education_score: float
    semantic_score: float
    matching_skills: List[str]
    missing_skills: List[str]
    relevant_experience: Optional[str]
    match_explanation: str
    gaps_identified: List[str]
    created_at: datetime
    job: Optional[JobResponse] = None
    model_config = ConfigDict(from_attributes=True)

class RecommendationsListResponse(BaseModel):
    recommendations: List[RecommendationResponse]
    total: int
    top_matched_job: Optional[RecommendationResponse] = None
