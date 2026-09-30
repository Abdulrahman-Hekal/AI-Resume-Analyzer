from typing import Optional, List
from sqlalchemy.orm import Session
from app.db.models import KnowledgeDocument, KnowledgeChunk

class KnowledgeRepository:
    @staticmethod
    def get_document_by_id(db: Session, doc_id: int) -> Optional[KnowledgeDocument]:
        return db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()

    @staticmethod
    def get_all_documents(db: Session, category: Optional[str] = None) -> List[KnowledgeDocument]:
        query = db.query(KnowledgeDocument)
        if category:
            query = query.filter(KnowledgeDocument.category == category)
        return query.order_by(KnowledgeDocument.created_at.desc()).all()

    @staticmethod
    def get_chunks_by_document(db: Session, doc_id: int) -> List[KnowledgeChunk]:
        return db.query(KnowledgeChunk).filter(KnowledgeChunk.document_id == doc_id).order_by(KnowledgeChunk.chunk_index.asc()).all()

    @staticmethod
    def count_chunks(db: Session) -> int:
        return db.query(KnowledgeChunk).count()
