# Technology Stack

**Analysis Date:** 2026-01-18

## Languages

**Primary:**
- Python 3.10+ - Backend API and ML pipeline (`backend/`, `ml/`)
- TypeScript 5.3 - Mobile app (`mobile/src/`)

**Secondary:**
- JavaScript - React Native build tooling, Babel config
- Shell - Deployment scripts (`deploy.sh`)

## Runtime

**Environment:**
- Python 3.10+ - Backend services
- Node.js 18.x+ - React Native/Expo development
- CUDA (optional) - GPU acceleration for ML models

**Package Manager:**
- pip (Python) - `backend/requirements.txt`, `ml/requirements.txt`
- npm/bun - `mobile/package.json`

**Lockfiles:**
- None for Python (requirements.txt only)
- `mobile/package-lock.json` present

## Frameworks

**Core:**
- FastAPI 0.109+ - Backend REST API (`backend/main.py`)
- React Native 0.73.6 - Mobile app (`mobile/`)
- Expo 50.0 - Mobile development platform

**ML/AI:**
- transformers 4.36+ - MERaLiON ASR model (`backend/services/transcription.py`)
- pyannote.audio 3.1+ - Speaker diarization (`backend/services/diarization.py`)
- torch 2.0+ - Deep learning framework

**Testing:**
- pytest 7.4+ - Python backend tests (`backend/tests/`)
- pytest-asyncio - Async test support

**Build/Dev:**
- uvicorn - ASGI server for FastAPI
- Babel - React Native transpilation
- Expo CLI - Mobile development

## Key Dependencies

**Critical (Backend):**
- `fastapi` - REST API framework (`backend/main.py`)
- `transformers` - HuggingFace models for MERaLiON (`backend/services/transcription.py`)
- `pyannote.audio` - Speaker diarization (`backend/services/diarization.py`)
- `sqlalchemy` - ORM for database (`backend/database.py`)
- `pydub` - Audio processing (`backend/processor.py`)

**Critical (Mobile):**
- `@supabase/supabase-js` - Auth and real-time (`mobile/src/lib/supabase.ts`)
- `expo-av` - Audio recording (`mobile/src/hooks/useRecording.ts`)
- `@react-navigation/*` - Navigation (`mobile/src/navigation/`)
- `axios` - HTTP client (`mobile/src/api/client.ts`)

**Infrastructure:**
- `psycopg2-binary` - PostgreSQL driver
- `redis` - Background job queue
- `boto3` - AWS S3 storage
- `firebase-admin` - Real-time updates (optional)

## Configuration

**Environment:**
- `.env` files for secrets (gitignored)
- `backend/config.py` - Pydantic Settings for typed config
- Required: `SUPABASE_URL`, `SUPABASE_JWT_SECRET`, `HUGGINGFACE_TOKEN`
- Optional: `TRANSCRIPTION_API_URL` for external Colab notebook

**Build:**
- `mobile/tsconfig.json` - TypeScript configuration
- `mobile/babel.config.js` - Babel/React Native
- `backend/alembic/` - Database migrations

## Platform Requirements

**Development:**
- Windows/macOS/Linux
- Python 3.10+, Node.js 18+
- Docker for Redis (optional)
- FFmpeg for audio processing (pydub dependency)

**Production:**
- Linux server with GPU (recommended for ML)
- Supabase (PostgreSQL + Auth + Storage)
- Redis for job queue
- 16GB+ RAM for ML models

---

*Stack analysis: 2026-01-18*
*Update after major dependency changes*
