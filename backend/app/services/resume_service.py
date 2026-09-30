import os
import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException, status
from app.core.config import settings
from app.utils.file_validation import validate_uploaded_file
from app.services.resume_parser import ResumeParser
from app.repositories.resumes import ResumeRepository
from app.db.models import Resume
from app.schemas.resume import ResumeResponse

class ResumeService:
    @staticmethod
    async def upload_resume(db: Session, user_id: int, file: UploadFile) -> Resume:
        # Read content
        content = await file.read()

        # Validate file
        ext = validate_uploaded_file(file, content)

        # Parse text from file
        raw_text = ResumeParser.parse(content, ext)

        # Save to disk safely
        safe_name = f"{uuid.uuid4().hex}_{file.filename}"
        file_path = os.path.join(settings.UPLOAD_DIR, safe_name)
        with open(file_path, "wb") as f:
            f.write(content)

        # Store in database
        resume = ResumeRepository.create(
            db=db,
            user_id=user_id,
            filename=file.filename or safe_name,
            file_path=file_path,
            file_type=ext,
            file_size_bytes=len(content),
            raw_text=raw_text
        )

        return resume

    @staticmethod
    def get_user_resumes(db: Session, user_id: int) -> List[ResumeResponse]:
        resumes = ResumeRepository.get_by_user_id(db, user_id)
        result = []
        for r in resumes:
            res_obj = ResumeResponse(
                id=r.id,
                user_id=r.user_id,
                filename=r.filename,
                file_type=r.file_type,
                file_size_bytes=r.file_size_bytes,
                created_at=r.created_at,
                has_analysis=r.analysis is not None
            )
            result.append(res_obj)
        return result

    @staticmethod
    def get_resume(db: Session, resume_id: int, user_id: int, is_admin: bool = False) -> Resume:
        resume = ResumeRepository.get_by_id(db, resume_id)
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume with ID {resume_id} not found."
            )
        if resume.user_id != user_id and not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resume."
            )
        return resume

    @staticmethod
    def delete_resume(db: Session, resume_id: int, user_id: int, is_admin: bool = False) -> None:
        resume = ResumeService.get_resume(db, resume_id, user_id, is_admin)
        # Attempt to delete file from disk
        if os.path.exists(resume.file_path):
            try:
                os.remove(resume.file_path)
            except Exception:
                pass
        ResumeRepository.delete(db, resume)
