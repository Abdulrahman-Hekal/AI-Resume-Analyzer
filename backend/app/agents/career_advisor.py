from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.services.rag_service import RAGService
from app.services.ai_service import get_ai_provider, AIProvider
from app.schemas.career import (
    CareerQuestionResponse,
    CareerRoadmapStep,
    CareerGuidanceOverview,
    RetrievedChunkInfo
)
from app.core.logging import logger

class CareerAdvisorAgent:
    """
    AGENT 3 — Career Advisor Agent
    Responsibilities:
    - Analyzes candidate skill gaps and career trajectories
    - Generates structured career roadmaps and certification plans
    - Answers career Q&A grounded strictly in the RAG Knowledge Base
    - Returns citations and retrieved sources for verifiable intelligence
    """

    def __init__(self, ai_provider: Optional[AIProvider] = None, rag_service: Optional[RAGService] = None):
        self.ai = ai_provider or get_ai_provider()
        self.rag = rag_service or RAGService(self.ai)

    def generate_career_roadmap(self, missing_skills: List[str], target_role: Optional[str] = None) -> List[CareerRoadmapStep]:
        """Generate structured 3-phase career progression roadmap."""
        role = target_role or "Fullstack / Cloud Software Engineer"
        top_missing = missing_skills[:6] if missing_skills else ["System Design", "Cloud Architecture (AWS)", "Docker & K8s", "CI/CD Automation"]

        p1_skills = top_missing[:2] or ["System Design Fundamentals", "Advanced Data Structures"]
        p2_skills = top_missing[2:4] or ["Cloud Infrastructure (AWS/GCP)", "Docker Containers"]
        p3_skills = top_missing[4:6] or ["Production Observability", "Microservices & Distributed Systems"]

        return [
            CareerRoadmapStep(
                step_number=1,
                phase="Phase 1: Core Competency & Architectural Foundation",
                focus_skills=p1_skills,
                description=f"Establish rigorous architectural mastery. Build clean, modular APIs and study standard system design trade-offs.",
                recommended_certifications=["AWS Certified Cloud Practitioner", "Meta Backend Developer Certificate"],
                recommended_courses=["FastAPI Modern Web APIs", "Designing Data-Intensive Applications (Book)"]
            ),
            CareerRoadmapStep(
                step_number=2,
                phase="Phase 2: Cloud Native & Containerization Deployment",
                focus_skills=p2_skills,
                description=f"Containerize applications and deploy scalable microservices with automated testing and continuous integration.",
                recommended_certifications=["Docker Certified Associate (DCA)", "AWS Certified Solutions Architect Associate"],
                recommended_courses=["Docker & Kubernetes Mastery", "GitHub Actions CI/CD Pipeline Automation"]
            ),
            CareerRoadmapStep(
                step_number=3,
                phase="Phase 3: Production Scale & Domain Specialization",
                focus_skills=p3_skills,
                description=f"Lead high-impact initiatives, optimize database queries, implement caching layers (Redis), and mentor junior peers.",
                recommended_certifications=["Kubernetes Administrator (CKA)", "HashiCorp Certified Terraform Associate"],
                recommended_courses=["Advanced Microservices Architecture", "Performance Tuning and Distributed Caching"]
            )
        ]

    async def answer_career_question(
        self,
        db: Session,
        question: str,
        candidate_profile: Optional[Dict[str, Any]] = None,
        target_role: Optional[str] = None
    ) -> CareerQuestionResponse:
        """
        Answers candidate questions using the RAG Pipeline:
        1. Semantic retrieval from knowledge base (Job descriptions, roadmaps, guidelines)
        2. Context construction with source citations
        3. LLM generation grounded in retrieved knowledge
        4. Structured recommendations
        """
        logger.info(f"CareerAdvisorAgent answering question: '{question[:60]}...'")

        # 1. RAG Semantic Retrieval
        grounded_context, citations = await self.rag.build_grounded_context(db, question, top_k=4)
        is_grounded = len(citations) > 0

        # Build candidate context if available
        cand_context = ""
        missing_skills = []
        if candidate_profile:
            c_name = candidate_profile.get("candidate_name", "Candidate")
            c_skills = candidate_profile.get("technical_skills", [])
            missing_skills = candidate_profile.get("missing_areas", [])
            cand_context = (
                f"\nCANDIDATE CONTEXT:\n"
                f"- Name: {c_name}\n"
                f"- Current Technical Skills: {', '.join(c_skills[:10])}\n"
                f"- Noted Improvement Areas: {', '.join(missing_skills[:5])}\n"
            )

        system_prompt = (
            "You are an expert AI Career Advisor Agent. "
            "You provide practical, highly actionable, realistic career advice. "
            "IMPORTANT: Base your answers primarily on the retrieved knowledge base documents provided below. "
            "When citing guidelines or roadmaps, reference the retrieved documents. "
            "Avoid generic buzzwords; give clear, concrete advice."
        )

        prompt = (
            f"USER CAREER QUESTION: {question}\n"
            f"{cand_context}\n"
            f"--- BEGIN RETRIEVED KNOWLEDGE BASE CONTEXT (RAG) ---\n"
            f"{grounded_context if grounded_context else 'No specific internal documents matched above threshold. Rely on established software engineering industry standards.'}\n"
            f"--- END RETRIEVED KNOWLEDGE BASE CONTEXT ---\n\n"
            f"Please provide an insightful, structured response answering the user's question, "
            f"highlighting high-leverage skills to learn, recommended certifications, and next steps."
        )

        try:
            answer_text = await self.ai.generate(prompt, system_prompt=system_prompt)
        except Exception as e:
            logger.warning(f"AI generation failed for CareerAdvisor: {e}. Using deterministic advisor template.")
            answer_text = (
                "Based on curated industry knowledge and roadmap standards:\n"
                "1. Focus on mastering high-demand skills: Clean API architecture, containerization (Docker), and cloud deployment.\n"
                "2. When enhancing your resume, quantify your achievements using metrics (latency, scale, cost efficiency).\n"
                "3. Build complete end-to-end portfolio projects rather than following superficial tutorial scaffolds."
            )

        roadmap = self.generate_career_roadmap(missing_skills, target_role)

        suggested_certs = [
            "AWS Certified Solutions Architect - Associate",
            "Certified Kubernetes Application Developer (CKAD)",
            "HashiCorp Certified: Terraform Associate"
        ]

        suggested_resources = [
            {"title": "roadmap.sh (Developer Roadmaps)", "url": "https://roadmap.sh", "type": "Interactive Guide"},
            {"title": "freeCodeCamp Backend & APIs", "url": "https://www.freecodecamp.org", "type": "Free Interactive Course"},
            {"title": "System Design Primer", "url": "https://github.com/donnemartin/system-design-primer", "type": "Open Source Repository"}
        ]

        return CareerQuestionResponse(
            question=question,
            answer=answer_text,
            grounded_by_rag=is_grounded,
            retrieved_sources=citations,
            recommended_skills=missing_skills[:5] if missing_skills else ["System Design", "Cloud Infrastructure", "Docker"],
            suggested_certifications=suggested_certs,
            suggested_resources=suggested_resources,
            career_roadmap=roadmap,
            ai_provider_used=self.ai.name
        )
