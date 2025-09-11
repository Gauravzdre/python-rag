# Pro RAG Chatbot API

A production-grade RAG (Retrieval-Augmented Generation) chatbot backend service built with FastAPI, LangChain, and ChromaDB.

## Features

- **FastAPI** backend with automatic API documentation
- **JWT Authentication** for secure endpoints
- **Document Upload** and processing with text chunking
- **Vector Search** using ChromaDB for similarity matching
- **OpenAI Integration** for embeddings and LLM responses
- **CORS Support** for frontend integration
- **Docker Support** for easy deployment

## Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   - Copy `.env` and add your OpenAI API key
   - Set a strong SECRET_KEY for JWT authentication

3. **Run the Application**
   ```bash
   uvicorn app.main:app --reload
   ```

4. **Access the API**
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs
   - Health Check: http://localhost:8000/healthcheck

## API Endpoints

- `POST /query` - Ask questions to the RAG system
- `POST /upload` - Upload documents for indexing
- `GET /healthcheck` - Health check endpoint

## Docker Deployment

```bash
docker build -t rag-chatbot .
docker run -p 8000:8000 rag-chatbot
```

## Framework Versions

- Python: 3.9+ (3.11 recommended)
- FastAPI: 0.116.1
- LangChain: 0.3.0
- ChromaDB: 0.5.x
- OpenAI: 1.14.0

## Next Steps

- Add support for PDF and Markdown documents
- Implement streaming responses
- Add user management and multi-tenancy
- Integrate with headless CMS
- Add advanced chunking strategies
