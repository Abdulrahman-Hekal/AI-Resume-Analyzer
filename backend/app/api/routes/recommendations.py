from typing import List
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.api.deps import get_current_user
from app.db.models import User, Job, Recommendation
from app.services.resume_service import ResumeService
from app.repositories.analyses import AnalysisRepository
from app.repositories.jobs import JobRepository
from app.agents.job_matcher import JobMatchingAgent
from app.schemas.recommendation import RecommendationResponse, RecommendationsListResponse
from app.schemas.job import JobResponse
from app.core.logging import logger

router = APIRouter(prefix="/resumes", tags=["Job Matching & Recommendations"])

@router.post("/{resume_id}/recommendations", response_model=RecommendationsListResponse)
async def generate_recommendations(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Triggers the Job Matching Agent (Agent 2) to evaluate the resume against all active jobs.
    Calculates multi-factor scores:
      final_score = (skill * 0.40) + (exp * 0.25) + (edu * 0.15) + (sem * 0.20)
    Persists and returns recommendations sorted by match percentage descending.
    """
    resume = ResumeService.get_resume(db, resume_id, current_user.id, is_admin=(current_user.role == "admin"))
    analysis = AnalysisRepository.get_by_resume_id(db, resume_id)
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resume must be analyzed before generating recommendations. Please trigger analysis first."
        )

    jobs, total_jobs = JobRepository.get_all(db, skip=0, limit=200)
    if not jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No job listings found in database to compare against. Please add jobs or seed data."
        )

    # Clean previous recommendations for this analysis
    db.query(Recommendation).filter(Recommendation.analysis_id == analysis.id).delete()
    db.commit()

    agent = JobMatchingAgent()
    cand_profile = {
        "candidate_name": analysis.candidate_name,
        "professional_summary": analysis.professional_summary or "",
        "technical_skills": analysis.technical_skills or [],
        "soft_skills": analysis.soft_skills or [],
        "education": analysis.education or [],
        "experience": analysis.experience or [],
        "projects": analysis.projects or []
    }

    created_recs = []
    for job in jobs:
        job_data = {
            "title": job.title,
            "company": job.company,
            "description": job.description,
            "required_skills": job.required_skills or [],
            "preferred_skills": job.preferred_skills or [],
            "experience_years": job.experience_years,
            "education_level": job.education_level,
            "location": job.location,
            "employment_type": job.employment_type
        }

        eval_res = await agent.match_resume_to_job(cand_profile, job_data)

        rec = Recommendation(
            analysis_id=analysis.id,
            job_id=job.id,
            match_score=eval_res["match_score"],
            skill_score=eval_res["skill_score"],
            experience_score=eval_res["experience_score"],
            education_score=eval_res["education_score"],
            semantic_score=eval_res["semantic_score"],
            matching_skills=eval_res["matching_skills"],
            missing_skills=eval_res["missing_skills"],
            relevant_experience=eval_res["relevant_experience"],
            match_explanation=eval_res["match_explanation"],
            gaps_identified=eval_res["gaps_identified"]
        )
        db.add(rec)
        created_recs.append(rec)

    db.commit()

    # Re-fetch with relationships
    db_recs = db.query(Recommendation).filter(
        Recommendation.analysis_id == analysis.id
    ).order_by(Recommendation.match_score.desc()).all()

    rec_responses = []
    for r in db_recs:
        resp = RecommendationResponse.model_validate(r)
        if r.job:
            resp.job = JobResponse.model_validate(r.job)
        rec_responses.append(resp)

    top_job = rec_responses[0] if rec_responses else None

    return RecommendationsListResponse(
        recommendations=rec_responses,
        total=len(rec_responses),
        top_matched_job=top_job
    )

@router.get("/{resume_id}/recommendations", response_model=RecommendationsListResponse)
def get_recommendations(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve existing stored recommendations for this resume."""
    ResumeService.get_resume(db, resume_id, current_user.id, is_admin=(current_user.role == "admin"))
    analysis = AnalysisRepository.get_by_resume_id(db, resume_id)
    if not analysis:
        return RecommendationsListResponse(recommendations=[], total=0, top_matched_job=None)

    db_recs = db.query(Recommendation).filter(
        Recommendation.analysis_id == analysis.id
    ).order_by(Recommendation.match_score.desc()).all()

    rec_responses = []
    for r in db_recs:
        resp = RecommendationResponse.model_validate(r)
        if r.job:
            resp.job = JobResponse.model_validate(r.job)
        rec_responses.append(resp)

    top_job = rec_responses[0] if rec_responses else None
    return RecommendationsListResponse(
        recommendations=rec_responses,
        total=len(rec_responses),
        top_matched_job=top_job
    )

@router.get("/{resume_id}/match/{job_id}", response_model=RecommendationResponse)
async def get_live_job_match(
    resume_id: int,
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Computes real-time match details between a resume and a specific job."""
    ResumeService.get_resume(db, resume_id, current_user.id, is_admin=(current_user.role == "admin"))
    analysis = AnalysisRepository.get_by_resume_id(db, resume_id)
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resume must be analyzed before inspecting job match."
        )

    job = JobRepository.get_by_id(db, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

    agent = JobMatchingAgent()
    cand_profile = {
        "candidate_name": analysis.candidate_name,
        "professional_summary": analysis.professional_summary or "",
        "technical_skills": analysis.technical_skills or [],
        "education": analysis.education or [],
        "experience": analysis.experience or []
    }
    job_data = {
        "title": job.title,
        "company": job.company,
        "description": job.description,
        "required_skills": job.required_skills or [],
        "preferred_skills": job.preferred_skills or [],
        "experience_years": job.experience_years,
        "education_level": job.education_level,
        "location": job.location,
        "employment_type": job.employment_type
    }

    eval_res = await agent.match_resume_to_job(cand_profile, job_data)

    resp = RecommendationResponse(
        id=0,
        analysis_id=analysis.id,
        job_id=job.id,
        match_score=eval_res["match_score"],
        skill_score=eval_res["skill_score"],
        experience_score=eval_res["experience_score"],
        education_score=eval_res["education_score"],
        semantic_score=eval_res["semantic_score"],
        matching_skills=eval_res["matching_skills"],
        missing_skills=eval_res["missing_skills"],
        relevant_experience=eval_res["relevant_experience"],
        match_explanation=eval_res["match_explanation"],
        gaps_identified=eval_res["gaps_identified"],
        created_at=analysis.created_at,
        job=JobResponse.model_validate(job)
    )
    return resp
