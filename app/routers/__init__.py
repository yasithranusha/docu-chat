from fastapi import APIRouter
from .chat import router as chat_router
from .documents import router as documents_router
from .agent_chat import router as agent_chat_router

# Combined API router - includes all sub-routers
api_router = APIRouter()
api_router.include_router(chat_router)
api_router.include_router(documents_router)
api_router.include_router(agent_chat_router)  # Day 8: Modern agent-based chat

__all__ = [
    "api_router",
    "chat_router",
    "documents_router",
    "agent_chat_router"
]
