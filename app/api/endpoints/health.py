"""
Backward-compatibility bridge: routes forward to app.api.v1.endpoints.health.
"""
from app.api.v1.endpoints.health import router

__all__ = ["router"]
