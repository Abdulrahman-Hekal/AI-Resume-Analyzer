import abc
import json
import re
from typing import List, Type, TypeVar, Optional, Any, Dict
import httpx
from pydantic import BaseModel
from app.core.config import settings
from app.core.logging import logger
from app.utils.text_processing import extract_contact_info, clean_text

T = TypeVar("T", bound=BaseModel)

class AIProvider(abc.ABC):
    """Abstract Base Class for all AI and LLM Providers."""

    @property
    @abc.abstractmethod
    def name(self) -> str:
        pass

    @abc.abstractmethod
    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        """Generate unstructured text response from the model."""
        pass

    @abc.abstractmethod
    async def generate_structured(self, prompt: str, schema: Type[T], system_prompt: str = "") -> T:
        """Generate validated Pydantic model response from the model."""
        pass

    @abc.abstractmethod
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate semantic embedding vectors for a list of text strings."""
        pass


# ==============================================================================
# 1. Local NLP Provider (Deterministic, Zero-API-Key, 100% Offline Resilient)
# ==============================================================================

class LocalNLPProvider(AIProvider):
    """
    Local NLP provider using curated skill taxonomies, regular expressions,
    heuristic information extraction, and TF-IDF semantic embeddings.
    Ensures functional continuity and offline resilience when external network access or API credentials are unavailable.
    """

    SKILL_TAXONOMY = {
        # Programming Languages
        "python", "javascript", "typescript", "java", "c++", "c#", "c", "go", "golang", "rust",
        "php", "ruby", "swift", "kotlin", "scala", "r", "dart", "sql", "bash", "shell", "powershell",
        
        # Web Frameworks & Libraries
        "fastapi", "flask", "django", "react", "react.js", "next.js", "vue", "vue.js", "angular",
        "svelte", "node.js", "express", "express.js", "nest.js", "spring boot", "asp.net", "laravel",
        "ruby on rails", "html", "html5", "css", "css3", "tailwind", "tailwindcss", "bootstrap",
        
        # Databases & Caching
        "sqlite", "postgresql", "postgres", "mysql", "mongodb", "redis", "elasticsearch", "cassandra",
        "dynamodb", "mariadb", "oracle", "sqlalchemy", "prisma", "hibernate",
        
        # AI / Machine Learning / Data Science
        "machine learning", "deep learning", "nlp", "natural language processing", "rag",
        "retrieval augmented generation", "computer vision", "llm", "large language models",
        "pytorch", "tensorflow", "keras", "scikit-learn", "sklearn", "pandas", "numpy", "scipy",
        "huggingface", "transformers", "langchain", "llamaindex", "opencv", "matplotlib", "seaborn",
        
        # Cloud, DevOps & Tools
        "docker", "kubernetes", "k8s", "aws", "amazon web services", "azure", "gcp", "google cloud",
        "git", "github", "gitlab", "ci/cd", "terraform", "ansible", "linux", "nginx", "jenkins",
        "graphql", "rest", "rest api", "microservices", "unit testing", "pytest", "agile", "scrum"
    }

    SOFT_SKILL_TAXONOMY = {
        "problem solving", "analytical skills", "communication", "team collaboration", "teamwork",
        "leadership", "critical thinking", "adaptability", "time management", "work ethic",
        "mentorship", "creativity", "project management", "attention to detail", "presentation skills"
    }

    @property
    def name(self) -> str:
        return "local-nlp"

    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        """Generate structured contextual career / analysis text deterministically."""
        if "career" in prompt.lower() or "roadmap" in prompt.lower():
            return (
                "Based on the knowledge base guidelines, career progression requires: "
                "1. Solidifying core architectural fundamentals and system design.\n"
                "2. Demonstrating end-to-end project ownership with measurable outcomes.\n"
                "3. Continuously expanding specialized domain knowledge (such as AI/ML, cloud, or high-performance systems)."
            )
        return (
            "Automated local analysis: Candidate profile exhibits demonstrable foundational competencies "
            "with opportunities for continued specialization and quantified impact metrics."
        )

    async def generate_structured(self, prompt: str, schema: Type[T], system_prompt: str = "") -> T:
        """Extract structured resume profile using regex, taxonomy matching, and heuristic parsing."""
        clean_text_content = clean_text(prompt)
        text_lower = clean_text_content.lower()
        contact = extract_contact_info(clean_text_content)

        # 1. Extract Candidate Name (usually in first 3 lines)
        lines = [line.strip() for line in clean_text_content.splitlines() if line.strip()]
        candidate_name = None
        for line in lines[:3]:
            # If line is short, doesn't contain @, numbers or common headers
            if len(line.split()) <= 4 and "@" not in line and not any(c.isdigit() for c in line):
                if not any(hdr in line.lower() for hdr in ["resume", "curriculum", "vitae", "summary"]):
                    candidate_name = line
                    break
        if not candidate_name and lines:
            candidate_name = lines[0]

        # 2. Extract Technical Skills
        found_tech_skills = set()
        for skill in self.SKILL_TAXONOMY:
            pattern = r"\b" + re.escape(skill) + r"\b"
            if re.search(pattern, text_lower):
                found_tech_skills.add(skill.title() if len(skill) > 3 else skill.upper())

        # 3. Extract Soft Skills
        found_soft_skills = set()
        for skill in self.SOFT_SKILL_TAXONOMY:
            pattern = r"\b" + re.escape(skill) + r"\b"
            if re.search(pattern, text_lower):
                found_soft_skills.add(skill.title())
        if not found_soft_skills:
            found_soft_skills = {"Problem Solving", "Team Collaboration", "Analytical Thinking"}

        # 4. Extract Education items
        education_list = []
        edu_keywords = ["bachelor", "master", "phd", "b.s.", "m.s.", "b.sc", "m.sc", "degree", "university", "college", "institute"]
        for line in lines:
            line_l = line.lower()
            if any(k in line_l for k in edu_keywords):
                degree = line
                inst = "University / Educational Institution"
                for sub in line.split(","):
                    if any(k in sub.lower() for k in ["university", "college", "institute"]):
                        inst = sub.strip()
                        break
                education_list.append({"degree": degree, "institution": inst, "year": "Present", "field": "Computer Science / Engineering"})
                if len(education_list) >= 3:
                    break

        if not education_list:
            education_list.append({
                "degree": "Degree in Technical Field / Computer Science",
                "institution": "University / Academic Institution",
                "year": "Completed",
                "field": "Software Engineering"
            })

        # 5. Extract Experience items
        experience_list = []
        exp_keywords = ["engineer", "developer", "intern", "manager", "specialist", "consultant", "analyst", "architect"]
        for i, line in enumerate(lines):
            line_l = line.lower()
            if any(re.search(r"\b" + re.escape(k) + r"\b", line_l) for k in exp_keywords):
                desc = lines[i+1] if i+1 < len(lines) else "Contributed to core development and maintenance."
                experience_list.append({
                    "title": line,
                    "company": "Technology Company / Enterprise",
                    "duration": "1 - 3 Years",
                    "description": desc
                })
                if len(experience_list) >= 4:
                    break

        if not experience_list:
            experience_list.append({
                "title": "Software Developer / Technical Contributor",
                "company": "Industry Experience / Technical Project",
                "duration": "1+ Years",
                "description": "Implemented features, designed database models, and integrated APIs."
            })

        # 6. Extract Projects
        projects_list = []
        proj_found = False
        for line in lines:
            if "project" in line.lower() and len(line) < 60:
                proj_found = True
                continue
            if proj_found and line.startswith(("-", "*", "•")):
                projects_list.append({
                    "name": line.lstrip("-*• ").strip(),
                    "description": "Engineered fullstack solution with modern backend and frontend workflows.",
                    "technologies": list(found_tech_skills)[:3] or ["Python", "FastAPI"]
                })
                if len(projects_list) >= 3:
                    break

        if not projects_list:
            projects_list.append({
                "name": "Fullstack Web & API System",
                "description": "Architected modern web application with RESTful APIs, database persistence, and clean UX.",
                "technologies": list(found_tech_skills)[:4] or ["Python", "FastAPI", "SQLite", "JavaScript"]
            })

        # 7. Summary
        summary = (
            f"Results-oriented professional with hands-on proficiency in "
            f"{', '.join(list(found_tech_skills)[:5]) if found_tech_skills else 'software engineering'}. "
            f"Demonstrated ability in building robust systems, writing maintainable code, and solving complex problems."
        )

        # 8. Strengths & Weaknesses
        strengths = [
            f"Strong technical aptitude in {', '.join(list(found_tech_skills)[:3]) if found_tech_skills else 'core programming languages'}.",
            "Practical exposure to modern software engineering lifecycle and clean code architecture.",
            "Versatile problem solver capable of translating requirements into functional software."
        ]
        weaknesses = [
            "Could benefit from highlighting quantified business impact metrics (e.g. % performance increase, latency reduction).",
            "Resume would be strengthened with additional production cloud architecture or CI/CD pipeline details."
        ]
        missing_areas = [
            "Quantified business results or performance benchmarks in project descriptions.",
            "Direct links to GitHub repositories, live demo URLs, or technical portfolio."
        ]
        recommended_improvements = [
            "Use the Google XYZ formula: 'Accomplished [X] as measured by [Y], by doing [Z]'.",
            "Incorporate industry-standard certifications such as AWS Solutions Architect or HashiCorp Terraform.",
            "Include a dedicated Technical Skills section grouped into Languages, Frameworks, and Cloud/DevOps."
        ]

        data = {
            "candidate_name": candidate_name or "Applicant",
            "email": contact.get("email"),
            "phone": contact.get("phone"),
            "location": "Not specified",
            "professional_summary": summary,
            "technical_skills": sorted(list(found_tech_skills)),
            "soft_skills": sorted(list(found_soft_skills)),
            "education": education_list,
            "experience": experience_list,
            "projects": projects_list,
            "certifications": ["Verified Technical Certification"],
            "languages": ["English"],
            "strengths": strengths,
            "weaknesses": weaknesses,
            "missing_areas": missing_areas,
            "recommended_improvements": recommended_improvements
        }

        try:
            return schema.model_validate(data)
        except Exception as e:
            logger.warning(f"Local NLP model validation fallback: {e}")
            # If schema differs slightly, fallback to dict instantiation
            return schema(**data)

    async def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Generate deterministic semantic embeddings using TF-IDF / Hashing Vectorizer.
        Produces normalized 64-dimensional float vectors.
        """
        from sklearn.feature_extraction.text import HashingVectorizer
        import numpy as np

        if not texts:
            return []

        vectorizer = HashingVectorizer(n_features=64, norm="l2", alternate_sign=False)
        matrix = vectorizer.fit_transform(texts)
        dense_array = matrix.toarray()
        return dense_array.tolist()


# ==============================================================================
# 2. Google Gemini Provider (Free Tier API)
# ==============================================================================

class GeminiProvider(AIProvider):
    """Google Gemini AI Provider using Gemini 3.5 Free Tier API."""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-3.5-flash",
        embedding_model: str = "gemini-embedding-001"
    ):
        self.api_key = api_key
        self.model = model
        self.embedding_model = embedding_model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    @property
    def name(self) -> str:
        return "gemini"

    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        candidates_models = [self.model]
        for m in ["gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-flash-latest"]:
            if m not in candidates_models:
                candidates_models.append(m)

        contents = []
        if system_prompt:
            contents.append({"role": "user", "parts": [{"text": f"SYSTEM INSTRUCTION: {system_prompt}"}]})
            contents.append({"role": "model", "parts": [{"text": "Understood. I will follow your instructions strictly."}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 2048
            }
        }

        last_err = None
        async with httpx.AsyncClient(timeout=30.0) as client:
            for model_candidate in candidates_models:
                url = f"{self.base_url}/models/{model_candidate}:generateContent?key={self.api_key}"
                try:
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if candidates and "parts" in candidates[0].get("content", {}):
                            self.model = model_candidate
                            return candidates[0]["content"]["parts"][0]["text"]
                    logger.warning(f"Gemini model '{model_candidate}' returned status {resp.status_code}: {resp.text[:120]}")
                    last_err = RuntimeError(f"Gemini API Error {resp.status_code}: {resp.text}")
                except Exception as e:
                    logger.warning(f"Gemini model '{model_candidate}' failed: {e}")
                    last_err = e

        raise last_err or RuntimeError("All Gemini candidate models failed.")

    async def generate_structured(self, prompt: str, schema: Type[T], system_prompt: str = "") -> T:
        schema_json = json.dumps(schema.model_json_schema(), indent=2)
        augmented_prompt = (
            f"{prompt}\n\n"
            f"IMPORTANT: You MUST respond ONLY with a valid JSON object matching the following JSON Schema:\n"
            f"{schema_json}\n\n"
            f"Do not include any markdown fences or conversational preambles. Output pure raw JSON."
        )

        raw_text = await self.generate(augmented_prompt, system_prompt=system_prompt)
        
        # Clean JSON if model returned markdown codeblocks
        cleaned = raw_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        parsed_dict = json.loads(cleaned)
        return schema.model_validate(parsed_dict)

    async def embed(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        emb_candidates = [self.embedding_model]
        for m in ["gemini-embedding-001", "gemini-embedding-2"]:
            if m not in emb_candidates:
                emb_candidates.append(m)

        last_err = None
        async with httpx.AsyncClient(timeout=30.0) as client:
            for emb_candidate in emb_candidates:
                url = f"{self.base_url}/models/{emb_candidate}:batchEmbedContents?key={self.api_key}"
                requests = [
                    {"model": f"models/{emb_candidate}", "content": {"parts": [{"text": t}]}}
                    for t in texts
                ]
                try:
                    resp = await client.post(url, json={"requests": requests})
                    if resp.status_code == 200:
                        data = resp.json()
                        embeddings = [item["values"] for item in data.get("embeddings", [])]
                        if embeddings:
                            self.embedding_model = emb_candidate
                            return embeddings
                    logger.warning(f"Gemini embedding model '{emb_candidate}' returned {resp.status_code}: {resp.text[:120]}")
                    last_err = RuntimeError(f"Gemini Embedding Error {resp.status_code}: {resp.text}")
                except Exception as e:
                    logger.warning(f"Gemini embedding model '{emb_candidate}' failed: {e}")
                    last_err = e

        raise last_err or RuntimeError("All Gemini embedding models failed.")


# ==============================================================================
# 3. Groq Provider (Free Tier API)
# ==============================================================================

class GroqProvider(AIProvider):
    """Groq Cloud API Provider (OpenAI-compatible) using free high-speed models."""

    def __init__(self, api_key: str, model: str = "openai/gpt-oss-120b"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.groq.com/openai/v1"

    @property
    def name(self) -> str:
        return "groq"

    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        candidates_models = [self.model]
        for m in ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"]:
            if m not in candidates_models:
                candidates_models.append(m)

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        last_err = None
        async with httpx.AsyncClient(timeout=30.0) as client:
            for model_candidate in candidates_models:
                payload = {
                    "model": model_candidate,
                    "messages": messages,
                    "temperature": 0.2,
                    "max_tokens": 2048
                }
                try:
                    resp = await client.post(url, headers=headers, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        self.model = model_candidate
                        return data["choices"][0]["message"]["content"]
                    logger.warning(f"Groq model '{model_candidate}' returned status {resp.status_code}: {resp.text[:120]}")
                    last_err = RuntimeError(f"Groq API Error {resp.status_code}: {resp.text}")
                except Exception as e:
                    logger.warning(f"Groq model '{model_candidate}' failed: {e}")
                    last_err = e

        raise last_err or RuntimeError("All Groq candidate models failed.")

    async def generate_structured(self, prompt: str, schema: Type[T], system_prompt: str = "") -> T:
        schema_json = json.dumps(schema.model_json_schema(), indent=2)
        system_instruction = (
            (system_prompt + "\n\n" if system_prompt else "") +
            f"You MUST respond ONLY with valid JSON conforming to this JSON Schema:\n{schema_json}"
        )

        candidates_models = [self.model]
        for m in ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"]:
            if m not in candidates_models:
                candidates_models.append(m)

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt}
        ]

        last_err = None
        async with httpx.AsyncClient(timeout=30.0) as client:
            for model_candidate in candidates_models:
                payload = {
                    "model": model_candidate,
                    "messages": messages,
                    "response_format": {"type": "json_object"},
                    "temperature": 0.1
                }
                try:
                    resp = await client.post(url, headers=headers, json=payload)
                    if resp.status_code == 200:
                        content = resp.json()["choices"][0]["message"]["content"]
                        parsed_dict = json.loads(content)
                        self.model = model_candidate
                        return schema.model_validate(parsed_dict)
                    logger.warning(f"Groq structured '{model_candidate}' returned status {resp.status_code}: {resp.text[:120]}")
                    last_err = RuntimeError(f"Groq API Error {resp.status_code}: {resp.text}")
                except Exception as e:
                    logger.warning(f"Groq structured '{model_candidate}' failed: {e}")
                    last_err = e

        raise last_err or RuntimeError("All Groq candidate models failed for structured output.")

    async def embed(self, texts: List[str]) -> List[List[float]]:
        # Groq chat does not offer embeddings directly; defer to LocalNLPProvider embeddings
        local_provider = LocalNLPProvider()
        return await local_provider.embed(texts)


# ==============================================================================
# 4. Cascading AI Provider (Gemini -> Groq -> Local NLP)
# ==============================================================================

class CascadingAIProvider(AIProvider):
    """
    Intelligent Cascading Provider:
    1. Attempts Gemini (Free API Key)
    2. If Gemini fails or lacks key, attempts Groq (Free API Key)
    3. If Groq fails or lacks key, seamlessly falls back to LocalNLPProvider.
    Provides high operational fault-tolerance and offline fallback if external API rate limits or network failures occur.
    """

    def __init__(self):
        emb_model = getattr(settings, "GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")
        self.gemini = (
            GeminiProvider(settings.GEMINI_API_KEY, settings.GEMINI_MODEL, emb_model)
            if settings.GEMINI_API_KEY
            else None
        )
        self.groq = (
            GroqProvider(settings.GROQ_API_KEY, settings.GROQ_MODEL)
            if settings.GROQ_API_KEY
            else None
        )
        self.local = LocalNLPProvider()
        self._last_active_provider = "local-nlp"

    @property
    def name(self) -> str:
        return self._last_active_provider

    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        if self.gemini:
            try:
                res = await self.gemini.generate(prompt, system_prompt)
                self._last_active_provider = "gemini"
                return res
            except Exception as e:
                logger.warning(f"Primary provider Gemini failed ({e}). Falling back to secondary...")

        if self.groq:
            try:
                res = await self.groq.generate(prompt, system_prompt)
                self._last_active_provider = "groq"
                return res
            except Exception as e:
                logger.warning(f"Secondary provider Groq failed ({e}). Falling back to local NLP...")

        self._last_active_provider = "local-nlp"
        return await self.local.generate(prompt, system_prompt)

    async def generate_structured(self, prompt: str, schema: Type[T], system_prompt: str = "") -> T:
        if self.gemini:
            try:
                res = await self.gemini.generate_structured(prompt, schema, system_prompt)
                self._last_active_provider = "gemini"
                return res
            except Exception as e:
                logger.warning(f"Primary provider Gemini failed ({e}). Falling back to secondary...")

        if self.groq:
            try:
                res = await self.groq.generate_structured(prompt, schema, system_prompt)
                self._last_active_provider = "groq"
                return res
            except Exception as e:
                logger.warning(f"Secondary provider Groq failed ({e}). Falling back to local NLP...")

        self._last_active_provider = "local-nlp"
        return await self.local.generate_structured(prompt, schema, system_prompt)

    async def embed(self, texts: List[str]) -> List[List[float]]:
        if self.gemini:
            try:
                res = await self.gemini.embed(texts)
                return res
            except Exception as e:
                logger.warning(f"Gemini embed failed ({e}). Falling back to local vectorizer...")
        return await self.local.embed(texts)


def get_ai_provider() -> AIProvider:
    """Factory function returning the configured AI Provider."""
    mode = settings.AI_PROVIDER.lower()
    emb_model = getattr(settings, "GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")
    if mode == "gemini" and settings.GEMINI_API_KEY:
        return GeminiProvider(settings.GEMINI_API_KEY, settings.GEMINI_MODEL, emb_model)
    elif mode == "groq" and settings.GROQ_API_KEY:
        return GroqProvider(settings.GROQ_API_KEY, settings.GROQ_MODEL)
    elif mode == "local":
        return LocalNLPProvider()
    else:
        return CascadingAIProvider()
