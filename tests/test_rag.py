import pytest
from app.utils.text_processing import chunk_text, cosine_similarity
from app.services.ai_service import LocalNLPProvider
from app.services.rag_service import RAGService
from app.agents.career_advisor import CareerAdvisorAgent

def test_chunking():
    text = "Word " * 500  # 500 words
    chunks = chunk_text(text, chunk_size_words=200, overlap_words=40)
    assert len(chunks) >= 3
    # Check that chunks are non-empty
    for c in chunks:
        assert len(c.split()) > 50

@pytest.mark.asyncio
async def test_vector_embeddings_and_cosine_similarity():
    ai = LocalNLPProvider()
    texts = [
        "FastAPI is a modern web framework for Python.",
        "Python web development with FastAPI and REST APIs.",
        "Gardening tips for growing organic tomatoes in spring."
    ]
    vectors = await ai.embed(texts)
    assert len(vectors) == 3
    assert len(vectors[0]) == 64

    # The first two technical texts should have much higher similarity than the gardening text
    sim_tech = cosine_similarity(vectors[0], vectors[1])
    sim_unrelated = cosine_similarity(vectors[0], vectors[2])
    assert sim_tech > sim_unrelated

@pytest.mark.asyncio
async def test_rag_ingest_and_retrieve(db_session):
    rag = RAGService(ai_provider=LocalNLPProvider())
    
    # Ingest document
    doc = await rag.ingest_document(
        db=db_session,
        title="Docker Containerization Guide",
        category="skill_description",
        content="Docker packages applications into containers. It isolates dependencies, uses Dockerfiles, and runs reliably on Linux servers."
    )
    assert doc.id is not None

    # Retrieve relevant chunks
    results = await rag.retrieve(db_session, query="How does Docker run containerized applications?")
    assert len(results) > 0
    top_chunk, score = results[0]
    assert "Docker" in top_chunk.content
    assert score > 0.1

@pytest.mark.asyncio
async def test_career_advisor_rag_grounded_answer(db_session):
    rag = RAGService(ai_provider=LocalNLPProvider())
    await rag.ingest_document(
        db=db_session,
        title="Resume ATS Optimization",
        category="resume_guideline",
        content="Resumes should use the Google XYZ formula and single-column formatting for ATS systems."
    )

    agent = CareerAdvisorAgent(ai_provider=LocalNLPProvider(), rag_service=rag)
    response = await agent.answer_career_question(
        db=db_session,
        question="How can I improve my resume for ATS parsers?"
    )

    assert response.grounded_by_rag is True
    assert len(response.retrieved_sources) > 0
    assert any("ATS" in src.document_title for src in response.retrieved_sources)
    assert len(response.career_roadmap) == 3
    assert len(response.suggested_certifications) > 0

@pytest.mark.asyncio
async def test_rag_category_filtering(db_session):
    """Verify that RAG can selectively query within a specific knowledge category."""
    rag = RAGService(ai_provider=LocalNLPProvider())
    await rag.ingest_document(
        db=db_session,
        title="Python Backend Roadmap",
        category="career_roadmap",
        content="Roadmap for backend developers mastering Python, asynchronous programming, and system design."
    )
    await rag.ingest_document(
        db=db_session,
        title="Python Software Engineer Job",
        category="job_description",
        content="Job posting for Python developers working with cloud databases."
    )

    # Filter only career_roadmap
    results = await rag.retrieve(db_session, query="roadmap for python", category_filter="career_roadmap")
    assert len(results) > 0
    for chunk, _ in results:
        assert chunk.document.category == "career_roadmap"

@pytest.mark.asyncio
async def test_build_grounded_context_citations(db_session):
    """Verify context text format and citation structure for UI display."""
    rag = RAGService(ai_provider=LocalNLPProvider())
    context_str, citations = await rag.build_grounded_context(db_session, "Python roadmap", top_k=2)
    assert isinstance(context_str, str)
    assert isinstance(citations, list)
    if citations:
        assert hasattr(citations[0], "document_title")
        assert hasattr(citations[0], "category")
        assert hasattr(citations[0], "similarity_score")

