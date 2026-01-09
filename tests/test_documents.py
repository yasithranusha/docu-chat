import pytest
from unittest.mock import Mock, MagicMock, patch
from fastapi.testclient import TestClient
from io import BytesIO

from app.main import app
from app.models import Document, DocumentStatus
from app.services import get_rag_service

client = TestClient(app)


@pytest.fixture
def mock_rag_service():
    """Mock RAG service for testing"""
    mock_service = Mock()
    mock_service.process_pdf.return_value = 42  # Return 42 chunks
    return mock_service


def test_upload_pdf_success(mock_rag_service):
    """Test successful PDF upload and processing"""

    # Override RAG service dependency
    app.dependency_overrides[get_rag_service] = lambda: mock_rag_service

    # Create a fake PDF file
    pdf_content = b"%PDF-1.4\n%Fake PDF content for testing"
    files = {"file": ("test_document.pdf", BytesIO(pdf_content), "application/pdf")}

    # Make upload request
    response = client.post("/documents/upload", files=files)

    # Assertions
    assert response.status_code == 201
    data = response.json()

    assert data["message"] == "Document uploaded and processed successfully"
    assert data["document"]["filename"] == "test_document.pdf"
    assert data["document"]["status"] == "completed"
    assert data["document"]["chunks_count"] == 42
    assert "id" in data["document"]

    # Verify RAG service was called
    mock_rag_service.process_pdf.assert_called_once()

    # Clean up override
    app.dependency_overrides.pop(get_rag_service)


def test_upload_pdf_processing_failure(mock_rag_service, db_session):
    """Test PDF upload when processing fails"""

    # Configure mock to raise an exception
    mock_rag_service.process_pdf.side_effect = Exception("Processing failed")

    app.dependency_overrides[get_rag_service] = lambda: mock_rag_service

    # Create a fake PDF file
    pdf_content = b"%PDF-1.4\n%Fake PDF content"
    files = {"file": ("test.pdf", BytesIO(pdf_content), "application/pdf")}

    # Make upload request
    response = client.post("/documents/upload", files=files)

    # Should return 500 error
    assert response.status_code == 500
    assert "Failed to process document" in response.json()["detail"]

    # Verify document status is FAILED in database
    doc = db_session.query(Document).first()
    assert doc is not None
    assert doc.status == DocumentStatus.FAILED

    app.dependency_overrides.pop(get_rag_service)


def test_upload_invalid_file_type():
    """Test uploading non-PDF file"""
    files = {"file": ("test.txt", BytesIO(b"Not a PDF"), "text/plain")}

    response = client.post("/documents/upload", files=files)

    assert response.status_code == 400
    assert "PDF" in response.json()["detail"]


def test_upload_without_file():
    """Test upload endpoint without file"""
    response = client.post("/documents/upload")

    assert response.status_code == 422


def test_document_status_tracking(mock_rag_service, db_session):
    """Test that document status is tracked correctly through processing"""

    def check_status_progression(file_path, document_id):
        """Mock that checks document status during processing"""
        doc = db_session.query(Document).filter(Document.id == document_id).first()

        # Should be PROCESSING when this is called
        assert doc.status == DocumentStatus.PROCESSING

        return 10  # Return chunk count

    mock_rag_service.process_pdf.side_effect = check_status_progression
    app.dependency_overrides[get_rag_service] = lambda: mock_rag_service

    # Upload PDF
    pdf_content = b"%PDF-1.4\n%Test"
    files = {"file": ("status_test.pdf", BytesIO(pdf_content), "application/pdf")}

    response = client.post("/documents/upload", files=files)

    assert response.status_code == 201

    # Final status should be COMPLETED
    data = response.json()
    assert data["document"]["status"] == "completed"

    app.dependency_overrides.pop(get_rag_service)


@patch('os.remove')
@patch('os.path.exists')
def test_file_cleanup_on_error(mock_exists, mock_remove, mock_rag_service):
    """Test that uploaded files are cleaned up when processing fails"""

    mock_exists.return_value = True
    mock_rag_service.process_pdf.side_effect = Exception("Processing error")

    app.dependency_overrides[get_rag_service] = lambda: mock_rag_service

    pdf_content = b"%PDF-1.4\n%Test"
    files = {"file": ("cleanup_test.pdf", BytesIO(pdf_content), "application/pdf")}

    response = client.post("/documents/upload", files=files)

    # Should fail
    assert response.status_code == 500

    # Verify cleanup was attempted
    assert mock_remove.called

    app.dependency_overrides.pop(get_rag_service)
