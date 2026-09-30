from typing import List, Tuple, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.db.models import KnowledgeDocument, KnowledgeChunk
from app.services.ai_service import get_ai_provider, AIProvider
from app.utils.text_processing import chunk_text, cosine_similarity
from app.schemas.career import RetrievedChunkInfo
from app.core.config import settings
from app.core.logging import logger

class RAGService:
    """
    Production Retrieval-Augmented Generation (RAG) Service.
    - Chunks knowledge documents
    - Computes dense vector embeddings
    - Stores and retrieves chunks using vector cosine similarity
    - Grounds LLM prompts in verified domain knowledge
    """

    def __init__(self, ai_provider: Optional[AIProvider] = None):
        self.ai = ai_provider or get_ai_provider()

    async def ingest_document(
        self,
        db: Session,
        title: str,
        category: str,
        content: str,
        source: str = "curated"
    ) -> KnowledgeDocument:
        """
        Ingest a document into the RAG knowledge base:
        1. Save KnowledgeDocument record
        2. Split content into overlapping chunks
        3. Compute embedding vectors for all chunks
        4. Store chunks with embeddings
        """
        doc = KnowledgeDocument(
            title=title,
            category=category,
            source=source,
            content=content
        )
        db.add(doc)
        db.flush()

        chunks = chunk_text(content, chunk_size_words=220, overlap_words=40)
        if not chunks:
            chunks = [content]

        logger.info(f"Ingesting doc '{title}' ({category}): generating embeddings for {len(chunks)} chunks")
        embeddings = await self.ai.embed(chunks)

        for idx, (chunk_str, emb) in enumerate(zip(chunks, embeddings)):
            chunk_record = KnowledgeChunk(
                document_id=doc.id,
                chunk_index=idx,
                content=chunk_str,
                embedding=emb,
                token_count=len(chunk_str.split())
            )
            db.add(chunk_record)

        db.commit()
        db.refresh(doc)
        return doc

    async def retrieve(
        self,
        db: Session,
        query: str,
        top_k: Optional[int] = None,
        category_filter: Optional[str] = None
    ) -> List[Tuple[KnowledgeChunk, float]]:
        """
        Semantic Vector Retrieval:
        1. Embed the user query
        2. Fetch candidate chunks from SQLite
        3. Compute cosine similarity against all chunks
        4. Return top_k ranked chunks above threshold
        """
        k = top_k or settings.RAG_TOP_K
        query_embeddings = await self.ai.embed([query])
        if not query_embeddings:
            return []
        q_vec = query_embeddings[0]

        query_builder = db.query(KnowledgeChunk).join(KnowledgeDocument)
        if category_filter:
            query_builder = query_builder.filter(KnowledgeDocument.category == category_filter)

        all_chunks = query_builder.all()
        scored_chunks: List[Tuple[KnowledgeChunk, float]] = []
        local_q_vec = None

        for chunk in all_chunks:
            if not chunk.embedding:
                continue
            
            # Check for embedding dimension compatibility
            if len(chunk.embedding) == len(q_vec):
                sim = cosine_similarity(q_vec, chunk.embedding)
            else:
                # Fallback to deterministic local query vector if chunk was embedded with Local NLP
                if local_q_vec is None:
                    from app.services.ai_service import LocalNLPProvider
                    local_embs = await LocalNLPProvider().embed([query])
                    local_q_vec = local_embs[0] if local_embs else []
                if len(chunk.embedding) == len(local_q_vec):
                    sim = cosine_similarity(local_q_vec, chunk.embedding)
                else:
                    sim = 0.0

            if sim >= settings.RAG_SIMILARITY_THRESHOLD:
                scored_chunks.append((chunk, sim))

        # Sort descending by similarity score
        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        return scored_chunks[:k]

    async def build_grounded_context(
        self,
        db: Session,
        query: str,
        top_k: Optional[int] = None,
        category_filter: Optional[str] = None
    ) -> Tuple[str, List[RetrievedChunkInfo]]:
        """
        Retrieves top relevant chunks and formats them into an explicit grounding context block.
        Also returns structured metadata for UI citation display.
        """
        results = await self.retrieve(db, query, top_k=top_k, category_filter=category_filter)
        if not results:
            return "", []

        context_snippets = []
        citations: List[RetrievedChunkInfo] = []

        for idx, (chunk, score) in enumerate(results, 1):
            doc_title = chunk.document.title if chunk.document else "Knowledge Document"
            doc_category = chunk.document.category if chunk.document else "General"
            
            snippet_formatted = (
                f"[Source {idx}: '{doc_title}' | Category: {doc_category} | Match: {score*100:.1f}%]\n"
                f"{chunk.content}\n"
            )
            context_snippets.append(snippet_formatted)

            citations.append(RetrievedChunkInfo(
                document_title=doc_title,
                category=doc_category,
                snippet=chunk.content[:280] + ("..." if len(chunk.content) > 280 else ""),
                similarity_score=round(score * 100, 1)
            ))

        full_context = "\n---\n".join(context_snippets)
        return full_context, citations
