import pytest
from app.services.matching_service import MatchingService
from app.services.ai_service import LocalNLPProvider
from app.agents.job_matcher import JobMatchingAgent

def test_skill_overlap_calculation():
    cand_skills = ["Python", "FastAPI", "Docker", "Git"]
    req_skills = ["Python", "FastAPI", "PostgreSQL", "Docker"]
    pref_skills = ["Git", "Kubernetes"]

    score, matching, missing = MatchingService.compute_skill_overlap(cand_skills, req_skills, pref_skills)
    assert "Python" in matching
    assert "FastAPI" in matching
    assert "Docker" in matching
    assert "PostgreSQL" in missing
    assert 50.0 <= score <= 90.0

def test_experience_scoring():
    exp_items = [
        {"title": "Backend Developer", "duration": "2 years", "company": "Co A"},
        {"title": "Software Engineer", "duration": "1 year", "company": "Co B"}
    ]
    # Required 3.0 yrs -> should be ~100%
    score, summary = MatchingService.compute_experience_score(exp_items, 3.0)
    assert score == 100.0

    # Required 6.0 yrs -> should be around 50%
    score2, summary2 = MatchingService.compute_experience_score(exp_items, 6.0)
    assert 40.0 <= score2 <= 60.0

def test_education_scoring():
    edu_items = [{"degree": "Bachelor of Science in Computer Science"}]
    score_bachelor = MatchingService.compute_education_score(edu_items, "Bachelor's")
    assert score_bachelor == 100.0

    score_master_req = MatchingService.compute_education_score(edu_items, "Master's")
    assert score_master_req < 100.0
    assert score_master_req >= 80.0

@pytest.mark.asyncio
async def test_full_composite_match_evaluation():
    ai = LocalNLPProvider()
    profile = {
        "candidate_name": "Sarah Connor",
        "professional_summary": "Full Stack developer experienced in Python, FastAPI, and relational databases.",
        "technical_skills": ["Python", "FastAPI", "SQLite", "JavaScript", "HTML"],
        "education": [{"degree": "B.S. Software Engineering"}],
        "experience": [{"title": "Software Developer", "duration": "2 years", "company": "Tech"}]
    }

    job = {
        "title": "Python FastAPI Developer",
        "company": "SkyNet Solutions",
        "description": "Develop high-throughput REST APIs in FastAPI using Python and SQLite database.",
        "required_skills": ["Python", "FastAPI", "SQLite"],
        "preferred_skills": ["JavaScript"],
        "experience_years": 2.0,
        "education_level": "Bachelor's"
    }

    result = await MatchingService.evaluate_match(profile, job, ai)
    
    # Check bounds
    assert 0.0 <= result["match_score"] <= 100.0
    assert 0.0 <= result["skill_score"] <= 100.0
    assert 0.0 <= result["experience_score"] <= 100.0
    assert 0.0 <= result["education_score"] <= 100.0
    assert 0.0 <= result["semantic_score"] <= 100.0

    # Check exact formula balance
    expected = round(
        result["skill_score"] * 0.40
        + result["experience_score"] * 0.25
        + result["education_score"] * 0.15
        + result["semantic_score"] * 0.20,
        1
    )
    assert abs(result["match_score"] - expected) <= 0.1

    # Check Agent explanation
    agent = JobMatchingAgent(ai_provider=ai)
    match_with_agent = await agent.match_resume_to_job(profile, job)
    assert "match_explanation" in match_with_agent
    assert len(match_with_agent["match_explanation"]) > 20

def test_java_vs_javascript_safety():
    """Verify that Java and JavaScript are strictly separated and never falsely matched as substrings."""
    cand_js_only = ["JavaScript", "TypeScript"]
    score, matching, missing = MatchingService.compute_skill_overlap(
        candidate_skills=cand_js_only,
        required_skills=["Java"],
        preferred_skills=[]
    )
    assert score == 0.0
    assert "Java" in missing
    assert "Java" not in matching

    # Candidate with Java only should not match JavaScript
    cand_java_only = ["Java", "Spring Boot"]
    score2, matching2, missing2 = MatchingService.compute_skill_overlap(
        candidate_skills=cand_java_only,
        required_skills=["JavaScript"],
        preferred_skills=[]
    )
    assert score2 == 0.0
    assert "JavaScript" in missing2
    assert "JavaScript" not in matching2

    # Single character skill "C" should not match "CSS" or "Docker"
    cand_c_only = ["C"]
    score3, matching3, missing3 = MatchingService.compute_skill_overlap(
        candidate_skills=cand_c_only,
        required_skills=["CSS", "Docker"],
        preferred_skills=[]
    )
    assert score3 == 0.0
    assert len(matching3) == 0

def test_edge_case_perfect_candidate():
    """Edge Case 1: Perfect candidate with full skill, experience, and degree alignment."""
    cand_skills = ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS"]
    score, matching, missing = MatchingService.compute_skill_overlap(
        candidate_skills=cand_skills,
        required_skills=["Python", "FastAPI", "PostgreSQL"],
        preferred_skills=["Docker", "AWS"]
    )
    assert score == 100.0
    assert len(missing) == 0

def test_edge_case_no_matching_skills():
    """Edge Case 2: Candidate with skills having zero overlap with job requirements."""
    cand_skills = ["Ruby", "Ruby on Rails", "Erlang"]
    score, matching, missing = MatchingService.compute_skill_overlap(
        candidate_skills=cand_skills,
        required_skills=["Python", "FastAPI"],
        preferred_skills=["Docker"]
    )
    assert score == 0.0
    assert set(missing) == {"Python", "FastAPI"}
    assert len(matching) == 0

def test_edge_case_partial_skill_overlap():
    """Edge Case 3: Candidate matches exactly half of required skills."""
    cand_skills = ["Python", "Git"]
    score, matching, missing = MatchingService.compute_skill_overlap(
        candidate_skills=cand_skills,
        required_skills=["Python", "Go"],
        preferred_skills=[]
    )
    assert score == 50.0
    assert "Python" in matching
    assert "Go" in missing

def test_edge_case_experience_variations():
    """Edge Cases 4 & 5: More experience than required and less experience than required."""
    exp_senior = [{"title": "Senior Engineer", "duration": "10 years", "company": "Global Tech"}]
    # Required 3 yrs, candidate has 10 yrs -> capped at 100.0
    score_over, _ = MatchingService.compute_experience_score(exp_senior, 3.0)
    assert score_over == 100.0

    exp_junior = [{"title": "Junior Developer", "duration": "1 year", "company": "StartUp"}]
    # Required 4 yrs, candidate has 1 yr -> exactly 25.0 (no artificial floor)
    score_under, _ = MatchingService.compute_experience_score(exp_junior, 4.0)
    assert score_under == 25.0

    # 0 experience items -> exactly 0.0
    score_zero, _ = MatchingService.compute_experience_score([], 3.0)
    assert score_zero == 0.0

def test_edge_case_missing_education():
    """Edge Case 6: Candidate has no education listed."""
    score_empty = MatchingService.compute_education_score([], "Bachelor's")
    assert score_empty == 0.0

    # If job has no requirement ('any'), empty education is acceptable (100.0)
    score_any = MatchingService.compute_education_score([], "any")
    assert score_any == 100.0

def test_edge_case_related_degree_names():
    """Edge Case 7: Different but related degree acronyms and terminology."""
    deg_bs = [{"degree": "B.S. in Computer Science"}]
    deg_bsc = [{"degree": "B.Sc. Information Technology"}]
    deg_btech = [{"degree": "B.Tech Computer Engineering"}]
    deg_ms = [{"degree": "Master of Science in Software Systems"}]

    assert MatchingService.compute_education_score(deg_bs, "Bachelor's") == 100.0
    assert MatchingService.compute_education_score(deg_bsc, "Bachelor's") == 100.0
    assert MatchingService.compute_education_score(deg_btech, "Bachelor's") == 100.0
    assert MatchingService.compute_education_score(deg_ms, "Bachelor's") == 100.0
    assert MatchingService.compute_education_score(deg_ms, "Master's") == 100.0

def test_edge_case_empty_job_requirements():
    """Edge Case 8: Job has no mandatory skills, experience, or degree requirements."""
    score, matching, missing = MatchingService.compute_skill_overlap(
        candidate_skills=["Python"],
        required_skills=[],
        preferred_skills=[]
    )
    assert score == 100.0

    exp_score, _ = MatchingService.compute_experience_score([], 0.0)
    assert exp_score == 100.0

    edu_score = MatchingService.compute_education_score([], "any")
    assert edu_score == 100.0

@pytest.mark.asyncio
async def test_edge_case_empty_resume_profile():
    """Edge Case 9 & 10: Completely empty resume profile vs standard job -> strictly 0 - 100 bounded."""
    ai = LocalNLPProvider()
    empty_profile = {
        "candidate_name": "Anonymous",
        "professional_summary": "",
        "technical_skills": [],
        "education": [],
        "experience": []
    }
    job = {
        "title": "Backend Engineer",
        "company": "Scale Corp",
        "description": "Develop scalable APIs in Python.",
        "required_skills": ["Python", "FastAPI"],
        "preferred_skills": [],
        "experience_years": 3.0,
        "education_level": "Bachelor's"
    }

    result = await MatchingService.evaluate_match(empty_profile, job, ai)
    assert result["skill_score"] == 0.0
    assert result["experience_score"] == 0.0
    assert result["education_score"] == 0.0
    assert result["semantic_score"] == 0.0
    assert result["match_score"] == 0.0

    # Ensure all components strictly between 0 and 100
    for key in ["match_score", "skill_score", "experience_score", "education_score", "semantic_score"]:
        assert 0.0 <= result[key] <= 100.0

