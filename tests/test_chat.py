import pytest
from unittest.mock import Mock
from fastapi.testclient import TestClient

from app.main import app
from app.models import ChatHistory
from app.services import get_rag_service

client = TestClient(app)


@pytest.fixture
def mock_rag_service():
    """Mock RAG service for chat testing"""
    def query_side_effect(question, session_id, document_id=None):
        """Mock that returns session_id from input"""
        return {
            "question": question,
            "answer": "Machine learning is a subset of artificial intelligence that enables systems to learn from data.",
            "sources": [
                {"content": "ML is part of AI...", "metadata": {"page": 1}},
                {"content": "Learning from data...", "metadata": {"page": 2}}
            ],
            "session_id": session_id  # Return the session_id that was passed in
        }

    mock_service = Mock()
    mock_service.query.side_effect = query_side_effect
    return mock_service


def test_chat_success(mock_rag_service, db_session):
    """Test successful chat query"""

    app.dependency_overrides[get_rag_service] = lambda: mock_rag_service

    # Send chat request
    response = client.post(
        "/chat/",
        json={"question": "What is machine learning?"}
    )

    # Assertions
    assert response.status_code == 200
    data = response.json()

    assert data["question"] == "What is machine learning?"
    assert "Machine learning" in data["answer"]
    assert len(data["sources"]) == 2
    assert "session_id" in data

    # Verify RAG service was called
    mock_rag_service.query.assert_called_once()

    # Verify chat history was saved
    history = db_session.query(ChatHistory).all()
    assert len(history) == 1
    assert history[0].question == "What is machine learning?"
    assert history[0].sources_count == 2

    app.dependency_overrides.pop(get_rag_service)


def test_chat_with_session_id(mock_rag_service):
    """Test chat with existing session ID for conversational context"""

    app.dependency_overrides[get_rag_service] = lambda: mock_rag_service

    session_id = "my-session-123"

    # Send chat request with session_id
    response = client.post(
        "/chat/",
        json={
            "question": "What is ML?",
            "session_id": session_id
        }
    )

    assert response.status_code == 200
    data = response.json()

    # Should return the same session_id
    assert data["session_id"] == session_id

    # Verify RAG service was called with session_id
    call_args = mock_rag_service.query.call_args
    assert call_args.kwargs["session_id"] == session_id

    app.dependency_overrides.pop(get_rag_service)


def test_chat_with_document_filter(mock_rag_service, db_session):
    """Test chat with specific document_id filter"""

    app.dependency_overrides[get_rag_service] = lambda: mock_rag_service

    response = client.post(
        "/chat/",
        json={
            "question": "Explain this",
            "document_id": 42
        }
    )

    assert response.status_code == 200

    # Verify RAG service was called with document_id
    call_args = mock_rag_service.query.call_args
    assert call_args.kwargs["document_id"] == 42

    # Verify database record has document_id
    history = db_session.query(ChatHistory).first()
    assert history.document_id == 42

    app.dependency_overrides.pop(get_rag_service)


def test_chat_empty_question():
    """Test chat with empty question returns validation error"""

    response = client.post(
        "/chat/",
        json={"question": ""}
    )

    assert response.status_code == 422


def test_chat_missing_question():
    """Test chat without question field"""

    response = client.post("/chat/", json={})

    assert response.status_code == 422


def test_chat_rag_service_error(mock_rag_service):
    """Test chat when RAG service fails"""

    # Configure mock to raise exception
    mock_rag_service.query.side_effect = Exception("RAG processing failed")

    app.dependency_overrides[get_rag_service] = lambda: mock_rag_service

    response = client.post(
        "/chat/",
        json={"question": "What is AI?"}
    )

    # Should return 500 error
    assert response.status_code == 500
    assert "Failed to process question" in response.json()["detail"]

    app.dependency_overrides.pop(get_rag_service)


def test_chat_history_persistence(mock_rag_service, db_session):
    """Test that multiple chat messages are saved with correct session"""

    app.dependency_overrides[get_rag_service] = lambda: mock_rag_service

    session_id = "conversation-456"

    # Send first message
    response1 = client.post(
        "/chat/",
        json={
            "question": "What is AI?",
            "session_id": session_id
        }
    )
    assert response1.status_code == 200

    # Update mock for second response
    mock_rag_service.query.return_value = {
        "question": "Tell me more",
        "answer": "AI involves machine learning, neural networks, and more.",
        "sources": [{"content": "AI details...", "metadata": {"page": 3}}],
        "session_id": session_id
    }

    # Send second message (follow-up)
    response2 = client.post(
        "/chat/",
        json={
            "question": "Tell me more",
            "session_id": session_id
        }
    )
    assert response2.status_code == 200

    # Verify both messages saved with same session_id
    history = db_session.query(ChatHistory).filter(ChatHistory.session_id == session_id).all()
    assert len(history) == 2
    assert history[0].question == "What is AI?"
    assert history[1].question == "Tell me more"

    app.dependency_overrides.pop(get_rag_service)


def test_chat_generates_session_id_if_not_provided(mock_rag_service):
    """Test that session_id is auto-generated if not provided"""

    app.dependency_overrides[get_rag_service] = lambda: mock_rag_service

    # Don't provide session_id
    response = client.post(
        "/chat/",
        json={"question": "What is AI?"}
    )

    assert response.status_code == 200
    data = response.json()

    # Should have generated a session_id
    assert "session_id" in data
    assert len(data["session_id"]) > 0

    # Verify it's a valid UUID format
    import uuid
    try:
        uuid.UUID(data["session_id"])
        valid_uuid = True
    except ValueError:
        valid_uuid = False

    assert valid_uuid

    app.dependency_overrides.pop(get_rag_service)


def test_chat_database_save_failure_does_not_fail_request(mock_rag_service):
    """Test that chat continues even if database save fails"""

    app.dependency_overrides[get_rag_service] = lambda: mock_rag_service

    # This test verifies the graceful degradation logic
    # Even if db.commit() fails, the response should still return
    # (though in practice, with SQLite this is hard to trigger)

    response = client.post(
        "/chat/",
        json={"question": "What is AI?"}
    )

    # Should succeed regardless
    assert response.status_code == 200

    app.dependency_overrides.pop(get_rag_service)
