# Software Requirements Specification (SRS) Traceability Matrix

This document traces all functional requirements (FR-1 through FR-7), AI agent workflows, Retrieval-Augmented Generation (RAG) pipelines, non-functional requirements, and required deliverables to their concrete source-code implementation and automated test coverage.

Strict evaluation status values used: `PASS`, `PARTIAL`, `FAIL`.

---

## 1. Functional Requirements (FR)

| Requirement | Implementation | Test | Status | Notes |
| :--- | :--- | :--- | :---: | :--- |
| **FR-1.1: Register** | `app/api/routes/auth.py`<br>`app/services/auth_service.py` | `tests/test_auth.py::test_register_success`<br>`tests/test_auth.py::test_register_duplicate_email` | **PASS** | Validates email uniqueness, bcrypt password hashing, returns JWT bearer token. |
| **FR-1.2: Login** | `app/api/routes/auth.py`<br>`app/services/auth_service.py` | `tests/test_auth.py::test_login_success`<br>`tests/test_auth.py::test_login_invalid_password` | **PASS** | Verifies credentials against salted bcrypt hash, generates access JWT token. |
| **FR-1.3: Logout** | `frontend/js/auth.js`<br>`frontend/js/api.js` | `tests/test_auth.py::test_me_unauthorized` | **PASS** | Client-side stateless JWT token purge with server-side validation on expiration. |
| **FR-2.1: PDF Upload** | `app/api/routes/resumes.py`<br>`app/services/resume_parser.py` | `tests/test_resume_parser.py::test_pdf_extraction`<br>`tests/test_resume_parser.py::test_api_resume_upload_and_list` | **PASS** | Streams bytes, extracts text via `pypdf`, extracts contact info, saves file to disk securely. |
| **FR-2.2: DOCX Upload** | `app/api/routes/resumes.py`<br>`app/services/resume_parser.py` | `tests/test_resume_parser.py::test_docx_extraction`<br>`tests/test_resume_parser.py::test_api_resume_upload_and_list` | **PASS** | Parses paragraphs and structured table cells via `python-docx`. |
| **FR-2.3: Upload Validation** | `app/utils/file_validation.py` | `tests/test_resume_parser.py::test_empty_file_validation`<br>`tests/test_resume_parser.py::test_invalid_extension`<br>`tests/test_resume_parser.py::test_oversized_file_validation` | **PASS** | Validates size (0 to 10MB limit) and allowed extensions (`.pdf`, `.docx`). |
| **FR-2.4: Graceful Invalid-File Handling** | `app/utils/file_validation.py`<br>`app/services/resume_parser.py` | `tests/test_resume_parser.py::test_corrupted_pdf_header`<br>`tests/test_resume_parser.py::test_fake_docx_header`<br>`tests/test_resume_parser.py::test_scanned_image_only_pdf_disclaimer`<br>`tests/test_resume_parser.py::test_corrupted_pdf_structure` | **PASS** | Validates magic bytes (`%PDF-`, `PK\x03\x04`), handles corrupt streams, returns clear 400 errors for scanned PDFs requiring OCR. |
| **FR-3.1: Resume Information Extraction** | `app/agents/resume_analyzer.py`<br>`app/schemas/analysis.py` | `tests/test_api.py::test_end_to_end_user_flow` | **PASS** | Extracts contact details (email, phone), candidate name, and objective profile. |
| **FR-3.2: Technical Skills Extraction** | `app/services/ai_service.py`<br>`app/agents/resume_analyzer.py` | `tests/test_api.py::test_end_to_end_user_flow` | **PASS** | Standardizes industry skills into canonical tags (e.g. Python, FastAPI, Docker, React). |
| **FR-3.3: Soft Skills Extraction** | `app/services/ai_service.py`<br>`app/agents/resume_analyzer.py` | `tests/test_api.py::test_end_to_end_user_flow` | **PASS** | Categorizes interpersonal and problem-solving competencies. |
| **FR-3.4: Education Extraction** | `app/services/ai_service.py`<br>`app/agents/resume_analyzer.py` | `tests/test_api.py::test_end_to_end_user_flow` | **PASS** | Extracts degree, institution, field of study, and graduation period. |
| **FR-3.5: Experience Extraction** | `app/services/ai_service.py`<br>`app/agents/resume_analyzer.py` | `tests/test_api.py::test_end_to_end_user_flow` | **PASS** | Extracts roles, companies, durations, and core responsibilities. |
| **FR-3.6: Summary Generation** | `app/services/ai_service.py`<br>`app/agents/resume_analyzer.py` | `tests/test_api.py::test_end_to_end_user_flow` | **PASS** | Synthesizes an executive professional summary reflecting candidate experience. |
| **FR-4.1: Resume/Job Comparison** | `app/services/matching_service.py`<br>`app/agents/job_matcher.py` | `tests/test_matching.py::test_full_composite_match_evaluation`<br>`tests/test_api.py::test_end_to_end_user_flow` | **PASS** | Multi-factor evaluation across skills, experience, education, and semantic similarity. |
| **FR-4.2: Matching Score** | `app/services/matching_service.py` | `tests/test_matching.py::test_full_composite_match_evaluation`<br>`tests/test_matching.py::test_edge_case_empty_resume_profile` | **PASS** | Transparent 4-part weighted formula strictly bounded between 0.0% and 100.0%. |
| **FR-4.3: Job Recommendations** | `app/api/routes/recommendations.py` | `tests/test_api.py::test_end_to_end_user_flow` | **PASS** | Ranks available job postings by match score descending, identifies top match. |
| **FR-4.4: Recommendation Explanations** | `app/agents/job_matcher.py` | `tests/test_matching.py::test_full_composite_match_evaluation`<br>`tests/test_api.py::test_end_to_end_user_flow` | **PASS** | Generates 2-4 sentence narrative explaining candidate fit and bridging strategies. |
| **FR-5.1: Missing Skills Identification** | `app/services/matching_service.py` | `tests/test_matching.py::test_skill_overlap_calculation`<br>`tests/test_matching.py::test_java_vs_javascript_safety` | **PASS** | Identifies unfulfilled mandatory and preferred skills without substring false-positives. |
| **FR-5.2: Weaknesses & Gaps** | `app/agents/resume_analyzer.py`<br>`app/services/matching_service.py` | `tests/test_api.py::test_end_to_end_user_flow` | **PASS** | Identifies unquantified metrics, short durations, or degree mismatches. |
| **FR-5.3: Actionable Improvements** | `app/agents/resume_analyzer.py`<br>`app/schemas/analysis.py` | `tests/test_api.py::test_end_to_end_user_flow` | **PASS** | Suggests Google XYZ bullet formula and domain-specific enhancements. |
| **FR-5.4: Recommended Certifications** | `app/agents/career_advisor.py`<br>`app/api/routes/career.py` | `tests/test_rag.py::test_career_advisor_rag_grounded_answer`<br>`tests/test_api.py::test_end_to_end_user_flow` | **PASS** | Targets industry certifications (AWS, CKA, Terraform) based on skill gaps. |
| **FR-5.5: Curated Learning Resources** | `app/agents/career_advisor.py`<br>`app/db/seed.py` | `tests/test_rag.py::test_career_advisor_rag_grounded_answer` | **PASS** | Links to verified high-ROI documentation, books, and courses. |
| **FR-6.1: Add Jobs** | `app/api/routes/jobs.py`<br>`app/services/job_service.py` | `tests/test_jobs.py::test_create_and_get_job`<br>`tests/test_api.py::test_job_ownership_and_modification_permissions` | **PASS** | Creates job posting with required/preferred skills, exp years, and education level. |
| **FR-6.2: Edit Jobs** | `app/api/routes/jobs.py`<br>`app/services/job_service.py` | `tests/test_jobs.py::test_update_and_delete_job`<br>`tests/test_api.py::test_job_ownership_and_modification_permissions` | **PASS** | Updates existing job listing with creator/admin authorization check. |
| **FR-6.3: Delete Jobs** | `app/api/routes/jobs.py`<br>`app/services/job_service.py` | `tests/test_jobs.py::test_update_and_delete_job`<br>`tests/test_api.py::test_job_ownership_and_modification_permissions` | **PASS** | Cascades delete through associated recommendation rows. |
| **FR-6.4: View Jobs** | `app/api/routes/jobs.py`<br>`app/services/job_service.py` | `tests/test_jobs.py::test_create_and_get_job`<br>`tests/test_jobs.py::test_job_search_filters` | **PASS** | Returns paginated list and detailed individual view. |
| **FR-7.1: Job Search & Filters** | `app/repositories/jobs.py`<br>`app/services/job_service.py` | `tests/test_jobs.py::test_job_search_filters` | **PASS** | Multi-criteria search across keyword, skill, min/max experience, location, and type. |

---

## 2. AI Agents & Workflows

| Requirement | Implementation | Test | Status | Notes |
| :--- | :--- | :--- | :---: | :--- |
| **Agent 1: Resume Analyzer Agent** | `app/agents/resume_analyzer.py` | `tests/test_api.py::test_end_to_end_user_flow` | **PASS** | Takes raw resume text, validates structured output via `StructuredResumeProfile` Pydantic schema, enforces zero-hallucination rules. |
| **Agent 2: Job Matching Agent** | `app/agents/job_matcher.py` | `tests/test_matching.py::test_full_composite_match_evaluation`<br>`tests/test_api.py::test_end_to_end_user_flow` | **PASS** | Evaluates candidate against job listings using deterministic mathematical scoring plus LLM match rationale explanation. |
| **Agent 3: Career Advisor Agent** | `app/agents/career_advisor.py` | `tests/test_rag.py::test_career_advisor_rag_grounded_answer`<br>`tests/test_api.py::test_end_to_end_user_flow` | **PASS** | Answers career queries by executing pre-generation RAG vector retrieval, generating citations, and structuring a 3-phase progression roadmap. |

---

## 3. Retrieval-Augmented Generation (RAG) Requirements

| Requirement | Implementation | Test | Status | Notes |
| :--- | :--- | :--- | :---: | :--- |
| **RAG-1: Job Descriptions Category** | `app/db/seed.py`<br>`app/services/rag_service.py` | `tests/test_rag.py::test_rag_category_filtering` | **PASS** | Curated benchmark role requirements seeded in `knowledge_documents`. |
| **RAG-2: Skill Descriptions Category** | `app/db/seed.py`<br>`app/services/rag_service.py` | `tests/test_rag.py::test_rag_ingest_and_retrieve` | **PASS** | In-depth technical architecture profiles (FastAPI, Docker, Microservices). |
| **RAG-3: Career Roadmaps Category** | `app/db/seed.py`<br>`app/services/rag_service.py` | `tests/test_rag.py::test_rag_category_filtering` | **PASS** | Structured career trajectories (Junior to Senior, Fullstack, AI/ML). |
| **RAG-4: Learning Resources Category** | `app/db/seed.py`<br>`app/services/rag_service.py` | `tests/test_rag.py::test_career_advisor_rag_grounded_answer` | **PASS** | High-ROI certifications, books, and courses. |
| **RAG-5: Resume Guidelines Category** | `app/db/seed.py`<br>`app/services/rag_service.py` | `tests/test_rag.py::test_career_advisor_rag_grounded_answer` | **PASS** | ATS formatting guidelines and Google XYZ formula rules. |
| **RAG-6: Retrieval Before Generation** | `app/agents/career_advisor.py`<br>`app/services/rag_service.py` | `tests/test_rag.py::test_career_advisor_rag_grounded_answer` | **PASS** | Pipeline explicitly queries vector database before prompt assembly; verified with citations. |

---

## 4. Non-Functional Requirements (NFR)

| Requirement | Implementation | Test | Status | Notes |
| :--- | :--- | :--- | :---: | :--- |
| **NFR-1: User-Friendly Interface** | Pure Vanilla HTML5, CSS3, JavaScript | Manual browser verification | **PASS** | Clean responsive UI, dark mode palette, zero heavy frontend frameworks, accessible layout. |
| **NFR-2: Input Validation** | Pydantic V2 models (`app/schemas/`) | `tests/test_auth.py`<br>`tests/test_jobs.py` | **PASS** | Validates email formatting, string lengths, ranges, and JSON payloads. |
| **NFR-3: Invalid-File Handling** | `app/utils/file_validation.py` | `tests/test_resume_parser.py` (all 10 tests) | **PASS** | Checks extensions, 10MB limit, empty files, corrupt headers, and explains scanned PDF constraints. |
| **NFR-4: Response Time** | Async FastAPI + SQLite indexed lookups | Pytest execution metrics (< 9s for 43 tests) | **PASS** | Sub-second response times on local database operations. |
| **NFR-5: REST API Architecture** | `app/api/routes/` | `tests/test_api.py` | **PASS** | RESTful semantics, standard HTTP status codes (200, 201, 400, 401, 403, 404, 413). |
| **NFR-6: Meaningful Errors** | `fastapi.HTTPException` with explicit `detail` | All error test assertions | **PASS** | Error payloads deliver actionable messages without leaking stack traces. |
| **NFR-7: Modular Code Structure** | Clean layered architecture (`db`, `models`, `schemas`, `repositories`, `services`, `agents`, `api`) | Entire test suite | **PASS** | Strict separation of concerns across data access, business logic, and presentation. |

---

## 5. Required Deliverables

| Deliverable | Location in Repository | Status | Verification Notes |
| :--- | :--- | :---: | :--- |
| **Source Code** | `backend/` and `frontend/` | **PASS** | Complete, runnable, zero placeholder code. |
| **API Documentation** | `docs/api.md` & interactive Swagger UI at `/docs` | **PASS** | Complete endpoint specs, schemas, and status codes. |
| **Demonstration Assets** | `samples/` & `scripts/seed_data.py` | **PASS** | Pre-seeded accounts, realistic jobs, sample DOCX resumes. |
| **ER Diagram** | `docs/database.md` | **PASS** | Mermaid ER diagram accurately reflecting all 7 SQLAlchemy models and relationships. |
