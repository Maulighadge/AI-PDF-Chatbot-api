import os
import uuid
from typing import Dict, Any, List
from pypdf import PdfReader
from app.core.config import settings

class PDFService:
    def __init__(self):
        self.upload_dir = settings.UPLOAD_DIR
        os.makedirs(self.upload_dir, exist_ok=True)
        # In-memory document storage for session-based QA
        self.documents_store: Dict[str, Dict[str, Any]] = {}

    def save_and_extract(self, filename: str, content: bytes) -> Dict[str, Any]:
        doc_id = str(uuid.uuid4())
        file_path = os.path.join(self.upload_dir, f"{doc_id}_{filename}")
        
        with open(file_path, "wb") as f:
            f.write(content)
            
        reader = PdfReader(file_path)
        pages_content: List[Dict[str, Any]] = []
        total_text = ""
        
        for idx, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            pages_content.append({
                "page_number": idx + 1,
                "text": text,
                "char_count": len(text)
            })
            total_text += f"\n--- Page {idx + 1} ---\n" + text

        metadata = {
            "title": reader.metadata.title if reader.metadata and reader.metadata.title else filename,
            "author": reader.metadata.author if reader.metadata and reader.metadata.author else "Unknown",
            "total_pages": len(reader.pages),
            "file_size_bytes": len(content),
            "filename": filename
        }

        doc_data = {
            "doc_id": doc_id,
            "filename": filename,
            "file_path": file_path,
            "metadata": metadata,
            "pages": pages_content,
            "full_text": total_text
        }
        
        self.documents_store[doc_id] = doc_data
        return {
            "doc_id": doc_id,
            "filename": filename,
            "total_pages": len(reader.pages),
            "metadata": metadata,
            "summary_preview": total_text[:500] if total_text else "No text extracted."
        }

    def get_document(self, doc_id: str) -> Dict[str, Any]:
        return self.documents_store.get(doc_id)

    def list_documents(self) -> List[Dict[str, Any]]:
        return [
            {
                "doc_id": d["doc_id"],
                "filename": d["filename"],
                "total_pages": d["metadata"]["total_pages"]
            }
            for d in self.documents_store.values()
        ]

pdf_service = PDFService()
