from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.api.deps import get_current_user
from app.db.models import User
from app.services.resume_service import ResumeService
from app.repositories.analyses import AnalysisRepository
from app.agents.resume_analyzer import ResumeAnalyzerAgent
from app.schemas.analysis import ResumeAnalysisResponse

router = APIRouter(prefix="/resumes", tags=["Resume Analysis"])

@router.post("/{resume_id}/analyze", response_model=ResumeAnalysisResponse)
async def analyze_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Triggers the Resume Analyzer Agent (Agent 1) to process extracted resume text.
    Extracts structured personal info, skills, education, work experience, projects,
    strengths, weaknesses, and improvement areas.
    """
    resume = ResumeService.get_resume(db, resume_id, current_user.id, is_admin=(current_user.role == "admin"))
    
    agent = ResumeAnalyzerAgent()
    profile, provider_used = await agent.analyze(resume.raw_text)

    # Persist the structured analysis
    analysis_record = AnalysisRepository.save_analysis(
        db=db,
        resume_id=resume.id,
        user_id=current_user.id,
        analysis_data=profile.model_dump(),
        provider_name=provider_used
    )

    return ResumeAnalysisResponse.model_validate(analysis_record)

@router.get("/{resume_id}/analysis", response_model=ResumeAnalysisResponse)
def get_resume_analysis(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve the stored structured analysis for a given resume."""
    ResumeService.get_resume(db, resume_id, current_user.id, is_admin=(current_user.role == "admin"))
    analysis = AnalysisRepository.get_by_resume_id(db, resume_id)
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume has not been analyzed yet. Please trigger POST /api/resumes/{id}/analyze first."
        )
    return ResumeAnalysisResponse.model_validate(analysis)
