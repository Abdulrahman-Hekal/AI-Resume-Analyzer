from typing import Optional, List
from sqlalchemy.orm import Session
from app.db.models import Resume

class ResumeRepository:
    @staticmethod
    def get_by_id(db: Session, resume_id: int) -> Optional[Resume]:
        return db.query(Resume).filter(Resume.id == resume_id).first()

    @staticmethod
    def get_by_user_id(db: Session, user_id: int) -> List[Resume]:
        return db.query(Resume).filter(Resume.user_id == user_id).order_by(Resume.created_at.desc()).all()

    @staticmethod
    def create(
        db: Session,
        user_id: int,
        filename: str,
        file_path: str,
        file_type: str,
        file_size_bytes: int,
        raw_text: str
    ) -> Resume:
        resume = Resume(
            user_id=user_id,
            filename=filename,
            file_path=file_path,
            file_type=file_type,
            file_size_bytes=file_size_bytes,
            raw_text=raw_text
        )
        db.add(resume)
        db.commit()
        db.refresh(resume)
        return resume

    @staticmethod
    def delete(db: Session, resume: Resume) -> None:
        db.delete(resume)
        db.commit()
