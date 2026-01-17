# Quick Start: ML Pipeline Integration

This is a quick reference guide for connecting the ML pipeline to your web application.

## ✅ What's Already Set Up

The integration is **already built and connected**! Here's what exists:

1. ✅ **Recording** → Audio chunks uploaded to backend
2. ✅ **Processing Queue** → Sessions queued to Redis when recording stops
3. ✅ **Worker** → Processes sessions with transcription + diarization
4. ✅ **Database** → Results saved to `SessionSpeaker` and `SpeakerWordCount`
5. ✅ **Claiming** → Users claim speakers, creating `WordCount` records
6. ✅ **Stats/Wrapped** → Reads from `WordCount` table

## 🚀 Quick Start (3 Steps)

### Step 1: Start Redis

```bash
# Using Docker (recommended)
docker run -d -p 6379:6379 redis:latest

# Or locally (macOS)
brew services start redis
```

Verify it's running:
```bash
redis-cli ping
# Should return: PONG
```

### Step 2: Start Backend + Worker

**Option A: Using start.sh (recommended)**
```bash
cd Hack-Roll/backend
./start.sh
```

**Option B: Manual (two terminals)**

Terminal 1 - API Server:
```bash
cd Hack-Roll/backend
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

Terminal 2 - Worker:
```bash
cd Hack-Roll/backend
source venv/bin/activate
python worker.py
```

### Step 3: Start Frontend

```bash
cd Hack-Roll/mobile
npm start
```

## 📋 Verify Everything Works

Run the verification script:

```bash
cd Hack-Roll/backend
python verify_integration.py
```

This checks:
- ✅ Redis connection
- ✅ Database connection
- ✅ ML models configuration
- ✅ API endpoints
- ✅ Worker readiness
- ✅ Storage configuration

## 🔄 Complete Flow

1. **Record Audio** (Browser/Mobile)
   - User starts recording
   - Chunks uploaded every 30 seconds
   - User stops recording

2. **Processing** (Automatic)
   - Session ends → Queued to Redis
   - Worker picks up job
   - Transcription + Diarization runs
   - Results saved to database

3. **Claim Speakers** (User Action)
   - User views speakers via `/sessions/{id}/speakers`
   - User claims speakers via `/sessions/{id}/claim`
   - `WordCount` records created

4. **View Stats/Wrapped**
   - `/users/me/wrapped` shows year recap
   - `/users/me/stats` shows personal stats
   - `/groups/{id}/stats` shows group stats

## ⚠️ Important Notes

### WordCount Records Are Created After Claiming

The `WordCount` table (used by Wrapped/stats) is **only populated after users claim speakers**. This is by design:

- **SpeakerWordCount** → Created automatically during processing (per speaker)
- **WordCount** → Created when users claim speakers (per user)

This allows flexible attribution (self, user, or guest).

### Worker Must Be Running

The ML processing **only happens if the worker is running**. If sessions are stuck in "processing" status:

1. Check if worker is running: `ps aux | grep worker.py`
2. Check Redis: `redis-cli ping`
3. Check worker logs for errors

### Processing Time

- **Small sessions** (< 1 min): ~30-60 seconds
- **Medium sessions** (1-5 min): ~2-5 minutes
- **Large sessions** (> 5 min): ~5-15 minutes

Processing happens in background, so users can continue using the app.

## 🐛 Troubleshooting

### Sessions stuck in "processing"
```bash
# Check worker is running
ps aux | grep worker.py

# Check Redis
redis-cli ping

# Check queue
redis-cli LLEN lahstats:processing
```

### No speakers detected
- Verify audio quality (16kHz mono recommended)
- Check `HUGGINGFACE_TOKEN` is set
- Check worker logs for diarization errors

### WordCount table empty
- Remember: WordCount is created AFTER claiming
- Use `/sessions/{id}/speakers` to see available speakers
- Claim speakers via `/sessions/{id}/claim`

### Wrapped shows no data
- Ensure speakers have been claimed
- Check `WordCount` table has records
- Verify date range (Wrapped shows current year by default)

## 📚 More Information

- **Full Integration Guide**: See `ML_PIPELINE_INTEGRATION_GUIDE.md`
- **Running the App**: See `RUNNING_THE_APP.md`
- **ML Pipeline Details**: See `ML_PIPELINE_COMPLETE.md`

## 🔗 Key Files

- `backend/routers/sessions.py` → Session endpoints
- `backend/processor.py` → ML processing pipeline
- `backend/worker.py` → Background job worker
- `backend/routers/stats.py` → Stats/Wrapped endpoints
- `mobile/src/hooks/useRecording.ts` → Recording logic
