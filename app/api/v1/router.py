from fastapi import APIRouter
from app.api.v1.endpoints import health, documents, chats

api_router = APIRouter()

# Register core endpoint routers
api_router.include_router(health.router)
api_router.include_router(documents.router)
api_router.include_router(chats.router)
