from typing import Optional
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.api.deps import get_current_user, get_optional_current_user
from app.db.models import User
from app.services.job_service import JobService
from app.schemas.job import JobCreate, JobUpdate, JobResponse, JobListResponse

router = APIRouter(prefix="/jobs", tags=["Jobs Management & Search"])

@router.get("/search", response_model=JobListResponse)
def search_jobs(
    q: Optional[str] = Query(None, description="General keyword across title, company, description, location"),
    skill: Optional[str] = Query(None, description="Required or preferred technical skill"),
    min_exp: Optional[float] = Query(None, ge=0, description="Minimum years of experience"),
    max_exp: Optional[float] = Query(None, ge=0, description="Maximum years of experience"),
    location: Optional[str] = Query(None, description="Job location or 'Remote'"),
    employment_type: Optional[str] = Query(None, description="Full-time, Part-time, Contract, etc."),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Search and filter jobs using multi-criteria query parameters."""
    def clean_str(val: Optional[str]) -> Optional[str]:
        if val is None:
            return None
        v = val.strip()
        if v.lower() in ("undefined", "null", ""):
            return None
        return v

    return JobService.search_jobs(
        db=db,
        keyword=clean_str(q),
        skill=clean_str(skill),
        min_experience=min_exp,
        max_experience=max_exp,
        location=clean_str(location),
        employment_type=clean_str(employment_type),
        skip=skip,
        limit=limit
    )

@router.get("", response_model=JobListResponse)
def list_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Retrieve all available job postings."""
    return JobService.list_jobs(db, skip=skip, limit=limit)

@router.get("/{job_id}", response_model=JobResponse)
def get_job_details(job_id: int, db: Session = Depends(get_db)):
    """Retrieve full details of a specific job posting."""
    job = JobService.get_job(db, job_id)
    return JobResponse.model_validate(job)

@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(
    job_in: JobCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new job posting. Requires authenticated user/admin."""
    return JobService.create_job(db, job_in, user_id=current_user.id)

@router.put("/{job_id}", response_model=JobResponse)
def update_job(
    job_id: int,
    job_in: JobUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an existing job posting."""
    is_admin = (current_user.role == "admin")
    return JobService.update_job(db, job_id, job_in, user_id=current_user.id, is_admin=is_admin)

@router.delete("/{job_id}", status_code=status.HTTP_200_OK)
def delete_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a job posting."""
    is_admin = (current_user.role == "admin")
    JobService.delete_job(db, job_id, user_id=current_user.id, is_admin=is_admin)
    return {"message": f"Job {job_id} successfully deleted."}
