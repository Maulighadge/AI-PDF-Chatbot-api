from pydantic import BaseModel, ConfigDict
from typing import Optional, List

class DocumentItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    size_bytes: int
    total_pages: int
    status: str
    created_at: Optional[str] = None

class DocumentIngestData(BaseModel):
    id: str
    filename: str
    total_pages: int
    chunks_count: int
    status: str

class DocumentUploadResponse(BaseModel):
    success: bool = True
    message: str
    data: DocumentIngestData

class DocumentListResponse(BaseModel):
    success: bool = True
    documents: List[DocumentItem]

class DocumentDetailResponse(BaseModel):
    success: bool = True
    document: DocumentItem

class DocumentDeleteResponse(BaseModel):
    success: bool = True
    message: str
