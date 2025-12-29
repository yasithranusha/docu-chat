from pydantic_settings import BaseSettings
from typing import List
from importlib.metadata import version, PackageNotFoundError


class Settings(BaseSettings):
    """
    Automatically loads environment variables from .env file and validates types.
    """

    # API Keys
    GOOGLE_API_KEY: str
    PINECONE_API_KEY: str

    # Pinecone Configuration
    PINECONE_INDEX_NAME: str = "docu-chat"

    # Database
    DATABASE_URL: str

    # Environment
    ENVIRONMENT: str = "development"

    # API Settings
    API_TITLE: str = "DocuChat API"

    # Upload Settings
    MAX_FILE_SIZE_MB: int = 10
    UPLOAD_DIR: str = "./uploads"

    # Logging
    LOG_LEVEL: str = "INFO"

    # CORS - converts comma-separated string to list
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def api_version(self) -> str:
        """
        Reads version from pyproject.toml via installed package metadata.
        Falls back to development version if package not installed.
        """
        try:
            return version("docu-chat")
        except PackageNotFoundError:
            return "0.1.0-dev"

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()

def get_settings() -> Settings:
    """ FastAPI dependency for settings """
    return settings