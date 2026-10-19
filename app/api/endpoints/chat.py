from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from app.services.pdf_service import pdf_service

router = APIRouter(prefix="/chat", tags=["Chat & QA"])

class ChatRequest(BaseModel):
    doc_id: Optional[str] = None
    question: str
    chat_history: Optional[List[dict]] = []

class ChatResponse(BaseModel):
    answer: str
    doc_id: Optional[str] = None
    sources: Optional[List[dict]] = []

@router.post("/query", response_model=ChatResponse)
async def query_chat(request: ChatRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
        
    doc = None
    if request.doc_id:
        doc = pdf_service.get_document(request.doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Specified document ID not found.")

    # Starter smart-matching QA response before LLM integration
    if doc:
        # Search for keyword matches across pages
        query_words = set(request.question.lower().split())
        matched_pages = []
        for p in doc["pages"]:
            page_text_lower = p["text"].lower()
            matches = sum(1 for w in query_words if len(w) > 3 and w in page_text_lower)
            if matches > 0:
                matched_pages.append({
                    "page_number": p["page_number"],
                    "excerpt": p["text"][:200] + ("..." if len(p["text"]) > 200 else "")
                })

        answer = (
            f"Based on your document '{doc['filename']}', I found relevant content on "
            f"{len(matched_pages)} page(s). You can integrate your preferred LLM provider "
            f"(OpenAI, Gemini, Anthropic, or Ollama) to generate full synthesized answers."
        )
        return ChatResponse(
            answer=answer,
            doc_id=request.doc_id,
            sources=matched_pages[:3]
        )
    else:
        return ChatResponse(
            answer="Backend API is running! Please upload a PDF to ask questions about it, or connect your API key.",
            doc_id=None,
            sources=[]
        )
