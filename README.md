# AI-PDF-Chatbot-api

Backend API service for AI PDF Chatbot built with Python and FastAPI.

## Features
- **FastAPI** high-performance REST API with automatic interactive OpenAPI/Swagger docs (`/docs`)
- **PDF Ingestion & Processing**: Extracts text and metadata from uploaded PDF documents
- **CORS enabled**: Pre-configured to communicate seamlessly with React frontend
- **Environment Configuration**: Powered by Pydantic Settings & `.env`

## Getting Started

### 1. Setup Virtual Environment
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Development Server
```bash
uvicorn app.main:app --reload --port 8000
```
Interactive Swagger documentation will be available at `http://localhost:8000/docs`.
