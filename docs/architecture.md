# System Architecture & Design

## 1. Architectural Overview

The **AI Resume Analyzer** is designed as a modern, decoupled web application following a clean layered architecture. The system combines deterministic business logic (validation, authentication, database persistence, score calculations) with semantic artificial intelligence (structured resume parsing, explainable job matching, and RAG-grounded career advising).

```
+-------------------------------------------------------------------------+
|                  Client Layer (Vanilla HTML5 / CSS3 / JS)               |
|   - Landing Page     - Dashboard        - Resume Analysis Console        |
|   - Job Directory    - Job Details View - Career Advisor Chat (RAG)     |
+------------------------------------+------------------------------------+
                                     | RESTful JSON APIs (JWT Bearer)
                                     v
+-------------------------------------------------------------------------+
|                       FastAPI Application Server                        |
|   - CORS Middleware   - JWT Auth Filter   - Centralized Error Handler   |
|   - Routers: Auth, Resumes, Analysis, Jobs, Recommendations, Career    |
+------------------------------------+------------------------------------+
                                     |
         +---------------------------+---------------------------+
         |                                                       |
         v                                                       v
+------------------------------------+   +--------------------------------+
|         AI Agents & RAG            |   |     Data Access & Repositories |
|  - Agent 1: Resume Analyzer        |   |  - UserRepository              |
|  - Agent 2: Job Matcher            |   |  - ResumeRepository            |
|  - Agent 3: Career Advisor (RAG)   |   |  - JobRepository               |
|  - Cascading AI Provider:          |   |  - AnalysisRepository          |
|    Gemini -> Groq -> Local NLP     |   |  - KnowledgeRepository         |
+------------------------------------+   +--------------------------------+
         |                                                       |
         +---------------------------+---------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                        Storage & Persistence Layer                      |
|   - SQLite Relational Database (`resume_analyzer.db`)                  |
|   - Dense Vector Embeddings (Cosine Similarity Index)                   |
|   - Uploaded Resume Storage (`./uploads/`)                              |
+-------------------------------------------------------------------------+
```

---

## 2. Layered Structure

### 2.1 Presentation Layer (Frontend)
- Built strictly with **HTML5, CSS3, and modular Vanilla JavaScript**.
- Zero frontend frameworks (no React, Angular, Vue, Next.js, or Svelte).
- Communicates asynchronously with the backend via a centralized `APIClient` (`js/api.js`).
- Implements a sophisticated dark mode palette (OKLCH color system) with high-density information layouts, accessible contrast (WCAG AA), responsive cards, and live modal dialogs.

### 2.2 API & Application Layer (FastAPI)
- Uses **FastAPI** for high-throughput asynchronous request handling and automated OpenAPI/Swagger documentation.
- **Security & Authorization**: JWT token verification via `pyjwt` and password hashing via `bcrypt`.
- **Centralized Error Handling**: Captures validation and operational exceptions, returning human-friendly JSON error objects without exposing server stack traces to clients.

### 2.3 Domain & AI Agent Layer
The application visibly separates three dedicated agents:
1. **Resume Analyzer Agent**: Extracts structured personal information, technical skills, soft skills, education, experience, projects, certifications, strengths, and weaknesses into strict Pydantic models.
2. **Job Matching Agent**: Decomposes candidate-job fit using a transparent multi-dimensional formula and generates an explainable AI rationale.
3. **Career Advisor Agent**: Employs Retrieval-Augmented Generation (RAG) to ground answers in verified career roadmaps, ATS guidelines, and technical skill descriptions.

### 2.4 AI Provider Abstraction & Cascading Strategy
The core AI engine implements the `AIProvider` Abstract Base Class:
```python
class AIProvider(abc.ABC):
    async def generate(self, prompt: str, system_prompt: str = "") -> str: ...
    async def generate_structured(self, prompt: str, schema: Type[T], system_prompt: str = "") -> T: ...
    async def embed(self, texts: List[str]) -> List[List[float]]: ...
```

To guarantee 100% operational resilience during live demonstrations and university evaluations, the system uses a **Cascading AI Architecture**:
1. **Primary Provider (Gemini)**: Utilizes Google Gemini Free Tier API (`gemini-3.5-flash` / `gemini-3.5-flash-lite` with `gemini-embedding-001` embeddings) with automatic multi-model candidate fallback.
2. **Secondary Fallback (Groq)**: Automatically engages Groq Free Tier API (`openai/gpt-oss-120b` / `openai/gpt-oss-20b`) if Gemini is unconfigured or encounters rate limits.
3. **Tertiary Fallback (Local NLP Engine)**: Executes deterministic regex parsing, taxonomy dictionary extraction, and TF-IDF semantic embeddings locally with zero external API dependencies or network requirements.

---

## 3. Design Patterns Applied

- **Repository Pattern**: Encapsulates database queries into clean repositories (`UserRepository`, `ResumeRepository`, `JobRepository`, `AnalysisRepository`, `KnowledgeRepository`), decoupling business logic from ORM implementation details.
- **Dependency Injection**: FastAPI's `Depends` injects database sessions (`get_db`) and authenticated user contexts (`get_current_user`, `get_current_admin`).
- **Factory Pattern**: `get_ai_provider()` instantiates the appropriate provider dynamically based on environment configuration.
- **Fail-Safe Degradation**: Ensures that external API errors never crash the user session or leave endpoints in an unhandled 500 state.
