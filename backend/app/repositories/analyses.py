from typing import Optional, List
from sqlalchemy.orm import Session
from app.db.models import ResumeAnalysis

class AnalysisRepository:
    @staticmethod
    def get_by_resume_id(db: Session, resume_id: int) -> Optional[ResumeAnalysis]:
        return db.query(ResumeAnalysis).filter(ResumeAnalysis.resume_id == resume_id).first()

    @staticmethod
    def get_by_id(db: Session, analysis_id: int) -> Optional[ResumeAnalysis]:
        return db.query(ResumeAnalysis).filter(ResumeAnalysis.id == analysis_id).first()

    @staticmethod
    def save_analysis(
        db: Session,
        resume_id: int,
        user_id: int,
        analysis_data: dict,
        provider_name: str
    ) -> ResumeAnalysis:
        # Check if an analysis already exists for this resume; if so, update it
        existing = db.query(ResumeAnalysis).filter(ResumeAnalysis.resume_id == resume_id).first()
        if existing:
            for k, v in analysis_data.items():
                if hasattr(existing, k):
                    setattr(existing, k, v)
            existing.ai_provider_used = provider_name
            db.commit()
            db.refresh(existing)
            return existing

        analysis = ResumeAnalysis(
            resume_id=resume_id,
            user_id=user_id,
            candidate_name=analysis_data.get("candidate_name"),
            email=analysis_data.get("email"),
            phone=analysis_data.get("phone"),
            location=analysis_data.get("location"),
            professional_summary=analysis_data.get("professional_summary"),
            technical_skills=analysis_data.get("technical_skills", []),
            soft_skills=analysis_data.get("soft_skills", []),
            education=analysis_data.get("education", []),
            experience=analysis_data.get("experience", []),
            projects=analysis_data.get("projects", []),
            certifications=analysis_data.get("certifications", []),
            languages=analysis_data.get("languages", []),
            strengths=analysis_data.get("strengths", []),
            weaknesses=analysis_data.get("weaknesses", []),
            missing_areas=analysis_data.get("missing_areas", []),
            recommended_improvements=analysis_data.get("recommended_improvements", []),
            ai_provider_used=provider_name
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        return analysis
