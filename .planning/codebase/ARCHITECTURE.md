# Architecture

**Analysis Date:** 2026-01-17

## Pattern Overview

**Overall:** Mobile-Backend Split Architecture with ML Processing Pipeline

**Key Characteristics:**
- Mobile-first recording experience (React Native)
- Python backend API with background job processing
- ML pipeline for speaker diarization and speech-to-text
- Real-time sync via Firebase Realtime Database
- Cloud storage for audio files (S3)

## Layers

**Mobile App Layer:**
- Purpose: User interface for recording, claiming, and viewing stats
- Contains: React Native screens, hooks, components
- Location: `mobile/src/`
- Depends on: Backend API, Firebase for real-time updates
- Used by: End users

**API Layer:**
- Purpose: HTTP endpoints for session management and data access
- Contains: FastAPI routers with request validation
- Location: `backend/routers/sessions.py`, `backend/routers/groups.py`
- Depends on: Service layer, database models
- Used by: Mobile app

**Service Layer:**
- Purpose: Core business logic and external service integrations
- Contains: Diarization, transcription, Firebase sync services
- Location: `backend/services/diarization.py`, `backend/services/transcription.py`, `backend/services/firebase.py`
- Depends on: ML models, external APIs, storage
- Used by: Processor, API layer

**Processing Layer:**
- Purpose: Background audio processing pipeline
- Contains: Session processor, word counting, sample generation
- Location: `backend/processor.py`, `backend/worker.py`
- Depends on: Services, storage, database
- Used by: Redis job queue

**Data Layer:**
- Purpose: Database models and persistence
- Contains: SQLAlchemy models, migrations
- Location: `backend/models.py`, `backend/database.py`, `backend/alembic/`
- Depends on: PostgreSQL
- Used by: All backend layers

**ML Layer:**
- Purpose: Model training and fine-tuning (optional)
- Contains: Training scripts, evaluation, data processing
- Location: `ml/scripts/`
- Depends on: HuggingFace transformers, PyTorch
- Used by: Development workflow (not runtime)

## Data Flow

**Recording Flow:**

1. User opens RecordingScreen → taps "Start Recording"
2. Mobile app creates session via `POST /sessions/start`
3. Audio captured at 16kHz mono, chunked every 30s
4. Chunks uploaded via `POST /sessions/{id}/upload` → stored in S3
5. User stops → `POST /sessions/{id}/end`
6. Backend queues processing job in Redis

**Processing Flow:**

1. Worker picks up job from Redis queue
2. `processor.py` concatenates audio chunks from S3
3. Speaker diarization via pyannote → segments by speaker
4. Each segment transcribed via MERaLiON ASR
5. Post-processing corrections applied
6. Word counts calculated per speaker
7. 5-second samples generated for claiming
8. Results saved to database, Firebase updated

**Claiming Flow:**

1. User polls `GET /sessions/{id}/status` until ready
2. Mobile fetches speakers via `GET /sessions/{id}/speakers`
3. User plays audio samples, identifies themselves
4. User claims via `POST /sessions/{id}/claim`
5. Word counts attributed to user in database
6. Firebase syncs live counts to group

**State Management:**
- Database: PostgreSQL for persistent state (sessions, speakers, word counts)
- Firebase: Real-time sync for live counts and session status
- S3: Audio file storage (chunks, full audio, samples)
- Redis: Job queue for background processing

## Key Abstractions

**Session:**
- Purpose: Represents a recording session lifecycle
- Examples: `backend/models.py` Session model, `backend/routers/sessions.py`
- Pattern: State machine (recording → processing → ready_for_claiming → completed)

**Speaker:**
- Purpose: Unknown speaker identity before claiming
- Examples: `backend/models.py` SessionSpeaker model
- Pattern: Temporary identity resolved via claiming

**Service:**
- Purpose: Encapsulate external service interactions
- Examples: `backend/services/diarization.py`, `backend/services/transcription.py`, `backend/services/firebase.py`
- Pattern: Singleton-like modules with cached clients

**Hook:**
- Purpose: Encapsulate mobile state and logic
- Examples: `mobile/src/hooks/useRecording.ts`, `mobile/src/hooks/useSessionStatus.ts`
- Pattern: React custom hooks

## Entry Points

**Backend API:**
- Location: `backend/main.py`
- Triggers: HTTP requests from mobile app
- Responsibilities: Initialize FastAPI, include routers, configure middleware

**Background Worker:**
- Location: `backend/worker.py`
- Triggers: Redis job queue
- Responsibilities: Process audio sessions, run ML pipeline

**Mobile App:**
- Location: `mobile/src/` (app entry via Expo)
- Triggers: User interaction
- Responsibilities: Recording UI, claiming flow, statistics display

## Error Handling

**Strategy:** Throw exceptions, catch at API boundaries, return structured errors

**Patterns:**
- FastAPI HTTPException for API errors
- Background job retry via Redis
- Mobile error state in hooks
- Firebase for real-time status updates including errors

## Cross-Cutting Concerns

**Logging:**
- Console logging in development
- Structured logs recommended for production

**Validation:**
- Pydantic schemas at API boundary (`backend/schemas.py`)
- Mobile validation in hooks and screens

**Authentication:**
- Not fully implemented yet (hackathon scope)
- User IDs passed as parameters

---

*Architecture analysis: 2026-01-17*
*Update when major patterns change*
