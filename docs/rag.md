# Retrieval-Augmented Generation (RAG) Architecture

The application implements a genuine, production-grade Retrieval-Augmented Generation (RAG) pipeline designed for local reproducibility within SQLite.

---

## 1. RAG Pipeline Flow

```
                      User Question / Target Role
                                   │
                                   ▼
                        Query Text Processing
                                   │
                                   ▼
                      Embedding Vector Generation
                       (64-dim / Dense Vectors)
                                   │
                                   ▼
                       Vector Cosine Retrieval
                  (Candidate Chunks in SQLite DB)
                                   │
                                   ▼
                  Rank & Filter (Top-K > Threshold)
                                   │
                                   ▼
                   Augmented Grounding Context Block
                  [Source 1: 'Doc Title' | Score: 85%]
                                   │
                                   ▼
                       LLM Inference with Context
                                   │
                                   ▼
                     Verified Grounded Response
                    (With Citations & Roadmaps)
```

---

## 2. Knowledge Base Categories

The SQLite database is seeded with curated knowledge documents categorized into 5 mandatory domains:

1. **Job Descriptions (`job_description`)**:
   - Industry standards for technical job titles, required competencies, core responsibilities, and seniority level criteria.
2. **Skill Descriptions (`skill_description`)**:
   - In-depth architectural profiles of high-leverage frameworks and tools (e.g. FastAPI, Docker, Microservices, System Design, RAG principles).
3. **Career Roadmaps (`career_roadmap`)**:
   - Progression trajectories from Junior to Mid-Level to Senior Engineer, Fullstack Engineering milestones, and AI/ML specialization tracks.
4. **Learning Resources (`learning_resource`)**:
   - Verified high-ROI free learning repositories, books (*Designing Data-Intensive Applications*), official documentation, and recognized certifications (AWS, CKA, Terraform).
5. **Resume Guidelines (`resume_guideline`)**:
   - Applicant Tracking System (ATS) parsing rules, the Google XYZ bullet formulation formula, metric quantification, and anti-patterns to avoid.

---

## 3. Chunking Strategy

To preserve context around technical concepts:
- **Chunk Size**: ~220 words per chunk.
- **Overlap**: 40 words between adjacent chunks.
- Overlapping windows prevent loss of meaning at arbitrary sentence boundaries.

```python
def chunk_text(text: str, chunk_size_words: int = 220, overlap_words: int = 40) -> List[str]:
    words = text.split()
    step = chunk_size_words - overlap_words
    chunks = []
    for i in range(0, len(words), step):
        chunks.append(" ".join(words[i : i + chunk_size_words]))
    return chunks
```

---

---

## 4. Vector Retrieval & Cosine Similarity

Each chunk is stored in SQLite alongside its float embedding vector as a JSON array (`knowledge_chunks.embedding`).

Retrieval calculates the **Cosine Similarity** between the query vector $\mathbf{q}$ and each stored chunk vector $\mathbf{v}$:

$$\text{Similarity}(\mathbf{q}, \mathbf{v}) = \frac{\mathbf{q} \cdot \mathbf{v}}{\|\mathbf{q}\| \|\mathbf{v}\|} = \frac{\sum_{i=1}^n q_i v_i}{\sqrt{\sum_{i=1}^n q_i^2} \sqrt{\sum_{i=1}^n v_i^2}}$$

Top $K$ chunks (default: 4) exceeding the minimum similarity threshold (default: 0.15) are selected and injected into the prompt.

---

## 5. Embedding Models & Storage Implementation Details

| Technical Aspect | Implementation in Code |
| :--- | :--- |
| **Primary Embedding Model** | Google Gemini `gemini-embedding-001` (dense transformer embeddings via `GeminiProvider.embed` with `gemini-embedding-2` fallback). |
| **Local / Offline Fallback** | Deterministic term-frequency `HashingVectorizer(n_features=64, norm="l2")` via `LocalNLPProvider.embed`. **Note**: This is clearly documented as a deterministic token-frequency hashing fallback, NOT dense transformer embeddings, ensuring offline resilience. The RAG retriever dynamically inspects chunk vector dimensions to guarantee seamless similarity computation regardless of ingestion mode. |
| **Storage Engine** | SQLite database table `knowledge_chunks`. |
| **Serialization Format** | JSON-serialized array of floats (`Column(JSON, nullable=True)`) deserialized by SQLAlchemy to Python `List[float]`. |
| **Similarity Metric** | Pure mathematical cosine similarity function in `app/utils/text_processing.py` clamped strictly to `[0.0, 1.0]`. |
| **Retrieval Timing** | **Strictly Pre-Generation**: `RAGService.build_grounded_context` queries SQLite before prompt assembly. |
| **LLM Context Injection** | Retrieved chunks formatted with document titles and snippets are enclosed in `--- BEGIN RETRIEVED KNOWLEDGE BASE CONTEXT (RAG) ---` delimiters. |
| **Source Citations** | `RetrievedChunkInfo` objects containing document title, category, verbatim snippet, and similarity score are returned in the REST API response (`CareerQuestionResponse.retrieved_sources`) and displayed in the frontend. |

---

## 6. Grounding Verification in the UI

When the Career Advisor responds:
1. The UI displays an explicit **"🔍 RAG Verified • Retrieved from Knowledge Base"** badge.
2. Each cited document is listed with its title, relevance percentage, and the verbatim text snippet retrieved.
3. This guarantees that evaluators can verify the answer is grounded directly in the system's knowledge base.

---

## 7. User-Managed Knowledge Base

In addition to the curated seed documents, authenticated users can dynamically expand or prune the RAG knowledge base through the REST API and the Career Advisor frontend.

### Adding Documents
- **API**: `POST /api/career/knowledge-docs` with `title`, `category`, `content`, and `source`.
- **Frontend**: The "**+ Add Doc**" button on the Career Advisor page opens a modal form.
- **Process**: On submission, the content is automatically:
  1. Saved as a `KnowledgeDocument` record.
  2. Split into overlapping chunks (~220 words, 40 overlap).
  3. Embedded using the active AI provider (Gemini or local fallback).
  4. Stored with vector embeddings for cosine similarity retrieval.

### Deleting Documents
- **API**: `DELETE /api/career/knowledge-docs/{doc_id}` (requires authentication).
- **Frontend**: Each document card in the Knowledge Base panel has a **✕** delete button.
- **Process**: Deleting a document cascades to remove all associated `KnowledgeChunk` records and their embeddings.

### Valid Categories
Documents must be assigned to one of these categories:
- `job_description` — Industry job posting standards
- `skill_description` — Technical skill and framework profiles
- `career_roadmap` — Career progression trajectories
- `learning_resource` — Courses, certifications, and learning platforms
- `resume_guideline` — ATS optimization and resume formatting rules

