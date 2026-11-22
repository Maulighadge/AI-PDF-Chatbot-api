from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Header
from sqlalchemy.orm import Session
from typing import Optional
from app.db.session import get_db
from app.services.pdf_service import pdf_service
from app.schemas.document import (
    DocumentUploadResponse,
    DocumentListResponse,
    DocumentDetailResponse,
    DocumentDeleteResponse
)

router = APIRouter(tags=["Documents"])

@router.post(
    "/documents",
    response_model=DocumentUploadResponse,
    status_code=200,
    summary="Upload & Ingest PDF Document"
)
@router.post(
    "/pdf/upload",
    response_model=DocumentUploadResponse,
    include_in_schema=False
)
async def upload_document(
    file: UploadFile = File(..., description="PDF file to ingest"),
    db: Session = Depends(get_db),
    x_gemini_api_key: Optional[str] = Header(None, alias="X-Gemini-Api-Key")
):
    """
    Upload PDF, validate, extract page-by-page, chunk, and embed vectors into ChromaDB.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
        
    try:
        result = pdf_service.process_and_ingest(
            filename=file.filename,
            content=content,
            db=db,
            api_key=x_gemini_api_key
        )
        return {
            "success": True,
            "message": f"Successfully processed and indexed {file.filename}",
            "data": result
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")

@router.get(
    "/documents",
    response_model=DocumentListResponse,
    summary="List all uploaded documents"
)
@router.get(
    "/pdf/documents",
    response_model=DocumentListResponse,
    include_in_schema=False
)
def list_documents(db: Session = Depends(get_db)):
    """
    List uploaded documents and ingestion status.
    """
    return {
        "success": True,
        "documents": pdf_service.list_documents(db)
    }

@router.get(
    "/documents/{doc_id}",
    response_model=DocumentDetailResponse,
    summary="Get document details by ID"
)
def get_document(doc_id: str, db: Session = Depends(get_db)):
    """
    Get document metadata and status by document ID.
    """
    doc = pdf_service.get_document(doc_id, db)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    return {
        "success": True,
        "document": {
            "id": doc.id,
            "filename": doc.filename,
            "size_bytes": doc.size_bytes,
            "total_pages": doc.total_pages,
            "status": doc.status,
            "created_at": doc.created_at.isoformat() if doc.created_at else None
        }
    }

@router.delete(
    "/documents/{doc_id}",
    response_model=DocumentDeleteResponse,
    summary="Delete document and its vector embeddings"
)
def delete_document(doc_id: str, db: Session = Depends(get_db)):
    """
    Delete a document, its physical file, chunks and embeddings.
    """
    deleted = pdf_service.delete_document(doc_id, db)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found.")
    return {
        "success": True,
        "message": f"Document {doc_id} and associated chunks successfully deleted."
    }
