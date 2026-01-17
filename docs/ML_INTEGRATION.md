# ML Pipeline Integration Guide

**For:** Backend Engineer (Winston)
**Last Updated:** 2026-01-17

This guide explains how the ML services integrate with the backend, how to trigger processing, and how data flows through the system.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [ML Services](#ml-services)
4. [Database Models](#database-models)
5. [Processing Pipeline](#processing-pipeline)
6. [API Integration](#api-integration)
7. [Worker Setup](#worker-setup)
8. [Environment Variables](#environment-variables)
9. [Testing](#testing)
10. [Error Handling](#error-handling)
11. [Common Issues](#common-issues)

---

## Overview

The ML pipeline processes recorded audio sessions to:
1. **Identify speakers** - Who spoke when (speaker diarization)
2. **Transcribe speech** - Convert audio to text (ASR)
3. **Count Singlish words** - Track target words like "lah", "walao", etc.

### High-Level Flow

```
Mobile App                    Backend                         ML Services
    │                            │                                │
    │  POST /sessions/start      │                                │
    ├───────────────────────────>│                                │
    │                            │                                │
    │  POST /sessions/{id}/upload (chunks every 30s)              │
    ├───────────────────────────>│  Save to AudioChunk table      │
    │                            │  Upload to Supabase Storage    │
    │                            │                                │
    │  POST /sessions/{id}/end   │                                │
    ├───────────────────────────>│  Queue job to Redis            │
    │                            │         │                      │
    │                            │         ▼                      │
    │                            │    worker.py picks up job      │
    │                            │         │                      │
    │                            │         ▼                      │
    │                            │    processor.py                │
    │                            │         │                      │
    │                            │         ├──────────────────────> diarization.py
    │                            │         │                      │ (pyannote model)
    │                            │         │<─────────────────────┤
    │                            │         │                      │
    │                            │         ├──────────────────────> transcription.py
    │                            │         │                      │ (MERaLiON model)
    │                            │         │<─────────────────────┤
    │                            │         │                      │
    │                            │    Save results to DB          │
    │                            │    Session.status = "ready_for_claiming"
    │                            │                                │
    │  GET /sessions/{id}/status │                                │
    ├───────────────────────────>│  Returns progress/status       │
    │                            │                                │
    │  GET /sessions/{id}/speakers                                │
    ├───────────────────────────>│  Returns speakers + sample audio URLs
    │                            │                                │
    │  POST /sessions/{id}/claim │                                │
    ├───────────────────────────>│  Attributes words to user      │
```

---

## Architecture

### File Structure

```
backend/
├── processor.py              # Main processing pipeline (Phase 4)
├── worker.py                 # Redis job worker
├── services/
│   ├── diarization.py        # Speaker diarization (pyannote)
│   └── transcription.py      # ASR + corrections (MERaLiON)
├── models.py                 # Database models
├── storage.py                # Supabase Storage client
└── routers/
    └── sessions.py           # Session API endpoints
```

### Component Responsibilities

| Component | Responsibility |
|-----------|---------------|
| `routers/sessions.py` | API endpoints, queue jobs |
| `worker.py` | Listen to Redis queue, call processor |
| `processor.py` | Orchestrate full pipeline |
| `services/diarization.py` | Speaker segmentation |
| `services/transcription.py` | Speech-to-text + Singlish corrections |
| `storage.py` | Audio file upload/download |

---

## ML Services

### 1. Speaker Diarization (`services/diarization.py`)

**Model:** `pyannote/speaker-diarization-3.1`

**Purpose:** Segment audio by speaker ("who spoke when")

**Key Functions:**

```python
from services.diarization import diarize_audio, extract_speaker_segment, SpeakerSegment

# Run diarization on audio file
segments: List[SpeakerSegment] = diarize_audio("/path/to/audio.wav")

# Each segment contains:
# - speaker_id: str      (e.g., "SPEAKER_00", "SPEAKER_01")
# - start_time: float    (seconds)
# - end_time: float      (seconds)
# - duration: float      (property)

# Extract audio for a specific time range
audio_bytes: bytes = extract_speaker_segment(
    audio_path="/path/to/audio.wav",
    start_time=5.0,
    end_time=10.0
)
```

**Requirements:**
- `HUGGINGFACE_TOKEN` environment variable (for gated model access)
- Accept model terms at: https://huggingface.co/pyannote/speaker-diarization-3.1
- Also accept: https://huggingface.co/pyannote/segmentation-3.0

### 2. Transcription (`services/transcription.py`)

**Model:** `MERaLiON/MERaLiON-2-10B-ASR`

**Purpose:** Convert speech to text, with Singlish corrections

**Key Functions:**

```python
from services.transcription import (
    transcribe_audio,
    apply_corrections,
    count_target_words,
    process_transcription
)

# Transcribe audio file
raw_text: str = transcribe_audio("/path/to/segment.wav")
# Output: "while up why you do that la"

# Apply Singlish corrections
corrected_text: str = apply_corrections(raw_text)
# Output: "walao why you do that lah"

# Count target words
word_counts: Dict[str, int] = count_target_words(corrected_text)
# Output: {"walao": 1, "lah": 1}

# Combined convenience function
corrected, counts = process_transcription(raw_text)
```

**Corrections Dictionary:**

The service automatically corrects common ASR misrecognitions:

| ASR Output | Corrected To |
|------------|--------------|
| "while up" | walao |
| "wa lao" | walao |
| "cheap buy" | cheebai |
| "lunch hour" | lanjiao |
| "pie say" | paiseh |
| "shook" | shiok |
| "la" | lah |
| "low" | lor |

**Target Words Tracked:**

```python
TARGET_WORDS = [
    # Vulgar
    'walao', 'cheebai', 'lanjiao',
    # Particles
    'lah', 'lor', 'sia', 'meh', 'leh', 'hor', 'ah',
    # Colloquial
    'can', 'paiseh', 'shiok', 'sian', 'alamak', 'aiyo',
    'bodoh', 'kiasu', 'kiasi', 'bojio'
]
```

---

## Database Models

### Processing-Related Tables

```
┌─────────────────┐     ┌─────────────────────┐     ┌────────────────────┐
│    Session      │     │   SessionSpeaker    │     │  SpeakerWordCount  │
├─────────────────┤     ├─────────────────────┤     ├────────────────────┤
│ id              │────<│ session_id          │────<│ session_speaker_id │
│ group_id        │     │ speaker_label       │     │ word               │
│ started_by      │     │ segment_count       │     │ count              │
│ status          │     │ total_duration_secs │     └────────────────────┘
│ progress        │     │ sample_audio_url    │
│ audio_url       │     │ claimed_by          │     ┌────────────────────┐
│ duration_secs   │     │ claimed_at          │     │     WordCount      │
│ error_message   │     │ claim_type          │     ├────────────────────┤
└─────────────────┘     │ attributed_to_user  │     │ session_id         │
                        │ guest_name          │     │ user_id            │
        ┌───────────────┴─────────────────────┤     │ group_id           │
        │                                     │     │ word               │
┌───────┴───────┐                             │     │ count              │
│  AudioChunk   │                             │     │ detected_at        │
├───────────────┤                             │     └────────────────────┘
│ session_id    │                             │              ▲
│ chunk_number  │                             │              │
│ storage_path  │                             │     (Created when user
│ duration_secs │                             │      claims a speaker)
└───────────────┘                             │
                                              │
                            ┌─────────────────┘
                            │ After claiming,
                            │ SpeakerWordCount
                            │ copied to WordCount
                            │ with user_id
```

### Session Status Values

| Status | Description |
|--------|-------------|
| `recording` | Session active, chunks being uploaded |
| `processing` | Worker processing audio |
| `ready_for_claiming` | Processing done, waiting for users to claim speakers |
| `completed` | All speakers claimed |
| `failed` | Processing failed (check `error_message`) |

### Session Progress

During processing, `Session.progress` updates to show status:

| Progress | Stage |
|----------|-------|
| 0-10% | Concatenating audio chunks |
| 10-40% | Running speaker diarization |
| 40-85% | Transcribing segments |
| 85-95% | Saving results to database |
| 95-100% | Generating speaker sample clips |

---

## Processing Pipeline

### processor.py Functions

```python
# Main entry point - called by worker
async def process_session(session_id: UUID) -> Dict:
    """
    Full pipeline:
    1. Concatenate chunks → WAV file
    2. Diarization → speaker segments
    3. Transcribe each segment → count words
    4. Save SessionSpeaker + SpeakerWordCount
    5. Generate 5s sample clips
    6. Update session status
    """

# Synchronous wrapper for worker.py
def process_session_sync(session_id: UUID) -> Dict:
    """Wrapper that runs async function in event loop"""
```

### Pipeline Stages

#### Stage 1: Concatenate Chunks

```python
audio_path, duration = await concatenate_chunks(db, session_id, temp_files)
```

- Queries `AudioChunk` table for all chunks
- Downloads each chunk from Supabase Storage
- Concatenates using pydub
- Converts to 16kHz mono WAV
- Returns path to temp file

#### Stage 2: Speaker Diarization

```python
segments = run_diarization(audio_path)
```

- Calls `diarize_audio()` from diarization service
- Returns list of `SpeakerSegment` objects
- Each segment has speaker_id, start_time, end_time

#### Stage 3: Transcribe and Count

```python
speaker_results = await transcribe_and_count(audio_path, segments, db, session)
```

For each segment:
1. Extract audio clip using `extract_speaker_segment()`
2. Transcribe using `transcribe_audio()`
3. Apply corrections using `apply_corrections()`
4. Count words using `count_target_words()`
5. Accumulate counts per speaker

Returns: `Dict[speaker_id, Dict[word, count]]`

#### Stage 4: Save Results

```python
speaker_records = save_speaker_results(db, session_id, speaker_results)
```

- Creates `SessionSpeaker` record for each detected speaker
- Creates `SpeakerWordCount` records for each word count
- Returns mapping of speaker_id → SessionSpeaker

#### Stage 5: Generate Samples

```python
await generate_speaker_samples(db, session_id, audio_path, speaker_records, segments)
```

- Finds longest segment for each speaker
- Extracts 5-second sample clip
- Uploads to Supabase Storage
- Updates `SessionSpeaker.sample_audio_url`

---

## API Integration

### Endpoints That Trigger/Query Processing

#### End Session (Triggers Processing)

```http
POST /sessions/{session_id}/end
```

**Backend should:**
1. Update `Session.status = "processing"`
2. Queue job to Redis: `{"session_id": "...", "queued_at": "..."}`
3. Return immediately (processing happens async)

```python
# Example in sessions.py
@router.post("/{session_id}/end")
async def end_session(session_id: UUID, db: Session = Depends(get_db)):
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    session.status = "processing"
    session.ended_at = datetime.utcnow()
    db.commit()

    # Queue to Redis
    await redis.lpush("lahstats:processing", json.dumps({
        "session_id": str(session_id),
        "queued_at": datetime.utcnow().isoformat()
    }))

    return {"status": "processing"}
```

#### Check Status

```http
GET /sessions/{session_id}/status
```

**Returns:**
```json
{
    "status": "processing",
    "progress": 45,
    "error_message": null
}
```

#### Get Speakers (For Claiming UI)

```http
GET /sessions/{session_id}/speakers
```

**Returns:**
```json
{
    "speakers": [
        {
            "id": "uuid",
            "speaker_label": "SPEAKER_00",
            "sample_audio_url": "https://...",
            "total_duration_seconds": 45.5,
            "word_counts": {
                "lah": 15,
                "walao": 3
            },
            "claimed_by": null
        },
        {
            "id": "uuid",
            "speaker_label": "SPEAKER_01",
            "sample_audio_url": "https://...",
            "total_duration_seconds": 38.2,
            "word_counts": {
                "sia": 8,
                "lor": 12
            },
            "claimed_by": null
        }
    ]
}
```

#### Claim Speaker

```http
POST /sessions/{session_id}/claim
Content-Type: application/json

{
    "speaker_id": "uuid",
    "claim_type": "self"
}
```

**Backend should:**
1. Update `SessionSpeaker.claimed_by`, `claimed_at`, `claim_type`
2. Copy `SpeakerWordCount` → `WordCount` with user_id
3. Check if all speakers claimed → update `Session.status = "completed"`

```python
# Example claiming logic
@router.post("/{session_id}/claim")
async def claim_speaker(
    session_id: UUID,
    request: ClaimRequest,
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    speaker = db.query(SessionSpeaker).filter(
        SessionSpeaker.id == request.speaker_id
    ).first()

    # Update speaker claim
    speaker.claimed_by = current_user.id
    speaker.claimed_at = datetime.utcnow()
    speaker.claim_type = request.claim_type
    speaker.attributed_to_user_id = current_user.id

    # Copy word counts to final WordCount table
    session = speaker.session
    for swc in speaker.word_counts:
        word_count = WordCount(
            session_id=session.id,
            user_id=current_user.id,
            group_id=session.group_id,
            word=swc.word,
            count=swc.count
        )
        db.add(word_count)

    # Check if all speakers claimed
    unclaimed = db.query(SessionSpeaker).filter(
        SessionSpeaker.session_id == session_id,
        SessionSpeaker.claimed_by == None
    ).count()

    if unclaimed == 0:
        session.status = "completed"

    db.commit()
    return {"success": True}
```

---

## Worker Setup

### worker.py Implementation

```python
import asyncio
import json
import logging
import redis
from processor import process_session_sync

logger = logging.getLogger(__name__)

QUEUE_NAME = "lahstats:processing"
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")

def main():
    r = redis.from_url(REDIS_URL)
    logger.info(f"Worker listening on queue: {QUEUE_NAME}")

    while True:
        try:
            # Blocking pop from queue
            _, job_data = r.brpop(QUEUE_NAME)
            job = json.loads(job_data)

            session_id = job["session_id"]
            logger.info(f"Processing session: {session_id}")

            # Run processing
            result = process_session_sync(session_id)

            logger.info(f"Completed session {session_id}: {result}")

        except Exception as e:
            logger.error(f"Worker error: {e}")
            # Optionally implement retry logic

if __name__ == "__main__":
    main()
```

### Running the Worker

```bash
# Terminal 1: API server
cd backend
uvicorn main:app --reload --port 8000

# Terminal 2: Redis
docker run -d -p 6379:6379 redis:latest

# Terminal 3: Worker
cd backend
python worker.py
```

---

## Environment Variables

### Required for ML Pipeline

```bash
# .env file in backend/

# HuggingFace token for pyannote (REQUIRED)
HUGGINGFACE_TOKEN=hf_xxxxxxxxxxxxx

# Redis for job queue
REDIS_URL=redis://localhost:6379

# Supabase for storage
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJxxxxx
STORAGE_BUCKET=audio

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/lahstats
```

### Getting HuggingFace Token

1. Create account at https://huggingface.co
2. Go to https://huggingface.co/settings/tokens
3. Create new token with "read" access
4. Accept model terms:
   - https://huggingface.co/pyannote/speaker-diarization-3.1
   - https://huggingface.co/pyannote/segmentation-3.0

---

## Testing

### Test Processing Locally

```python
# test_processing.py
import asyncio
from processor import process_session

async def test():
    # Use a real session ID from your database
    session_id = "your-session-uuid"
    result = await process_session(session_id)
    print(result)

asyncio.run(test())
```

### Test Individual Services

```python
# Test diarization
from services.diarization import diarize_audio
segments = diarize_audio("test_audio.wav")
for seg in segments:
    print(f"{seg.speaker_id}: {seg.start_time:.1f}s - {seg.end_time:.1f}s")

# Test transcription
from services.transcription import transcribe_audio, apply_corrections, count_target_words
text = transcribe_audio("test_audio.wav")
corrected = apply_corrections(text)
counts = count_target_words(corrected)
print(f"Text: {corrected}")
print(f"Counts: {counts}")
```

### Unit Tests

```bash
cd backend
python -m pytest tests/ -v

# Test specific modules
python -m pytest tests/test_word_counting.py -v
python -m pytest tests/test_transcription.py -v
```

---

## Error Handling

### Processing Failures

If processing fails:
1. `Session.status` set to `"failed"`
2. `Session.error_message` contains error details
3. Exception logged with full traceback

```python
# Check for failed sessions
failed_sessions = db.query(Session).filter(
    Session.status == "failed"
).all()

for session in failed_sessions:
    print(f"Session {session.id} failed: {session.error_message}")
```

### Retry Logic

```python
# In worker.py - simple retry
MAX_RETRIES = 3

def process_with_retry(session_id):
    for attempt in range(MAX_RETRIES):
        try:
            return process_session_sync(session_id)
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} failed: {e}")
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(5 * (attempt + 1))  # Exponential backoff
```

### Common Error Types

| Error | Cause | Solution |
|-------|-------|----------|
| `HUGGINGFACE_TOKEN not set` | Missing env var | Set token in .env |
| `Access to model restricted` | Token not authorized | Accept model terms on HF |
| `No audio chunks found` | No uploads for session | Check upload logic |
| `Diarization failed` | Audio format issue | Ensure 16kHz mono WAV |
| `CUDA out of memory` | GPU memory insufficient | Use `device_map="auto"` |

---

## Common Issues

### 1. PyTorch 2.6+ Compatibility

pyannote has issues with PyTorch 2.6+. The diarization service includes a workaround:

```python
# Already in diarization.py - monkey-patches torch.load
import torch
_original_torch_load = torch.load
def _patched_torch_load(*args, **kwargs):
    kwargs.setdefault('weights_only', False)
    return _original_torch_load(*args, **kwargs)
torch.load = _patched_torch_load
```

### 2. GPU Memory (MERaLiON)

MERaLiON-2-10B needs ~20GB VRAM. For smaller GPUs:

```python
# Already in transcription.py - uses device_map="auto" for GPUs < 20GB
# This offloads layers to CPU automatically
```

### 3. Model Loading Time

First request is slow (model loading):
- pyannote: ~30 seconds
- MERaLiON: ~2-3 minutes

Models are cached after first load (singleton pattern).

### 4. Audio Format Issues

Ensure audio is:
- 16kHz sample rate
- Mono channel
- WAV format (for best compatibility)

The processor automatically converts using pydub.

### 5. Supabase Storage Permissions

Ensure storage bucket has correct policies:

```sql
-- Allow authenticated uploads
CREATE POLICY "Allow uploads" ON storage.objects
    FOR INSERT TO authenticated
    WITH CHECK (bucket_id = 'audio');

-- Allow public reads (for sample audio)
CREATE POLICY "Allow public reads" ON storage.objects
    FOR SELECT TO public
    USING (bucket_id = 'audio');
```

---

## Quick Reference

### Import Cheatsheet

```python
# Processor
from processor import process_session, process_session_sync

# Diarization
from services.diarization import (
    diarize_audio,
    extract_speaker_segment,
    SpeakerSegment
)

# Transcription
from services.transcription import (
    transcribe_audio,
    transcribe_segment,
    apply_corrections,
    count_target_words,
    process_transcription,
    TARGET_WORDS,
    SAMPLE_RATE
)

# Models
from models import (
    Session,
    SessionSpeaker,
    SpeakerWordCount,
    WordCount,
    AudioChunk
)
```

### Status Flow

```
recording → processing → ready_for_claiming → completed
                ↓
              failed
```

### Contact

- **ML questions:** Nickolas
- **Backend questions:** Winston
- **Frontend questions:** Harshith, Toshiki

---

*Last updated: 2026-01-17*
