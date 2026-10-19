from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Header
from sqlalchemy.orm import Session
from typing import Optional
from app.db.session import get_db
from app.services.pdf_service import pdf_service

router = APIRouter(tags=["Documents"])

@router.post("/documents")
@router.post("/pdf/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    x_gemini_api_key: Optional[str] = Header(None, alias="X-Gemini-Api-Key")
):
    """
    Blueprint Section 9 & 10A: Upload PDF, validate, extract page-by-page, chunk, and embed.
    """
    if not file.filename.lower().endswith(".pdf"):
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

@router.get("/documents")
@router.get("/pdf/documents")
def list_documents(db: Session = Depends(get_db)):
    """
    Blueprint Section 9: List uploaded documents and ingestion status.
    """
    return {
        "success": True,
        "documents": pdf_service.list_documents(db)
    }

@router.get("/documents/{doc_id}")
def get_document(doc_id: str, db: Session = Depends(get_db)):
    """
    Blueprint Section 9: Get document details and status.
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

@router.delete("/documents/{doc_id}")
def delete_document(doc_id: str, db: Session = Depends(get_db)):
    """
    Blueprint Section 9: Delete a document, its chunks and embeddings.
    """
    deleted = pdf_service.delete_document(doc_id, db)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found.")
    return {
        "success": True,
        "message": f"Document {doc_id} and associated chunks successfully deleted."
    }
