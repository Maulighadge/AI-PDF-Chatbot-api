import re
from typing import List, Dict, Any
import tiktoken
from app.core.config import settings

class ChunkingService:
    def __init__(self):
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception:
            self.tokenizer = None

    def count_tokens(self, text: str) -> int:
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        return max(1, len(text.split()))

    def chunk_document_pages(
        self, 
        document_id: str, 
        filename: str, 
        pages: List[Dict[str, Any]], 
        chunk_size: int = None, 
        chunk_overlap: int = None
    ) -> List[Dict[str, Any]]:
        """
        Splits page text into manageable overlapping chunks while preserving page_number.
        Blueprint: Target 500-800 tokens, 50-100 token overlap.
        """
        target_chunk_size = chunk_size or settings.CHUNK_SIZE
        target_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        
        all_chunks: List[Dict[str, Any]] = []
        global_chunk_idx = 0

        for page_data in pages:
            page_num = page_data["page_number"]
            page_text = page_data.get("text", "")
            
            # Normalize whitespace while preserving paragraph boundaries
            normalized_text = re.sub(r'[ \t]+', ' ', page_text)
            normalized_text = re.sub(r'\n{3,}', '\n\n', normalized_text).strip()
            
            if not normalized_text:
                continue

            # Split into paragraphs/sentences
            paragraphs = normalized_text.split('\n\n')
            current_chunk = ""
            
            for para in paragraphs:
                para = para.strip()
                if not para:
                    continue

                potential_text = (current_chunk + "\n\n" + para).strip() if current_chunk else para
                token_count = self.count_tokens(potential_text)

                if token_count <= target_chunk_size:
                    current_chunk = potential_text
                else:
                    if current_chunk:
                        all_chunks.append({
                            "document_id": document_id,
                            "filename": filename,
                            "chunk_index": global_chunk_idx,
                            "page_number": page_num,
                            "content": current_chunk,
                            "token_count": self.count_tokens(current_chunk)
                        })
                        global_chunk_idx += 1
                        
                        # Overlap: keep last part of previous chunk
                        words = current_chunk.split()
                        overlap_words = words[-target_overlap:] if len(words) > target_overlap else []
                        overlap_prefix = " ".join(overlap_words)
                        current_chunk = (overlap_prefix + "\n\n" + para).strip() if overlap_prefix else para
                    else:
                        # Paragraph itself is larger than chunk size, divide it into slices
                        para_words = para.split()
                        start_idx = 0
                        while start_idx < len(para_words):
                            end_idx = min(start_idx + target_chunk_size, len(para_words))
                            slice_text = " ".join(para_words[start_idx:end_idx])
                            all_chunks.append({
                                "document_id": document_id,
                                "filename": filename,
                                "chunk_index": global_chunk_idx,
                                "page_number": page_num,
                                "content": slice_text,
                                "token_count": self.count_tokens(slice_text)
                            })
                            global_chunk_idx += 1
                            start_idx += max(1, target_chunk_size - target_overlap)
                        current_chunk = ""

            if current_chunk:
                all_chunks.append({
                    "document_id": document_id,
                    "filename": filename,
                    "chunk_index": global_chunk_idx,
                    "page_number": page_num,
                    "content": current_chunk,
                    "token_count": self.count_tokens(current_chunk)
                })
                global_chunk_idx += 1

        return all_chunks

chunking_service = ChunkingService()
