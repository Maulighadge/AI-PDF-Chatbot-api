from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any

class CreateChatRequest(BaseModel):
    title: Optional[str] = "New Chat"

class ChatSessionItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class ChatSessionResponse(BaseModel):
    success: bool = True
    session: ChatSessionItem

class ChatSessionListResponse(BaseModel):
    success: bool = True
    sessions: List[ChatSessionItem]

class SourceCitation(BaseModel):
    filename: str
    page_number: int
    excerpt: str

class ChatMessageItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    role: str
    content: str
    sources: Optional[List[SourceCitation]] = []
    created_at: Optional[str] = None

class ChatMessagesResponse(BaseModel):
    success: bool = True
    messages: List[ChatMessageItem]

class QuestionRequest(BaseModel):
    question: str
    document_id: Optional[str] = None
    stream: Optional[bool] = False

class ChatAnswerResponse(BaseModel):
    success: bool = True
    message_id: str
    answer: str
    sources: List[SourceCitation]

class SimpleQueryRequest(BaseModel):
    doc_id: Optional[str] = None
    question: str

class SimpleQueryResponse(BaseModel):
    answer: str
    sources: List[SourceCitation]
    doc_id: Optional[str] = None
