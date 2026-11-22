"""
Backward-compatibility bridge: routes forward to app.api.v1.endpoints.chats.
"""
from app.api.v1.endpoints.chats import router
from app.schemas.chat import CreateChatRequest, QuestionRequest, SimpleQueryRequest

__all__ = ["router", "CreateChatRequest", "QuestionRequest", "SimpleQueryRequest"]
