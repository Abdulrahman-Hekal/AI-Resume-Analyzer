# Setup and Execution Guide

This document outlines step-by-step instructions to run, test, and demonstrate the **AI Resume Analyzer**.

---

## 1. Prerequisites

- **Python**: Version 3.11 or higher (Python 3.13 tested and verified)
- **Git** (optional)
- Standard web browser (Chrome, Edge, Firefox, Safari)

---

## 2. Environment Setup

### Step 1: Create and Activate Virtual Environment

**On Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**On macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

---

### Step 3: Configure Environment Variables

Copy the provided `.env.example` file to `.env`:
```bash
# Windows
copy .env.example .env

# Linux / macOS
cp .env.example .env
```

The application runs immediately out-of-the-box in **cascade mode** with its local deterministic NLP & TF-IDF engine. 

To optionally connect external Free Tier LLMs:
- **Google Gemini (Free API Key)**: Add `GEMINI_API_KEY="your-gemini-key"` (Get free key: [Google AI Studio](https://aistudio.google.com/app/apikey))
- **Groq (Free API Key)**: Add `GROQ_API_KEY="your-groq-key"` (Get free key: [Groq Console](https://console.groq.com/keys))

---

## 3. Database Initialization & Demo Seeding

Seed the SQLite database with initial users, 5 realistic jobs, and 8 curated RAG knowledge documents:

```bash
# From the project root:
python scripts/seed_data.py
```

*Note: The application will also auto-seed the database on startup if empty.*

---

## 4. Running the Application

Launch the unified FastAPI server (which serves both the REST API and the Vanilla HTML/CSS/JS frontend):

```bash
# Windows / Linux:
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```

Open your browser to:
- **Frontend Web Application**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive API Documentation (Swagger UI)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **System Health Status**: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

---

## 5. Demo Credentials & Sample Resumes

### Demo Accounts:
| Role | Email | Password |
|---|---|---|
| **Candidate / Job Seeker** | `candidate@resumeai.com` | `Candidate123!` |
| **Recruiter / Admin** | `admin@resumeai.com` | `AdminPass123!` |

*(Both accounts are pre-configured with 1-click auto-fill buttons on the login page).*

### Sample Test Resumes:
Pre-generated resumes are provided in the `samples/` directory:
1. `samples/sample_alex_morgan_fullstack.docx` (Fullstack & Python Developer)
2. `samples/sample_sarah_connor_ml_engineer.docx` (Machine Learning & AI Engineer)

---

## 6. Running Automated Tests

Run the complete 26-test suite covering authentication, parsing, matching formulas, RAG retrieval, and security:

```bash
pytest -v
```
