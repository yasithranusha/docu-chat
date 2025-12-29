from pydantic import BaseModel, Field
from typing import Optional, List

class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1)
    document_id: Optional[int] = None

class ChatResponse(BaseModel):
    question: str
    answer: str
    sources: List[dict]

