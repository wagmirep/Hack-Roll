"""
tests/conftest.py - Pytest Configuration and Fixtures

PURPOSE:
    Define shared pytest fixtures and configuration for all backend tests.
    Provides test database, mock services, and common test utilities.

RESPONSIBILITIES:
    - Configure test database (SQLite in-memory or test PostgreSQL)
    - Provide FastAPI test client fixture
    - Mock external services (S3, Firebase, Redis)
    - Create sample test data fixtures
    - Clean up after tests

REFERENCED BY:
    - test_sessions.py - Uses client, db fixtures
    - test_processing.py - Uses mock services
    - test_word_counting.py - Uses sample data

REFERENCES:
    - main.py - FastAPI app for test client
    - database.py - Database setup
    - models.py - Model creation

FIXTURES:
    - client: TestClient
        FastAPI test client for HTTP requests

    - db: Session
        Test database session (rolled back after each test)

    - mock_s3: MagicMock
        Mocked S3 storage service

    - mock_redis: MagicMock
        Mocked Redis queue

    - mock_firebase: MagicMock
        Mocked Firebase service

    - sample_session: Session
        Pre-created test session

    - sample_audio: bytes
        Sample audio file for testing

    - sample_transcription: str
        Sample transcription text with Singlish words
"""
