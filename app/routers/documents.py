import os
import shutil
import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Document, DocumentStatus
from app.schemas import DocumentUploadResponse, DocumentResponse
from app.services import RAGService, get_rag_service
from app.config import settings

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=201,
    summary="Upload and process PDF document",
    description="Upload a PDF document, process it into chunks, and store in vector database"
)
async def upload_document(
    file: UploadFile = File(..., description="PDF file to upload"),
    db: Session = Depends(get_db),
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Upload and process a PDF document:
    1. Validate file type (.pdf only)
    2. Save file to disk with unique filename
    3. Create database record with status=PENDING
    4. Process document into chunks (status=PROCESSING)
    5. Update status to COMPLETED or FAILED
    """
    # Validate file type
    if not file.filename or not file.filename.endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are allowed")

    # Sanitize filename (prevent path traversal)
    safe_filename = Path(file.filename).name

    # Create unique filename (prevent overwrites)
    unique_id = uuid.uuid4().hex[:8]
    unique_filename = f"{unique_id}_{safe_filename}"

    # Ensure uploads directory exists
    upload_dir = settings.UPLOAD_DIR
    os.makedirs(upload_dir, exist_ok=True)

    # Build full path
    file_path = os.path.join(upload_dir, unique_filename)

    # Create database record with status=PENDING
    db_document = Document(
        filename=safe_filename,
        file_path=file_path,
        status=DocumentStatus.PENDING
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)

    try:
        # Save file to disk
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            # Update status to FAILED
            db_document.status = DocumentStatus.FAILED
            db.commit()
            raise HTTPException(500, f"Failed to save file: {str(e)}")
        finally:
            await file.close()

        # Update status to PROCESSING
        db_document.status = DocumentStatus.PROCESSING
        db.commit()

        # Process with RAG service
        chunks = rag_service.process_pdf(file_path, db_document.id)

        # Update status to COMPLETED
        db_document.chunks_count = chunks
        db_document.status = DocumentStatus.COMPLETED
        db.commit()
        db.refresh(db_document)

        # Return success response
        return DocumentUploadResponse(
            message="Document uploaded and processed successfully",
            document=DocumentResponse.model_validate(db_document)
        )

    except Exception as e:
        # Update status to FAILED on any error
        db_document.status = DocumentStatus.FAILED
        db.commit()

        # Clean up file if it exists
        if os.path.exists(file_path):
            os.remove(file_path)

        raise HTTPException(500, f"Failed to process document: {str(e)}")