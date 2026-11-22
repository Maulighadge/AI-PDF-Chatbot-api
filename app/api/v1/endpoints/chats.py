import json
from fastapi import APIRouter, HTTPException, Depends, Header
from sqlalchemy.orm import Session
from typing import Optional, Union
from sse_starlette.sse import EventSourceResponse

from app.db.session import get_db
from app.services.chat_service import chat_service
from app.services.llm_service import llm_service
from app.schemas.chat import (
    CreateChatRequest,
    ChatSessionResponse,
    ChatSessionListResponse,
    ChatMessagesResponse,
    QuestionRequest,
    ChatAnswerResponse,
    SimpleQueryRequest,
    SimpleQueryResponse,
    SourceCitation
)
from app.schemas.common import BaseResponse

router = APIRouter(tags=["Chats & QA"])

@router.post(
    "/chats",
    response_model=ChatSessionResponse,
    status_code=200,
    summary="Create a new chat conversation session"
)
def create_chat_session(request: CreateChatRequest, db: Session = Depends(get_db)):
    """
    Initialize a new chat conversation thread.
    """
    session = chat_service.create_session(title=request.title or "New Chat", db=db)
    return {
        "success": True,
        "session": {
            "id": session.id,
            "title": session.title,
            "created_at": session.created_at.isoformat() if session.created_at else None
        }
    }

@router.get(
    "/chats",
    response_model=ChatSessionListResponse,
    summary="List all chat sessions"
)
def list_chat_sessions(db: Session = Depends(get_db)):
    """
    Retrieve all chat sessions sorted by most recent activity.
    """
    return {
        "success": True,
        "sessions": chat_service.list_sessions(db)
    }

@router.delete(
    "/chats/{session_id}",
    response_model=BaseResponse,
    summary="Delete a chat session"
)
def delete_chat_session(session_id: str, db: Session = Depends(get_db)):
    """
    Delete a conversation session and all its messages.
    """
    deleted = chat_service.delete_session(session_id, db)
    if not deleted:
        raise HTTPException(status_code=404, detail="Chat session not found.")
    return {"success": True, "message": "Session deleted."}

@router.get(
    "/chats/{session_id}/messages",
    response_model=ChatMessagesResponse,
    summary="Get conversation messages"
)
def get_chat_messages(session_id: str, db: Session = Depends(get_db)):
    """
    Get all messages and citations for a specific conversation session.
    """
    return {
        "success": True,
        "messages": chat_service.get_messages(session_id, db)
    }

@router.post(
    "/chats/{session_id}/messages",
    response_model=Optional[ChatAnswerResponse],
    summary="Ask a question in chat session (with optional streaming)"
)
async def send_chat_message(
    session_id: str,
    request: QuestionRequest,
    db: Session = Depends(get_db),
    x_gemini_api_key: Optional[str] = Header(None, alias="X-Gemini-Api-Key")
):
    """
    Retrieve evidence chunks from indexed PDFs, ground prompt, and stream or return grounded response.
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
@router.post(
    "/chat/query",
    response_model=SimpleQueryResponse,
    summary="Simple single-turn QA query",
    include_in_schema=False
)
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
