import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_read_root():
    """Test root endpoint returns API information"""
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "environment" in data


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data
    assert "environment" in data
    assert data["service"] == "docu-chat-api"


def test_invalid_endpoint():
    """Test that invalid endpoints return 404"""
    response = client.get("/invalid-endpoint")

    assert response.status_code == 404


def test_upload_without_file():
    """Test document upload without file returns error"""
    response = client.post("/documents/upload")

    assert response.status_code == 422  # Unprocessable Entity


def test_upload_non_pdf():
    """Test uploading non-PDF file returns error"""
    # Create a fake text file
    files = {"file": ("test.txt", b"This is not a PDF", "text/plain")}
    response = client.post("/documents/upload", files=files)

    assert response.status_code == 400
    assert "PDF" in response.json()["detail"]


def test_chat_without_question():
    """Test chat endpoint without question returns error"""
    response = client.post(
        "/chat/",
        json={}
    )

    assert response.status_code == 422  # Validation error


def test_chat_with_empty_question():
    """Test chat endpoint with empty question returns error"""
    response = client.post(
        "/chat/",
        json={"question": ""}
    )

    assert response.status_code == 422  # Validation error (min_length=1)


# Note: Testing actual PDF processing and chat responses would require
# mocking the RAG service and database, which is beyond basic testing.
# These tests verify the API structure and validation works correctly.
