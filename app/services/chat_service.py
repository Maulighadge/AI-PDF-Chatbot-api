import json
from typing import List, Dict, Any, Optional, AsyncGenerator
from sqlalchemy.orm import Session
from app.db.models import ChatSession, ChatMessage
from app.services.vector_store import vector_store
from app.services.llm_service import llm_service

class ChatService:
    def create_session(self, title: str, db: Session) -> ChatSession:
        session = ChatSession(title=title)
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    def list_sessions(self, db: Session) -> List[Dict[str, Any]]:
        sessions = db.query(ChatSession).order_by(ChatSession.updated_at.desc()).all()
        return [
            {
                "id": s.id,
                "title": s.title,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "updated_at": s.updated_at.isoformat() if s.updated_at else None
            }
            for s in sessions
        ]

    def get_messages(self, session_id: str, db: Session) -> List[Dict[str, Any]]:
        messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc()).all()
        return [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "sources": m.sources_json or [],
                "created_at": m.created_at.isoformat() if m.created_at else None
            }
            for m in messages
        ]

    def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        sources: Optional[List[Dict[str, Any]]],
        db: Session
    ) -> ChatMessage:
        msg = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            sources_json=sources
        )
        db.add(msg)
        db.commit()
        db.refresh(msg)
        return msg

    def delete_session(self, session_id: str, db: Session) -> bool:
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            return False
        db.delete(session)
        db.commit()
        return True

    def retrieve_evidence(
        self,
        question: str,
        document_id: Optional[str] = None,
        top_k: int = 5,
        api_key: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Embeds the question and retrieves top relevant chunks.
        """
        query_embeddings = llm_service.embed_texts([question], api_key=api_key)
        if not query_embeddings:
            return []
        
        return vector_store.search(
            query_embedding=query_embeddings[0],
            document_id=document_id,
            top_k=top_k
        )

chat_service = ChatService()
