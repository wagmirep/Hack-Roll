# Testing Patterns

**Analysis Date:** 2026-01-17

## Test Framework

**Backend (Python):**
- Runner: pytest with pytest-asyncio
- Config: `backend/tests/conftest.py`
- Location: `backend/tests/`

**Mobile (TypeScript):**
- Runner: Jest
- Config: Referenced in `mobile/package.json`
- Location: `mobile/__tests__/`
- Utilities: @testing-library/react-native

**Run Commands:**
```bash
# Backend
cd backend
pytest                              # Run all tests
pytest tests/test_sessions.py       # Single file
pytest -v                           # Verbose output

# Mobile
cd mobile
bun test                            # or npm test
bun test -- --watch                 # Watch mode
bun test path/to/file.test.ts      # Single file
```

## Test File Organization

**Backend:**
- Location: `backend/tests/` (separate from source)
- Naming: `test_*.py` (pytest discovery pattern)
- Files:
  - `conftest.py` - Shared fixtures
  - `test_sessions.py` - Session endpoint tests
  - `test_processing.py` - Processing pipeline tests
  - `test_word_counting.py` - Word counting logic tests

**Mobile:**
- Location: `mobile/__tests__/` (separate from source)
- Naming: `*.test.ts` or `*.test.tsx`
- Structure mirrors `src/`:
  - `__tests__/hooks/useRecording.test.ts`
  - `__tests__/screens/RecordingScreen.test.tsx`
  - `__tests__/utils/formatting.test.ts`

**Structure:**
```
backend/
  tests/
    __init__.py
    conftest.py
    test_sessions.py
    test_processing.py
    test_word_counting.py

mobile/
  __tests__/
    hooks/
      useRecording.test.ts
    screens/
      RecordingScreen.test.tsx
      ClaimingScreen.test.tsx
    utils/
      formatting.test.ts
```

## Test Structure

**Python (pytest):**
```python
"""Test module docstring"""

def test_create_session_success(client, db):
    # Arrange
    payload = {"group_id": "...", "started_by": "..."}

    # Act
    response = client.post("/sessions/start", json=payload)

    # Assert
    assert response.status_code == 200
    assert response.json()["status"] == "recording"


def test_create_session_invalid_group(client):
    # Test error case
    response = client.post("/sessions/start", json={"group_id": "invalid"})
    assert response.status_code == 422
```

**TypeScript (Jest):**
```typescript
describe('useRecording', () => {
  describe('initial state', () => {
    it('should have isRecording as false', () => {
      const { result } = renderHook(() => useRecording());
      expect(result.current.isRecording).toBe(false);
    });
  });

  describe('startRecording', () => {
    it('should create session via API', async () => {
      // Test implementation
    });
  });
});
```

**Patterns:**
- Arrange/Act/Assert structure
- Descriptive test names (test_* or should *)
- One assertion focus per test
- Use fixtures for common setup

## Mocking

**Python (pytest):**
```python
# conftest.py
@pytest.fixture
def mock_s3(mocker):
    return mocker.patch('storage.s3_client')

@pytest.fixture
def mock_redis(mocker):
    return mocker.patch('worker.redis_client')

@pytest.fixture
def mock_firebase(mocker):
    return mocker.patch('services.firebase.get_firebase_app')
```

**TypeScript (Jest):**
```typescript
// Mock modules
jest.mock('../api/client');
jest.mock('expo-av');

// Mock in test
const mockUploadChunk = jest.mocked(client.uploadChunk);
mockUploadChunk.mockResolvedValue({ uploaded: true });
```

**What to Mock:**
- External services: S3, Firebase, Redis
- ML models: pyannote, MERaLiON (for unit tests)
- Expo native modules: expo-av Audio
- Network calls

**What NOT to Mock:**
- Pure functions (word counting, corrections)
- Internal utility functions
- Data transformations

## Fixtures and Factories

**Python Fixtures (`conftest.py`):**
- `client` - FastAPI TestClient
- `db` - Test database session
- `mock_s3`, `mock_redis`, `mock_firebase` - Mocked services
- `sample_session` - Pre-created session
- `sample_audio` - Sample audio bytes
- `sample_transcription` - Sample text with Singlish words

**TypeScript:**
- Factory functions in test files
- Shared test data in `__tests__/fixtures/` if needed

## Coverage

**Requirements:**
- No enforced coverage target (hackathon)
- Focus on critical paths: session lifecycle, word counting, claiming

**View Coverage:**
```bash
# Backend
pytest --cov=. --cov-report=html
open htmlcov/index.html

# Mobile
bun test -- --coverage
```

## Test Types

**Unit Tests:**
- Scope: Single function/module in isolation
- Mocking: All external dependencies
- Examples: `test_word_counting.py`, `useRecording.test.ts`

**Integration Tests:**
- Scope: Multiple modules together
- Mocking: External services only
- Examples: `test_sessions.py` (endpoint + database)

**E2E Tests:**
- Not implemented yet
- Manual testing for hackathon

## Common Patterns

**Async Testing (Python):**
```python
@pytest.mark.asyncio
async def test_process_session():
    result = await process_session(session_id)
    assert result.status == 'completed'
```

**Async Testing (TypeScript):**
```typescript
it('should handle async operation', async () => {
  const result = await asyncFunction();
  expect(result).toBe('expected');
});
```

**Error Testing:**
```python
def test_invalid_input_raises():
    with pytest.raises(ValueError):
        invalid_function(None)
```

```typescript
it('should throw on invalid input', async () => {
  await expect(asyncCall()).rejects.toThrow('error message');
});
```

---

*Testing analysis: 2026-01-17*
*Update when test patterns change*
