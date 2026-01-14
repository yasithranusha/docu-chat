from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import ChatRequest, ChatResponse
from app.services import RAGService, get_rag_service
from .chat_common import process_chat_request

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post(
    "/",
    response_model=ChatResponse,
    summary="Ask a question about documents (classic chains)",
    description="""
    Classic chain-based RAG with conversational context.

    - Always retrieves documents first
    - Then generates answer
    - Simple, predictable, fast (1 LLM call)
    - Good for pure Q&A

    Use the same session_id for follow-up questions to maintain context.
    """
)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Chat endpoint using classic chain-based RAG.

    Always retrieves documents and generates an answer.
    Best for straightforward document Q&A.
    """
    return await process_chat_request(
        request=request,
        db=db,
        rag_service=rag_service,
        service_type="Classic RAG"
    )