from fastapi import APIRouter, Depends
from app.models import ChatRequest, ChatResponse
from app.services import RAGService, get_rag_service

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("/", response_model=ChatResponse)
async def chat(
        request:ChatRequest,
        rag_service: RAGService = Depends(get_rag_service)
):
    result = rag_service.query(request.question, request.document_id)
    return ChatResponse(**result)