from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI PDF Chatbot API"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"
    
    # File Storage
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 15
    
    # Database
    DATABASE_URL: str = "sqlite:///./ai_pdf_chatbot.db"
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    
    # RAG & Chunking
    CHUNK_SIZE: int = 600        # target ~500-800 tokens
    CHUNK_OVERLAP: int = 80      # ~50-100 token overlap
    TOP_K_CHUNKS: int = 5        # default 4-6 retrieved passages
    
    # LLM Settings (Google Gemini)
    GEMINI_API_KEY: str = ""
    LLM_MODEL: str = "gemini-2.5-flash"
    EMBEDDING_MODEL: str = "text-embedding-004"

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
