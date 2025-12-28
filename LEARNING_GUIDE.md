# 🎓 7-Day Learning Guide - Build DocuChat Yourself

## Overview

This guide walks you through building a production-ready RAG system **from scratch**. Each day adds new features to your growing project, teaching core concepts through hands-on coding.

**Total Time**: 18-24 hours over 7 days
**Difficulty**: Intermediate (assumes Python + LangChain basics)
**Approach**: Progressive - each day builds on the previous

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+ (check: `python3 --version`)
- Poetry installed (`pip install poetry`)
- Google Gemini API key ([Get one](https://makersuite.google.com/app/apikey))
- Pinecone account ([Sign up](https://app.pinecone.io/))

### Initial Setup

```bash
cd /Users/yasithranusha/Developer/docu-chat-learn

# Initialize Poetry project
poetry init --python "^3.11"

# Create environment
poetry install

# Create .env file
echo "GOOGLE_API_KEY=your_key_here" > .env
echo "PINECONE_API_KEY=your_key_here" >> .env
echo "PINECONE_INDEX_NAME=docu-chat" >> .env
```

---

## 📅 Day-by-Day Plan

### Day 1: Basic RAG (3-4 hours)

**🎯 Goal**: Answer questions from a PDF using in-memory RAG

**What You'll Learn**:
- Core RAG: Retrieval + Generation
- Document loading and chunking
- Creating embeddings
- Vector similarity search
- LLM answer generation

**What You'll Build**:

Create `simple_rag.py` that:
1. Loads a PDF file
2. Splits into chunks (1000 chars, 200 overlap)
3. Creates embeddings with Google Gemini
4. Stores in FAISS (in-memory vector store)
5. Answers questions using retrieved context

**Dependencies to add**:
```bash
poetry add langchain langchain-community langchain-google-genai
poetry add faiss-cpu pypdf python-dotenv
```

**Key Concepts**:
- **Chunking**: Why? LLMs have token limits. Smaller chunks = more precise retrieval.
- **Embeddings**: Convert text → numbers. Similar meaning = similar vectors.
- **FAISS**: Fast similarity search library. In-memory = data lost on restart.
- **RAG Flow**: Question → Embed → Search similar → Send to LLM with context

**Implementation Steps**:

1. **Load PDF**:
```python
from langchain_community.document_loaders import PyPDFLoader

loader = PyPDFLoader("your_document.pdf")
documents = loader.load()
```

2. **Split into chunks**:
```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)
chunks = text_splitter.split_documents(documents)
```

3. **Create embeddings and vector store**:
```python
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS

embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
vectorstore = FAISS.from_documents(chunks, embeddings)
```

4. **Build QA chain**:
```python
from langchain_google_genai import GoogleGenerativeAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

llm = GoogleGenerativeAI(model="gemini-pro", temperature=0.3)

prompt = ChatPromptTemplate.from_messages([
    ("system", "Use the context to answer questions. {context}"),
    ("human", "{input}")
])

document_chain = create_stuff_documents_chain(llm, prompt)
retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
qa_chain = create_retrieval_chain(retriever, document_chain)
```

5. **Test it**:
```python
result = qa_chain.invoke({"input": "What is this about?"})
print(result["answer"])
```

**Success Criteria**:
- ✅ Script runs without errors
- ✅ Answers questions based on PDF content
- ✅ Can explain what embeddings are
- ✅ Understand the RAG flow

**Troubleshooting**:
- "API key not found" → Check `.env` file and `load_dotenv()`
- "No content extracted" → Verify PDF is valid and not corrupted
- Slow performance → Normal! Embedding creation takes time

**Reference**: Compare with `/Users/yasithranusha/Developer/docu-chat-api` (but try yourself first!)

---

### Day 2: Pinecone Integration (2-3 hours)

**🎯 Goal**: Replace FAISS with Pinecone for persistent storage

**What You'll Learn**:
- Why cloud vector databases
- Pinecone setup and indexing
- Metadata filtering
- Production considerations

**What You'll Build**:

Create `app/services/rag_service.py` with a `RAGService` class:
- Initialize Pinecone client
- Create index if doesn't exist
- Store embeddings in Pinecone
- Query with metadata filters

**Dependencies to add**:
```bash
poetry add pinecone-client langchain-pinecone
```

**Implementation Steps**:

1. **Initialize Pinecone**:
```python
from pinecone import Pinecone, ServerlessSpec

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index_name = "docu-chat"

# Create index if doesn't exist
if index_name not in [idx.name for idx in pc.list_indexes()]:
    pc.create_index(
        name=index_name,
        dimension=768,  # Google embedding-001 dimension
        metric='cosine',
        spec=ServerlessSpec(cloud='aws', region='us-east-1')
    )
```

2. **Store documents**:
```python
from langchain_pinecone import PineconeVectorStore

# Add metadata to chunks
for i, chunk in enumerate(chunks):
    chunk.metadata["document_id"] = 1
    chunk.metadata["chunk_index"] = i

# Store in Pinecone
PineconeVectorStore.from_documents(
    documents=chunks,
    embedding=embeddings,
    index_name=index_name
)
```

3. **Query with filtering**:
```python
vectorstore = PineconeVectorStore(
    index_name=index_name,
    embedding=embeddings
)

retriever = vectorstore.as_retriever(
    search_kwargs={
        "k": 4,
        "filter": {"document_id": {"$eq": 1}}  # Optional
    }
)
```

**Key Differences from Day 1**:
- FAISS: In-memory, lost on restart, single-machine
- Pinecone: Cloud-hosted, persistent, scalable, multi-user

**Success Criteria**:
- ✅ Pinecone index created
- ✅ Embeddings persist after restart
- ✅ Can query with metadata filters
- ✅ Understand Pinecone vs FAISS trade-offs

---

### Day 3: FastAPI Backend (3-4 hours)

**🎯 Goal**: Create REST API for document upload and chat

**What You'll Learn**:
- FastAPI framework
- File upload handling
- Pydantic schemas
- API routing
- Error handling

**Project Structure**:
```
docu-chat-learn/
├── app/
│   ├── main.py              # FastAPI app
│   ├── config.py            # Settings
│   ├── routers/
│   │   ├── documents.py     # Upload endpoints
│   │   └── chat.py          # Chat endpoints
│   ├── services/
│   │   └── rag_service.py   # RAG logic (from Day 2)
│   └── models/
│       └── schemas.py       # Pydantic models
├── .env
└── pyproject.toml
```

**Dependencies to add**:
```bash
poetry add fastapi uvicorn python-multipart
```

**What You'll Build**:

**1. app/main.py**:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import documents, chat

app = FastAPI(title="DocuChat API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router)
app.include_router(chat.router)

@app.get("/")
def read_root():
    return {"message": "DocuChat API", "version": "1.0.0"}
```

**2. app/models/schemas.py**:
```python
from pydantic import BaseModel, Field
from typing import Optional, List

class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1)
    document_id: Optional[int] = None

class ChatResponse(BaseModel):
    question: str
    answer: str
    sources: List[dict]
```

**3. app/routers/chat.py**:
```python
from fastapi import APIRouter, Depends
from app.models.schemas import ChatRequest, ChatResponse
from app.services.rag_service import RAGService

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    rag_service = RAGService()  # We'll improve this later
    result = rag_service.query(request.question, request.document_id)
    return ChatResponse(**result)
```

**4. app/routers/documents.py**:
```python
from fastapi import APIRouter, UploadFile, File
import shutil

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    # Save file
    file_path = f"uploads/{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Process with RAG service
    rag_service = RAGService()
    chunks = rag_service.process_pdf(file_path, document_id=1)

    return {"filename": file.filename, "chunks": chunks}
```

**Run the server**:
```bash
poetry run uvicorn app.main:app --reload
```

**Test with curl**:
```bash
# Upload PDF
curl -X POST "http://localhost:8000/documents/upload" \
  -F "file=@test.pdf"

# Ask question
curl -X POST "http://localhost:8000/chat/" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is this about?"}'
```

**Success Criteria**:
- ✅ API starts on port 8000
- ✅ Can upload PDF via API
- ✅ Can ask questions via API
- ✅ Swagger docs at http://localhost:8000/docs

---

### Day 4: Database Integration (2-3 hours)

**🎯 Goal**: Add PostgreSQL to track documents and metadata

**What You'll Learn**:
- SQLAlchemy ORM
- Database models
- Alembic migrations
- CRUD operations

**Dependencies to add**:
```bash
poetry add sqlalchemy psycopg2-binary alembic
```

**What You'll Build**:

**1. app/database.py**:
```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://user:pass@localhost/docu_chat"
# Or SQLite for testing: "sqlite:///./docu_chat.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**2. app/models/database.py**:
```python
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from app.database import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    chunks_count = Column(Integer, default=0)
    status = Column(String(50), default="processing")

class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    sources_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

**3. Setup Alembic**:
```bash
poetry run alembic init alembic

# Edit alembic.ini
# sqlalchemy.url = postgresql://user:pass@localhost/docu_chat

# Edit alembic/env.py
from app.database import Base
from app.models.database import Document, ChatHistory
target_metadata = Base.metadata

# Create migration
poetry run alembic revision --autogenerate -m "Initial tables"
poetry run alembic upgrade head
```

**4. Update routers to use database**:
```python
from fastapi import Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.database import Document, ChatHistory

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # ... save file ...

    # Save to database
    doc = Document(
        filename=file.filename,
        file_path=file_path,
        chunks_count=len(chunks),
        status="completed"
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    return {"id": doc.id, "filename": doc.filename}
```

**Success Criteria**:
- ✅ Database tables created
- ✅ Documents tracked in DB
- ✅ Can list all documents
- ✅ Chat history saved

---

### Day 5: Chat History & Sessions (2 hours)

**🎯 Goal**: Save all conversations to database

**What You Already Have**:
- ChatHistory model (from Day 4)

**What You'll Do**:

Update `app/routers/chat.py` to save every Q&A:
```python
@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    rag_service: RAGService = Depends(get_rag_service)
):
    # Query RAG
    result = rag_service.query(request.question, request.document_id)

    # Save to history
    chat_record = ChatHistory(
        document_id=request.document_id,
        question=request.question,
        answer=result["answer"],
        sources_count=len(result["sources"])
    )
    db.add(chat_record)
    db.commit()

    return ChatResponse(**result)
```

Add history endpoint:
```python
@router.get("/history")
async def get_history(db: Session = Depends(get_db)):
    history = db.query(ChatHistory).order_by(ChatHistory.created_at.desc()).limit(50).all()
    return history
```

**Success Criteria**:
- ✅ All Q&A saved to database
- ✅ Can retrieve chat history
- ✅ Timestamps recorded

---

### Day 6: Conversational Context (3-4 hours)

**🎯 Goal**: Enable follow-up questions with context

**What You'll Learn**:
- Session management
- History-aware retrieval
- Question reformulation
- LangChain conversational chains

**What You'll Build**:

**1. Add session_id to schema**:
```python
class ChatRequest(BaseModel):
    question: str
    document_id: Optional[int] = None
    session_id: Optional[str] = None  # NEW

class ChatResponse(BaseModel):
    question: str
    answer: str
    sources: List[dict]
    session_id: str  # NEW
```

**2. Update ChatHistory model**:
```bash
# Add column
poetry run alembic revision --autogenerate -m "Add session_id"
poetry run alembic upgrade head
```

```python
class ChatHistory(Base):
    # ... existing columns ...
    session_id = Column(String(255), index=True, nullable=True)
```

**3. Update chat router**:
```python
import uuid
from langchain_core.messages import AIMessage, HumanMessage

@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest, db: Session, rag_service: RAGService):
    # Generate session ID if not provided
    session_id = request.session_id or str(uuid.uuid4())

    # Retrieve chat history for this session (last 10 messages)
    chat_history_messages = []
    if request.session_id:
        recent_chats = db.query(ChatHistory).filter(
            ChatHistory.session_id == request.session_id
        ).order_by(ChatHistory.created_at.desc()).limit(10).all()

        # Build LangChain message format
        for chat in reversed(recent_chats):
            chat_history_messages.append(HumanMessage(content=chat.question))
            chat_history_messages.append(AIMessage(content=chat.answer))

    # Query with history
    result = rag_service.query(
        question=request.question,
        document_id=request.document_id,
        chat_history=chat_history_messages or None
    )

    # Save with session_id
    chat_record = ChatHistory(
        session_id=session_id,
        document_id=request.document_id,
        question=request.question,
        answer=result["answer"],
        sources_count=len(result["sources"])
    )
    db.add(chat_record)
    db.commit()

    return ChatResponse(**result, session_id=session_id)
```

**4. Update RAG service to handle history**:
```python
from langchain.chains import create_history_aware_retriever
from langchain_core.prompts import MessagesPlaceholder

def query(self, question: str, document_id: Optional[int] = None,
          chat_history: Optional[List] = None):

    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

    if chat_history and len(chat_history) > 0:
        # Contextualize question prompt
        contextualize_q_prompt = ChatPromptTemplate.from_messages([
            ("system", "Given chat history and latest question, "
                      "reformulate it as standalone question."),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])

        # Create history-aware retriever
        history_aware_retriever = create_history_aware_retriever(
            self.llm, retriever, contextualize_q_prompt
        )

        # QA prompt with history
        qa_prompt = ChatPromptTemplate.from_messages([
            ("system", "Use context to answer. {context}"),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])

        question_answer_chain = create_stuff_documents_chain(self.llm, qa_prompt)
        rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

        result = rag_chain.invoke({
            "input": question,
            "chat_history": chat_history
        })
    else:
        # No history - simple QA
        # ... (same as Day 1)

    return result
```

**Test conversational flow**:
```bash
# First question
curl -X POST "http://localhost:8000/chat/" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is ML?"}'
# Response: {"answer": "...", "session_id": "abc-123"}

# Follow-up (use same session_id)
curl -X POST "http://localhost:8000/chat/" \
  -H "Content-Type: application/json" \
  -d '{"question": "Give me an example", "session_id": "abc-123"}'
# Response: Understands "example of ML" from context!
```

**Success Criteria**:
- ✅ Session IDs generated automatically
- ✅ Follow-up questions work with context
- ✅ "it", "that", "the first one" references understood
- ✅ Last 10 messages retrieved per session

**Reference**: Check `/Users/yasithranusha/Developer/docu-chat-api/CONVERSATIONAL_CHAT_GUIDE.md` for detailed explanation

---

### Day 7: Production Ready (2-3 hours)

**🎯 Goal**: Add error handling, logging, testing, deployment

**What You'll Add**:

**1. Logging**:
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info("Processing document...")
logger.error(f"Failed to process: {str(e)}")
```

**2. Error handling**:
```python
from fastapi import HTTPException, status

try:
    result = rag_service.query(...)
except Exception as e:
    logger.error(f"Query failed: {str(e)}")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Error processing query"
    )
```

**3. Configuration management**:
```python
# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    google_api_key: str
    pinecone_api_key: str
    pinecone_index_name: str
    database_url: str

    class Config:
        env_file = ".env"

def get_settings():
    return Settings()
```

**4. Testing with pytest**:
```bash
poetry add --group dev pytest pytest-asyncio httpx
```

```python
# tests/test_api.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "DocuChat API"

def test_chat_endpoint():
    response = client.post(
        "/chat/",
        json={"question": "What is ML?"}
    )
    assert response.status_code == 200
    assert "answer" in response.json()
```

Run tests:
```bash
poetry run pytest
```

**5. Docker deployment**:
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN pip install poetry

COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false && poetry install --no-dev

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - db

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: docu_chat
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

**Success Criteria**:
- ✅ All tests pass
- ✅ Error handling in place
- ✅ Logging configured
- ✅ Docker build succeeds
- ✅ Ready for deployment

---

## 🎯 Daily Checklist

Track your progress:

**Day 1**: Basic RAG
- [ ] Environment setup
- [ ] PDF loading works
- [ ] Chunking implemented
- [ ] Embeddings created
- [ ] FAISS vector store working
- [ ] Questions answered correctly

**Day 2**: Pinecone
- [ ] Pinecone account created
- [ ] Index initialized
- [ ] Embeddings stored in Pinecone
- [ ] Queries return results
- [ ] Data persists after restart

**Day 3**: FastAPI
- [ ] FastAPI app created
- [ ] Upload endpoint works
- [ ] Chat endpoint works
- [ ] Swagger docs accessible
- [ ] CORS configured

**Day 4**: Database
- [ ] Database connected
- [ ] Models defined
- [ ] Migrations working
- [ ] Documents tracked
- [ ] CRUD operations functional

**Day 5**: Chat History
- [ ] ChatHistory saves Q&A
- [ ] History endpoint works
- [ ] Can query past chats

**Day 6**: Conversational
- [ ] Session tracking added
- [ ] History retrieval works
- [ ] Follow-up questions understood
- [ ] Context maintained

**Day 7**: Production
- [ ] Error handling added
- [ ] Logging configured
- [ ] Tests written and passing
- [ ] Docker builds successfully

---

## 💡 Learning Tips

1. **Commit after each day**:
```bash
git add .
git commit -m "Day X: [feature] complete"
```

2. **Take notes**: Write down what you learned, what was hard, aha moments

3. **Experiment**: Change chunk sizes, try different prompts, break things intentionally

4. **Explain to yourself**: If you can't explain it, you don't understand it yet

5. **Reference when stuck**:
   - Check your crash course notes first
   - Then LangChain docs
   - Finally `/Users/yasithranusha/Developer/docu-chat-api`

6. **Don't skip days**: Each builds on the previous

---

## 📚 Resources

- **Your Crash Course**: `/Users/yasithranusha/Developer/Learn/langchain-crash-course`
- **Reference Project**: `/Users/yasithranusha/Developer/docu-chat-api`
- **LangChain Docs**: https://python.langchain.com/docs
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **Pinecone Docs**: https://docs.pinecone.io

---

## 🎉 After Completion

You'll have built:
- ✅ Production RAG system
- ✅ REST API with FastAPI
- ✅ Database-backed chat history
- ✅ Conversational AI with context
- ✅ Docker deployment setup
- ✅ Portfolio-ready project

**Next steps**:
- Add user authentication
- Build a frontend (React/Vue)
- Deploy to AWS/GCP
- Add streaming responses
- Implement RAG evaluation

Good luck! Remember: the struggle is where the learning happens. 💪
