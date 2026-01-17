# Technology Stack

**Analysis Date:** 2026-01-17

## Languages

**Primary:**
- Python 3.x - Backend API, ML pipeline, audio processing (`backend/`, `ml/`)
- TypeScript - Mobile app and frontend components (`mobile/src/`)

**Secondary:**
- JavaScript - Configuration, scripts (`deploy.sh`, package.json scripts)
- SQL - Database migrations (`backend/alembic/`)

## Runtime

**Environment:**
- Python 3.x (Backend API, ML processing)
- Node.js (React Native mobile app via Expo)
- Expo SDK (Mobile development framework)

**Package Manager:**
- pip - Python dependencies (`backend/requirements.txt`, `ml/requirements.txt`)
- Bun/npm - JavaScript dependencies (`mobile/package.json`)

## Frameworks

**Core:**
- FastAPI - Python web framework for backend API (`backend/main.py`)
- React Native + Expo - Mobile app framework (`mobile/`)
- SQLAlchemy - Python ORM for database access (`backend/database.py`, `backend/models.py`)

**Testing:**
- pytest / pytest-asyncio - Python backend tests (`backend/tests/`)
- Jest - JavaScript/TypeScript tests (`mobile/__tests__/`)
- @testing-library/react-native - React Native component testing

**Build/Dev:**
- uvicorn - ASGI server for FastAPI (`backend/main.py`)
- Alembic - Database migrations (`backend/alembic/`)
- Expo CLI - Mobile development tooling

## Key Dependencies

**Critical:**
- transformers - HuggingFace library for MERaLiON ASR model (`backend/services/transcription.py`)
- pyannote.audio - Speaker diarization model (`backend/services/diarization.py`)
- torch - PyTorch for ML inference (`backend/requirements.txt`)
- expo-av - Audio recording/playback in mobile app (`mobile/src/hooks/useRecording.ts`)

**Infrastructure:**
- redis - Job queue for background processing (`backend/worker.py`)
- psycopg2-binary - PostgreSQL client (`backend/database.py`)
- boto3 - AWS S3 storage client (`backend/storage.py`)
- firebase-admin - Firebase Realtime Database (`backend/services/firebase.py`)
- @react-navigation/native - Mobile navigation (`mobile/src/screens/`)

**Audio Processing:**
- librosa - Audio loading and processing (`backend/requirements.txt`)
- soundfile - Audio file I/O (`backend/requirements.txt`)
- pydub - Audio manipulation (`backend/requirements.txt`)

## Configuration

**Environment:**
- .env files - Environment variables (`backend/.env.example`, `mobile/.env.example`)
- Key configs: DATABASE_URL, REDIS_URL, S3_BUCKET, AWS credentials, HUGGINGFACE_TOKEN, FIREBASE credentials

**Build:**
- No tsconfig.json detected yet - placeholder structure
- Alembic for database migrations (`backend/alembic/`)

## Platform Requirements

**Development:**
- macOS/Linux/Windows with Python 3.x and Node.js
- Docker for Redis and PostgreSQL (`docker-compose.yml`)
- GPU recommended for ML model inference

**Production:**
- Docker containers or cloud deployment
- PostgreSQL database
- Redis for job queue
- AWS S3 for audio storage
- Firebase Realtime Database for live sync

---

*Stack analysis: 2026-01-17*
*Update after major dependency changes*
