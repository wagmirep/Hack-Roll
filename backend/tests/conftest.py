"""
tests/conftest.py - Pytest Configuration and Fixtures

Provides test database, mock services, and common test utilities.
"""

import os
import sys
import uuid
import pytest
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock, patch
from decimal import Decimal

# Set test environment variables BEFORE importing config
os.environ["SUPABASE_URL"] = "https://test-project.supabase.co"
os.environ["SUPABASE_JWT_SECRET"] = "test-jwt-secret-for-testing-only"
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "test-service-role-key"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379"
os.environ["HUGGINGFACE_TOKEN"] = "test-hf-token"

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base
from models import Profile, Group, Session, SessionSpeaker, AudioChunk


# Test database setup (in-memory SQLite)
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def db_engine():
    """Create test database engine."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db(db_engine):
    """Create test database session."""
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=db_engine
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def sample_user(db):
    """Create a sample user profile."""
    user = Profile(
        id=uuid.uuid4(),
        username="testuser",
        display_name="Test User",
    )
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def sample_group(db, sample_user):
    """Create a sample group."""
    group = Group(
        id=uuid.uuid4(),
        name="Test Group",
        created_by=sample_user.id,
        invite_code="TEST123",
    )
    db.add(group)
    db.commit()
    return group


@pytest.fixture
def sample_session(db, sample_user, sample_group):
    """Create a sample recording session."""
    session = Session(
        id=uuid.uuid4(),
        group_id=sample_group.id,
        started_by=sample_user.id,
        status="recording",
        progress=0,
    )
    db.add(session)
    db.commit()
    return session


@pytest.fixture
def sample_chunks(db, sample_session):
    """Create sample audio chunks for a session."""
    chunks = []
    for i in range(3):
        chunk = AudioChunk(
            id=uuid.uuid4(),
            session_id=sample_session.id,
            chunk_number=i,
            storage_path=f"sessions/{sample_session.id}/chunk_{i}.wav",
            duration_seconds=Decimal("10.0"),
        )
        db.add(chunk)
        chunks.append(chunk)
    db.commit()
    return chunks


@pytest.fixture
def mock_storage():
    """Mock storage service."""
    with patch("processor.storage") as mock:
        mock.get_public_url = MagicMock(
            side_effect=lambda path: f"https://storage.example.com/{path}"
        )
        mock.upload_processed_audio = AsyncMock(
            side_effect=lambda session_id, content, filename: f"sessions/{session_id}/{filename}"
        )
        yield mock


@pytest.fixture
def mock_diarization():
    """Mock diarization service."""
    from services.diarization import SpeakerSegment

    # Return fake speaker segments
    mock_segments = [
        SpeakerSegment(
            speaker_id="SPEAKER_00",
            start_time=0.0,
            end_time=5.0,
            duration=5.0,
        ),
        SpeakerSegment(
            speaker_id="SPEAKER_01",
            start_time=5.5,
            end_time=10.0,
            duration=4.5,
        ),
        SpeakerSegment(
            speaker_id="SPEAKER_00",
            start_time=10.5,
            end_time=15.0,
            duration=4.5,
        ),
    ]

    with patch("processor.diarize_audio") as mock:
        mock.return_value = mock_segments
        yield mock, mock_segments


@pytest.fixture
def mock_transcription():
    """Mock transcription service."""
    transcriptions = [
        "Wah this one damn good lah",
        "Cannot lah, I got other things lor",
        "Walao eh the traffic today really jialat sia",
    ]

    with patch("processor.transcribe_audio") as mock:
        mock.side_effect = transcriptions
        yield mock, transcriptions


@pytest.fixture
def mock_extract_segment():
    """Mock segment extraction."""
    with patch("processor.extract_speaker_segment") as mock:
        # Return fake WAV bytes
        mock.return_value = b"RIFF" + b"\x00" * 100
        yield mock


# Sample transcription text with known Singlish words
SAMPLE_TRANSCRIPTION = """
Wah this mala damn shiok sia!
After gym go eat, confirm shiok one lah.
Cannot lor, I got other things.
Walao eh the traffic today really jialat.
So sian ah, queue so long again.
"""

EXPECTED_WORD_COUNTS = {
    "wah": 1,
    "shiok": 2,
    "sia": 1,
    "lah": 1,
    "one": 1,
    "cannot": 1,
    "lor": 1,
    "walao": 1,
    "jialat": 1,
    "sian": 1,
    "ah": 1,
}
