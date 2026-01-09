import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.database import get_db
from app.models import ChatHistory
from app.schemas import ChatRequest, ChatResponse
from app.services import RAGService, get_rag_service
from app.logger import get_logger

logger = get_logger(__name__)

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

    logger.info(
        f"Chat request - Session: {session_id[:8]}... - "
        f"Question length: {len(request.question)} chars"
    )

    try:
        # Query RAG service (includes conversational context)
        result = rag_service.query(
            question=request.question,
            session_id=session_id,
            document_id=request.document_id
        )

        logger.info(
            f"RAG query successful - Session: {session_id[:8]}... - "
            f"Sources found: {len(result.get('sources', []))}"
        )

    except Exception as e:
        logger.error(
            f"RAG query failed - Session: {session_id[:8]}... - "
            f"Error: {type(e).__name__} - {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process question: {str(e)}"
        )

    # Save to database
    try:
        chat_history = ChatHistory(
            document_id=request.document_id,
            session_id=session_id,
            question=request.question,
            answer=result["answer"],
            sources_count=len(result.get("sources", []))
        )
        db.add(chat_history)
        db.commit()

        logger.info(f"Chat history saved - Session: {session_id[:8]}...")

    except SQLAlchemyError as e:
        logger.error(f"Failed to save chat history: {str(e)}")
        db.rollback()
        # Don't fail the request, just log the error
        logger.warning("Continuing despite database save failure")

    # Return response with session_id
    return ChatResponse(
        question=result["question"],
        answer=result["answer"],
        session_id=result["session_id"],
        sources=result.get("sources", [])
    )