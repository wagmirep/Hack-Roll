# Running the Full Application

This guide explains what needs to be running for the complete app to work.

## Architecture Overview

```
┌──────────────┐
│  Mobile App  │ (React Native/Expo)
│  (Frontend)  │
└──────┬───────┘
       │ HTTP Requests
       ↓
┌──────────────┐
│  FastAPI     │ (Backend API Server)
│  Backend     │ - Handles REST API endpoints
└──────┬───────┘ - Uploads audio chunks to Supabase Storage
       │         - Creates DB records
       │         - Queues jobs in Redis
       ↓
┌──────────────┐
│    Redis     │ (Job Queue)
│              │ - Queue: lahstats:processing
└──────┬───────┘ - Stores pending audio processing jobs
       │
       ↓
┌──────────────┐
│   Worker     │ (Background Processor)
│  (worker.py) │ - Runs ML models (MERaLiON, pyannote)
└──────┬───────┘ - Processes audio chunks
       │         - Updates database with results
       │
       ↓
┌──────────────┐
│   Supabase   │ (PostgreSQL + Storage)
│              │ - Database tables
└──────────────┘ - Audio file storage
```

## Required Components

### 1. **Supabase (Already Running)**
- **What**: Cloud-hosted PostgreSQL database + Object Storage
- **Status**: ✅ Already running (cloud service)
- **URL**: `https://tamrgxhjyabdvtubseyu.supabase.co`
- **No action needed**

---

### 2. **Redis Server**
- **What**: In-memory data store used as a job queue
- **Purpose**: Queues audio processing jobs between API and worker
- **Queue name**: `lahstats:processing`

**Check if running:**
```bash
redis-cli ping
# Should return: PONG
```

**Start Redis (if not running):**
```bash
# macOS (Homebrew):
brew services start redis

# Or run in foreground:
redis-server
```

**Stop Redis:**
```bash
brew services stop redis
```

---

### 3. **Backend API Server (FastAPI)**
- **What**: REST API that the mobile app communicates with
- **Location**: `/Hack-Roll/backend/`
- **Port**: 8000 (default)

**To start:**
```bash
cd /Users/winstonyang/Desktop/Coding/Hackathons/hacknroll/Hack-Roll/backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Key endpoints:**
- `POST /sessions` - Create new recording session
- `POST /sessions/{id}/chunks` - Upload audio chunks
- `POST /sessions/{id}/end` - End session and trigger processing
- `GET /sessions/{id}` - Get session status
- `GET /sessions/{id}/speakers` - Get speaker list
- `GET /sessions/{id}/results` - Get final results

**Environment variables required:**
- See `backend/.env` file
- Must include: `SUPABASE_URL`, `SUPABASE_KEY`, `REDIS_HOST`, `HUGGINGFACE_TOKEN`

---

### 4. **Background Worker**
- **What**: Python process that runs ML models on audio
- **Location**: `/Hack-Roll/backend/`
- **Purpose**: 
  - Downloads audio chunks from Supabase Storage
  - Runs speaker diarization (pyannote)
  - Runs transcription (MERaLiON)
  - Counts Singlish words
  - Updates database with results

**To start:**
```bash
cd /Users/winstonyang/Desktop/Coding/Hackathons/hacknroll/Hack-Roll/backend
source venv/bin/activate
python worker.py
```

**Dependencies:**
- ✅ **FFmpeg** (now installed)
- PyTorch
- pyannote-audio
- MERaLiON model
- All Python packages in `requirements.txt`

**What it does:**
1. Listens to Redis queue `lahstats:processing`
2. When a job arrives (session ID):
   - Downloads all audio chunks for that session
   - Concatenates chunks into one file
   - Runs diarization to detect speakers
   - Runs transcription on each speaker segment
   - Counts Singlish words per speaker
   - Saves results to database
3. Updates session status to `completed` or `failed`

**Expected processing time:**
- ~20-60 seconds per 30-second audio chunk (depending on hardware)

---

### 5. **Mobile App (Frontend)**
- **What**: React Native app using Expo
- **Location**: `/Hack-Roll/mobile/`
- **Port**: Varies (Expo dev server)

**To start:**
```bash
cd /Users/winstonyang/Desktop/Coding/Hackathons/hacknroll/Hack-Roll/mobile
npm start
# or
expo start
```

**Environment variables required:**
- See `mobile/.env` file
- Must include: `EXPO_PUBLIC_API_URL` (pointing to backend)
- Must include: `EXPO_PUBLIC_SUPABASE_URL`, `EXPO_PUBLIC_SUPABASE_ANON_KEY`

---

## Complete Startup Sequence

### Terminal 1: Redis
```bash
redis-server
# Or: brew services start redis
```

### Terminal 2: Backend API
```bash
cd /Users/winstonyang/Desktop/Coding/Hackathons/hacknroll/Hack-Roll/backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Terminal 3: Background Worker
```bash
cd /Users/winstonyang/Desktop/Coding/Hackathons/hacknroll/Hack-Roll/backend
source venv/bin/activate
python worker.py
```

### Terminal 4: Mobile App
```bash
cd /Users/winstonyang/Desktop/Coding/Hackathons/hacknroll/Hack-Roll/mobile
npm start
```

---

## System Requirements

### Software Dependencies
- ✅ **Python 3.10+** (you have 3.14)
- ✅ **FFmpeg** (just installed - required for audio processing)
- ✅ **Redis** (check with `redis-cli ping`)
- ✅ **Node.js/npm** (for mobile app)
- **PostgreSQL Client** (optional, for direct DB access)

### Python ML Dependencies (in venv)
- PyTorch
- pyannote-audio
- transformers
- pydub (requires FFmpeg)
- librosa
- soundfile
- All listed in `backend/requirements.txt`

---

## Typical User Flow

1. **User starts recording** in mobile app
   - App sends `POST /sessions` → API creates session in DB
   - Returns `session_id`

2. **User continues recording**
   - Every 30 seconds, app sends `POST /sessions/{id}/chunks` → API
   - API uploads chunk to Supabase Storage
   - API creates `audio_chunks` record in DB

3. **User stops recording**
   - App sends `POST /sessions/{id}/end` → API
   - API queues job in Redis: `{"session_id": "...", "queued_at": "..."}`
   - API returns immediately

4. **Worker picks up job**
   - Downloads all chunks
   - Concatenates audio
   - Runs diarization (identifies speakers)
   - Runs transcription (converts speech to text)
   - Counts Singlish words per speaker
   - Updates `sessions` table with status: `completed`

5. **User views results**
   - App polls `GET /sessions/{id}` until status is `completed`
   - App fetches `GET /sessions/{id}/speakers` (list of speakers)
   - App fetches `GET /sessions/{id}/results` (word counts per speaker)
   - Displays "wrapped" screen

---

## Troubleshooting

### Audio Processing Fails - FFmpeg Missing
- **Error**: `[Errno 2] No such file or directory: 'ffprobe'`
- **Fix**: ✅ FFmpeg is now installed
- **Verify**: `ffprobe -version` should work

### Speaker Diarization Fails - Missing HuggingFace Token
- **Error**: `HUGGINGFACE_TOKEN environment variable is required`
- **Fix**: 
  1. Go to https://huggingface.co/settings/tokens
  2. Create a new token (Read access)
  3. Go to https://huggingface.co/pyannote/speaker-diarization-3.1
  4. Click "Agree and access repository"
  5. Add to `backend/.env`: `HUGGINGFACE_TOKEN=hf_your_token_here`
  6. Restart the worker
- **Verify**: Worker should download the model on first run (will take a few minutes)

### Worker Not Processing Jobs
- **Check Redis**: `redis-cli ping`
- **Check Queue**: `redis-cli LLEN lahstats:processing`
- **Check Worker Logs**: Look for errors in Terminal 3

### API Connection Issues
- **Check Backend is Running**: Visit `http://localhost:8000/docs`
- **Check `.env` Files**: Ensure all required variables are set
- **Check Ports**: Ensure port 8000 is not in use by another process

### Database Issues
- **Check Supabase Dashboard**: Verify tables exist
- **Run Migrations**: See `backend/migrations/README.md`
- **Check Credentials**: Ensure `SUPABASE_KEY` is correct in `.env`

---

## Quick Health Check

Run this script to verify all components:

```bash
#!/bin/bash

echo "=== Health Check ==="

# 1. Redis
echo -n "Redis: "
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Running"
else
    echo "❌ Not running - start with: redis-server"
fi

# 2. FFmpeg
echo -n "FFmpeg: "
if command -v ffprobe > /dev/null 2>&1; then
    echo "✅ Installed ($(ffprobe -version | head -1 | cut -d' ' -f3))"
else
    echo "❌ Not installed - run: brew install ffmpeg"
fi

# 3. Backend API
echo -n "Backend API: "
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Running on port 8000"
else
    echo "❌ Not running - start backend: uvicorn main:app --reload"
fi

# 4. Python venv
echo -n "Python venv: "
if [ -d "backend/venv" ]; then
    echo "✅ Exists"
else
    echo "❌ Missing - create with: python -m venv venv"
fi

# 5. Supabase connectivity
echo -n "Supabase: "
if curl -s https://tamrgxhjyabdvtubseyu.supabase.co > /dev/null 2>&1; then
    echo "✅ Reachable"
else
    echo "❌ Cannot connect"
fi
```

---

## Current Status

As of now:
- ✅ **FFmpeg**: Installed (version 8.0.1) - Working!
- ✅ **Supabase**: Running (cloud)
- ✅ **Redis**: Running (worker is connecting)
- ❌ **HuggingFace Token**: Missing - Required for speaker diarization
- ❓ **Backend API**: Status unknown - check with `curl http://localhost:8000/docs`
- 🔄 **Worker**: Running but failing due to missing HuggingFace token
- ❓ **Mobile App**: Status unknown

**Next steps:**
1. **CRITICAL**: Add `HUGGINGFACE_TOKEN` to `backend/.env`:
   - Get token from: https://huggingface.co/settings/tokens
   - Accept pyannote terms: https://huggingface.co/pyannote/speaker-diarization-3.1
   - Add to `.env`: `HUGGINGFACE_TOKEN=hf_your_token_here`
2. Restart the worker after adding the token
3. Check if there are any pending jobs: `redis-cli LLEN lahstats:processing`
