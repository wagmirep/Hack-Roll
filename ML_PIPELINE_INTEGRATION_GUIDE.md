# ML Pipeline Integration Guide

This guide explains how the audio recording, ML processing (transcription + diarization), and Wrapped stats flow together.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND (Browser/Mobile)                     │
│                                                                   │
│  1. User starts recording                                        │
│     → Creates session via /sessions (POST)                      │
│     → Uploads audio chunks every 30s via /sessions/{id}/chunks    │
│     → Stops recording → calls /sessions/{id}/end                │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                       BACKEND API                                │
│                                                                   │
│  2. /sessions/{id}/end endpoint:                                 │
│     → Marks session status = "processing"                        │
│     → Queues job to Redis queue "lahstats:processing"            │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    WORKER (Background Job)                        │
│                                                                   │
│  3. Worker picks up job from Redis queue                         │
│     → Calls processor.process_session_sync(session_id)           │
│                                                                   │
│  4. Processing Pipeline:                                         │
│     a. Concatenate audio chunks into full audio                  │
│     b. Run speaker diarization (pyannote) → identifies speakers  │
│     c. Transcribe each speaker segment (MERaLiON ASR)           │
│     d. Apply Singlish corrections                                │
│     e. Count target words per speaker                            │
│     f. Save to SessionSpeaker + SpeakerWordCount tables          │
│     g. Mark session status = "ready_for_claiming"                │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    USER CLAIMING                                 │
│                                                                   │
│  5. Users claim speakers via /sessions/{id}/claim               │
│     → When claiming as 'self' or 'user':                        │
│       Creates WordCount records from SpeakerWordCount            │
│                                                                   │
│  6. After all speakers claimed:                                  │
│     → Session status = "completed"                                │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    STATS & WRAPPED                                │
│                                                                   │
│  7. Wrapped/Stats endpoints read from WordCount table:          │
│     → /users/me/wrapped → aggregates WordCount by user           │
│     → /users/me/stats → personal statistics                      │
│     → /groups/{id}/stats → group statistics                      │
└─────────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. Frontend Recording (`mobile/src/hooks/useRecording.ts`)
- Records audio using Expo Audio API
- Uploads chunks every 30 seconds to `/sessions/{session_id}/chunks`
- Calls `/sessions/{session_id}/end` when recording stops

### 2. Backend Session Endpoint (`backend/routers/sessions.py`)
- `/sessions/{id}/end`: Marks session as "processing" and queues job to Redis

### 3. Worker (`backend/worker.py`)
- Listens to Redis queue `lahstats:processing`
- Processes sessions asynchronously
- Updates session status and progress

### 4. Processor (`backend/processor.py`)
- `process_session()`: Full ML pipeline
  - Concatenates chunks
  - Diarization (identifies speakers)
  - Transcription (converts speech to text)
  - Word counting (counts Singlish words)
  - Saves to `SessionSpeaker` and `SpeakerWordCount` tables

### 5. Claiming (`backend/routers/sessions.py`)
- `/sessions/{id}/claim`: Users claim speakers
- Creates `WordCount` records when claiming as 'self' or 'user'

### 6. Stats/Wrapped (`backend/routers/stats.py`)
- `/users/me/wrapped`: Reads from `WordCount` table
- Aggregates word counts by user for year recap

## Database Tables Flow

1. **Session** → Created when recording starts
2. **AudioChunk** → Created when chunks are uploaded
3. **SessionSpeaker** → Created during processing (after diarization)
4. **SpeakerWordCount** → Created during processing (word counts per speaker)
5. **WordCount** → Created when speakers are claimed (links to users)

## Setup Requirements

### 1. Redis Server
The worker requires Redis to queue processing jobs:

```bash
# Using Docker
docker run -d -p 6379:6379 redis:latest

# Or locally
redis-server
```

### 2. Environment Variables
Ensure these are set in `backend/.env`:
```bash
REDIS_URL=redis://localhost:6379
SUPABASE_URL=your_supabase_url
SUPABASE_JWT_SECRET=your_jwt_secret
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

### 3. Worker Process
The worker must be running to process sessions:

```bash
# From backend directory
python worker.py
```

Or use the provided scripts:
```bash
# Start backend + worker together
./start.sh
```

### 4. ML Models
- **Diarization**: Requires HuggingFace token (set `HUGGINGFACE_TOKEN`)
- **Transcription**: Either:
  - Local MERaLiON model (default)
  - External API (set `TRANSCRIPTION_API_URL`)

## Testing the Integration

1. **Start Redis**:
   ```bash
   docker run -d -p 6379:6379 redis:latest
   ```

2. **Start Backend**:
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

3. **Start Worker** (in separate terminal):
   ```bash
   cd backend
   python worker.py
   ```

4. **Start Frontend** and record audio:
   - Recording uploads chunks automatically
   - Stop recording triggers processing
   - Worker processes session in background
   - Check session status via `/sessions/{id}`

5. **Claim Speakers**:
   - Get speakers via `/sessions/{id}/speakers`
   - Claim speakers via `/sessions/{id}/claim`
   - WordCount records are created

6. **View Stats/Wrapped**:
   - `/users/me/wrapped` shows aggregated stats
   - `/users/me/stats` shows personal statistics

## Troubleshooting

### Sessions stuck in "processing"
- Check if worker is running: `python worker.py`
- Check Redis connection: `redis-cli ping`
- Check worker logs for errors

### No speakers detected
- Verify audio quality (16kHz mono recommended)
- Check diarization logs
- Ensure HuggingFace token is set

### WordCount table empty
- Remember: WordCount is only created AFTER claiming speakers
- Check `SpeakerWordCount` table for unclaimed speakers
- Use `/sessions/{id}/speakers` to see available speakers

### Wrapped shows no data
- Ensure speakers have been claimed
- Check `WordCount` table has records
- Verify date range (Wrapped shows current year by default)

## Data Flow Summary

```
Recording → Chunks → Processing Queue → Worker → ML Pipeline → 
SessionSpeaker + SpeakerWordCount → User Claims → WordCount → 
Stats/Wrapped
```

The key insight: **WordCount records are created only after users claim speakers**. This allows flexible attribution (self, user, or guest).
