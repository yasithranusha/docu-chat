# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Reference

See `README.md` for project overview, features, tech stack, API endpoints, and usage examples.

See `LEARNING_GUIDE.md` for the 7-day progressive implementation tutorial and detailed learning resources.

## Development Commands

**Preferred: Use Makefile commands** (shorter, easier)

```bash
# Show all available commands
make help

# Development server (most common)
make dev

# Testing & quality
make test
make lint
make format

# Database migrations
make migrate
make migrate-create MSG="description"

# Setup project
make install
make setup      # install + migrate
```

**Alternative: Direct Poetry commands**

```bash
# Install dependencies
poetry install

# Run development server
poetry run uvicorn app.main:app --reload

# Run production server
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000
```


## Architecture (RAG Flow)

This is a RAG (Retrieval-Augmented Generation) system. The core flow:

1. **Document Upload** → PDF split into chunks (RecursiveCharacterTextSplitter: 1000 chars, 200 overlap)
2. **Embedding** → Chunks converted to vectors (HuggingFace `all-MiniLM-L6-v2`, dim=384, free, runs locally)
3. **Storage** → Vectors in Pinecone (cosine metric), metadata in PostgreSQL
4. **Query** → User question embedded → Semantic search in Pinecone → Top-k retrieval
5. **Generation** → Retrieved context + question → Gemini Pro → Answer
6. **Conversational Context** → Session-based history (last 10 messages) enables follow-ups

### Current Status

Early stage implementation:
- `app/main.py` has basic FastAPI setup
- Imports reference `app.routes.chat` but routes directory doesn't exist yet
- Following progressive implementation plan from LEARNING_GUIDE.md

## Key Implementation Patterns

### Project Structure

```
app/
├── main.py              # FastAPI entry point
├── config.py            # Pydantic Settings for env vars
├── database.py          # SQLAlchemy setup with get_db() dependency
├── routers/             # API route handlers
│   ├── documents.py     # Upload, list, delete documents
│   └── chat.py          # Q&A with conversational context
├── models/
│   ├── database.py      # SQLAlchemy ORM models (Document, ChatHistory)
│   └── schemas.py       # Pydantic request/response models
└── services/
    └── rag_service.py   # LangChain + Pinecone + Gemini logic
```

### Conversational Context Implementation

Critical for follow-up questions:
- Use `session_id` (UUID) to group conversations
- Retrieve last 10 `ChatHistory` records for session
- Convert to LangChain message format (`HumanMessage`, `AIMessage`)
- Use `create_history_aware_retriever` with `MessagesPlaceholder`
- This reformulates vague questions ("tell me more") into standalone queries

### Database Models

**Document table:**
```python
id, filename, file_path, upload_date, chunks_count, status
```

**ChatHistory table:**
```python
id, document_id, session_id, question, answer, sources_count, created_at
```

### Dependency Injection Pattern

Use FastAPI dependencies for clean architecture:
```python
db: Session = Depends(get_db)
rag_service: RAGService = Depends(get_rag_service)
```

## Configuration

Poetry uses in-project virtualenvs (`.venv/` directory).

Required `.env` variables:
- `GOOGLE_API_KEY` - Gemini API key
- `PINECONE_API_KEY` - Pinecone API key
- `PINECONE_INDEX_NAME` - Index name (e.g., "docu-chat")
- `DATABASE_URL` - PostgreSQL or SQLite connection string

## Important Notes for Claude Code

- All document processing must be async to avoid blocking FastAPI
- When creating routes, ensure proper error handling and logging
- Session management is critical for conversational features
- Pinecone index must have dimension=384 for HuggingFace all-MiniLM-L6-v2
- Use dependency injection for database sessions (don't create sessions in routes)
- Follow the progressive implementation approach from LEARNING_GUIDE.md
