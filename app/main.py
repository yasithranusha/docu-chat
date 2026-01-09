from dotenv import load_dotenv

load_dotenv()

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
from app.routers import api_router
from app.config import settings
from app.schemas import RootResponse, HealthResponse
from app.logger import get_logger
import time

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for startup and shutdown events.
    Replaces deprecated @app.on_event decorators.
    """
    # Startup
    logger.info(f"Starting {settings.API_TITLE} v{settings.api_version}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Pinecone Index: {settings.PINECONE_INDEX_NAME}")

    yield

    # Shutdown
    logger.info(f"Shutting down {settings.API_TITLE}")

app = FastAPI(
    title=settings.API_TITLE,
    version=settings.api_version,
    description="AI-powered document Q&A system using RAG (Retrieval-Augmented Generation) with LangChain, Google Gemini, and Pinecone.",
    lifespan=lifespan,  # Modern lifespan event handler
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


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests and responses"""
    start_time = time.time()

    # Log request
    logger.info(f"Request: {request.method} {request.url.path}")

    try:
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Log response
        logger.info(
            f"Response: {request.method} {request.url.path} "
            f"- Status: {response.status_code} - Duration: {duration:.3f}s"
        )

        return response

    except Exception as e:
        logger.error(f"Request failed: {request.method} {request.url.path} - Error: {str(e)}")
        raise


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions"""
    logger.error(
        f"Unhandled exception: {type(exc).__name__} - {str(exc)} "
        f"- Path: {request.url.path}"
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error occurred",
            "error_type": type(exc).__name__
        }
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