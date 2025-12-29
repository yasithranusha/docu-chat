from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import api_router
from app.config import settings

app = FastAPI(
    title=settings.API_TITLE,
    version=settings.api_version
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.get("/")
def read_root():
    return {
        "message": settings.API_TITLE,
        "version": settings.api_version,
        "environment": settings.ENVIRONMENT
    }