from fastapi import Depends
from sqlalchemy.orm import Session
from pinecone import Pinecone
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings

from app.database import get_db
from app.config import settings
from .rag_service import RAGService
from .agent_rag_service import AgentRAGService


# Singleton instances for expensive resources
_pinecone_client = None
_embeddings = None
_llm = None


def get_pinecone_client() -> Pinecone:
    """Get or create Pinecone client singleton"""
    global _pinecone_client
    if _pinecone_client is None:
        _pinecone_client = Pinecone(api_key=settings.PINECONE_API_KEY)
    return _pinecone_client


def get_embeddings() -> HuggingFaceEmbeddings:
    """Get or create HuggingFace embeddings singleton (384 dimensions, free, runs locally)"""
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2"  # Fast, high quality, 384 dimensions
        )
    return _embeddings


def get_llm() -> ChatGoogleGenerativeAI:
    """Get or create Chat LLM singleton"""
    global _llm
    if _llm is None:
        _llm = ChatGoogleGenerativeAI(
            model="gemini-pro",
            temperature=0.3,
            google_api_key=settings.GOOGLE_API_KEY
        )
    return _llm


def get_rag_service(
    db: Session = Depends(get_db),
    pinecone_client: Pinecone = Depends(get_pinecone_client),
    embeddings: HuggingFaceEmbeddings = Depends(get_embeddings),
    llm: ChatGoogleGenerativeAI = Depends(get_llm)
) -> RAGService:
    """
    Dependency injection factory for RAGService (Classic Chains).
    Injects all dependencies using FastAPI's Depends system.
    """
    return RAGService(
        db=db,
        pinecone_client=pinecone_client,
        index_name=settings.PINECONE_INDEX_NAME,
        embeddings=embeddings,
        llm=llm
    )


def get_agent_rag_service(
    db: Session = Depends(get_db),
    pinecone_client: Pinecone = Depends(get_pinecone_client),
    embeddings: HuggingFaceEmbeddings = Depends(get_embeddings),
    llm: ChatGoogleGenerativeAI = Depends(get_llm)
) -> AgentRAGService:
    """
    Dependency injection factory for AgentRAGService (Modern Agents).

    EXACT SAME pattern as get_rag_service() - same parameters, same order.
    Shares singleton resources (LLM, embeddings) with classic service.
    """
    return AgentRAGService(
        db=db,
        pinecone_client=pinecone_client,
        index_name=settings.PINECONE_INDEX_NAME,
        embeddings=embeddings,
        llm=llm
    )


__all__ = [
    "RAGService",
    "AgentRAGService",
    "get_rag_service",
    "get_agent_rag_service",
    "get_pinecone_client",
    "get_embeddings",
    "get_llm"
]
