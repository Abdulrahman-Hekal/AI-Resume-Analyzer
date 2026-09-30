# AI Agent Architecture & Multi-Agent Collaboration

The system visibly implements three specialized AI Agents, each dedicated to a distinct stage of the talent intelligence workflow.

```
                    +---------------------------+
                    |    Extracted Resume Text  |
                    +-------------+-------------+
                                  |
                                  v
+-------------------------------------------------------------------------------+
|                       AGENT 1: Resume Analyzer Agent                          |
|  - Role: Information extraction & candidate profiler                          |
|  - Guarantees: Strict Pydantic model validation, zero hallucination           |
|  - Outputs: Technical skills, soft skills, experience, education, strengths   |
+---------------------------------+---------------------------------------------+
                                  |
                                  v Structured Profile
+---------------------------------+---------------------------------------------+
|                       AGENT 2: Job Matching Agent                             |
|  - Role: Deterministic evaluation + AI semantic rationale                     |
|  - Formula: Skill (40%) + Exp (25%) + Edu (15%) + Semantic (20%)              |
|  - Outputs: Match score (0-100), matching/missing skills, match explanation   |
+---------------------------------+---------------------------------------------+
                                  |
                                  v Match Gaps & Profile
+---------------------------------+---------------------------------------------+
|                       AGENT 3: Career Advisor Agent (RAG)                     |
|  - Role: Grounded career coach & roadmap generator                            |
|  - Pipeline: User Question -> Vector Embedding -> RAG Chunks -> Grounded LLM  |
|  - Outputs: Grounded answer with citations, 3-phase roadmap, certifications   |
+-------------------------------------------------------------------------------+
```

---

## 1. Important AI Engineering Principles
1. **Deterministic Code Over AI Guesswork**:
   - Validation (file types, size, magic bytes) is handled in pure Python.
   - Authentication and password hashing are handled strictly via bcrypt and JWT.
   - Core scoring components (skill overlap percentage, years of experience calculation, education hierarchy) are calculated using transparent mathematical formulas.
2. **Zero Hallucination Standard**:
   - The LLM is explicitly forbidden from inventing candidate details (such as unlisted phone numbers, false degrees, or unearned certifications).
   - If an attribute is missing from the resume text, the agent outputs `null` or an empty list.
   - Direct regex extraction verifies and cross-checks candidate emails and contact information.

---

## 2. Agent 1 — Resume Analyzer Agent (`app/agents/resume_analyzer.py`)

- **Input**: Cleaned plain text extracted from PDF or DOCX resume.
- **Output**: Validated `StructuredResumeProfile` Pydantic model:
  - `candidate_name`, `email`, `phone`, `location`
  - `professional_summary`
  - `technical_skills`: List of standardized industry tools and languages
  - `soft_skills`: Interpersonal and analytical competencies
  - `education`: List of degrees, institutions, graduation dates, majors
  - `experience`: List of roles, companies, durations, responsibilities
  - `projects`: Technical initiatives and technologies utilized
  - `certifications` & `languages`
  - `strengths`: Objective technical and professional advantages
  - `weaknesses`: Actionable resume gaps (e.g. missing quantified metrics)
  - `recommended_improvements`: Concrete edits using the Google XYZ formula

---

## 3. Agent 2 — Job Matching Agent (`app/agents/job_matcher.py`)

- **Philosophy**: Never blindly trust an LLM to generate an arbitrary percentage score.
- **Formula & Weights**:
  $$\text{Final Score} = (\text{Skill Score} \times 0.40) + (\text{Experience Score} \times 0.25) + (\text{Education Score} \times 0.15) + (\text{Semantic Score} \times 0.20)$$

| Component | Weight | Calculation Method |
|---|---|---|
| **Skill Overlap** | **40%** | Ratio of matched required skills (80% weight) and preferred skills (20% weight) |
| **Experience Fit** | **25%** | Candidate estimated experience years vs. job required experience |
| **Education Level** | **15%** | Educational hierarchy ladder (High School < Associate < Bachelor's < Master's < PhD) |
| **Semantic Similarity**| **20%** | Cosine similarity between candidate summary embedding and job description embedding |

- **Agent Rationale**: The agent takes the mathematical scores and produces an explainable, 2-4 sentence narrative detailing why the candidate fits the role and how to bridge any remaining gaps.

---

## 4. Agent 3 — Career Advisor Agent (`app/agents/career_advisor.py`)

- **Role**: Answers career development and technical interview questions grounded in the RAG knowledge base.
- **Features**:
  - Incorporates the candidate's actual analyzed weaknesses to provide bespoke advice.
  - Generates a **3-Phase Career Progression Roadmap**:
    - *Phase 1*: Core Competency & Architectural Foundation
    - *Phase 2*: Cloud Native & Containerization Deployment
    - *Phase 3*: Production Scale & Domain Specialization
  - Surfaces **Retrieved Source Citations** with similarity scores and document titles to verify that advice is grounded rather than hallucinated.

---

## 5. Cascading AI Provider Architecture

To guarantee maximum reliability during demonstrations:

```
                  Incoming Request
                         |
                         v
             +-----------------------+
             | Gemini Free Tier API  | -----> Success (Returns Response)
             +-----------+-----------+
                         | (Fails or No API Key)
                         v
             +-----------------------+
             |  Groq Free Tier API   | -----> Success (Returns Response)
             +-----------+-----------+
                         | (Fails or No API Key)
                         v
             +-----------------------+
             | Local Deterministic   | -----> Always Succeeds (100% Offline)
             | NLP & TF-IDF Vectors  |
             +-----------------------+
```
