import os
import hashlib
from typing import List, AsyncGenerator, Optional, Dict, Any
from google import genai
from google.genai import types
from app.core.config import settings
from app.prompts.rag_prompts import RAG_SYSTEM_PROMPT, build_rag_prompt

class LLMService:
    def __init__(self):
        self.default_api_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")

    def get_client(self, api_key: Optional[str] = None) -> Optional[genai.Client]:
        key = api_key or self.default_api_key
        if key and key.strip():
            return genai.Client(api_key=key.strip())
        return None

    def embed_texts(self, texts: List[str], api_key: Optional[str] = None) -> List[List[float]]:
        """
        Embeds a list of strings. Uses Gemini text-embedding-004 if API key is set;
        otherwise provides deterministic normalized semantic hash vectors (768-dim) for offline/local testing.
        """
        client = self.get_client(api_key)
        if client:
            try:
                response = client.models.embed_content(
                    model=settings.EMBEDDING_MODEL,
                    contents=texts
                )
                if hasattr(response, "embeddings") and response.embeddings:
                    return [list(e.values) for e in response.embeddings]
            except Exception as e:
                print(f"Gemini embedding API call failed: {e}. Falling back to local vector generation.")

        # Fallback local pseudo-embedding (768 dimensions)
        embeddings = []
        for t in texts:
            words = t.lower().split()
            vec = [0.0] * 768
            for w in words:
                h = int(hashlib.md5(w.encode('utf-8')).hexdigest(), 16)
                idx = h % 768
                vec[idx] += 1.0
            norm = sum(x * x for x in vec) ** 0.5 or 1.0
            embeddings.append([x / norm for x in vec])
        return embeddings

    async def generate_rag_answer_stream(
        self,
        question: str,
        evidence_chunks: List[Dict[str, Any]],
        api_key: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Generates streaming answer text strictly grounded in evidence passages.
        Yields text tokens.
        """
        prompt = build_rag_prompt(question, evidence_chunks)
        client = self.get_client(api_key)

        if not evidence_chunks:
            yield "I could not find relevant information in the uploaded document to answer your question."
            return

        if client:
            try:
                response = client.models.generate_content_stream(
                    model=settings.LLM_MODEL,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=RAG_SYSTEM_PROMPT,
                        temperature=0.2
                    )
                )
                for chunk in response:
                    if chunk.text:
                        yield chunk.text
                return
            except Exception as e:
                yield f"[Gemini Error: {str(e)}]\n\n"

        # Fallback answer when no Gemini API key is configured yet
        yield (
            f"I found {len(evidence_chunks)} relevant passage(s) in your document.\n\n"
            f"**Evidence Summary:**\n"
        )
        for idx, chunk in enumerate(evidence_chunks[:3]):
            yield f"• **Page {chunk.get('page_number', 1)}**: {chunk.get('content', '')[:160]}...\n"

        yield (
            "\n💡 *To generate real-time AI synthesized answers, please provide your Google Gemini API key "
            "in `backend/.env` or in the API Key settings modal.*"
        )

llm_service = LLMService()
