import re
from typing import List, Dict, Any, Tuple
from app.core.config import settings
from app.utils.text_processing import cosine_similarity
from app.services.ai_service import AIProvider

class MatchingService:
    """
    Transparent Multi-Factor Matching Engine.
    Formula:
      final_score = (skill_score * 0.40) + (experience_score * 0.25) + (education_score * 0.15) + (semantic_score * 0.20)
    All components normalized to 0.0 - 100.0 scale.
    """

    EDUCATION_LEVEL_WEIGHTS = {
        "any": 100.0,
        "high school": 40.0,
        "associate": 60.0,
        "diploma": 60.0,
        "bachelor": 85.0,
        "undergraduate": 85.0,
        "master": 95.0,
        "postgraduate": 95.0,
        "phd": 100.0,
        "doctorate": 100.0,
        "doctor of philosophy": 100.0
    }

    @classmethod
    def _normalize_degree(cls, text: str) -> str:
        """Normalizes degree strings and acronyms (B.S., B.Sc., B.Tech, M.S., Ph.D.) to base tiers."""
        s = text.lower()
        # Normalizes abbreviations to standardized level names
        s = re.sub(r"\bb\.?\s*s\.?(?:c\.?)?\b", "bachelor", s)
        s = re.sub(r"\bb\.?\s*tech\.?\b", "bachelor", s)
        s = re.sub(r"\bm\.?\s*s\.?(?:c\.?)?\b", "master", s)
        s = re.sub(r"\bm\.?\s*tech\.?\b", "master", s)
        s = re.sub(r"\bph\.?\s*d\.?\b", "phd", s)
        return s

    @classmethod
    def _normalize_skill(cls, skill: str) -> str:
        s = skill.lower().strip()
        # Handle specific languages where punctuation matters
        if s in ("c++", "cpp"):
            return "cpp"
        if s in ("c#", "csharp"):
            return "csharp"
        if s in (".net", "dotnet"):
            return "dotnet"
            
        # Strip punctuation and spaces
        s = re.sub(r"[.\-_/\s]", "", s)
        alias_map = {
            "js": "javascript",
            "ts": "typescript",
            "py": "python",
            "postgres": "postgresql",
            "psql": "postgresql",
            "mongo": "mongodb",
            "k8s": "kubernetes",
            "reactjs": "react",
            "nodejs": "node",
            "vuejs": "vue",
            "angularjs": "angular",
            "aws": "amazonwebservices",
            "amazonwebservices": "amazonwebservices",
            "gcp": "googlecloud",
            "googlecloud": "googlecloud",
            "golang": "go",
            "html5": "html",
            "css3": "css"
        }
        return alias_map.get(s, s)

    @classmethod
    def compute_skill_overlap(
        cls,
        candidate_skills: List[str],
        required_skills: List[str],
        preferred_skills: List[str]
    ) -> Tuple[float, List[str], List[str]]:
        """
        Calculates skill match percentage, returning matching and missing skills.
        Required skills carry 80% weight, preferred skills carry 20% weight.
        Uses exact normalized matching to avoid false substring matches (e.g. Java vs JavaScript).
        """
        cand_norm = {cls._normalize_skill(s) for s in candidate_skills if s and s.strip()}
        
        matching: List[str] = []
        missing: List[str] = []

        # Check required skills
        req_matched = 0
        total_req = len(required_skills)
        for req in required_skills:
            norm = cls._normalize_skill(req)
            if norm in cand_norm:
                req_matched += 1
                matching.append(req)
            else:
                missing.append(req)

        # Check preferred skills
        pref_matched = 0
        total_pref = len(preferred_skills)
        for pref in preferred_skills:
            norm = cls._normalize_skill(pref)
            if norm in cand_norm:
                pref_matched += 1
                if pref not in matching:
                    matching.append(f"{pref} (Preferred)")

        # Calculate weighted skill score
        req_ratio = (req_matched / total_req) if total_req > 0 else 1.0
        pref_ratio = (pref_matched / total_pref) if total_pref > 0 else 1.0

        if total_req > 0 and total_pref > 0:
            score = (req_ratio * 0.80 + pref_ratio * 0.20) * 100.0
        elif total_req > 0:
            score = req_ratio * 100.0
        elif total_pref > 0:
            score = pref_ratio * 100.0
        else:
            # Job specifies no required or preferred skills
            score = 100.0

        return round(min(100.0, max(0.0, score)), 1), matching, missing

    @classmethod
    def compute_experience_score(
        cls,
        experience_items: List[Dict[str, Any]],
        required_years: float
    ) -> Tuple[float, str]:
        """
        Estimates total experience years from listed positions and calculates alignment.
        Candidate with no experience receives 0.0.
        Candidate exceeding required years is capped at 100.0.
        """
        if required_years <= 0.0:
            return 100.0, "Entry level position / No minimum experience required."

        if not experience_items:
            return 0.0, "No professional experience listed."

        total_estimated_years = 0.0
        summary_snippets = []
        for item in experience_items:
            duration_str = str(item.get("duration", "")).lower()
            years_found = re.findall(r"(\d+(?:\.\d+)?)\s*(?:years|year|yrs|yr)", duration_str)
            if years_found:
                total_estimated_years += sum(float(y) for y in years_found)
            else:
                total_estimated_years += 1.5
            title = item.get("title", "Developer")
            comp = item.get("company", "Company")
            summary_snippets.append(f"{title} at {comp}")

        score = (total_estimated_years / required_years) * 100.0
        score = min(100.0, max(0.0, score))

        summary_text = (
            f"Candidate has approx {total_estimated_years:.1f} years of relevant experience "
            f"across {len(experience_items)} role(s) (Required: {required_years:.1f} yrs). "
            f"Roles: {', '.join(summary_snippets[:3]) if summary_snippets else 'Technical background'}."
        )
        return round(score, 1), summary_text

    @classmethod
    def compute_education_score(
        cls,
        education_items: List[Dict[str, Any]],
        required_level: str
    ) -> float:
        """
        Calculates compatibility between candidate's highest degree and job requirement.
        Returns 0.0 if candidate has no education items and job requires a degree.
        """
        req_norm = required_level.lower().strip()
        if "any" in req_norm or not req_norm:
            return 100.0

        req_weight = 85.0  # default Bachelor's
        for k, v in cls.EDUCATION_LEVEL_WEIGHTS.items():
            if k in req_norm:
                req_weight = v
                break

        if not education_items:
            return 0.0

        highest_cand_weight = 0.0
        for item in education_items:
            deg = str(item.get("degree", ""))
            field = str(item.get("field", ""))
            combined = cls._normalize_degree(f"{deg} {field}")
            for k, v in cls.EDUCATION_LEVEL_WEIGHTS.items():
                if k in combined and v > highest_cand_weight:
                    highest_cand_weight = v

        if highest_cand_weight == 0.0:
            # Candidate listed education, but degree wasn't recognized in standard taxonomy
            highest_cand_weight = 50.0

        if highest_cand_weight >= req_weight:
            return 100.0
        else:
            return round((highest_cand_weight / req_weight) * 100.0, 1)

    @classmethod
    async def compute_semantic_score(
        cls,
        candidate_summary: str,
        candidate_skills: List[str],
        job_title: str,
        job_description: str,
        ai_provider: AIProvider
    ) -> float:
        """
        Calculates semantic embedding cosine similarity between candidate profile and job description.
        Returns 0.0 if profile or job text is empty.
        Clamped strictly to 0.0 - 100.0.
        """
        # If candidate has neither summary nor skills, return 0.0
        if not candidate_summary.strip() and not candidate_skills:
            return 0.0
        if not job_title.strip() and not job_description.strip():
            return 0.0

        cand_text = f"{candidate_summary} Skills: {', '.join(candidate_skills)}".strip()
        job_text = f"{job_title}. {job_description}".strip()

        embeddings = await ai_provider.embed([cand_text, job_text])
        if len(embeddings) == 2:
            sim = cosine_similarity(embeddings[0], embeddings[1])
            # Scale cosine similarities (0.0 - 1.0) to a 0.0 - 100.0 score
            scaled = (sim - 0.1) / 0.75 * 100.0
            return round(min(100.0, max(0.0, scaled)), 1)
        return 50.0

    @classmethod
    async def evaluate_match(
        cls,
        candidate_profile: Dict[str, Any],
        job_data: Dict[str, Any],
        ai_provider: AIProvider
    ) -> Dict[str, Any]:
        """
        Computes the complete multi-dimensional match evaluation:
        final_score = (skill * 0.40) + (exp * 0.25) + (edu * 0.15) + (sem * 0.20)
        """
        # 1. Skill Score
        skills = candidate_profile.get("technical_skills", [])
        req_skills = job_data.get("required_skills", [])
        pref_skills = job_data.get("preferred_skills", [])
        skill_score, matching_skills, missing_skills = cls.compute_skill_overlap(skills, req_skills, pref_skills)

        # 2. Experience Score
        exp_items = candidate_profile.get("experience", [])
        req_years = float(job_data.get("experience_years", 0.0))
        experience_score, exp_summary = cls.compute_experience_score(exp_items, req_years)

        # 3. Education Score
        edu_items = candidate_profile.get("education", [])
        req_edu = job_data.get("education_level", "Bachelor's")
        education_score = cls.compute_education_score(edu_items, req_edu)

        # 4. Semantic Score
        summary = candidate_profile.get("professional_summary", "")
        title = job_data.get("title", "")
        desc = job_data.get("description", "")
        semantic_score = await cls.compute_semantic_score(summary, skills, title, desc, ai_provider)

        # Composite Score Calculation
        final_score = (
            skill_score * settings.WEIGHT_SKILLS
            + experience_score * settings.WEIGHT_EXPERIENCE
            + education_score * settings.WEIGHT_EDUCATION
            + semantic_score * settings.WEIGHT_SEMANTIC
        )
        final_score = round(min(100.0, max(0.0, final_score)), 1)

        gaps = []
        if missing_skills:
            gaps.append(f"Missing required skills: {', '.join(missing_skills[:4])}")
        if experience_score < 70.0 and req_years > 0:
            gaps.append(f"Experience level below the {req_years:.1f} years target")
        if education_score < 80.0:
            gaps.append(f"Education level differs from preferred '{req_edu}' requirement")

        return {
            "match_score": final_score,
            "skill_score": skill_score,
            "experience_score": experience_score,
            "education_score": education_score,
            "semantic_score": semantic_score,
            "matching_skills": matching_skills,
            "missing_skills": missing_skills,
            "relevant_experience": exp_summary,
            "gaps_identified": gaps
        }
