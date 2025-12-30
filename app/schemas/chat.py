"""Chat request and response schemas"""
from pydantic import BaseModel, Field
from typing import Optional, List


class ChatRequest(BaseModel):
    """Request schema for chat endpoint"""
    question: str = Field(min_length=1, description="Question to ask about documents")
    document_id: Optional[int] = Field(None, description="Optional document ID to search within")


class ChatResponse(BaseModel):
    """Response schema for chat endpoint"""
    question: str
    answer: str
    sources: List[dict]
