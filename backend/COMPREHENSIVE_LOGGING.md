# Comprehensive Logging Guide

## Overview

Enhanced logging has been added throughout the audio recording pipeline to help you track exactly what's happening as audio chunks are uploaded and processed.

## What's Been Added

### 1. Request-Level Logging (main.py)
Every HTTP request is now logged with:
- Request method and path
- Query parameters
- Response status code
- Response time

**Example output:**
```
🌐 POST /sessions
✅ POST /sessions → 201 (0.15s)

🌐 POST /sessions/abc123/chunks
✅ POST /sessions/abc123/chunks → 200 (0.45s)

🌐 POST /sessions/abc123/end
✅ POST /sessions/abc123/end → 200 (0.12s)
```

### 2. Session Creation Logging (routers/sessions.py)
When a new session is created:
```
================================================================================
🎙️  NEW SESSION REQUEST
   User: 12345678-abcd-1234-5678-123456789abc (john_doe)
   Group ID: None (Personal session)
   ✓ User is member of group abc123
✅ Session created successfully
   Session ID: def456
   Status: recording
   Started at: 2026-01-17 15:30:00
🎬 Ready to receive audio chunks...
================================================================================
```

### 3. Chunk Upload Logging (routers/sessions.py)
For every audio chunk uploaded:
```
================================================================================
📥 CHUNK UPLOAD REQUEST - Session: def456
   File: audio.webm, Content-Type: audio/webm
   Duration: 30.0s
   User: 12345678-abcd-1234-5678-123456789abc
   Session status: recording
📤 Uploading chunk #1 for session def456
   Total chunks so far: 0
✅ Chunk uploaded to Supabase Storage
   Storage path: sessions/def456/chunks/chunk_0001_20260117_153015.webm
✅ Chunk #1 record saved to database
   Session now has 1 chunk(s)
================================================================================
```

### 4. Session End & Job Queueing (routers/sessions.py)
When the recording stops:
```
================================================================================
🛑 END SESSION REQUEST - Session: def456
   User: 12345678-abcd-1234-5678-123456789abc
   Final duration: 90.5s
   Session has 3 audio chunk(s)
📝 Updating session status: recording → processing
✅ Session status updated in database
📮 Queueing job to Redis...
✅ Job queued successfully to Redis
   Queue: lahstats:processing
   Queue length: 1
   Payload: {"session_id": "def456", "queued_at": "2026-01-17T15:32:30.123456"}
🎬 Worker should pick this up shortly...
================================================================================
```

### 5. Worker Processing (worker.py)
The worker already has comprehensive logging showing:
- When jobs are picked up from Redis
- Audio download progress
- FFmpeg conversion
- Diarization and transcription progress
- Word counting results
- Database updates

**Example output:**
```
======================================================================
🎬 Processing session: def456
   Queued at: 2026-01-17T15:32:30.123456
----------------------------------------------------------------------
📥 Found 3 chunks to concatenate
✅ Concatenated audio: 90.5s
🔊 Running diarization...
   Detected 2 speakers
📝 Transcribing audio...
   Transcription complete: 450 words
📊 Counting Singlish words...
   Speaker 0: 23 words
   Speaker 1: 18 words
✅ Session completed successfully
======================================================================
```

## How to View Logs

### Backend API Logs (Terminal)

When you run the backend API:
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

You'll see logs directly in this terminal for:
- Session creation
- Chunk uploads
- Session ending
- Job queueing

### Worker Logs (Terminal)

The worker terminal (Terminal 11) shows:
- Job pickup from Redis
- Audio processing pipeline
- ML model execution
- Results saving

### Combined View

**Recommended setup for testing:**

**Terminal 1: Backend API**
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000 | tee backend.log
```

**Terminal 2: Worker**
```bash
cd backend
source venv/bin/activate
python worker.py | tee worker.log
```

This saves logs to files while displaying them, so you can review later.

## Log Levels

The logging uses different levels:
- **INFO**: Normal operations (green ✅, blue 🌐, etc.)
- **WARNING**: Potential issues (yellow ⚠️)
- **ERROR**: Failures (red ❌)
- **DEBUG**: Detailed information (only in DEBUG mode)

## What to Look For

### Successful Recording Flow

1. ✅ Session created
2. ✅ Multiple chunk uploads (one every ~30 seconds)
3. ✅ Session ended
4. ✅ Job queued to Redis
5. ✅ Worker picks up job
6. ✅ Audio concatenated
7. ✅ Diarization runs
8. ✅ Transcription completes
9. ✅ Words counted
10. ✅ Results saved

### Common Issues to Watch For

**No chunks received:**
```
🛑 END SESSION REQUEST
   Session has 0 audio chunk(s)
```
→ Frontend isn't sending chunks or API isn't receiving them

**Job not picked up:**
```
✅ Job queued successfully to Redis
   Queue length: 1
(Worker shows no activity)
```
→ Worker not running or Redis connection issue

**FFmpeg errors:**
```
⚠️  Couldn't find ffprobe or avprobe
```
→ FFmpeg not installed (should be fixed now)

**HuggingFace errors:**
```
❌ HUGGINGFACE_TOKEN environment variable is required
```
→ Token missing or invalid (should be fixed now)

## Debugging Tips

### 1. Check Each Component

```bash
# Backend API running?
curl http://localhost:8000/health

# Redis running?
redis-cli ping

# Worker running?
ps aux | grep "python worker.py"
```

### 2. Check Redis Queue

```bash
# How many jobs are queued?
redis-cli LLEN lahstats:processing

# View queued jobs
redis-cli LRANGE lahstats:processing 0 -1

# View failed jobs
redis-cli LRANGE lahstats:failed 0 -1
```

### 3. Filter Logs by Session

If you have a specific session ID:
```bash
# Backend logs
grep "def456" backend.log

# Worker logs
grep "def456" worker.log
```

### 4. Watch Logs in Real-Time

```bash
# Backend
tail -f backend.log | grep "📥\|📤\|🛑\|✅\|❌"

# Worker
tail -f worker.log | grep "🎬\|✅\|❌"
```

## Example Full Flow

Here's what you should see for a complete recording:

```
# BACKEND API TERMINAL
================================================================================
🎙️  NEW SESSION REQUEST
   User: abc123 (test_user)
   Group ID: Personal session
✅ Session created successfully
   Session ID: session-1
================================================================================

================================================================================
📥 CHUNK UPLOAD REQUEST - Session: session-1
   File: chunk.webm, Content-Type: audio/webm
   Duration: 30.0s
📤 Uploading chunk #1
✅ Chunk #1 record saved to database
================================================================================

# ... more chunks ...

================================================================================
🛑 END SESSION REQUEST - Session: session-1
   Session has 3 audio chunk(s)
📮 Queueing job to Redis...
✅ Job queued successfully
🎬 Worker should pick this up shortly...
================================================================================

# WORKER TERMINAL
======================================================================
🎬 Processing session: session-1
----------------------------------------------------------------------
📥 Found 3 chunks to concatenate
✅ Concatenated audio: 90.5s
🔊 Running diarization...
   Detected 2 speakers
📝 Transcribing audio...
📊 Counting Singlish words...
✅ Processing complete!
======================================================================
```

## Turning Off Verbose Logging

If the logs are too verbose for production, edit `backend/config.py`:

```python
# Change DEBUG mode
DEBUG = False  # Reduces log verbosity
```

Or set the log level in worker.py:
```python
logging.basicConfig(level=logging.WARNING)  # Only show warnings and errors
```

---

**Ready to test!** Start the backend API and worker, then record some audio from the mobile app. Watch the logs in real-time to see the full pipeline in action! 🚀
