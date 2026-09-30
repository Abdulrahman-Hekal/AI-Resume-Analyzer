from typing import Dict, Any, List, Optional
from app.services.matching_service import MatchingService
from app.services.ai_service import get_ai_provider, AIProvider
from app.core.logging import logger

class JobMatchingAgent:
    """
    AGENT 2 — Job Matching Agent
    Responsibilities:
    - Analyzes candidate profile vs available job listings
    - Applies the transparent multi-factor scoring formula
    - Generates semantic AI-reasoned explanation for the match
    - Pinpoints exact matching skills, missing skills, and mitigation strategy
    """

    def __init__(self, ai_provider: Optional[AIProvider] = None):
        self.ai = ai_provider or get_ai_provider()

    async def match_resume_to_job(
        self,
        candidate_profile: Dict[str, Any],
        job_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculates scores and generates AI explanation for a single job pairing.
        """
        # 1. Deterministic Multi-Factor Scoring
        scores = await MatchingService.evaluate_match(candidate_profile, job_data, self.ai)

        # 2. AI Semantic Explanation Generation
        cand_name = candidate_profile.get("candidate_name", "The candidate")
        job_title = job_data.get("title", "Position")
        company = job_data.get("company", "Company")
        match_score = scores["match_score"]
        matching_skills = scores["matching_skills"]
        missing_skills = scores["missing_skills"]

        system_prompt = (
            "You are a Job Matching AI Agent. "
            "Explain clearly why the candidate matches this specific role based on the calculated multi-factor score. "
            "Be transparent, concise (2-4 sentences), and constructive. Mention their matching strengths and how to bridge any missing skills."
        )

        prompt = (
            f"Generate an objective match explanation for {cand_name} applying for '{job_title}' at '{company}'.\n"
            f"Overall Match Score: {match_score}%\n"
            f"Matching Skills: {', '.join(matching_skills) if matching_skills else 'General background'}\n"
            f"Missing Skills: {', '.join(missing_skills) if missing_skills else 'None'}\n"
            f"Skill Score: {scores['skill_score']}%, Experience Score: {scores['experience_score']}%, "
            f"Education Score: {scores['education_score']}%, Semantic Score: {scores['semantic_score']}%."
        )

        try:
            explanation = await self.ai.generate(prompt, system_prompt=system_prompt)
            explanation = explanation.strip().replace('"', "")
        except Exception as e:
            logger.warning(f"AI explanation generation failed: {e}. Using deterministic explanation.")
            explanation = (
                f"Candidate matches {match_score:.1f}% of requirements for {job_title} at {company}. "
                f"Strong skill alignment in {', '.join(matching_skills[:3]) if matching_skills else 'core domains'}. "
                f"To maximize competitiveness, focus on acquiring {', '.join(missing_skills[:3]) if missing_skills else 'complementary tooling'}."
            )

        scores["match_explanation"] = explanation
        return scores
