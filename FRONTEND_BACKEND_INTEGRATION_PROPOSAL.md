# Frontend-Backend Integration Proposal

## Overview
This document proposes the connections between the mobile frontend and the backend API, specifically focusing on integrating the **ML audio processing pipeline** (MERaLiON transcription + pyannote diarization) with the existing mobile app flow.

---

## Current State Analysis

### ✅ What's Already Connected (Working)

The mobile app **already has** API client methods for:

1. **Authentication** ✅
   - `/auth/me` - Get current user
   - `/auth/profile` - Update profile
   
2. **Groups** ✅
   - `POST /groups` - Create group
   - `POST /groups/join` - Join with invite code
   - `GET /groups/{id}` - Get group details
   - `GET /groups/{id}/members` - Get members
   - `GET /groups/{id}/stats` - Get group stats

3. **Sessions** ✅
   - `GET /sessions` - List sessions with filters
   - `POST /sessions` - Create new session
   - `POST /sessions/{id}/chunks` - Upload audio chunks
   - `POST /sessions/{id}/end` - End session
   - `GET /sessions/{id}` - Get session status
   - `GET /sessions/{id}/speakers` - Get speakers for claiming
   - `POST /sessions/{id}/claim` - Claim a speaker
   - `GET /sessions/{id}/results` - Get final results
   - `GET /sessions/{id}/my-stats` - Get user's stats for session

4. **Stats** ✅
   - `GET /users/me/stats` - Personal stats
   - `GET /users/me/wrapped` - Year in review
   - `GET /users/me/trends` - Trend data
   - `GET /users/global/leaderboard` - Global leaderboard

### ⚠️ What's NOT Connected (Missing)

The **ML audio processing** pipeline is NOT integrated:

1. **Audio Processing**
   - Backend has `processor.py` with full ML pipeline
   - Frontend uploads audio chunks but backend doesn't process them
   - No real speaker diarization happening
   - No real transcription happening
   - Mock data is being returned

2. **Real-time Processing Updates**
   - No polling/websocket for processing progress
   - Frontend screens expect processing but it's not wired up

---

## 🎯 Proposed Integrations

### Priority 1: Wire Up ML Audio Processing Pipeline

**What needs to happen:**

#### Backend Changes:

1. **Modify `POST /sessions/{id}/end` endpoint** (`routers/sessions.py:218`)
   ```python
   # Currently: Mock processing
   # TODO: Queue background processing job
   
   # Change to: Trigger actual processing
   from processor import process_session
   
   @router.post("/{session_id}/end")
   async def end_session(...):
       # ... existing code ...
       
       # BEFORE: session.status = "processing" (then nothing happens)
       
       # AFTER: Trigger background job
       session.status = "processing"
       db.commit()
       
       # Option A: Background task (FastAPI)
       background_tasks.add_task(process_session, session_id, db)
       
       # Option B: Redis queue worker (better for production)
       # queue.enqueue(process_session, session_id)
       
       return session
   ```

2. **Create background processing function**
   ```python
   # In processor.py or new file: background_jobs.py
   
   async def process_session(session_id: UUID, db: Session):
       """
       Background job that:
       1. Downloads all chunks from storage
       2. Concatenates audio
       3. Runs speaker diarization (pyannote)
       4. Runs transcription per speaker (MERaLiON)
       5. Applies Singlish corrections
       6. Counts target words
       7. Creates SessionSpeaker records
       8. Updates session status to "ready_for_claiming"
       """
       try:
           session = db.query(SessionModel).get(session_id)
           session.status = "processing"
           session.progress = 10
           db.commit()
           
           # Step 1: Get audio chunks from storage
           chunks = download_session_chunks(session_id, db)
           session.progress = 20
           db.commit()
           
           # Step 2: Concatenate audio
           full_audio_path = concatenate_audio_chunks(chunks)
           session.progress = 30
           db.commit()
           
           # Step 3: Speaker diarization
           from services.diarization import diarize_audio
           diarization = diarize_audio(full_audio_path)
           session.progress = 50
           db.commit()
           
           # Step 4: Transcribe each speaker segment
           from services.transcription import transcribe_segment, process_transcription
           speakers_data = []
           
           for speaker_label, segments in diarization.items():
               # Extract audio for this speaker
               speaker_audio = extract_speaker_audio(full_audio_path, segments)
               
               # Transcribe
               raw_text = transcribe_segment(speaker_audio)
               
               # Apply corrections and count words
               corrected_text, word_counts = process_transcription(raw_text)
               
               speakers_data.append({
                   'label': speaker_label,
                   'text': corrected_text,
                   'word_counts': word_counts,
                   'segments': segments,
                   'duration': sum(s['end'] - s['start'] for s in segments)
               })
           
           session.progress = 80
           db.commit()
           
           # Step 5: Create SessionSpeaker records
           for speaker in speakers_data:
               # Get sample audio segment
               sample_segment = speaker['segments'][0]
               sample_audio_url = upload_sample_audio(
                   full_audio_path, 
                   sample_segment['start'], 
                   sample_segment['end']
               )
               
               db_speaker = SessionSpeaker(
                   session_id=session_id,
                   speaker_label=speaker['label'],
                   segment_count=len(speaker['segments']),
                   total_duration_seconds=speaker['duration'],
                   transcription_preview=speaker['text'][:200],
                   word_counts=speaker['word_counts'],
                   sample_audio_url=sample_audio_url,
                   sample_start_time=sample_segment['start']
               )
               db.add(db_speaker)
           
           # Step 6: Update session
           session.status = "ready_for_claiming"
           session.progress = 100
           session.speaker_count = len(speakers_data)
           session.total_words_detected = sum(
               sum(s['word_counts'].values()) for s in speakers_data
           )
           db.commit()
           
       except Exception as e:
           logger.error(f"Processing failed for session {session_id}: {e}")
           session.status = "failed"
           session.error_message = str(e)
           db.commit()
   ```

#### Frontend Changes:

1. **Update ProcessingScreen to poll for status**
   ```typescript
   // In ProcessingScreen.tsx
   
   useEffect(() => {
       const pollInterval = setInterval(async () => {
           try {
               const session = await api.sessions.getStatus(sessionId);
               
               setProgress(session.progress || 0);
               setStatus(session.status);
               
               if (session.status === 'ready_for_claiming') {
                   clearInterval(pollInterval);
                   navigation.navigate('Claiming', { sessionId });
               } else if (session.status === 'failed') {
                   clearInterval(pollInterval);
                   Alert.alert('Processing Failed', session.error_message);
               }
           } catch (error) {
               console.error('Error polling status:', error);
           }
       }, 2000); // Poll every 2 seconds
       
       return () => clearInterval(pollInterval);
   }, [sessionId]);
   ```

2. **Claiming screen is already good** ✅
   - Already calls `api.sessions.getSpeakers()`
   - Already calls `api.sessions.claimSpeaker()`
   - Just needs real data from backend

3. **Results screen is already good** ✅
   - Already calls `api.sessions.getResults()`
   - Just needs real data from backend

---

### Priority 2: Optimize Audio Upload

**Current State:**
- Frontend uploads chunks during recording ✅
- Backend saves chunks to storage ✅
- Backend doesn't concatenate or process them ⚠️

**Proposed Enhancement:**

1. **Add chunk validation**
   ```python
   # In POST /sessions/{id}/chunks
   
   # Validate audio format
   if not file.content_type.startswith('audio/'):
       raise HTTPException(400, "Must be audio file")
   
   # Check chunk size (max 10MB per chunk)
   if file.size > 10 * 1024 * 1024:
       raise HTTPException(400, "Chunk too large")
   ```

2. **Track upload progress**
   ```python
   # Add to SessionModel
   chunks_uploaded: int = Column(Integer, default=0)
   total_chunks: int = Column(Integer, nullable=True)
   
   # In upload endpoint
   session.chunks_uploaded += 1
   ```

---

### Priority 3: Add Real-time Updates (Optional, Later)

**Instead of polling, use WebSockets or Server-Sent Events:**

```python
# Backend: Add WebSocket endpoint
from fastapi import WebSocket

@router.websocket("/sessions/{session_id}/ws")
async def session_updates(websocket: WebSocket, session_id: UUID):
    await websocket.accept()
    
    while True:
        # Send updates when processing progress changes
        session = db.query(SessionModel).get(session_id)
        await websocket.send_json({
            'status': session.status,
            'progress': session.progress
        })
        
        if session.status in ['ready_for_claiming', 'completed', 'failed']:
            break
        
        await asyncio.sleep(1)
```

```typescript
// Frontend: Connect to WebSocket
const ws = new WebSocket(`ws://localhost:8000/sessions/${sessionId}/ws`);

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    setProgress(data.progress);
    setStatus(data.status);
    
    if (data.status === 'ready_for_claiming') {
        navigation.navigate('Claiming', { sessionId });
    }
};
```

---

### Priority 4: Storage Integration

**Current State:**
- Backend has `storage.py` (S3/Supabase storage) ✅
- Not fully integrated with audio chunks

**Proposed:**

1. **Use Supabase Storage** (since you're already using Supabase)
   ```python
   # In storage.py - update to use Supabase Storage API
   
   from supabase import create_client
   
   supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
   
   def upload_chunk(session_id: UUID, chunk_index: int, file_data: bytes):
       bucket_name = "session-audio"
       file_path = f"{session_id}/chunk_{chunk_index}.webm"
       
       supabase.storage.from_(bucket_name).upload(
           file_path,
           file_data,
           {'content-type': 'audio/webm'}
       )
       
       return f"{settings.SUPABASE_URL}/storage/v1/object/public/{bucket_name}/{file_path}"
   
   def download_chunks(session_id: UUID):
       """Download all chunks for a session and concatenate"""
       # Implementation here
   ```

---

## 📋 Implementation Plan

### Phase 1: Basic ML Integration (1-2 days)
**Goal:** Get real transcription and diarization working

1. ✅ Create background processing function in `processor.py`
2. ✅ Wire up `/sessions/{id}/end` to trigger processing
3. ✅ Test with FastAPI BackgroundTasks (simple, no Redis needed yet)
4. ✅ Verify ProcessingScreen polls and gets updates
5. ✅ Test full flow: Record → Upload → Process → Claim → Results

**Files to modify:**
- `backend/routers/sessions.py` (add background task trigger)
- `backend/processor.py` (implement `process_session()`)
- `mobile/src/screens/ProcessingScreen.tsx` (add polling)

### Phase 2: Storage & Optimization (1 day)
**Goal:** Proper audio storage and retrieval

1. ✅ Integrate Supabase Storage for chunks
2. ✅ Add chunk validation
3. ✅ Implement audio concatenation
4. ✅ Add sample audio generation for speakers

**Files to modify:**
- `backend/storage.py`
- `backend/routers/sessions.py`

### Phase 3: Polish & Error Handling (1 day)
**Goal:** Production-ready error handling

1. ✅ Add retry logic for ML models
2. ✅ Better error messages
3. ✅ Timeout handling
4. ✅ Progress tracking accuracy

### Phase 4: Real-time Updates (Optional, 1 day)
**Goal:** Better UX with WebSockets

1. ✅ Add WebSocket endpoint
2. ✅ Update frontend to use WebSocket
3. ✅ Fallback to polling if WebSocket fails

---

## 🔌 Connection Summary

### What's Connected Now:
```
Mobile App → Backend API → Database ✅
Mobile App → Supabase Auth ✅
```

### What Needs Connecting:
```
Backend API → ML Pipeline (processor.py) ⚠️
Backend API → Audio Storage ⚠️
Backend Background Jobs → ML Processing ⚠️
```

### After Integration:
```
Mobile App → Backend API → Background Job → ML Pipeline → Database → Mobile App ✅
              ↓
         Audio Storage
```

---

## 🎬 User Flow (After Integration)

1. **User starts recording** → `POST /sessions` → Creates session in DB
2. **User records** → Audio chunks uploaded → `POST /sessions/{id}/chunks` → Saved to storage
3. **User stops recording** → `POST /sessions/{id}/end` → Triggers background processing
4. **Background processing** (30-60 seconds):
   - Downloads chunks from storage
   - Concatenates audio
   - Runs speaker diarization (pyannote)
   - Transcribes each speaker (MERaLiON)
   - Applies Singlish corrections
   - Counts target words
   - Creates speaker records
   - Updates status to "ready_for_claiming"
5. **ProcessingScreen polls** → `GET /sessions/{id}` → Shows progress
6. **Processing completes** → Navigate to ClaimingScreen
7. **Users claim speakers** → `GET /sessions/{id}/speakers` → Show speakers with previews
8. **User claims** → `POST /sessions/{id}/claim` → Links speaker to user
9. **View results** → `GET /sessions/{id}/results` → Shows final stats

---

## 💡 Key Design Decisions

### 1. Background Processing vs Synchronous
**Decision:** Use background processing
**Reason:** ML processing takes 30-60 seconds, can't block API response

**Options:**
- **Option A:** FastAPI BackgroundTasks (simple, good for development)
- **Option B:** Redis + Celery (production-grade, better monitoring)
- **Option C:** Supabase Edge Functions (serverless, auto-scaling)

**Recommendation:** Start with Option A, migrate to B for production

### 2. Real-time Updates: Polling vs WebSocket
**Decision:** Start with polling, add WebSocket later
**Reason:** Polling is simpler, WebSocket is better UX

**Polling:** Simple, works everywhere, 2-5 second delay acceptable
**WebSocket:** Real-time, but more complex, needs infrastructure

### 3. Storage: Local vs S3 vs Supabase
**Decision:** Use Supabase Storage
**Reason:** Already using Supabase, integrated auth, simple API

### 4. Audio Format
**Current:** WebM (frontend default)
**Needed:** WAV for ML models
**Solution:** Convert on backend using pydub/ffmpeg

---

## ⚡ Quick Start Implementation

**Minimal changes to get it working:**

1. **Backend** (1 file change):
   ```python
   # routers/sessions.py
   from fastapi import BackgroundTasks
   from processor import process_session_background
   
   @router.post("/{session_id}/end")
   async def end_session(
       background_tasks: BackgroundTasks,  # ADD THIS
       ...
   ):
       # ... existing code ...
       session.status = "processing"
       db.commit()
       
       # ADD THIS LINE
       background_tasks.add_task(process_session_background, str(session_id))
       
       return session
   ```

2. **Frontend** (1 file change):
   ```typescript
   // ProcessingScreen.tsx
   // Add polling useEffect (see Priority 1 above)
   ```

That's it! 🎉 The rest is just optimization.

---

## 📊 Expected Performance

### Processing Time Breakdown:
- Download chunks: 2-5 seconds
- Concatenate audio: 1-2 seconds
- Speaker diarization: 10-20 seconds (GPU: 5-10 seconds)
- Transcription: 20-40 seconds (GPU: 10-15 seconds)
- Post-processing: 1-2 seconds
- **Total: 34-69 seconds (GPU: 18-30 seconds)**

### Resource Requirements:
- **CPU**: High during processing
- **RAM**: 4-8GB for MERaLiON model
- **GPU**: 20GB VRAM recommended (40x faster)
- **Storage**: ~10MB per minute of audio

---

## 🚦 Go/No-Go Decision Points

**Ready to implement if:**
- ✅ Backend dependencies installed (PyTorch, transformers, pyannote)
- ✅ Models can load successfully
- ✅ Database schema supports SessionSpeaker
- ✅ Storage solution chosen (Supabase recommended)
- ✅ Frontend has polling mechanism

**Blockers:**
- ❌ No GPU available → Processing will be slow (60+ seconds)
- ❌ Insufficient RAM (<16GB) → Model loading fails
- ❌ No storage solution → Can't save/retrieve chunks
- ❌ Database schema missing → Need migrations

---

## 📝 Checklist Before Implementation

- [ ] Confirm database has `session_speakers` table
- [ ] Confirm Supabase Storage bucket created
- [ ] Test ML models can load (run test script)
- [ ] Review processor.py functions
- [ ] Plan background job strategy (FastAPI vs Redis)
- [ ] Set up error monitoring/logging
- [ ] Create test audio files
- [ ] Document environment variables needed

---

## ❓ Questions to Answer

1. **Do you want to implement this now?**
2. **Which background processing approach?** (FastAPI BackgroundTasks vs Redis)
3. **Which storage?** (Supabase Storage recommended)
4. **Do you have GPU access?** (Affects processing speed)
5. **Should we start with Phase 1 only?** (Minimal viable integration)

---

## 🎯 Recommendation

**Start with Phase 1 (Basic ML Integration)** using:
- FastAPI BackgroundTasks (simple)
- Supabase Storage (already using Supabase)
- Polling for updates (simple, works)

This gets you:
- Real transcription working
- Real speaker diarization working
- Real Singlish word counting
- Full user flow functional

Then optimize later with:
- Redis for production
- WebSockets for real-time
- Better error handling
- Performance optimizations

**Estimated time: 1-2 days for Phase 1** ⏱️

Ready to proceed? Let me know which approach you prefer!
