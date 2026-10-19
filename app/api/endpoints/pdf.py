from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.pdf_service import pdf_service

router = APIRouter(prefix="/pdf", tags=["PDF Processing"])

@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
        
    try:
        result = pdf_service.save_and_extract(file.filename, content)
        return {
            "success": True,
            "message": f"Successfully parsed {file.filename}",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")

@router.get("/documents")
def get_documents():
    return {
        "success": True,
        "documents": pdf_service.list_documents()
    }

@router.get("/{doc_id}")
def get_document_details(doc_id: str):
    doc = pdf_service.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    return {
        "success": True,
        "doc_id": doc["doc_id"],
        "filename": doc["filename"],
        "metadata": doc["metadata"],
        "total_pages": len(doc["pages"])
    }
