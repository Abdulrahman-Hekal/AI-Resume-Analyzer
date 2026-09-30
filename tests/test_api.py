import io
from tests.test_resume_parser import create_sample_docx_bytes

def test_health_check(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"
    assert "active_ai_provider" in res.json()

def test_frontend_static_assets_and_pages(client):
    """Verify that root landing page, HTML pages, CSS files, and JS files load with 200 OK."""
    # Root index
    r_index = client.get("/")
    assert r_index.status_code == 200
    assert "html" in r_index.headers.get("content-type", "")

    # Static CSS
    r_css1 = client.get("/css/style.css")
    assert r_css1.status_code == 200

    r_css2 = client.get("/css/components.css")
    assert r_css2.status_code == 200

    r_css3 = client.get("/css/pages.css")
    assert r_css3.status_code == 200

    # Static JS
    r_js1 = client.get("/js/api.js")
    assert r_js1.status_code == 200

    r_js2 = client.get("/js/auth.js")
    assert r_js2.status_code == 200

    r_js3 = client.get("/js/utils.js")
    assert r_js3.status_code == 200

    # Clean HTML page routes
    assert client.get("/login.html").status_code == 200
    assert client.get("/login").status_code == 200
    assert client.get("/dashboard").status_code == 200
    assert client.get("/career").status_code == 200


def test_end_to_end_user_flow(client):
    # 1. Register
    reg_payload = {
        "email": "e2e_student@university.edu",
        "password": "Password123!",
        "full_name": "E2E Student",
        "role": "user"
    }
    reg_res = client.post("/api/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Upload sample resume
    resume_text = (
        "E2E Candidate\n"
        "Email: e2e_student@university.edu | Phone: 555-987-6543\n\n"
        "Professional Summary:\n"
        "Dedicated software engineer with extensive experience in Python, FastAPI, SQLite, and Docker.\n\n"
        "Technical Skills:\n"
        "Python, FastAPI, SQL, SQLite, Docker, Git, JavaScript, REST API.\n\n"
        "Experience:\n"
        "Backend Developer at CloudCorp (2 years).\n"
        "Engineered RESTful microservices and optimized database queries.\n\n"
        "Education:\n"
        "Bachelor of Science in Computer Science, State University, 2024."
    )
    docx_bytes = create_sample_docx_bytes(resume_text)
    files = {"file": ("e2e_resume.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    up_res = client.post("/api/resumes", files=files, headers=headers)
    assert up_res.status_code == 201
    resume_id = up_res.json()["id"]

    # 3. Analyze resume with Resume Analyzer Agent (Agent 1)
    an_res = client.post(f"/api/resumes/{resume_id}/analyze", headers=headers)
    assert an_res.status_code == 200
    an_data = an_res.json()
    assert "Python" in an_data["technical_skills"] or "FastAPI" in an_data["technical_skills"]
    assert len(an_data["strengths"]) > 0

    # 4. Create a test job to match against
    job_payload = {
        "title": "Python Backend Engineer",
        "company": "Horizon Cloud",
        "description": "Develop high performance microservices using Python, FastAPI, and Docker.",
        "required_skills": ["Python", "FastAPI", "Docker"],
        "preferred_skills": ["SQL", "Git"],
        "experience_years": 2.0,
        "education_level": "Bachelor's",
        "location": "Remote",
        "employment_type": "Full-time"
    }
    client.post("/api/jobs", json=job_payload, headers=headers)

    # 5. Generate Recommendations with Job Matching Agent (Agent 2)
    rec_res = client.post(f"/api/resumes/{resume_id}/recommendations", headers=headers)
    assert rec_res.status_code == 200
    rec_data = rec_res.json()
    assert rec_data["total"] >= 1
    top_rec = rec_data["recommendations"][0]
    assert top_rec["match_score"] > 60.0
    assert len(top_rec["matching_skills"]) > 0
    assert len(top_rec["match_explanation"]) > 10

    # 6. Ask Career Advisor (Agent 3) with RAG
    q_payload = {
        "question": "What skills should I learn next to advance from junior to senior backend developer?",
        "resume_id": resume_id
    }
    q_res = client.post("/api/career/questions", json=q_payload, headers=headers)
    assert q_res.status_code == 200
    q_data = q_res.json()
    assert len(q_data["answer"]) > 20
    assert len(q_data["career_roadmap"]) == 3

def test_resume_isolation_and_authorization(client):
    # User 1
    u1 = client.post("/api/auth/register", json={"email": "u1@test.com", "password": "Pass123!", "full_name": "U1"}).json()
    h1 = {"Authorization": f"Bearer {u1['access_token']}"}

    # User 2
    u2 = client.post("/api/auth/register", json={"email": "u2@test.com", "password": "Pass123!", "full_name": "U2"}).json()
    h2 = {"Authorization": f"Bearer {u2['access_token']}"}

    # User 1 uploads resume
    docx_bytes = create_sample_docx_bytes("User 1 Resume Python Developer")
    up = client.post("/api/resumes", files={"file": ("u1.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}, headers=h1)
    res_id = up.json()["id"]

    # User 2 tries to access User 1's resume -> should be 403 Forbidden
    steal_res = client.get(f"/api/resumes/{res_id}", headers=h2)
    assert steal_res.status_code == 403
    assert "permission" in steal_res.json()["detail"].lower()

    # User 2 tries to analyze User 1's resume -> should be 403 Forbidden
    steal_analyze = client.post(f"/api/resumes/{res_id}/analyze", headers=h2)
    assert steal_analyze.status_code == 403

    # User 2 tries to generate recommendations for User 1's resume -> should be 403 Forbidden
    steal_rec = client.post(f"/api/resumes/{res_id}/recommendations", headers=h2)
    assert steal_rec.status_code == 403

    # User 2 tries to delete User 1's resume -> should be 403 Forbidden
    steal_delete = client.delete(f"/api/resumes/{res_id}", headers=h2)
    assert steal_delete.status_code == 403

def test_unauthorized_access_to_protected_endpoints(client):
    """Verify that unauthenticated requests to protected endpoints return 401 Unauthorized."""
    assert client.get("/api/resumes").status_code == 401
    assert client.post("/api/resumes").status_code == 401
    assert client.get("/api/auth/me").status_code == 401
    assert client.post("/api/jobs", json={}).status_code == 401

def test_job_ownership_and_modification_permissions(client):
    """Verify that non-creators and non-admins cannot edit or delete another user's job listing."""
    # User 1 creates a job
    u1 = client.post("/api/auth/register", json={"email": "creator@test.com", "password": "Pass123!", "full_name": "Job Creator"}).json()
    h1 = {"Authorization": f"Bearer {u1['access_token']}"}

    job_data = {
        "title": "Lead DevOps Engineer",
        "company": "InfraCorp",
        "description": "Maintain cloud infra and Kubernetes clusters.",
        "required_skills": ["Kubernetes", "Terraform"],
        "preferred_skills": ["AWS"],
        "experience_years": 5.0,
        "education_level": "Bachelor's"
    }
    job_res = client.post("/api/jobs", json=job_data, headers=h1)
    assert job_res.status_code == 201
    job_id = job_res.json()["id"]

    # User 2 (not creator, not admin) attempts to update the job
    u2 = client.post("/api/auth/register", json={"email": "other@test.com", "password": "Pass123!", "full_name": "Other User"}).json()
    h2 = {"Authorization": f"Bearer {u2['access_token']}"}

    update_res = client.put(f"/api/jobs/{job_id}", json={"title": "Hacked Title"}, headers=h2)
    assert update_res.status_code == 403
    assert "permission" in update_res.json()["detail"].lower()

    # User 2 attempts to delete the job
    delete_res = client.delete(f"/api/jobs/{job_id}", headers=h2)
    assert delete_res.status_code == 403

    # Creator updates successfully
    good_update = client.put(f"/api/jobs/{job_id}", json={"title": "Principal DevOps Engineer"}, headers=h1)
    assert good_update.status_code == 200
    assert good_update.json()["title"] == "Principal DevOps Engineer"

