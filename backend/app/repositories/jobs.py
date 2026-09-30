from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from app.db.models import Job
from app.schemas.job import JobCreate, JobUpdate

class JobRepository:
    @staticmethod
    def get_by_id(db: Session, job_id: int) -> Optional[Job]:
        return db.query(Job).filter(Job.id == job_id).first()

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> Tuple[List[Job], int]:
        query = db.query(Job).order_by(Job.created_at.desc())
        total = query.count()
        jobs = query.offset(skip).limit(limit).all()
        return jobs, total

    @staticmethod
    def search(
        db: Session,
        keyword: Optional[str] = None,
        skill: Optional[str] = None,
        min_experience: Optional[float] = None,
        max_experience: Optional[float] = None,
        location: Optional[str] = None,
        employment_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ):
        query = db.query(Job)

        if keyword:
            kw = f"%{keyword.strip()}%"
            query = query.filter(
                or_(
                    Job.title.ilike(kw),
                    Job.company.ilike(kw),
                    Job.description.ilike(kw),
                    Job.location.ilike(kw)
                )
            )

        if skill:
            sk = f"%{skill.strip().lower()}%"
            # In SQLite, JSON column stored as text can be searched via CAST or string matching
            query = query.filter(func.lower(Job.description).contains(skill.strip().lower()) | func.lower(Job.title).contains(skill.strip().lower()))

        if min_experience is not None:
            query = query.filter(Job.experience_years >= min_experience)

        if max_experience is not None:
            query = query.filter(Job.experience_years <= max_experience)

        if location:
            query = query.filter(Job.location.ilike(f"%{location.strip()}%"))

        if employment_type:
            query = query.filter(Job.employment_type.ilike(f"%{employment_type.strip()}%"))

        total = query.count()
        jobs = query.order_by(Job.created_at.desc()).offset(skip).limit(limit).all()
        return jobs, total

    @staticmethod
    def create(db: Session, job_in: JobCreate, user_id: Optional[int] = None) -> Job:
        job = Job(
            title=job_in.title.strip(),
            company=job_in.company.strip(),
            description=job_in.description.strip(),
            required_skills=job_in.required_skills,
            preferred_skills=job_in.preferred_skills,
            experience_years=job_in.experience_years,
            education_level=job_in.education_level.strip(),
            location=job_in.location.strip(),
            employment_type=job_in.employment_type.strip(),
            salary_range=job_in.salary_range,
            contact_email=job_in.contact_email,
            created_by_user_id=user_id
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def update(db: Session, job: Job, job_in: JobUpdate) -> Job:
        update_data = job_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(job, field, value)
        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def delete(db: Session, job: Job) -> None:
        db.delete(job)
        db.commit()
