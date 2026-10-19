import os
import uuid
from typing import Dict, Any, List, Optional
from pypdf import PdfReader
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.models import Document, DocumentChunk
from app.services.chunking_service import chunking_service
from app.services.vector_store import vector_store
from app.services.llm_service import llm_service

class PDFService:
    def __init__(self):
        self.upload_dir = settings.UPLOAD_DIR
        os.makedirs(self.upload_dir, exist_ok=True)

    def process_and_ingest(
        self, 
        filename: str, 
        content: bytes, 
        db: Session,
        api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Full PDF Ingestion Pipeline (Blueprint Section 10A):
        1. Validate size and extension
        2. Store privately with generated storage key
        3. Extract text page-by-page preserving page numbers
        4. Split into overlapping chunks
        5. Generate embeddings
        6. Store in Vector DB & Relational DB
        """
        # Validate size
        max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        if len(content) > max_bytes:
            raise ValueError(f"File exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB.")

        doc_id = str(uuid.uuid4())
        storage_key = f"{doc_id}_{filename}"
        file_path = os.path.join(self.upload_dir, storage_key)

        # 1. Save file privately
        with open(file_path, "wb") as f:
            f.write(content)

        # 2. Extract text page-by-page
        try:
            reader = PdfReader(file_path)
            pages_data: List[Dict[str, Any]] = []
            
            for idx, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                pages_data.append({
                    "page_number": idx + 1,
                    "text": page_text
                })

            total_pages = len(reader.pages)
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            raise ValueError(f"Failed to parse PDF: {str(e)}")

        # 3. Create Document DB Record (status='processing')
        doc_record = Document(
            id=doc_id,
            filename=filename,
            storage_key=storage_key,
            mime_type="application/pdf",
            size_bytes=len(content),
            status="processing",
            total_pages=total_pages
        )
        db.add(doc_record)
        db.commit()

        try:
            # 4. Chunk text with page awareness
            chunks = chunking_service.chunk_document_pages(
                document_id=doc_id,
                filename=filename,
                pages=pages_data
            )

            # 5. Generate embeddings
            chunk_texts = [c["content"] for c in chunks]
            embeddings = llm_service.embed_texts(chunk_texts, api_key=api_key)

            # 6. Store in ChromaDB vector store
            vector_store.add_chunks(chunks, embeddings)

            # 7. Persist chunks in Relational DB
            for c in chunks:
                db_chunk = DocumentChunk(
                    document_id=doc_id,
                    chunk_index=c["chunk_index"],
                    page_number=c["page_number"],
                    content=c["content"],
                    token_count=c["token_count"]
                )
                db.add(db_chunk)

            doc_record.status = "ready"
            db.commit()

            return {
                "id": doc_id,
                "filename": filename,
                "total_pages": total_pages,
                "chunks_count": len(chunks),
                "status": "ready"
            }
        except Exception as e:
            doc_record.status = "failed"
            db.commit()
            raise RuntimeError(f"Ingestion failed during chunking/embedding: {str(e)}")

    def list_documents(self, db: Session) -> List[Dict[str, Any]]:
        docs = db.query(Document).order_by(Document.created_at.desc()).all()
        return [
            {
                "id": d.id,
                "filename": d.filename,
                "total_pages": d.total_pages,
                "size_bytes": d.size_bytes,
                "status": d.status,
                "created_at": d.created_at.isoformat() if d.created_at else None
            }
            for d in docs
        ]

    def get_document(self, doc_id: str, db: Session) -> Optional[Document]:
        return db.query(Document).filter(Document.id == doc_id).first()

    def delete_document(self, doc_id: str, db: Session) -> bool:
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            return False

        # Remove vector chunks
        vector_store.delete_document(doc_id)

        # Remove physical file
        file_path = os.path.join(self.upload_dir, doc.storage_key)
        if os.path.exists(file_path):
            os.remove(file_path)

        # Remove DB record and cascade chunks
        db.delete(doc)
        db.commit()
        return True

pdf_service = PDFService()
