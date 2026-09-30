from typing import Optional, List
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.api.deps import get_optional_current_user, get_current_user
from app.db.models import User, KnowledgeDocument, KnowledgeChunk
from app.repositories.analyses import AnalysisRepository
from app.agents.career_advisor import CareerAdvisorAgent
from app.services.rag_service import RAGService
from app.schemas.career import (
    CareerQuestionRequest,
    CareerQuestionResponse,
    CareerGuidanceOverview
)
from app.schemas.knowledge import (
    KnowledgeDocCreate,
    KnowledgeDocResponse,
    KnowledgeDocListResponse,
    VALID_CATEGORIES
)

router = APIRouter(prefix="/career", tags=["Career Advisor & RAG"])

@router.post("/questions", response_model=CareerQuestionResponse)
async def ask_career_advisor(
    req: CareerQuestionRequest,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """
    Asks the Career Advisor Agent (Agent 3) a question.
    Executes semantic vector retrieval against the Knowledge Base (RAG)
    and grounds the AI answer with citations and actionable roadmaps.
    """
    candidate_profile = None
    if req.resume_id:
        analysis = AnalysisRepository.get_by_resume_id(db, req.resume_id)
        if analysis:
            candidate_profile = {
                "candidate_name": analysis.candidate_name,
                "technical_skills": analysis.technical_skills or [],
                "missing_areas": analysis.missing_areas or []
            }

    agent = CareerAdvisorAgent()
    response = await agent.answer_career_question(
        db=db,
        question=req.question,
        candidate_profile=candidate_profile,
        target_role=req.target_role
    )
    return response

@router.get("/guidance/{resume_id}", response_model=CareerGuidanceOverview)
def get_career_guidance(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generates personalized career roadmap and learning recommendations from an analyzed resume."""
    analysis = AnalysisRepository.get_by_resume_id(db, resume_id)
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume analysis not found. Please analyze the resume first."
        )

    agent = CareerAdvisorAgent()
    roadmap = agent.generate_career_roadmap(analysis.missing_areas or [])

    return CareerGuidanceOverview(
        resume_id=resume_id,
        candidate_name=analysis.candidate_name,
        target_recommendations=analysis.recommended_improvements or [],
        missing_critical_skills=analysis.missing_areas or [],
        learning_roadmap=roadmap,
        suggested_certifications=[
            "AWS Certified Solutions Architect",
            "Certified Kubernetes Application Developer (CKAD)",
            "HashiCorp Certified Terraform Associate"
        ],
        curated_resources=[
            {"title": "roadmap.sh", "url": "https://roadmap.sh", "type": "Career Roadmaps"},
            {"title": "FastAPI Official Documentation", "url": "https://fastapi.tiangolo.com", "type": "Framework Docs"},
            {"title": "freeCodeCamp Python & Data Systems", "url": "https://www.freecodecamp.org", "type": "Interactive Course"}
        ]
    )

@router.get("/knowledge-docs")
def list_knowledge_docs(db: Session = Depends(get_db)):
    """List knowledge base documents powering the RAG pipeline."""
    docs = db.query(KnowledgeDocument).order_by(KnowledgeDocument.created_at.desc()).all()
    return [
        {
            "id": d.id,
            "title": d.title,
            "category": d.category,
            "source": d.source,
            "chunks_count": len(d.chunks),
            "created_at": d.created_at
        }
        for d in docs
    ]

@router.get("/knowledge-docs/{doc_id}", response_model=KnowledgeDocResponse)
def get_knowledge_doc(doc_id: int, db: Session = Depends(get_db)):
    """Retrieve full details of a specific knowledge base document."""
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge document with ID {doc_id} was not found."
        )
    return KnowledgeDocResponse(
        id=doc.id,
        title=doc.title,
        category=doc.category,
        source=doc.source,
        content=doc.content,
        chunks_count=len(doc.chunks),
        created_at=doc.created_at
    )

@router.post("/knowledge-docs", response_model=KnowledgeDocResponse, status_code=status.HTTP_201_CREATED)
async def create_knowledge_doc(
    doc_in: KnowledgeDocCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add a new document to the RAG Knowledge Base.
    The document content is automatically chunked, embedded, and indexed for vector retrieval.
    Requires authentication.
    """
    # Validate category
    if doc_in.category not in VALID_CATEGORIES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid category '{doc_in.category}'. Must be one of: {', '.join(VALID_CATEGORIES)}"
        )

    rag = RAGService()
    doc = await rag.ingest_document(
        db=db,
        title=doc_in.title.strip(),
        category=doc_in.category,
        content=doc_in.content.strip(),
        source=doc_in.source.strip()
    )

    return KnowledgeDocResponse(
        id=doc.id,
        title=doc.title,
        category=doc.category,
        source=doc.source,
        content=doc.content,
        chunks_count=len(doc.chunks),
        created_at=doc.created_at
    )

@router.delete("/knowledge-docs/{doc_id}", status_code=status.HTTP_200_OK)
def delete_knowledge_doc(
    doc_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a knowledge base document and all its associated vector chunks.
    Requires authentication.
    """
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge document with ID {doc_id} was not found."
        )

    doc_title = doc.title
    db.delete(doc)
    db.commit()
    return {"message": f"Knowledge document '{doc_title}' (ID {doc_id}) and all its vector chunks successfully deleted."}

