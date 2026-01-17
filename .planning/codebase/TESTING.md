# Testing Patterns

**Analysis Date:** 2026-01-18

## Test Framework

**Runner:**
- pytest 7.4+ (Python backend)
- pytest-asyncio for async test support
- Config: No explicit `pytest.ini` (uses defaults)

**Assertion Library:**
- pytest built-in assert
- Standard assert statements with descriptive messages

**Run Commands:**
```bash
# Backend tests
cd backend
pytest                           # Run all tests
pytest tests/test_sessions.py    # Single file
pytest -v                        # Verbose output
pytest --tb=short                # Short traceback

# With coverage (if pytest-cov installed)
pytest --cov=. --cov-report=html
```

## Test File Organization

**Location:**
- `backend/tests/` - Separate tests directory
- `ml/tests/` - ML-specific tests

**Naming:**
- `test_*.py` - Test files
- `conftest.py` - Shared fixtures

**Structure:**
```
backend/
├── tests/
│   ├── __init__.py
│   ├── conftest.py           # Fixtures: db, mock services
│   ├── test_sessions.py      # Session endpoint tests
│   ├── test_word_counting.py # Singlish word counting
│   ├── test_transcription.py # Transcription service
│   ├── test_transcription_unit.py  # Unit tests
│   └── test_processing.py    # Processing pipeline
├── services/
│   └── transcription.py
└── processor.py
```

## Test Structure

**Suite Organization:**
```python
import pytest
from unittest.mock import patch, MagicMock

class TestWordCounting:
    """Tests for Singlish word counting logic."""

    def test_counts_single_word(self):
        """Should count a single occurrence of target word."""
        # arrange
        text = "This food is shiok lah"

        # act
        from services.transcription import count_target_words
        counts = count_target_words(text)

        # assert
        assert counts.get("shiok") == 1
        assert counts.get("lah") == 1

    def test_applies_corrections(self):
        """Should correct common ASR mistakes."""
        text = "Wah lao this is so good"

        from services.transcription import apply_corrections
        corrected = apply_corrections(text)

        assert "walao" in corrected.lower()
```

**Patterns:**
- Class-based grouping for related tests
- Descriptive test method names (`test_should_X_when_Y`)
- Arrange/Act/Assert structure
- Docstrings explaining test purpose

## Mocking

**Framework:**
- `unittest.mock` (patch, MagicMock, AsyncMock)
- Fixtures in `conftest.py` for common mocks

**Patterns:**
```python
# conftest.py fixtures
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

    mock_segments = [
        SpeakerSegment(speaker_id="SPEAKER_00", start_time=0.0, end_time=5.0),
        SpeakerSegment(speaker_id="SPEAKER_01", start_time=5.5, end_time=10.0),
    ]

    with patch("processor.diarize_audio") as mock:
        mock.return_value = mock_segments
        yield mock, mock_segments
```

**What to Mock:**
- External services (Supabase storage, HuggingFace models)
- Database (use in-memory SQLite)
- Audio processing (return fake bytes)
- Network calls (use AsyncMock for httpx)

**What NOT to Mock:**
- Pure functions (word counting, corrections)
- Data transformations
- Schema validation

## Fixtures and Factories

**Test Data:**
```python
# conftest.py
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

# Test data constants
SAMPLE_TRANSCRIPTION = """
Wah this mala damn shiok sia!
Cannot lor, I got other things.
Walao eh the traffic today really jialat.
"""

EXPECTED_WORD_COUNTS = {
    "wah": 1,
    "shiok": 1,
    "sia": 1,
    "cannot": 1,
    "lor": 1,
    "walao": 1,
    "jialat": 1,
}
```

**Location:**
- Fixtures: `backend/tests/conftest.py`
- Test constants: In conftest.py or individual test files

## Coverage

**Requirements:**
- No enforced coverage target
- Coverage tracked for awareness

**Configuration:**
- pytest-cov plugin (if installed)
- No specific exclusions configured

**View Coverage:**
```bash
pytest --cov=. --cov-report=html
open htmlcov/index.html
```

## Test Types

**Unit Tests:**
- Test single functions in isolation
- Mock all external dependencies
- Files: `test_word_counting.py`, `test_transcription_unit.py`
- Fast: Should run in milliseconds

**Integration Tests:**
- Test multiple components together
- Use in-memory SQLite database
- Mock external services (storage, ML models)
- Files: `test_sessions.py`, `test_processing.py`

**E2E Tests:**
- Not present in codebase
- Manual testing via scripts: `test_api.py`, `test_ml_pipeline.py`

## Common Patterns

**Async Testing:**
```python
import pytest

@pytest.mark.asyncio
async def test_async_operation():
    result = await async_function()
    assert result == expected
```

**Database Testing:**
```python
@pytest.fixture
def db_engine():
    """Create test database engine."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db(db_engine):
    """Create test database session."""
    TestingSessionLocal = sessionmaker(bind=db_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
```

**Environment Setup:**
```python
# Set test environment variables BEFORE importing config
os.environ["SUPABASE_URL"] = "https://test-project.supabase.co"
os.environ["SUPABASE_JWT_SECRET"] = "test-jwt-secret"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
```

**Snapshot Testing:**
- Not used in this codebase
- Prefer explicit assertions

## Mobile Testing

**Status:**
- No automated tests for React Native
- Manual testing via Expo

**Potential Setup:**
- Jest for unit tests
- React Native Testing Library for component tests
- Detox for E2E

---

*Testing analysis: 2026-01-18*
*Update when test patterns change*
