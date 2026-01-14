from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import ChatRequest, ChatResponse
from app.services import AgentRAGService, get_agent_rag_service
from .chat_common import process_chat_request

router = APIRouter(prefix="/agent", tags=["Agent Chat (Modern)"])


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=200,
    summary="Chat using modern agent (decides when to retrieve)",
    description="""
    Modern agent-based RAG that decides when to retrieve documents.

    Differences from /chat/ (classic):
    - Agent decides whether to retrieve or respond directly
    - Can handle greetings without unnecessary retrieval
    - More flexible for complex multi-step reasoning
    - Slightly higher latency (2 LLM calls vs 1)

    Try these examples:
    - "Hello!" → Agent responds without retrieval
    - "What is in the document?" → Agent retrieves then answers
    """
)
async def agent_chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    agent_service: AgentRAGService = Depends(get_agent_rag_service)
):
    """
    Chat using agent-based RAG (modern approach).

    The agent will intelligently decide whether to use retrieval or not.
    """
    return await process_chat_request(
        request=request,
        db=db,
        rag_service=agent_service,
        service_type="Agent"
    )


@router.get(
    "/compare",
    summary="Compare classic chains vs modern agents",
    description="Explains when to use each approach"
)
async def compare_approaches():
    """
    Compare classic chain-based RAG vs modern agent-based RAG.
    """
    return {
        "classic_chains": {
            "endpoint": "/chat/",
            "pattern": "Fixed pipeline: Always retrieve → Always answer",
            "advantages": [
                "Lower latency (1 LLM call)",
                "Predictable behavior",
                "Simple to debug",
                "Good for pure Q&A"
            ],
            "disadvantages": [
                "Wastes retrieval on greetings",
                "Can't do multi-step reasoning",
                "Fixed workflow"
            ],
            "use_when": [
                "Pure document Q&A",
                "Predictable queries",
                "Latency critical",
                "Simple use cases"
            ]
        },
        "modern_agents": {
            "endpoint": "/agent/chat",
            "pattern": "Dynamic: Agent decides when to retrieve",
            "advantages": [
                "Handles greetings without retrieval",
                "Multi-step reasoning",
                "Can use multiple tools",
                "More flexible"
            ],
            "disadvantages": [
                "Higher latency (2+ LLM calls)",
                "Less predictable",
                "Harder to debug",
                "More complex"
            ],
            "use_when": [
                "Conversational AI",
                "Complex queries",
                "Multiple data sources",
                "Production chatbots"
            ]
        },
        "recommendation": "Start with classic chains, migrate to agents when you need flexibility"
    }
