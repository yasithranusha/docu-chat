from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import List, Optional
from app.models import DocumentStatus


class DocumentBase(BaseModel):
    filename: str = Field(min_length=1, max_length=255, description="Original filename")

class DocumentCreate(DocumentBase):
    """
    Note: file is handled by UploadFile, this is for additional metadata if needed
    """
    pass

class DocumentResponse(DocumentBase):
    id: int
    upload_date: datetime
    chunks_count: int
    status: DocumentStatus

    model_config = ConfigDict(
        from_attributes=True,  # Allows conversion from ORM model
        json_schema_extra={
            "example": {
                "id": 1,
                "filename": "python_guide.pdf",
                "upload_date": "2025-12-31T10:00:00Z",
                "chunks_count": 42,
                "status": "completed"
            }
        }
    )


class DocumentUploadResponse(BaseModel):
    message: str = Field(description="Success message")
    document: DocumentResponse

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Document uploaded and processed successfully",
                "document": {
                    "id": 1,
                    "filename": "python_guide.pdf",
                    "upload_date": "2025-12-31T10:00:00Z",
                    "chunks_count": 42,
                    "status": "completed"
                }
            }
        }
    )


class DocumentListResponse(BaseModel):
    total: int = Field(ge=0, description="Total number of documents")
    documents: List[DocumentResponse]
    page: int = Field(ge=1, description="Current page number")
    page_size: int = Field(ge=1, le=100, description="Number of items per page")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 10,
                "documents": [
                    {
                        "id": 1,
                        "filename": "python_guide.pdf",
                        "upload_date": "2025-12-31T10:00:00Z",
                        "chunks_count": 42,
                        "status": "completed"
                    }
                ],
                "page": 1,
                "page_size": 10
            }
        }
    )


class DocumentDeleteResponse(BaseModel):
    message: str = Field(description="Success message")
    deleted_id: int = Field(description="ID of deleted document")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Document deleted successfully",
                "deleted_id": 1
            }
        }
    )
