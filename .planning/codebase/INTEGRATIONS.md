# External Integrations

**Analysis Date:** 2026-01-18

## APIs & External Services

**Speech Recognition:**
- MERaLiON-2-3B ASR - Singlish speech-to-text transcription
  - SDK/Client: transformers (HuggingFace) in `backend/services/transcription.py`
  - Model: `MERaLiON/MERaLiON-2-3B` (lightweight, CPU-optimized)
  - Auth: Public model, no token required
  - Alternative: External API via `TRANSCRIPTION_API_URL` for Colab notebook with 10B model

**Speaker Diarization:**
- pyannote/speaker-diarization-3.1 - Who spoke when
  - SDK/Client: pyannote.audio in `backend/services/diarization.py`
  - Auth: HuggingFace token in `HUGGINGFACE_TOKEN` env var
  - Required: Accept model license on HuggingFace

**External APIs:**
- None currently (ML models run locally or via optional Colab)

## Data Storage

**Databases:**
- PostgreSQL on Supabase - Primary data store
  - Connection: via `DATABASE_URL` env var (constructed from `SUPABASE_URL`)
  - Client: SQLAlchemy 2.0 ORM (`backend/database.py`)
  - Migrations: Alembic in `backend/alembic/`
  - Tables: profiles, groups, sessions, session_speakers, audio_chunks, word_counts

**File Storage:**
- Supabase Storage - Audio files (chunks and processed)
  - SDK/Client: Supabase client via `backend/storage.py`
  - Auth: Service role key in `SUPABASE_SERVICE_ROLE_KEY`
  - Bucket: `audio-chunks` (configured in `STORAGE_BUCKET`)
  - Paths: `sessions/{session_id}/chunk_{n}.wav`, `sessions/{session_id}/full_audio.wav`

**Caching:**
- Redis - Background job queue (optional)
  - Connection: `REDIS_URL` env var
  - Client: redis-py in `backend/redis_client.py`
  - Usage: Job queuing for audio processing

## Authentication & Identity

**Auth Provider:**
- Supabase Auth - Email/password authentication
  - Implementation: Supabase client SDK on mobile (`mobile/src/lib/supabase.ts`)
  - Token storage: AsyncStorage on mobile
  - Session management: JWT tokens validated server-side

**Backend Auth:**
- JWT validation in `backend/auth.py`
- Supabase JWT secret in `SUPABASE_JWT_SECRET`
- Protected routes use auth dependency injection

**OAuth Integrations:**
- None configured (email/password only)

## Monitoring & Observability

**Error Tracking:**
- None configured (console logging only)

**Analytics:**
- None configured

**Logs:**
- Python logging to stdout/stderr
- Request logging middleware in `backend/main.py`
- No external log aggregation

## CI/CD & Deployment

**Hosting:**
- Not specified (deployment-ready with Docker)
  - Dockerfile: `Dockerfile.claude`
  - Docker Compose: `docker-compose.yml`
  - Deploy script: `deploy.sh`

**CI Pipeline:**
- Not configured (no GitHub Actions workflows)

## Environment Configuration

**Development:**
- Required env vars:
  - `SUPABASE_URL` - Supabase project URL
  - `SUPABASE_JWT_SECRET` - JWT validation secret
  - `HUGGINGFACE_TOKEN` - For pyannote model access
- Optional:
  - `TRANSCRIPTION_API_URL` - External transcription endpoint
  - `REDIS_URL` - For background jobs
  - `FIREBASE_PROJECT_ID` - For real-time updates
- Secrets location: `.env` file (gitignored)
- Mock/stub services: In-memory SQLite for tests, mock fixtures

**Production:**
- Same env vars as development
- GPU recommended for faster ML inference
- Redis required for production job queue
- Supabase project with storage bucket configured

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- Firebase Realtime Database - Optional real-time group updates
  - Service: `backend/services/firebase.py`
  - Credentials: `FIREBASE_CREDENTIALS` (path to service account JSON)
  - Events: Session status updates, word count syncs

## External Model Dependencies

**HuggingFace Models:**

| Model | Purpose | Size | Auth Required |
|-------|---------|------|---------------|
| `MERaLiON/MERaLiON-2-3B` | ASR transcription | ~6GB | No |
| `pyannote/speaker-diarization-3.1` | Speaker segmentation | ~1GB | Yes (HF token) |

**Notes:**
- Models downloaded on first use (~7GB total)
- Cached in HuggingFace cache directory
- CPU inference supported but slow (GPU recommended)
- INT8 quantization applied for CPU optimization

## Service Dependencies Summary

```
┌─────────────────────────────────────────────────────────┐
│                    Mobile App                           │
│              (React Native / Expo)                      │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP / WebSocket
                         ▼
┌─────────────────────────────────────────────────────────┐
│                   FastAPI Backend                       │
│                  (backend/main.py)                      │
└───┬──────────┬──────────┬──────────┬──────────┬────────┘
    │          │          │          │          │
    ▼          ▼          ▼          ▼          ▼
┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────────────┐
│Supabase│ │Supabase│ │ Redis │ │Firebase│ │  HuggingFace  │
│  Auth  │ │Storage │ │ Queue │ │Realtime│ │    Models     │
│  (JWT) │ │ (Audio)│ │(Jobs) │ │(Sync)  │ │(ASR/Diarize)  │
└───────┘ └───────┘ └───────┘ └───────┘ └───────────────┘
    │
    ▼
┌───────────────┐
│   Supabase    │
│  PostgreSQL   │
│  (Database)   │
└───────────────┘
```

---

*Integration audit: 2026-01-18*
*Update when adding/removing external services*
