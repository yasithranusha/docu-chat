from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List


class ChatRequest(BaseModel):
    """Request schema for chat endpoint"""
    question: str = Field(min_length=1, description="Question to ask about documents")
    document_id: Optional[int] = Field(None, description="Optional document ID to search within")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity (UUID)")


class ChatResponse(BaseModel):
    """Response schema for chat endpoint"""
    question: str
    answer: str
    session_id: str = Field(description="Session ID for this conversation")
    sources: List[dict]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question": "What is this document about?",
                "answer": "This document discusses...",
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "sources": [{"content": "...", "metadata": {}}]
            }
        }
    )
