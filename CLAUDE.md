# CLAUDE.md — LahStats Project Instructions

**Claude reads this file automatically. Keep it updated.**

---

## Project Overview

**Name:** LahStats

**Description:** Singlish word tracking app with AI speaker recognition - one phone records everyone, automatically segments speakers, users claim their words, get Spotify Wrapped-style stats

**Tagline:** "Track your lah, lor, and more"

**Tech Stack:**
- **Mobile App:** React Native + Expo
- **Backend API:** FastAPI (Python)
- **ASR Model:** MERaLiON-2-10B-ASR (pre-trained, no fine-tuning)
- **Speaker Diarization:** pyannote/speaker-diarization-3.1
- **Database:** PostgreSQL (primary) + Firebase Realtime Database (live sync)
- **Queue:** Redis (for job processing)
- **Storage:** AWS S3 / Cloud Storage (audio files)
- **Package Manager:** Bun (frontend tooling), pip (Python)

---

## Project Architecture

### High-Level Flow

```
User opens app → Starts group recording (one phone on table)
    ↓
Mobile app records audio → Uploads chunks every 30s to backend
    ↓
User stops recording → Backend processes session
    ↓
Speaker Diarization: AI segments "who spoke when"
    ↓
Transcription: MERaLiON transcribes each speaker segment
    ↓
Post-Processing: Corrections + word counting
    ↓
Claiming UI: Users identify themselves by listening to samples
    ↓
Results: "Jeff said 'walao' 10x, Alice said 'lah' 15x"
    ↓
Weekly Wrapped: Spotify-style statistics visualization
```

### Key Technical Decisions

1. **One-Phone Recording:** Natural UX - one phone on table records everyone, not multi-phone
2. **No Voice Enrollment:** Too complex for hackathon, using claiming UI instead
3. **Pre-trained Models:** Using MERaLiON-2-10B-ASR as-is, no fine-tuning needed
4. **Post-Processing:** Corrections dictionary handles edge cases (e.g., "while up" → "walao")
5. **Claiming Flow:** After recording, users listen to 5s audio samples and click "That's me!"

---

## Team

| Name | Role | Responsibilities |
|------|------|------------------|
| Nickolas | ML | ASR integration, speaker diarization |
| Winston | Backend | Backend API, Database, Firebase sync, processing pipeline |
| Harshith | Mobile/Frontend | React Native app, recording, claiming UI, statistics visualization |
| Toshiki | Mobile/Frontend | React Native app, recording, claiming UI, Spotify Wrapped UI |

---

## System Components

### 1. Mobile App (React Native)

**Screens:**
- `RecordingScreen.js` - One-phone group recording with live duration
- `ProcessingScreen.js` - Shows progress while AI processes audio
- `ClaimingScreen.js` - Play samples, users click "That's me!"
- `ResultsScreen.js` - Session results per user
- `StatsScreen.js` - Weekly/monthly statistics
- `WrappedScreen.js` - Spotify Wrapped-style yearly recap

**Key Features:**
- Audio recording at 16kHz, mono, WAV format
- Chunk upload every 30 seconds
- Real-time status polling during processing
- Audio playback for claiming
- Firebase listener for live group updates

### 2. Backend API (FastAPI)

**Core Endpoints:**

```python
POST   /sessions/start              # Create recording session
POST   /sessions/{id}/upload        # Upload audio chunks
POST   /sessions/{id}/end           # Stop & trigger processing
GET    /sessions/{id}/status        # Poll processing progress
GET    /sessions/{id}/speakers      # Get claiming data
POST   /sessions/{id}/claim         # User claims speaker
GET    /groups/{id}/stats           # Group statistics
```

**Processing Pipeline:**

```python
# processor.py - Background job
async def process_session(session_id):
    # 1. Concatenate audio chunks
    full_audio = concatenate_chunks(session_id)
    
    # 2. Speaker diarization (pyannote)
    segments = diarization_pipeline(full_audio)
    # Output: [(0-5s: SPEAKER_00), (5-12s: SPEAKER_01), ...]
    
    # 3. Transcribe each segment (MERaLiON)
    for segment in segments:
        text = transcriber(segment.audio)['text']
        corrected = apply_corrections(text)  # Post-processing
        words = count_target_words(corrected)
        
    # 4. Generate claiming data
    # - Save 5s sample clip per speaker
    # - Aggregate word counts per speaker
    
    # 5. Mark ready for claiming
```

### 3. AI Models

**MERaLiON-2-10B-ASR:**
- **Model:** `MERaLiON/MERaLiON-2-10B-ASR` (HuggingFace)
- **Purpose:** Transcribe Singlish speech to text
- **Input:** 16kHz mono audio, max 30s chunks
- **Output:** Text transcription
- **Performance:** 85-90% accuracy on Singlish particles
- **Usage:** Pre-trained, no fine-tuning for hackathon

**pyannote Speaker Diarization:**
- **Model:** `pyannote/speaker-diarization-3.1`
- **Purpose:** Segment audio by speaker
- **Input:** Full session audio
- **Output:** Time-stamped speaker segments
- **Accuracy:** 85-90% segmentation in good conditions
- **Auth:** Requires HuggingFace token

**Post-Processing Corrections:**
```python
CORRECTIONS = {
    'while up': 'walao',
    'wa lao': 'walao',
    'cheap buy': 'cheebai',
    'lunch hour': 'lanjiao',
    'la': 'lah',
    'low': 'lor',
    # ... more corrections
}

TARGET_WORDS = [
    'walao', 'cheebai', 'lanjiao',  # Vulgar
    'lah', 'lor', 'sia', 'meh',      # Particles
    'can', 'paiseh', 'shiok', 'sian' # Colloquial
]
```

### 4. Database Schema

**PostgreSQL:**

```sql
-- Recording sessions
CREATE TABLE sessions (
    id UUID PRIMARY KEY,
    group_id UUID NOT NULL,
    started_by UUID NOT NULL,
    started_at TIMESTAMP NOT NULL,
    ended_at TIMESTAMP,
    status VARCHAR(50),  -- 'recording', 'processing', 'ready_for_claiming', 'completed'
    progress INT DEFAULT 0
);

-- Speaker data before claiming
CREATE TABLE session_speakers (
    id UUID PRIMARY KEY,
    session_id UUID NOT NULL,
    speaker_id VARCHAR(50),  -- 'SPEAKER_00', 'SPEAKER_01'
    total_words JSONB,       -- {'walao': 10, 'lah': 15}
    sample_audio_url TEXT,
    segment_count INT,
    claimed_by UUID,         -- NULL until claimed
    claimed_at TIMESTAMP
);

-- Final attributed word counts
CREATE TABLE word_counts (
    id BIGSERIAL PRIMARY KEY,
    session_id UUID NOT NULL,
    user_id UUID NOT NULL,
    group_id UUID NOT NULL,
    word VARCHAR(50),
    count INT,
    detected_at TIMESTAMP DEFAULT NOW()
);
```

**Firebase Realtime Database:**

```javascript
{
  "groups": {
    "group-123": {
      "live_counts": {
        "user-jeff": {"walao": 10, "lah": 15},
        "user-alice": {"sia": 8, "lor": 14}
      },
      "leaderboard": [...],
      "active_session": "session-abc"
    }
  }
}
```

---

## Implementation Roadmap

### Hackathon Timeline (24 hours)

**Hour 0-8: Core Backend**
- ✅ FastAPI project setup
- ✅ Session CRUD endpoints
- ✅ Audio chunk upload + storage
- ✅ PostgreSQL schema
- ✅ Redis queue setup
- ✅ pyannote integration test
- ✅ MERaLiON integration test

**Hour 8-16: Processing Pipeline**
- ✅ Audio concatenation
- ✅ Speaker diarization worker
- ✅ Per-segment transcription
- ✅ Post-processing corrections
- ✅ Word counting logic
- ✅ Sample audio generation
- ✅ Claiming data structure

**Hour 16-20: Mobile App**
- ✅ React Native setup (Expo)
- ✅ Recording screen + audio capture
- ✅ Chunk upload logic
- ✅ Processing status polling
- ✅ Claiming UI with audio playback
- ✅ Results visualization

**Hour 20-24: Integration + Demo**
- ✅ Firebase real-time sync
- ✅ Statistics aggregation
- ✅ Spotify Wrapped mockup
- ✅ End-to-end testing
- ✅ Demo video preparation
- ✅ Pitch deck

---

## Development Workflow

### Backend Development

```bash
# Setup
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Run API server
uvicorn main:app --reload --port 8000

# Run processing worker (separate terminal)
python worker.py

# Run Redis (Docker)
docker run -d -p 6379:6379 redis:latest

# Database migrations
alembic upgrade head
```

### Mobile Development

```bash
# Setup
cd mobile
bun install  # or npm install if needed

# Run on iOS simulator
bun run ios

# Run on Android emulator
bun run android

# Run on physical device (Expo Go)
bun run start
# Scan QR code with Expo Go app
```

### Model Testing

```python
# Test MERaLiON locally
from transformers import pipeline

transcriber = pipeline(
    "automatic-speech-recognition",
    model="MERaLiON/MERaLiON-2-10B-ASR",
    device=0  # GPU
)

result = transcriber("test_audio.wav")
print(result['text'])

# Test pyannote
from pyannote.audio import Pipeline

diarization = Pipeline.from_pretrained(
    "pyannote/speaker-diarization-3.1",
    use_auth_token="YOUR_HF_TOKEN"
)

result = diarization("test_audio.wav")
for turn, _, speaker in result.itertracks(yield_label=True):
    print(f"{speaker}: {turn.start:.1f}s - {turn.end:.1f}s")
```

---

## File Structure

```
/
├── backend/
│   ├── main.py                 # FastAPI app + endpoints
│   ├── processor.py            # Background processing worker
│   ├── models.py               # Database models
│   ├── database.py             # DB connection
│   ├── storage.py              # S3/storage utils
│   └── requirements.txt
│       ├── fastapi
│       ├── uvicorn
│       ├── transformers
│       ├── torch
│       ├── pyannote.audio
│       ├── librosa
│       ├── redis
│       └── psycopg2
│
├── mobile/
│   ├── src/
│   │   ├── screens/
│   │   │   ├── RecordingScreen.js
│   │   │   ├── ProcessingScreen.js
│   │   │   ├── ClaimingScreen.js
│   │   │   ├── ResultsScreen.js
│   │   │   └── WrappedScreen.js
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── api/            # API client
│   │   └── utils/
│   └── package.json
│
├── docs/
│   ├── API.md              # API documentation
│   ├── MODELS.md           # Model usage guide
│   └── DEPLOYMENT.md       # Deployment instructions
│
├── TASKS.md                # Task assignments
├── CLAUDE.md               # This file
└── README.md               # Project README
```

---

## Environment Variables

### Backend (.env)

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/lahstats

# Redis
REDIS_URL=redis://localhost:6379

# Storage
S3_BUCKET=lahstats-audio
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret

# Models
HUGGINGFACE_TOKEN=your-hf-token  # For pyannote

# Firebase
FIREBASE_PROJECT_ID=lahstats
FIREBASE_CREDENTIALS=path/to/credentials.json
```

### Mobile (.env)

```bash
API_URL=http://localhost:8000
FIREBASE_CONFIG=your-firebase-config-json
```

---

## Key Technical Challenges & Solutions

| Challenge | Solution |
|-----------|----------|
| **Overlapping speech** | Ignore segments with multiple speakers detected |
| **Background noise** | Require quiet recording environment |
| **Vulgar word accuracy** | Post-processing corrections dictionary |
| **Speaker confusion** | 5-second audio samples help users identify |
| **Processing time** | Show progress bar, 2-3 min typical processing |
| **Real-time updates** | Firebase listeners for live group sync |

---

## Demo Script

**Setup (Pre-recorded):**
- 3-minute conversation with clear Singlish usage
- Multiple speakers
- Pre-processed results ready

**Live Demo:**
1. "We're LahStats - Spotify Wrapped for Singlish"
2. [Show recording screen] "One phone records everyone"
3. [Play 30s of conversation]
4. "AI automatically figures out who spoke when"
5. [Show processing - "85% complete"]
6. [Show claiming UI] "Listen to samples, claim your words"
7. [Play Speaker A sample] "Jeff clicks 'That's me!'"
8. [Show results] "Jeff: walao (10), lah (15). Alice: sia (8)"
9. [Show Wrapped mockup] "Weekly stats: You said lah 247 times!"

---

## Testing Checklist

### Backend
- [ ] Audio upload works
- [ ] Session status updates correctly
- [ ] Diarization segments speakers
- [ ] MERaLiON transcribes Singlish
- [ ] Post-processing applies corrections
- [ ] Word counting accurate
- [ ] Claiming attribution works
- [ ] Firebase sync updates in real-time

### Mobile
- [ ] Recording captures 16kHz mono audio
- [ ] Chunks upload every 30s
- [ ] Processing screen polls status
- [ ] Audio samples play correctly
- [ ] Claiming works (one click per speaker)
- [ ] Results display per user
- [ ] Navigation flows smoothly

### Integration
- [ ] End-to-end: Record → Process → Claim → Results
- [ ] Multiple users can claim different speakers
- [ ] Word counts accurate across group
- [ ] Firebase updates all group members

---

## Known Limitations (Post-Hackathon TODO)

- [ ] Speaker diarization accuracy ~85% (not perfect)
- [ ] No voice enrollment (manual claiming required)
- [ ] 30s chunk upload (not true real-time)
- [ ] Post-processing only covers common misspellings
- [ ] No support for overlapping speech
- [ ] Requires relatively quiet environment

**Post-hackathon improvements:**
1. Add voice enrollment for automatic attribution
2. Real-time word detection (no claiming needed)
3. Better noise handling
4. Support for longer sessions (>30 min)

---

## Common Issues

| Problem | Solution |
|---------|----------|
| pyannote auth error | Set `HUGGINGFACE_TOKEN` in `.env` |
| MERaLiON OOM | Reduce batch size or use smaller model |
| Poor diarization | Check audio quality, reduce background noise |
| Slow processing | Use GPU for both models, Redis queue |
| Claiming not working | Verify sample audio URLs accessible from mobile |
| Firebase not syncing | Check Firebase credentials and rules |

---

## Resources

**Models:**
- MERaLiON-2-10B-ASR: https://huggingface.co/MERaLiON/MERaLiON-2-10B-ASR
- pyannote diarization: https://huggingface.co/pyannote/speaker-diarization-3.1
- IMDA National Speech Corpus: https://www.imda.gov.sg/how-we-can-help/national-speech-corpus

**Documentation:**
- FastAPI: https://fastapi.tiangolo.com/
- React Native: https://reactnative.dev/
- Expo: https://docs.expo.dev/
- Firebase: https://firebase.google.com/docs

**Research Papers:**
- MERaLiON-AudioLLM: https://arxiv.org/abs/2412.09818
- Singlish Understanding: https://arxiv.org/abs/2501.01034

---

*Last updated: January 15, 2026*

---

**Quick Commands:**

```bash
# Start everything
docker-compose up -d          # Redis + PostgreSQL
python backend/main.py        # API server
python backend/worker.py      # Processing worker
cd mobile && bun run start    # Mobile app

# Test models
python scripts/test_meralion.py
python scripts/test_pyannote.py

# Deploy
./deploy.sh
```
