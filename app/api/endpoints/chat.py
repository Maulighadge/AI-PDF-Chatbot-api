import json
from fastapi import APIRouter, HTTPException, Depends, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from sse_starlette.sse import EventSourceResponse
from app.db.session import get_db
from app.services.chat_service import chat_service
from app.services.llm_service import llm_service

router = APIRouter(tags=["Chats & QA"])

class CreateChatRequest(BaseModel):
    title: Optional[str] = "New Chat"

class QuestionRequest(BaseModel):
    question: str
    document_id: Optional[str] = None
    stream: Optional[bool] = False

# Blueprint Section 9: Session Management
@router.post("/chats")
def create_chat_session(request: CreateChatRequest, db: Session = Depends(get_db)):
    session = chat_service.create_session(title=request.title or "New Chat", db=db)
    return {
        "success": True,
        "session": {
            "id": session.id,
            "title": session.title,
            "created_at": session.created_at.isoformat()
        }
    }

@router.get("/chats")
def list_chat_sessions(db: Session = Depends(get_db)):
    return {
        "success": True,
        "sessions": chat_service.list_sessions(db)
    }

@router.delete("/chats/{session_id}")
def delete_chat_session(session_id: str, db: Session = Depends(get_db)):
    deleted = chat_service.delete_session(session_id, db)
    if not deleted:
        raise HTTPException(status_code=404, detail="Chat session not found.")
    return {"success": True, "message": "Session deleted."}

@router.get("/chats/{session_id}/messages")
def get_chat_messages(session_id: str, db: Session = Depends(get_db)):
    return {
        "success": True,
        "messages": chat_service.get_messages(session_id, db)
    }

@router.post("/chats/{session_id}/messages")
async def send_chat_message(
    session_id: str,
    request: QuestionRequest,
    db: Session = Depends(get_db),
    x_gemini_api_key: Optional[str] = Header(None, alias="X-Gemini-Api-Key")
):
    """
    Blueprint Section 9, 10B & 11: Ask question, retrieve evidence, ground prompt, stream or return answer.
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    # 1. Retrieve evidence chunks
    evidence = chat_service.retrieve_evidence(
        question=request.question,
        document_id=request.document_id,
        top_k=5,
        api_key=x_gemini_api_key
    )

    # 2. Extract citations
    sources = [
        {
            "filename": c.get("filename", "Document"),
            "page_number": c.get("page_number", 1),
            "excerpt": c.get("content", "")[:200] + ("..." if len(c.get("content", "")) > 200 else "")
        }
        for c in evidence
    ]

    # Save User message in DB
    chat_service.save_message(
        session_id=session_id,
        role="user",
        content=request.question,
        sources=None,
        db=db
    )

    # If streaming is requested (SSE)
    if request.stream:
        async def event_generator():
            yield {
                "event": "sources",
                "data": json.dumps(sources)
            }
            accumulated_answer = ""
            async for token in llm_service.generate_rag_answer_stream(
                question=request.question,
                evidence_chunks=evidence,
                api_key=x_gemini_api_key
            ):
                accumulated_answer += token
                yield {
                    "event": "token",
                    "data": token
                }

            # Save completed Assistant message
            chat_service.save_message(
                session_id=session_id,
                role="assistant",
                content=accumulated_answer,
                sources=sources,
                db=db
            )
            yield {
                "event": "done",
                "data": "[DONE]"
            }

        return EventSourceResponse(event_generator())

    # Standard non-streaming response
    accumulated_answer = ""
    async for token in llm_service.generate_rag_answer_stream(
        question=request.question,
        evidence_chunks=evidence,
        api_key=x_gemini_api_key
    ):
        accumulated_answer += token

    saved_msg = chat_service.save_message(
        session_id=session_id,
        role="assistant",
        content=accumulated_answer,
        sources=sources,
        db=db
    )

    return {
        "success": True,
        "message_id": saved_msg.id,
        "answer": accumulated_answer,
        "sources": sources
    }

# Backward compatibility route for simple /chat/query
class SimpleQueryRequest(BaseModel):
    doc_id: Optional[str] = None
    question: str

@router.post("/chat/query")
async def simple_query(
    request: SimpleQueryRequest,
    x_gemini_api_key: Optional[str] = Header(None, alias="X-Gemini-Api-Key")
):
    evidence = chat_service.retrieve_evidence(
        question=request.question,
        document_id=request.doc_id,
        top_k=5,
        api_key=x_gemini_api_key
    )
    sources = [
        {
            "page_number": c.get("page_number", 1),
            "filename": c.get("filename", ""),
            "excerpt": c.get("content", "")[:200]
        }
        for c in evidence
    ]
    accumulated = ""
    async for token in llm_service.generate_rag_answer_stream(
        question=request.question,
        evidence_chunks=evidence,
        api_key=x_gemini_api_key
    ):
        accumulated += token

    return {
        "answer": accumulated,
        "sources": sources,
        "doc_id": request.doc_id
    }
