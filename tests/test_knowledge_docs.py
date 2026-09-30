"""Tests for Knowledge Document CRUD (RAG Knowledge Base Management)."""

def test_create_knowledge_doc(client, admin_auth_headers):
    """Test creating a new knowledge document via the API."""
    payload = {
        "title": "Microservices Architecture Patterns",
        "category": "skill_description",
        "content": "Microservices architecture decomposes monolithic applications into small, independently deployable services. Key patterns include API Gateway, Circuit Breaker, Saga Pattern for distributed transactions, and Event Sourcing. Each service owns its database and communicates via REST or message queues.",
        "source": "Engineering Handbook"
    }
    res = client.post("/api/career/knowledge-docs", json=payload, headers=admin_auth_headers)
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == "Microservices Architecture Patterns"
    assert data["category"] == "skill_description"
    assert data["source"] == "Engineering Handbook"
    assert data["chunks_count"] >= 1
    assert data["id"] is not None


def test_create_knowledge_doc_invalid_category(client, admin_auth_headers):
    """Test that creating a document with an invalid category returns 422."""
    payload = {
        "title": "Invalid Category Doc",
        "category": "invalid_category",
        "content": "This document has an invalid category that should be rejected by the API validation."
    }
    res = client.post("/api/career/knowledge-docs", json=payload, headers=admin_auth_headers)
    assert res.status_code == 422


def test_create_knowledge_doc_requires_auth(client):
    """Test that creating a document without authentication returns 401."""
    payload = {
        "title": "Unauthorized Doc",
        "category": "skill_description",
        "content": "This should fail because no authentication token is provided in the request headers."
    }
    res = client.post("/api/career/knowledge-docs", json=payload)
    assert res.status_code == 401


def test_get_knowledge_doc(client, admin_auth_headers):
    """Test retrieving a specific knowledge document by ID."""
    # Create first
    payload = {
        "title": "FastAPI Security Best Practices",
        "category": "skill_description",
        "content": "FastAPI supports OAuth2 with JWT tokens, dependency injection for security, CORS middleware configuration, and rate limiting. Always hash passwords with bcrypt and validate input with Pydantic schemas.",
        "source": "Security Guidelines"
    }
    create_res = client.post("/api/career/knowledge-docs", json=payload, headers=admin_auth_headers)
    assert create_res.status_code == 201
    doc_id = create_res.json()["id"]

    # Get by ID
    get_res = client.get(f"/api/career/knowledge-docs/{doc_id}")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["title"] == "FastAPI Security Best Practices"
    assert "OAuth2" in data["content"]


def test_get_knowledge_doc_not_found(client):
    """Test that requesting a non-existent document returns 404."""
    res = client.get("/api/career/knowledge-docs/99999")
    assert res.status_code == 404


def test_delete_knowledge_doc(client, admin_auth_headers):
    """Test deleting a knowledge document removes it and its chunks."""
    # Create
    payload = {
        "title": "Temporary Test Document for Deletion",
        "category": "learning_resource",
        "content": "This temporary document is created solely to verify the delete endpoint works correctly and cleans up chunks.",
        "source": "Test Suite"
    }
    create_res = client.post("/api/career/knowledge-docs", json=payload, headers=admin_auth_headers)
    assert create_res.status_code == 201
    doc_id = create_res.json()["id"]

    # Delete
    del_res = client.delete(f"/api/career/knowledge-docs/{doc_id}", headers=admin_auth_headers)
    assert del_res.status_code == 200
    assert "successfully deleted" in del_res.json()["message"]

    # Verify gone
    get_res = client.get(f"/api/career/knowledge-docs/{doc_id}")
    assert get_res.status_code == 404


def test_delete_knowledge_doc_requires_auth(client):
    """Test that deleting a document without authentication returns 401."""
    res = client.delete("/api/career/knowledge-docs/1")
    assert res.status_code == 401


def test_list_knowledge_docs(client, admin_auth_headers):
    """Test listing all knowledge base documents."""
    # Create a doc first
    payload = {
        "title": "Resume Formatting Guide for 2025",
        "category": "resume_guideline",
        "content": "Modern resumes should use clean single-column layouts, standard section headings, and quantified achievements. Export as PDF for ATS compatibility.",
        "source": "HR Standards"
    }
    client.post("/api/career/knowledge-docs", json=payload, headers=admin_auth_headers)

    # List
    res = client.get("/api/career/knowledge-docs")
    assert res.status_code == 200
    docs = res.json()
    assert isinstance(docs, list)
    assert len(docs) >= 1
    assert "title" in docs[0]
    assert "category" in docs[0]
    assert "chunks_count" in docs[0]
