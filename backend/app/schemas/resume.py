from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class ResumeResponse(BaseModel):
    id: int
    user_id: int
    filename: str
    file_type: str
    file_size_bytes: int
    created_at: datetime
    has_analysis: bool = False
    model_config = ConfigDict(from_attributes=True)

class ResumeDetailResponse(ResumeResponse):
    raw_text: str

class ResumeListResponse(BaseModel):
    resumes: List[ResumeResponse]
    total: int
