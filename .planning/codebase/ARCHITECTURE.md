# Architecture

**Analysis Date:** 2026-01-18

## Pattern Overview

**Overall:** Monolithic Backend API + Mobile Client with ML Processing Pipeline

**Key Characteristics:**
- FastAPI backend serving REST endpoints
- React Native mobile app for recording/viewing
- Background processing pipeline for audio analysis
- External ML models (MERaLiON, pyannote) for Singlish transcription
- Supabase for auth, database, and storage

## Layers

**API Layer:**
- Purpose: Handle HTTP requests, route to appropriate handlers
- Contains: FastAPI routers, request/response schemas
- Location: `backend/routers/*.py`, `backend/schemas.py`
- Depends on: Service layer, database models
- Used by: Mobile app via HTTP

**Service Layer:**
- Purpose: Business logic and ML model integration
- Contains: Transcription, diarization, Firebase sync
- Location: `backend/services/*.py`
- Depends on: External models (HuggingFace), config
- Used by: API routers, processor

**Processing Layer:**
- Purpose: Orchestrate audio processing pipeline
- Contains: Chunk concatenation, diarization, transcription, word counting
- Location: `backend/processor.py`, `backend/worker.py`
- Depends on: Services, storage, database
- Used by: Background worker, triggered by API

**Data Layer:**
- Purpose: Database models and persistence
- Contains: SQLAlchemy models, Alembic migrations
- Location: `backend/models.py`, `backend/database.py`, `backend/alembic/`
- Depends on: SQLAlchemy, PostgreSQL
- Used by: All backend layers

**Mobile Layer:**
- Purpose: User interface for recording, claiming, viewing stats
- Contains: React Native screens, hooks, components
- Location: `mobile/src/`
- Depends on: Backend API, Supabase client
- Used by: End users

## Data Flow

**Recording Flow:**

1. User starts recording (`mobile/src/screens/RecordingScreen.tsx`)
2. Audio recorded via expo-av (`mobile/src/hooks/useRecording.ts`)
3. Chunks uploaded every 30s to backend (`POST /sessions/{id}/upload`)
4. Backend stores chunks in Supabase Storage (`backend/storage.py`)
5. User stops recording (`POST /sessions/{id}/end`)
6. Background worker processes session (`backend/worker.py`)

**Processing Pipeline:**

1. Worker triggers `process_session()` (`backend/processor.py`)
2. Concatenate audio chunks into single WAV file
3. Run speaker diarization with pyannote (`backend/services/diarization.py`)
4. Transcribe each segment with MERaLiON (`backend/services/transcription.py`)
5. Apply Singlish corrections, count target words
6. Save speaker results to database
7. Generate 5-second sample clips for claiming UI
8. Update session status to "ready_for_claiming"

**Claiming Flow:**

1. User polls session status (`GET /sessions/{id}/status`)
2. When ready, fetch speakers (`GET /sessions/{id}/speakers`)
3. User listens to samples, claims speaker identity
4. Claims submitted (`POST /sessions/{id}/claim`)
5. Word counts attributed to user profile

**State Management:**
- PostgreSQL (via Supabase) - Persistent state for sessions, users, word counts
- Supabase Auth - User authentication and JWT tokens
- Mobile AsyncStorage - Local caching of auth state
- Firebase Realtime Database - Optional real-time group updates

## Key Abstractions

**Session:**
- Purpose: Represents a recording session
- Location: `backend/models.py` (Session model)
- Pattern: State machine (recording -> processing -> ready_for_claiming -> completed)

**SpeakerSegment:**
- Purpose: Time-stamped speaker attribution from diarization
- Location: `backend/services/diarization.py`
- Pattern: Data class with speaker_id, start_time, end_time

**Transcription Service:**
- Purpose: Singlish-aware speech-to-text
- Location: `backend/services/transcription.py`
- Pattern: Singleton model loader with corrections dictionary

**Storage Abstraction:**
- Purpose: Upload/download audio files
- Location: `backend/storage.py`
- Pattern: Service class wrapping Supabase Storage

## Entry Points

**Backend API:**
- Location: `backend/main.py`
- Triggers: HTTP requests from mobile app
- Responsibilities: Register routers, configure CORS, startup/shutdown events

**Background Worker:**
- Location: `backend/worker.py`
- Triggers: Session end, queued via Redis
- Responsibilities: Process audio sessions asynchronously

**Mobile App:**
- Location: `mobile/expo/AppEntry.js` -> `mobile/App.tsx`
- Triggers: User launches app
- Responsibilities: Auth flow, navigation, screens

## Error Handling

**Strategy:** Exceptions propagate to boundaries, caught by middleware/handlers

**Patterns:**
- FastAPI global exception handler (`backend/main.py`)
- ProcessingError custom exception (`backend/processor.py`)
- Session status set to "failed" with error_message on processing failure
- Mobile shows error toasts for API failures

## Cross-Cutting Concerns

**Logging:**
- Python logging module throughout backend
- Request/response logging middleware (`backend/main.py`)
- Structured logs with context (session_id, speaker_id)

**Validation:**
- Pydantic models for API request/response (`backend/schemas.py`)
- Pydantic Settings for config validation (`backend/config.py`)

**Authentication:**
- Supabase Auth with JWT tokens
- Backend validates JWT via `backend/auth.py`
- Mobile stores auth state in context (`mobile/src/contexts/AuthContext.tsx`)

---

*Architecture analysis: 2026-01-18*
*Update when major patterns change*
