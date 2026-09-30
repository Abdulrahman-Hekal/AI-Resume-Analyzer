from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

VALID_CATEGORIES = [
    "job_description",
    "skill_description",
    "career_roadmap",
    "learning_resource",
    "resume_guideline"
]

class KnowledgeDocCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255, description="Document title")
    category: str = Field(
        ...,
        description=f"Document category. Must be one of: {', '.join(VALID_CATEGORIES)}"
    )
    content: str = Field(..., min_length=20, description="Full document text content to be chunked and embedded")
    source: str = Field("user_contributed", max_length=255, description="Source attribution")

class KnowledgeDocResponse(BaseModel):
    id: int
    title: str
    category: str
    source: str
    content: str
    chunks_count: int = 0
    created_at: datetime

class KnowledgeDocListResponse(BaseModel):
    documents: list[KnowledgeDocResponse]
    total: int
