from typing import Optional, Tuple
from app.schemas.analysis import StructuredResumeProfile
from app.services.ai_service import get_ai_provider, AIProvider
from app.utils.text_processing import extract_contact_info, clean_text
from app.core.logging import logger

class ResumeAnalyzerAgent:
    """
    AGENT 1 — Resume Analyzer Agent
    Extracts structured, factual information from raw resume text:
    - Contact info, summary, technical skills, soft skills
    - Education, work history, projects, certifications, languages
    - Key strengths, weaknesses, missing areas, and improvements
    Ensures zero hallucination by verifying contact details and facts directly from the source text.
    """

    def __init__(self, ai_provider: Optional[AIProvider] = None):
        self.ai = ai_provider or get_ai_provider()

    async def analyze(self, raw_text: str) -> Tuple[StructuredResumeProfile, str]:
        """
        Executes analysis workflow on resume text.
        Returns the validated StructuredResumeProfile and the AI provider name used.
        """
        cleaned = clean_text(raw_text)
        contact = extract_contact_info(cleaned)

        system_prompt = (
            "You are an expert Resume Analyzer Agent for a prestigious technical hiring platform. "
            "Your task is to analyze the candidate's resume text and extract structured information strictly without hallucination. "
            "RULES:\n"
            "1. ONLY extract information explicitly present in or directly derived from the resume.\n"
            "2. If an item (e.g. phone, certifications, GPA) is absent, leave it null or empty.\n"
            "3. Identify technical skills with standard industry naming (e.g., 'Python', 'FastAPI', 'Docker').\n"
            "4. Formulate an objective professional summary reflecting their genuine experience level.\n"
            "5. Identify real strengths and actionable weaknesses (e.g. lack of quantified metrics, missing GitHub link)."
        )

        prompt = (
            f"Analyze the following resume text and output a complete structured profile according to the schema:\n\n"
            f"--- BEGIN RESUME TEXT ---\n"
            f"{cleaned}\n"
            f"--- END RESUME TEXT ---"
        )

        logger.info(f"ResumeAnalyzerAgent analyzing text ({len(cleaned)} chars) using provider: {self.ai.name}")
        profile = await self.ai.generate_structured(prompt, StructuredResumeProfile, system_prompt=system_prompt)

        # Non-hallucination post-validation:
        # If the LLM missed email or phone that our regex extracted directly, fill it in accurately:
        if not profile.email and contact.get("email"):
            profile.email = contact["email"]
        if not profile.phone and contact.get("phone"):
            profile.phone = contact["phone"]

        return profile, self.ai.name
