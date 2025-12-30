from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from app.routers import api_router
from app.config import settings
from app.schemas import RootResponse, HealthResponse

app = FastAPI(
    title=settings.API_TITLE,
    version=settings.api_version,
    description="AI-powered document Q&A system using RAG (Retrieval-Augmented Generation) with LangChain, Google Gemini, and Pinecone.",
    contact={
        "name": "Yasith Silva",
        "email": "yasithranusha24@gmail.com",
        "url": "https://github.com/yasithranusha"
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    },
    openapi_tags=[
        {"name": "Health", "description": "Health checks and system info"},
        {"name": "Documents", "description": "Document upload and management"},
        {"name": "Chat", "description": "Q&A with conversational context"}
    ]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.get(
    "/",
    response_model=RootResponse,
    tags=["Health"],
    summary="Get API Information",
    description="Returns API version, title, and current environment."
)
def read_root() -> RootResponse:
    """Get API information"""
    return RootResponse(
        message=settings.API_TITLE,
        version=settings.api_version,
        environment=settings.ENVIRONMENT
    )


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Health Check",
    description="Returns service health status with timestamp, version, and environment info. Used for monitoring and load balancers."
)
def health_check() -> HealthResponse:
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        version=settings.api_version,
        environment=settings.ENVIRONMENT,
        service="docu-chat-api"
    )