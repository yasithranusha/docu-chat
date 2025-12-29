import os
import shutil
import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException

from app.services import RAGService, get_rag_service

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.post("/upload")
async def upload_document(
        file: UploadFile = File(...),
        rag_service: RAGService = Depends(get_rag_service)
):
    # Validate file type
    if not file.filename.endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are allowed")

    # Sanitize filename (prevent path traversal)
    safe_filename = Path(file.filename).name

    # Create unique filename (prevent overwrites)
    unique_id = uuid.uuid4().hex[:8]
    unique_filename = f"{unique_id}_{safe_filename}"

    # Ensure uploads directory exists
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)

    # Build full path
    file_path = os.path.join(upload_dir, unique_filename)

    # Save file to disk
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(500, f"Failed to save file: {str(e)}")
    finally:
        await file.close()  # Important: close the upload

    # Process with RAG service
    chunks = rag_service.process_pdf(file_path, document_id=1)

    return {
        "filename": safe_filename,
        "saved_as": unique_filename,
        "chunks": chunks
    }