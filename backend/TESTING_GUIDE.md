# Integration Testing Guide

## Quick Start

### Prerequisites

1. **Backend running:**
```bash
cd Hack-Roll/backend
source venv/bin/activate
uvicorn main:app --reload
```

2. **Worker running** (in separate terminal):
```bash
cd Hack-Roll/backend
source venv/bin/activate
python worker.py
```

3. **Redis running:**
```bash
# Check if Redis is running
redis-cli ping
# Should return: PONG

# If not running, start Redis:
redis-server
# Or with Homebrew: brew services start redis
```

### Get Authentication Token

Since authentication is handled by Supabase, you need a JWT token:

**Option 1: Via Mobile App (Easiest)**
1. Login to the mobile app
2. The app stores the JWT token
3. Extract it from the app's storage/logs

**Option 2: Via Supabase Dashboard**
1. Go to Supabase Dashboard → Authentication → Users
2. Find your test user
3. Click to view JWT token

**Option 3: Via Supabase API (Manual)**
```bash
curl -X POST https://tamrgxhjyabdvtubseyu.supabase.co/auth/v1/token?grant_type=password \
  -H "Content-Type: application/json" \
  -H "apikey: YOUR_SUPABASE_ANON_KEY" \
  -d '{
    "email": "test@example.com",
    "password": "your-password"
  }'
```

This returns:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "...",
  "user": {...}
}
```

Use the `access_token` value.

### Run Integration Test

```bash
cd Hack-Roll/backend
source venv/bin/activate

# Set your JWT token
export AUTH_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Run the test
python test_frontend_integration.py
```

### Expected Output

```
======================================================================
🚀 LahStats Frontend-Backend Integration Test
======================================================================

ℹ API Base: http://localhost:8000
ℹ Auth Token: ✓ Provided

======================================================================
Phase 1: Authentication Check
======================================================================

✓ Authenticated as: your_username

======================================================================
Phase 2: Session Creation
======================================================================

✓ Created session: a1b2c3d4-...
ℹ Status: recording, Progress: 0%

======================================================================
Phase 3: Upload Audio Chunks
======================================================================

✓ Uploaded chunk 1
ℹ Storage path: audio_chunks/a1b2c3d4-.../chunk_1.wav
✓ Uploaded chunk 2
...

======================================================================
Phase 4: End Session
======================================================================

✓ Session ended, processing started
ℹ Status: processing

======================================================================
Phase 5: Status Polling
======================================================================

ℹ ⏳ Waiting for processing (this may take 1-2 minutes)...
ℹ Status: processing, Progress: 10%
ℹ Status: processing, Progress: 40%
ℹ Status: processing, Progress: 85%
✓ Processing complete!

======================================================================
Phase 6: Retrieve Speakers
======================================================================

✓ Found 2 speaker(s)
ℹ Speaker SPEAKER_00:
  - Segments: 5
  - Words detected: 3
    • walao: 2
    • lah: 5
    • sia: 1
  - Sample audio: ✓

======================================================================
Phase 7: Claim Speaker
======================================================================

✓ Speaker claimed successfully
ℹ Message: Speaker claimed as yourself

======================================================================
Phase 8: Retrieve Results
======================================================================

✓ Retrieved results
ℹ Users: 1
ℹ All claimed: false
  - your_username: 8 total words

======================================================================
✅ All Tests Passed!
======================================================================

SUCCESS: Integration test passed!
```

## Troubleshooting

### "No AUTH_TOKEN provided!"
**Solution:** Set the AUTH_TOKEN environment variable
```bash
export AUTH_TOKEN="your-jwt-token-here"
```

### "Token validation failed: 401"
**Solution:** Your JWT token is expired. Get a new one from Supabase.

### "Connection refused" or "Network error"
**Solution:** Make sure the backend is running on localhost:8000
```bash
# In backend directory:
uvicorn main:app --reload
```

### "Status: failed" during processing
**Solution:** Check worker logs for errors
- Make sure worker is running: `python worker.py`
- Check Redis connection: `redis-cli ping`
- View worker output for detailed error messages

### Processing never completes
**Possible causes:**
1. Worker not running → Start worker: `python worker.py`
2. Redis not running → Start Redis: `redis-server`
3. ML models not loaded → Check worker logs for model loading errors
4. No HuggingFace token → Set HUGGINGFACE_TOKEN in .env

### "No speakers detected" (test data issue)
**Solution:** The test uses fake audio data, which won't have actual speech. This is expected.

For real testing, use actual audio files:
```python
# Modify test_chunk_upload() to use real audio:
with open("real_audio.wav", "rb") as f:
    audio_content = f.read()
```

## Manual API Testing

If the integration test fails, you can test endpoints individually:

### 1. Test Authentication
```bash
curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 2. Test Session Creation
```bash
curl -X POST http://localhost:8000/sessions \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"group_id": null}'
```

### 3. Test Chunk Upload
```bash
curl -X POST http://localhost:8000/sessions/SESSION_ID/chunks \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test.wav" \
  -F "duration_seconds=30"
```

### 4. Test Session End
```bash
curl -X POST http://localhost:8000/sessions/SESSION_ID/end \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"final_duration_seconds": 90}'
```

### 5. Check Status
```bash
curl http://localhost:8000/sessions/SESSION_ID \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Success Criteria

✅ All phases pass without errors  
✅ Session status transitions: recording → processing → ready_for_claiming  
✅ Speakers are detected (with real audio)  
✅ Word counts are populated  
✅ Claiming works  
✅ Results are retrieved  

## Next Steps

After successful integration test:
1. Test with real audio files
2. Test with multiple speakers
3. Test mobile app integration
4. Monitor production sessions
