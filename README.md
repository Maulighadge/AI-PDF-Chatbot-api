# AI-PDF-Chatbot-api

Backend API service for AI PDF Chatbot built with Python, FastAPI, and Google Gemini RAG pipeline.

## Features
- **FastAPI** high-performance REST API with automatic interactive OpenAPI/Swagger docs (`/docs`)
- **Modern Layered Architecture**: Dedicated versioned routers (`/api/v1`), Pydantic schemas, and decoupled services
- **PDF Ingestion & Processing**: Page-by-page text extraction, overlapping token chunking, and ChromaDB vector indexing
- **RAG & Citations**: Answers grounded in retrieved passages with source citations and page numbers
- **Streaming Support**: Real-time response token streaming via Server-Sent Events (SSE)
- **CORS enabled**: Pre-configured to communicate seamlessly with React frontend
- **Environment Configuration**: Powered by Pydantic Settings & `.env`

---

## API Structure

```
app/
├── api/
│   ├── v1/
│   │   ├── endpoints/
│   │   │   ├── health.py        # GET /api/v1/health
│   │   │   ├── documents.py     # POST /documents, GET /documents, DELETE /documents/:id
│   │   │   └── chats.py         # POST /chats, GET /chats, POST /chats/:id/messages
│   │   └── router.py            # Aggregated v1 API router
│   └── endpoints/               # Backward-compatibility routing bridges
├── core/
│   └── config.py                # Pydantic Settings & environment config
├── db/
│   ├── models.py                # SQLAlchemy Relational Models (Documents, Chunks, Chats)
│   └── session.py               # Database engine & session management
├── prompts/
│   └── rag_prompts.py           # Grounded RAG prompt templates
├── schemas/                     # Pydantic request & response validation schemas
│   ├── common.py                # BaseResponse
│   ├── health.py                # HealthResponse
│   ├── document.py              # DocumentUploadResponse, DocumentItem, etc.
│   └── chat.py                  # QuestionRequest, ChatAnswerResponse, SourceCitation, etc.
├── services/                    # Core business logic & AI orchestration
│   ├── pdf_service.py           # Ingestion, validation, and parsing
│   ├── chunking_service.py      # Page-aware overlapping token chunking
│   ├── vector_store.py          # ChromaDB collection & similarity search
│   ├── llm_service.py           # Google Gemini embeddings & streaming generation
│   └── chat_service.py          # Chat threads, messages, and evidence retrieval
└── main.py                      # FastAPI application entrypoint
```

---

## Key Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/health` | Health and operational status |
| `POST` | `/api/v1/documents` | Upload and index a PDF file |
| `GET` | `/api/v1/documents` | List uploaded documents |
| `GET` | `/api/v1/documents/{doc_id}` | Get document details and status |
| `DELETE`| `/api/v1/documents/{doc_id}` | Delete document and vector embeddings |
| `POST` | `/api/v1/chats` | Create a new chat session |
| `GET` | `/api/v1/chats` | List all chat sessions |
| `GET` | `/api/v1/chats/{session_id}/messages` | Get messages & citations for a session |
| `POST` | `/api/v1/chats/{session_id}/messages` | Ask question (JSON or SSE stream) |
| `DELETE`| `/api/v1/chats/{session_id}` | Delete a chat session |

*Note: Endpoints are also available under `/api/*` for compatibility with existing frontend clients.*

---

## Getting Started

### 1. Setup Virtual Environment
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env` and configure your settings:
```bash
cp .env.example .env
```
Make sure to add your `GEMINI_API_KEY`.

### 4. Run the Development Server
```bash
uvicorn app.main:app --reload --port 8000
```
Interactive Swagger documentation will be available at `http://localhost:8000/docs`.
