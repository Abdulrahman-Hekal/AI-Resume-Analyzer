from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, status, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.api.deps import get_current_user
from app.db.models import User
from app.services.resume_service import ResumeService
from app.schemas.resume import ResumeResponse, ResumeDetailResponse, ResumeListResponse

router = APIRouter(prefix="/resumes", tags=["Resumes"])

@router.post("", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a resume file (PDF or DOCX).
    Extracts text, validates file integrity, and persists resume record.
    """
    resume = await ResumeService.upload_resume(db, current_user.id, file)
    return ResumeResponse(
        id=resume.id,
        user_id=resume.user_id,
        filename=resume.filename,
        file_type=resume.file_type,
        file_size_bytes=resume.file_size_bytes,
        created_at=resume.created_at,
        has_analysis=False
    )

@router.get("", response_model=ResumeListResponse)
def list_resumes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve all resumes uploaded by the current user."""
    resumes = ResumeService.get_user_resumes(db, current_user.id)
    return ResumeListResponse(resumes=resumes, total=len(resumes))

@router.get("/{resume_id}", response_model=ResumeDetailResponse)
def get_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve a single resume by ID including its raw extracted text."""
    resume = ResumeService.get_resume(db, resume_id, current_user.id, is_admin=(current_user.role == "admin"))
    return ResumeDetailResponse(
        id=resume.id,
        user_id=resume.user_id,
        filename=resume.filename,
        file_type=resume.file_type,
        file_size_bytes=resume.file_size_bytes,
        created_at=resume.created_at,
        has_analysis=resume.analysis is not None,
        raw_text=resume.raw_text
    )

@router.delete("/{resume_id}", status_code=status.HTTP_200_OK)
def delete_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a resume and any associated analyses and recommendations."""
    ResumeService.delete_resume(db, resume_id, current_user.id, is_admin=(current_user.role == "admin"))
    return {"message": f"Resume {resume_id} and associated analyses successfully deleted."}
