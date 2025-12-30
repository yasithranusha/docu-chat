import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ChatHistory
from app.schemas import ChatRequest, ChatResponse
from app.services import RAGService, get_rag_service

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post(
    "/",
    response_model=ChatResponse,
    summary="Ask a question about documents",
    description="Ask questions with optional conversational context via session_id"
)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Chat endpoint with conversational context:
    1. Generate or use provided session_id
    2. Query RAG service
    3. Save question + answer to database
    4. Return answer with session_id

    Use the same session_id for follow-up questions to maintain context.
    """
    # Generate session_id if not provided
    session_id = request.session_id or str(uuid.uuid4())

    # Query RAG service
    result = rag_service.query(request.question, request.document_id)

    # Save to database
    chat_history = ChatHistory(
        document_id=request.document_id,
        session_id=session_id,
        question=request.question,
        answer=result["answer"],
        sources_count=len(result.get("sources", []))
    )
    db.add(chat_history)
    db.commit()

    # Return response with session_id
    return ChatResponse(
        question=result["question"],
        answer=result["answer"],
        session_id=session_id,
        sources=result.get("sources", [])
    )