# AI Resume Analyzer

An intelligent, full-stack talent intelligence and career guidance web platform. The system leverages autonomous **AI Agents** and a local **Retrieval-Augmented Generation (RAG)** pipeline to analyze uploaded resumes (PDF & DOCX), extract structured skills and facts without hallucination, compute transparent multi-factor job matches, and provide grounded career guidance.

Developed as a comprehensive university graduation software project adhering strictly to production engineering practices.

---

## 🌟 Key Features

1. **User Authentication & Authorization**:
   - Secure registration, login, and session persistence using **bcrypt** password hashing and **JWT Bearer tokens**.
   - Role-based authorization distinguishing standard candidates from administrators/recruiters.
   - User-isolated resume data protection preventing unauthorized cross-tenant data access.

2. **Resume Ingestion & Multi-Format Parsing**:
   - Supports both digital **PDF** and Microsoft Word **DOCX** documents.
   - Robust validation checking file size limits (10MB), extension whitelists, and file header magic bytes (`%PDF-` and `PK\x03\x04`).
   - Graceful detection and error handling for empty files, corrupted documents, or scanned image-only PDFs.

3. **Three Visibly Implemented AI Agents**:
   - **Agent 1: Resume Analyzer Agent**: Structured entity extraction into Pydantic models (technical skills, soft skills, education, experience, projects, strengths, and weaknesses).
   - **Agent 2: Job Matching Agent**: Multi-dimensional mathematical compatibility scoring combined with explainable AI reasoning.
   - **Agent 3: Career Advisor Agent**: RAG-grounded conversational coach generating actionable 3-phase career roadmaps and surfacing knowledge citations.

4. **Transparent Multi-Factor Matching Algorithm**:
   - Explains the exact formula behind every job match score:
     $$\text{Final Score} = (\text{Skill Score} \times 0.40) + (\text{Experience Score} \times 0.25) + (\text{Education Score} \times 0.15) + (\text{Semantic Score} \times 0.20)$$
   - Identifies matching skills (green check badges) and critical skill gaps to bridge.

5. **Retrieval-Augmented Generation (RAG) Subsystem**:
   - Curated knowledge base across 5 core categories: Job descriptions, Skill descriptions, Career roadmaps, Learning resources, and Resume guidelines.
   - Overlapping text chunking with dense vector embeddings stored in SQLite.
   - Real semantic vector retrieval via Cosine Similarity ranking, providing verifiable citations with relevance scores in the UI.

6. **Job Directory & CRUD Management**:
   - Multi-criteria job filtering: title, company, specific technical skill, maximum experience years, and employment type.
   - Interactive job creation modal for authorized users.

7. **Zero-Framework Frontend**:
   - Built purely with standard **HTML5, modern Vanilla CSS, and Vanilla JavaScript**.
   - Sophisticated Dark Mode design system (OKLCH palette, high contrast, WCAG AA compliant).
   - Real loading skeletons, animated progress gauges, interactive modal dialogs, and toast notifications.

---

## 🛠 Technology Stack

- **Backend**: Python 3.11+ / 3.13, FastAPI, Uvicorn, Pydantic v2
- **Database**: SQLite, SQLAlchemy 2.0 ORM
- **Parsers & ML**: `pypdf`, `python-docx`, `scikit-learn` (vector cosine similarity), `numpy`
- **Security**: `bcrypt`, `pyjwt`, `python-multipart`
- **Frontend**: Semantic HTML5, Vanilla CSS3 (Custom Design Tokens), Vanilla JavaScript (ES6+ Modules)
- **Testing**: `pytest`, `pytest-asyncio`, `httpx`

---

## 📁 Project Structure

```
Agents-Project/
├── backend/
│   └── app/
│       ├── main.py                  # FastAPI entry point & static mounting
│       ├── core/                    # Config, logging, security (JWT/bcrypt)
│       ├── db/                      # Database engine, SQLAlchemy models, seed data
│       ├── models/                  # Logical model definitions
│       ├── schemas/                 # Pydantic request/response & analysis schemas
│       ├── repositories/            # Encapsulated data access layer
│       ├── services/                # Business logic: parsers, RAG, AI providers
│       ├── agents/                  # 3 Dedicated AI Agents
│       ├── api/
│       │   ├── deps.py              # Auth & DB dependencies
│       │   └── routes/              # Modular API routers
│       └── utils/                   # File validation, regex contact extraction, chunking
├── frontend/                        # Pure HTML/CSS/Vanilla JS interface
│   ├── index.html                   # Landing page & demo flow overview
│   ├── login.html                   # User sign-in with 1-click demo access
│   ├── register.html                # Account creation
│   ├── dashboard.html               # Main candidate talent console
│   ├── resume.html                  # Drag & drop upload + 5 structured analysis tabs
│   ├── jobs.html                    # Searchable job directory & creation modal
│   ├── job-details.html             # Full job specs + live match breakdown
│   ├── career.html                  # Interactive Career Advisor chat with RAG citations
│   ├── css/                         # Design system tokens, components, page layouts
│   └── js/                          # REST API client, auth state, UI controllers
├── tests/                           # 26 automated unit & integration tests
├── docs/                            # Deep architectural and API documentation
│   ├── architecture.md              # System design & layered patterns
│   ├── api.md                       # Complete REST API reference
│   ├── ai-agents.md                 # Agent specifications & scoring formulas
│   ├── rag.md                       # RAG pipeline & vector retrieval details
│   ├── database.md                  # SQLite relational schema & Mermaid ER diagram
│   └── setup.md                     # Comprehensive setup guide
├── samples/                         # Pre-generated sample resumes (.docx)
├── scripts/
│   ├── seed_data.py                 # Initial database seeding script
│   └── generate_sample_resumes.py   # Test resume generator
├── .env.example                     # Environment template
├── .gitignore                       # Git exclusions
├── requirements.txt                 # Complete Python dependencies
└── README.md                        # Project documentation
```

---

## 🚀 Quick Start Guide

### 1. Set Up Environment
```bash
# Clone or navigate into project directory:
cd Agents-Project

# Create virtual environment:
python -m venv .venv

# Activate virtual environment:
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# Linux / macOS:
source .venv/bin/activate

# Install dependencies:
pip install -r requirements.txt
```

### 2. Configure Environment Variables
```bash
# Copy example configuration:
copy .env.example .env    # Windows
cp .env.example .env      # Linux/macOS
```
*(The system is pre-configured to run out-of-the-box in **cascade mode** with its local deterministic NLP & TF-IDF engine. You may optionally add free `GEMINI_API_KEY` or `GROQ_API_KEY` in `.env`).*

### 3. Seed Database with Demo Data
```bash
python scripts/seed_data.py
```

### 4. Run Application
```bash
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```

Open your browser at:
- **Web Application**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **API Swagger Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Endpoint**: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

---

## ⚡ 5-Minute Evaluation Demo Walkthrough

1. **Sign In**: Navigate to `http://127.0.0.1:8000/login.html` and log in instantly (`user@gmail.com` / `123456`).
2. **Upload Resume**: Go to **My Resumes** (`resume.html`) and drag & drop `samples/sample_alex_morgan_fullstack.docx`.
3. **Inspect Structured Extraction (Agent 1)**: Observe the 5 structured tabs:
   - *Overview*: Clean professional summary and verified contact details.
   - *Skills Matrix*: Standardized technical and soft skills.
   - *Experience & Education*: Timeline of past roles and academic background.
   - *Strengths & Weaknesses*: Objective advantages alongside actionable improvement areas.
4. **Inspect Job Recommendations (Agent 2)**: Switch to Tab 5 to see all active jobs ranked by the transparent formula breakdown (Skill 40% + Exp 25% + Edu 15% + Semantic 20%).
5. **Inspect Deep Match**: Click **"Full Job Match Analysis"** on any job to view the side-by-side comparison, matching skills, and missing skills.
6. **Ask Career Advisor (Agent 3 & RAG)**: Navigate to **Career Advisor** (`career.html`), click a prompt chip like *"What is the roadmap to transition from Junior to Senior Backend Engineer?"*, and observe the **RAG Grounding Citation box** displaying retrieved knowledge chunks alongside the generated 3-phase career roadmap!

---

## 🧪 Automated Testing

Execute the automated test suite covering all functional and non-functional requirements:

```bash
pytest -v
```

**Test Coverage Summary**:
- `test_auth.py`: Registration, duplicate validation, login, JWT decode, unauthorized rejection (6 tests).
- `test_resume_parser.py`: PDF extraction, DOCX extraction, empty file validation, oversized file rejection, corrupted header handling (6 tests).
- `test_jobs.py`: Job CRUD lifecycle, search filters by keyword, skill, and experience (3 tests).
- `test_matching.py`: Skill overlap, experience scoring, education hierarchy, full weighted formula evaluation, AI explanation (4 tests).
- `test_rag.py`: Text chunking with overlap, vector cosine similarity ranking, document ingestion, Career Advisor RAG grounding with source citations (4 tests).
- `test_api.py`: Full end-to-end integration workflow, cross-user privacy isolation, health endpoint (3 tests).
- **Total**: 26 passed tests, 0 failures.

---

## ⚠️ Limitations & Future Enhancements

- **Scanned OCR**: Resumes containing scanned images without selectable text are flagged with a user-friendly error; future iterations can integrate Tesseract OCR.
- **Persistent Vector Indexes**: The local RAG pipeline calculates cosine similarities over vector arrays in SQLite (optimal for university graduation scopes under 10,000 chunks); enterprise deployments can attach pgvector or Qdrant.
- **OAuth Providers**: Currently supports email/password authentication; GitHub/Google OAuth2 can be added in future versions.
