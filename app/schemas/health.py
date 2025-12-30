"""Health and system info response schemas"""
from pydantic import BaseModel, Field, ConfigDict


class RootResponse(BaseModel):
    message: str = Field(description="API title")
    version: str = Field(description="API version")
    environment: str = Field(description="Current environment")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "DocuChat API",
                "version": "0.1.0",
                "environment": "development"
            }
        }
    )


class HealthResponse(BaseModel):
    status: str = Field(description="Service health status")
    timestamp: str = Field(description="Current UTC timestamp in ISO format")
    version: str = Field(description="API version")
    environment: str = Field(description="Current environment")
    service: str = Field(description="Service identifier")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "timestamp": "2025-12-30T08:47:17.590908",
                "version": "0.1.0",
                "environment": "development",
                "service": "docu-chat-api"
            }
        }
    )
