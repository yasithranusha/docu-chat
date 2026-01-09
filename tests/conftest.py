"""
Pytest configuration and shared fixtures.
This file is automatically loaded by pytest.
"""
import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, get_db


# Single test database for all tests
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Set up test database once for entire test session"""
    # Create tables
    Base.metadata.create_all(bind=engine)
    # Override app dependency
    app.dependency_overrides[get_db] = override_get_db
    yield
    # Cleanup after all tests
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def cleanup_database():
    """Clean up database before each test"""
    # Drop and recreate all tables for clean state
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    # No cleanup needed here - handled by session-level fixture


@pytest.fixture(autouse=True)
def set_test_environment():
    """Set environment variables for testing"""
    os.environ["ENVIRONMENT"] = "testing"
    os.environ["DATABASE_URL"] = "sqlite:///./test.db"
    os.environ["GOOGLE_API_KEY"] = "test-google-key"
    os.environ["PINECONE_API_KEY"] = "test-pinecone-key"
    os.environ["PINECONE_INDEX_NAME"] = "test-index"


@pytest.fixture(scope="session")
def test_client():
    """Shared test client for all tests"""
    return TestClient(app)


@pytest.fixture(scope="session")
def test_pdf_content():
    """Reusable fake PDF content for testing"""
    return b"%PDF-1.4\n%\xE2\xE3\xCF\xD3\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/Resources <<\n/Font <<\n/F1 4 0 R\n>>\n>>\n/MediaBox [0 0 612 792]\n/Contents 5 0 R\n>>\nendobj\n4 0 obj\n<<\n/Type /Font\n/Subtype /Type1\n/BaseFont /Helvetica\n>>\nendobj\n5 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n100 700 Td\n(Test PDF) Tj\nET\nendstream\nendobj\nxref\n0 6\n0000000000 65535 f\n0000000015 00000 n\n0000000068 00000 n\n0000000125 00000 n\n0000000277 00000 n\n0000000361 00000 n\ntrailer\n<<\n/Size 6\n/Root 1 0 R\n>>\nstartxref\n453\n%%EOF"


@pytest.fixture
def db_session():
    """Provide a database session for direct database queries in tests"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
