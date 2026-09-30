from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.repositories.jobs import JobRepository
from app.schemas.job import JobCreate, JobUpdate, JobResponse, JobListResponse
from app.db.models import Job

class JobService:
    @staticmethod
    def get_job(db: Session, job_id: int) -> Job:
        job = JobRepository.get_by_id(db, job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job with ID {job_id} was not found."
            )
        return job

    @staticmethod
    def list_jobs(db: Session, skip: int = 0, limit: int = 50) -> JobListResponse:
        jobs, total = JobRepository.get_all(db, skip=skip, limit=limit)
        return JobListResponse(
            jobs=[JobResponse.model_validate(j) for j in jobs],
            total=total
        )

    @staticmethod
    def search_jobs(
        db: Session,
        keyword: Optional[str] = None,
        skill: Optional[str] = None,
        min_experience: Optional[float] = None,
        max_experience: Optional[float] = None,
        location: Optional[str] = None,
        employment_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> JobListResponse:
        jobs, total = JobRepository.search(
            db=db,
            keyword=keyword,
            skill=skill,
            min_experience=min_experience,
            max_experience=max_experience,
            location=location,
            employment_type=employment_type,
            skip=skip,
            limit=limit
        )
        return JobListResponse(
            jobs=[JobResponse.model_validate(j) for j in jobs],
            total=total
        )

    @staticmethod
    def create_job(db: Session, job_in: JobCreate, user_id: Optional[int] = None) -> JobResponse:
        job = JobRepository.create(db, job_in, user_id=user_id)
        return JobResponse.model_validate(job)

    @staticmethod
    def update_job(db: Session, job_id: int, job_in: JobUpdate, user_id: int, is_admin: bool = False) -> JobResponse:
        job = JobService.get_job(db, job_id)
        # Check permissions: only creator or admin can edit
        if job.created_by_user_id and job.created_by_user_id != user_id and not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to modify this job listing."
            )
        updated_job = JobRepository.update(db, job, job_in)
        return JobResponse.model_validate(updated_job)

    @staticmethod
    def delete_job(db: Session, job_id: int, user_id: int, is_admin: bool = False) -> None:
        job = JobService.get_job(db, job_id)
        if job.created_by_user_id and job.created_by_user_id != user_id and not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to delete this job listing."
            )
        JobRepository.delete(db, job)
