# External Integrations

**Analysis Date:** 2026-01-17

## APIs & External Services

**MERaLiON ASR (Speech-to-Text):**
- Purpose: Transcribe Singlish audio to text
- Model: `MERaLiON/MERaLiON-2-10B-ASR` from HuggingFace
- Integration: `backend/services/transcription.py`
- SDK/Client: transformers pipeline
- Auth: HuggingFace token in `HUGGINGFACE_TOKEN` env var
- Usage: Pre-trained model, no fine-tuning for hackathon

**pyannote Speaker Diarization:**
- Purpose: Segment audio by speaker identity
- Model: `pyannote/speaker-diarization-3.1` from HuggingFace
- Integration: `backend/services/diarization.py`
- SDK/Client: pyannote.audio Pipeline
- Auth: HuggingFace token in `HUGGINGFACE_TOKEN` env var
- Note: Requires accepting model license on HuggingFace

## Data Storage

**PostgreSQL:**
- Purpose: Primary relational database for sessions, speakers, word counts
- Connection: `DATABASE_URL` env var (e.g., `postgresql://user:pass@localhost:5432/lahstats`)
- Client: SQLAlchemy ORM (`backend/database.py`)
- Migrations: Alembic (`backend/alembic/`)
- Tables: sessions, session_speakers, word_counts (see `backend/models.py`)

**AWS S3:**
- Purpose: Audio file storage (chunks, full audio, speaker samples)
- Connection: `S3_BUCKET`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION` env vars
- Client: boto3 (`backend/storage.py`)
- Structure:
  - `sessions/{session_id}/chunks/*.wav` - Recording chunks
  - `sessions/{session_id}/full_audio.wav` - Concatenated audio
  - `sessions/{session_id}/samples/*.wav` - Speaker claiming samples

**Redis:**
- Purpose: Job queue for background audio processing
- Connection: `REDIS_URL` env var (e.g., `redis://localhost:6379`)
- Client: redis-py (`backend/worker.py`)
- Usage: Queue processing jobs when sessions end

## Authentication & Identity

**Firebase Authentication:**
- Purpose: User authentication (if implemented)
- Status: Not fully implemented for hackathon
- Configuration: `FIREBASE_PROJECT_ID`, `FIREBASE_CREDENTIALS` env vars
- Note: Currently user IDs passed as parameters without verification

## Real-time Sync

**Firebase Realtime Database:**
- Purpose: Live sync of session status and group word counts
- Integration: `backend/services/firebase.py`
- SDK/Client: firebase-admin SDK
- Auth: Service account JSON in `FIREBASE_CREDENTIALS` path
- Project: `FIREBASE_PROJECT_ID` env var
- Database URL: `FIREBASE_DATABASE_URL` env var (mobile)

**Firebase Structure:**
```json
{
  "groups": {
    "{group_id}": {
      "live_counts": { "{user_id}": {"walao": 10, "lah": 15} },
      "leaderboard": [...],
      "active_session": "{session_id}"
    }
  },
  "sessions": {
    "{session_id}": {
      "status": "processing",
      "progress": 45
    }
  }
}
```

## Monitoring & Observability

**Error Tracking:**
- Not configured (hackathon scope)
- Recommended: Sentry for production

**Analytics:**
- Not configured
- Word counting data could feed analytics

**Logs:**
- Console logging for development
- Docker/cloud logs for production

## CI/CD & Deployment

**Hosting:**
- Local: Docker Compose for Redis + PostgreSQL
- Production: Not fully configured (hackathon)
- Options: AWS/GCP/Azure, Vercel for frontend if needed

**CI Pipeline:**
- Not configured yet
- Recommended: GitHub Actions for tests

**Deployment Script:**
- `deploy.sh` - Deployment helper script
- `docker-compose.yml` - Local development services

## Environment Configuration

**Development:**
- Required env vars (backend): `DATABASE_URL`, `REDIS_URL`, `HUGGINGFACE_TOKEN`
- Required env vars (mobile): `API_URL`, Firebase config vars
- Secrets location: `.env` files (gitignored), copy from `.env.example`
- Docker services: `docker-compose up -d` for Redis + PostgreSQL

**Production:**
- Same env vars, production values
- S3 bucket, production database
- GPU instance for ML models

## Webhooks & Callbacks

**Incoming:**
- None currently

**Outgoing:**
- Firebase real-time updates (not webhooks, but real-time sync)

---

*Integration audit: 2026-01-17*
*Update when adding/removing external services*
