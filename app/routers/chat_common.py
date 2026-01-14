import uuid
from typing import Protocol
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models import ChatHistory
from app.schemas import ChatRequest, ChatResponse
from app.logger import get_logger

logger = get_logger(__name__)


class RAGServiceProtocol(Protocol):
    """Protocol for RAG services"""
    def query(self, question: str, session_id: str, document_id: int = None) -> dict:
        """Query the RAG service"""
        ...


async def process_chat_request(
    request: ChatRequest,
    db: Session,
    rag_service: RAGServiceProtocol,
    service_type: str = "RAG"
) -> ChatResponse:
    """
    Common logic for processing chat requests.

    Args:
        request: Chat request with question and optional session_id
        db: Database session
        rag_service: RAG service instance (classic or agent)
        service_type: String for logging ("RAG" or "Agent")

    Returns:
        ChatResponse with answer and sources
    """
    # Generate session_id if not provided
    session_id = request.session_id or str(uuid.uuid4())

    logger.info(
        f"{service_type} chat request - Session: {session_id[:8]}... - "
        f"Question: {request.question[:50]}..."
    )

    try:
        # Query service (classic or agent)
        result = rag_service.query(
            question=request.question,
            session_id=session_id,
            document_id=request.document_id
        )

        logger.info(
            f"{service_type} response - Session: {session_id[:8]}... - "
            f"Sources: {len(result.get('sources', []))}"
        )

    except Exception as e:
        logger.error(
            f"{service_type} query failed - Session: {session_id[:8]}... - "
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

        logger.info(f"{service_type} chat history saved - Session: {session_id[:8]}...")

    except SQLAlchemyError as e:
        logger.error(f"Failed to save {service_type} chat history: {str(e)}")
        db.rollback()
        # Graceful degradation - continue despite database failure
        logger.warning("Continuing despite database save failure")

    # Return response
    return ChatResponse(
        question=request.question,
        answer=result["answer"],
        sources=result.get("sources", []),
        session_id=session_id
    )
