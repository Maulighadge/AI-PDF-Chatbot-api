import os
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.core.config import settings

class VectorStoreService:
    def __init__(self):
        os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name="ai_pdf_chunks",
            metadata={"hnsw:space": "cosine"}
        )

    def add_chunks(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]]):
        if not chunks:
            return

        ids = [f"{c['document_id']}_{c['chunk_index']}" for c in chunks]
        documents = [c["content"] for c in chunks]
        metadatas = [
            {
                "document_id": c["document_id"],
                "filename": c.get("filename", ""),
                "page_number": c["page_number"],
                "chunk_index": c["chunk_index"],
                "token_count": c.get("token_count", 0)
            }
            for c in chunks
        ]

        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )

    def search(
        self,
        query_embedding: List[float],
        document_id: Optional[str] = None,
        top_k: int = None
    ) -> List[Dict[str, Any]]:
        k = top_k or settings.TOP_K_CHUNKS
        where_filter = {"document_id": document_id} if document_id else None

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where=where_filter
        )

        matched_chunks = []
        if results and "documents" in results and results["documents"]:
            docs = results["documents"][0]
            metadatas = results["metadatas"][0] if "metadatas" in results else []
            distances = results["distances"][0] if "distances" in results else []

            for idx, text in enumerate(docs):
                meta = metadatas[idx] if idx < len(metadatas) else {}
                dist = distances[idx] if idx < len(distances) else 1.0
                matched_chunks.append({
                    "content": text,
                    "document_id": meta.get("document_id"),
                    "filename": meta.get("filename"),
                    "page_number": meta.get("page_number", 1),
                    "chunk_index": meta.get("chunk_index", 0),
                    "distance": dist,
                    "score": round(1.0 - dist, 4) if dist is not None else 1.0
                })

        return matched_chunks

    def delete_document(self, document_id: str):
        try:
            self.collection.delete(where={"document_id": document_id})
        except Exception as e:
            print(f"Error removing vector chunks for {document_id}: {e}")

vector_store = VectorStoreService()
