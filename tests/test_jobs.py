def test_create_and_get_job(client, admin_auth_headers):
    payload = {
        "title": "Machine Learning Engineer",
        "company": "DeepTech AI",
        "description": "Building computer vision and NLP models using PyTorch and Python.",
        "required_skills": ["Python", "PyTorch", "NLP", "Machine Learning"],
        "preferred_skills": ["FastAPI", "Docker"],
        "experience_years": 2.5,
        "education_level": "Bachelor's",
        "location": "Boston, MA",
        "employment_type": "Full-time",
        "salary_range": "$110,000 - $135,000",
        "contact_email": "ml-jobs@deeptech.ai"
    }
    # Create
    create_res = client.post("/api/jobs", json=payload, headers=admin_auth_headers)
    assert create_res.status_code == 201
    job_id = create_res.json()["id"]
    assert create_res.json()["title"] == "Machine Learning Engineer"

    # Get details
    get_res = client.get(f"/api/jobs/{job_id}")
    assert get_res.status_code == 200
    assert get_res.json()["company"] == "DeepTech AI"
    assert get_res.json()["contact_email"] == "ml-jobs@deeptech.ai"
    assert "PyTorch" in get_res.json()["required_skills"]

def test_update_and_delete_job(client, admin_auth_headers):
    payload = {
        "title": "Temp QA Engineer",
        "company": "Test Co",
        "description": "Writing automated test suites in pytest.",
        "required_skills": ["Python", "Pytest"],
        "preferred_skills": [],
        "experience_years": 1.0,
        "education_level": "Bachelor's",
        "location": "Remote",
        "employment_type": "Contract",
        "contact_email": "qa@testco.com"
    }
    c_res = client.post("/api/jobs", json=payload, headers=admin_auth_headers)
    assert c_res.status_code == 201
    job_id = c_res.json()["id"]

    # Update
    u_res = client.put(f"/api/jobs/{job_id}", json={"title": "Senior QA Automation Engineer"}, headers=admin_auth_headers)
    assert u_res.status_code == 200
    assert u_res.json()["title"] == "Senior QA Automation Engineer"

    # Delete
    d_res = client.delete(f"/api/jobs/{job_id}", headers=admin_auth_headers)
    assert d_res.status_code == 200

    # Verify not found
    check = client.get(f"/api/jobs/{job_id}")
    assert check.status_code == 404

def test_job_search_filters(client, admin_auth_headers):
    j1 = {
        "title": "Cloud Architect",
        "company": "Amazonian Labs",
        "description": "Design secure AWS cloud solutions and Terraform infrastructure.",
        "required_skills": ["AWS", "Terraform", "Docker"],
        "preferred_skills": ["Kubernetes"],
        "experience_years": 5.0,
        "education_level": "Bachelor's",
        "location": "Seattle, WA",
        "employment_type": "Full-time",
        "contact_email": "cloudarch@amazonianlabs.io"
    }
    j2 = {
        "title": "Junior Python Web Developer",
        "company": "StartupX",
        "description": "Build web apps using FastAPI and SQLite.",
        "required_skills": ["Python", "FastAPI"],
        "preferred_skills": ["HTML", "CSS"],
        "experience_years": 1.0,
        "education_level": "Associate",
        "location": "Austin, TX",
        "employment_type": "Full-time",
        "contact_email": "webdev@startupx.com"
    }
    client.post("/api/jobs", json=j1, headers=admin_auth_headers)
    client.post("/api/jobs", json=j2, headers=admin_auth_headers)

    # Search keyword
    res_kw = client.get("/api/jobs/search?q=Amazonian")
    assert res_kw.status_code == 200
    assert res_kw.json()["total"] >= 1
    assert any(j["company"] == "Amazonian Labs" for j in res_kw.json()["jobs"])

    # Search skill
    res_sk = client.get("/api/jobs/search?skill=FastAPI")
    assert res_sk.status_code == 200
    assert any("FastAPI" in j["description"] for j in res_sk.json()["jobs"])

    # Search experience
    res_exp = client.get("/api/jobs/search?min_exp=4")
    assert res_exp.status_code == 200
    for j in res_exp.json()["jobs"]:
        assert j["experience_years"] >= 4.0

    # Search with empty query or sanitized strings
    res_empty = client.get("/api/jobs/search?q=&skill=&employment_type=&limit=50")
    assert res_empty.status_code == 200

    res_undef = client.get("/api/jobs/search?q=undefined&skill=null")
    assert res_undef.status_code == 200

