"""
Backward-compatibility bridge: routes forward to app.api.v1.endpoints.documents.
"""
from app.api.v1.endpoints.documents import router

__all__ = ["router"]
