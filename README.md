# DocuChat - AI Document Q&A System

An AI-powered document question-answering system built with FastAPI, LangChain, and Pinecone. Upload PDFs and ask questions using natural language with conversational context support.

## Features

- 📄 PDF document upload and processing
- 🔍 Semantic search using vector embeddings
- 🤖 AI-powered answers with Google Gemini
- 💬 Conversational context (follow-up questions)
- 🗄️ PostgreSQL database for metadata and history
- 🌲 Pinecone vector database for embeddings
- ✅ Production-ready REST API

## Tech Stack

- **Backend**: FastAPI, Python 3.11+
- **AI/ML**: LangChain, Google Gemini Pro
- **Vector Database**: Pinecone
- **Database**: PostgreSQL (or SQLite)
- **Deployment**: Docker, Uvicorn

## Quick Start

### Prerequisites

```bash
- Python 3.11+
- Poetry
- PostgreSQL (or SQLite)
- Google Gemini API key
- Pinecone API key
```

### Installation

```bash
# Clone repository
git clone <your-repo-url>
cd docu-chat-learn

# Install dependencies
poetry install

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run migrations
poetry run alembic upgrade head

# Start server
poetry run uvicorn app.main:app --reload
```

Visit http://localhost:8000/docs for API documentation.

## API Endpoints

### Documents
- `POST /documents/upload` - Upload PDF document
- `GET /documents` - List all documents
- `GET /documents/{id}` - Get document details
- `DELETE /documents/{id}` - Delete document

### Chat
- `POST /chat` - Ask questions about documents
  - Supports `session_id` for conversational context
  - Optional `document_id` to filter by specific document

### Health
- `GET /` - API information
- `GET /health` - Health check

## Usage Examples

### Upload Document

```bash
curl -X POST "http://localhost:8000/documents/upload" \
  -F "file=@document.pdf"
```

### Ask Question

```bash
curl -X POST "http://localhost:8000/chat/" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is this document about?"
  }'
```

### Conversational Follow-up

```bash
# Use session_id from previous response
curl -X POST "http://localhost:8000/chat/" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Can you elaborate on that?",
    "session_id": "abc-123-def-456"
  }'
```

## Architecture

```
User Request
    ↓
FastAPI Router
    ↓
RAG Service
    ├→ Pinecone (vector search)
    ├→ Google Gemini (embeddings & generation)
    └→ PostgreSQL (metadata & history)
    ↓
Response
```

## Configuration

Environment variables (`.env`):

```bash
# API Keys
GOOGLE_API_KEY=your_gemini_key
PINECONE_API_KEY=your_pinecone_key
PINECONE_INDEX_NAME=docu-chat

# Database
DATABASE_URL=postgresql://user:pass@localhost/docu_chat

# Optional
ENVIRONMENT=development
LOG_LEVEL=INFO
MAX_FILE_SIZE_MB=10
```

## Development

```bash
# Run tests
poetry run pytest

# Code formatting
poetry run black app/

# Linting
poetry run ruff check app/

# Type checking
poetry run mypy app/
```

## Deployment

### Docker

```bash
# Build image
docker build -t docu-chat .

# Run container
docker run -p 8000:8000 --env-file .env docu-chat
```

### Docker Compose

```bash
docker-compose up
```

## How It Works

1. **Document Upload**: PDF is processed and split into chunks
2. **Embedding**: Each chunk is converted to vector embeddings using Google Gemini
3. **Storage**: Embeddings stored in Pinecone, metadata in PostgreSQL
4. **Query**: User questions are embedded and matched against stored vectors
5. **Generation**: Retrieved context + question sent to Gemini for answer
6. **Context**: Session history enables conversational follow-ups

## Project Structure

```
docu-chat-learn/
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration
│   ├── database.py          # Database setup
│   ├── routers/             # API endpoints
│   │   ├── documents.py
│   │   └── chat.py
│   ├── models/              # Data models
│   │   ├── database.py      # SQLAlchemy models
│   │   └── schemas.py       # Pydantic schemas
│   └── services/            # Business logic
│       └── rag_service.py   # RAG implementation
├── tests/                   # Test suite
├── alembic/                 # Database migrations
├── .env.example             # Environment template
├── pyproject.toml           # Dependencies
└── README.md
```

## Contributing

Contributions welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Author

**Yasith Silva**
- Email: yasithranusha24@gmail.com
- GitHub: [@yasithranusha](https://github.com/yasithranusha)

## Acknowledgments

- LangChain for the RAG framework
- Google Gemini for AI capabilities
- Pinecone for vector database
