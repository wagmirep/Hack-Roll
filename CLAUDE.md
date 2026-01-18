# CLAUDE.md — Rabak Project Instructions

**Claude reads this file automatically. Keep it updated.**

---

## Project Overview

**Name:** Rabak

**Description:** Singlish word tracking app with AI speaker recognition - one phone records everyone, automatically segments speakers, users claim their words, get Spotify Wrapped-style stats

**Tagline:** "Track your lah, lor, and more"

**Tech Stack:**
- **Mobile App:** React Native + Expo (TypeScript)
- **Backend API:** FastAPI (Python)
- **ASR Model:** MERaLiON-2-10B-ASR (pre-trained, no fine-tuning)
- **Speaker Diarization:** pyannote/speaker-diarization-3.1
- **Database:** Supabase (PostgreSQL + Auth)
- **ML Processing:** Google Colab (offloaded for deployment)
- **Package Manager:** npm/bun (frontend), pip (Python)

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
2. **No Voice Enrollment:** Using claiming UI instead
3. **Pre-trained Models:** Using MERaLiON-2-10B-ASR as-is, no fine-tuning needed
4. **Post-Processing:** Corrections dictionary handles edge cases (e.g., "while up" → "walao")
5. **Claiming Flow:** After recording, users listen to 5s audio samples and click "That's me!"
6. **Three-Way Claiming:** Users can claim as self, tag another user, or tag as guest

---

## System Components

### 1. Mobile App (React Native)

**Screens:**
- `RecordingScreen.tsx` - One-phone group recording with pulsing animations
- `ProcessingScreen.tsx` - Shows progress while AI processes audio
- `ClaimingScreen.tsx` - Play samples, users click "That's me!"
- `ResultsScreen.tsx` - Session results per user
- `StatsScreen.tsx` - Weekly/monthly statistics
- `WrappedScreen.tsx` - Spotify Wrapped-style yearly recap

**Key Features:**
- Audio recording at 16kHz, mono, WAV format
- Chunk upload every 30 seconds
- Real-time status polling during processing
- Audio playback for claiming
- Polished animations (pulsing circles, spinning logo)

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
GET    /auth/search                 # Search users for tagging
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
- **Usage:** Pre-trained, no fine-tuning

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
    'pie say': 'paiseh',
    'a llama': 'alamak',
    'la': 'lah',
    'low': 'lor',
    # ... more corrections
}

TARGET_WORDS = [
    # Particles
    'lah', 'lor', 'sia', 'meh', 'leh', 'hor', 'ah',
    # Expressions
    'walao', 'alamak', 'aiyo', 'bojio',
    # Colloquial
    'can', 'paiseh', 'shiok', 'sian', 'bodoh', 'kiasu', 'kiasi'
]
```

### 4. Database Schema

**Supabase (PostgreSQL):**

```sql
-- Recording sessions
CREATE TABLE sessions (
    id UUID PRIMARY KEY,
    group_id UUID,  -- nullable for personal sessions
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
    claimed_at TIMESTAMP,
    claim_type VARCHAR(20),  -- 'self', 'user', 'guest'
    attributed_to_user_id UUID,
    guest_name VARCHAR(100)
);

-- Final attributed word counts
CREATE TABLE word_counts (
    id BIGSERIAL PRIMARY KEY,
    session_id UUID NOT NULL,
    user_id UUID NOT NULL,
    group_id UUID,  -- nullable for personal sessions
    word VARCHAR(50),
    count INT,
    detected_at TIMESTAMP DEFAULT NOW()
);
```

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
```

### Mobile Development

```bash
# Setup
cd mobile
npm install  # or bun install

# Run on iOS simulator
npm run ios

# Run on Android emulator
npm run android

# Run on physical device (Expo Go)
npm start
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
│   ├── storage.py              # Storage utils
│   ├── services/
│   │   ├── diarization.py      # Speaker segmentation
│   │   └── transcription.py    # ASR + corrections
│   └── requirements.txt
│
├── mobile/
│   ├── src/
│   │   ├── screens/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── api/
│   │   └── utils/
│   └── package.json
│
├── docs/
│   ├── API.md
│   ├── MODELS.md
│   └── DEPLOYMENT.md
│
├── TASKS.md
├── CLAUDE.md               # This file
└── README.md
```

---

## Environment Variables

### Backend (.env)

```bash
# Database
DATABASE_URL=postgresql://...supabase.co:5432/postgres
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# Models
HUGGINGFACE_TOKEN=your-hf-token  # For pyannote
```

### Mobile (.env)

```bash
EXPO_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
EXPO_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
EXPO_PUBLIC_API_URL=http://localhost:8000
```

---

## Key Technical Challenges & Solutions

| Challenge | Solution |
|-----------|----------|
| **Overlapping speech** | Ignore segments with multiple speakers detected |
| **Background noise** | Require quiet recording environment |
| **Word accuracy** | Post-processing corrections dictionary |
| **Speaker confusion** | 5-second audio samples help users identify |
| **Processing time** | Show progress bar, 2-3 min typical processing |
| **GPU requirements** | Offload ML processing to Google Colab |

---

## Demo Script

**Live Demo:**
1. "We're Rabak - Spotify Wrapped for Singlish"
2. [Show recording screen] "One phone records everyone"
3. [Play 30s of conversation]
4. "AI automatically figures out who spoke when"
5. [Show processing - "85% complete"]
6. [Show claiming UI] "Listen to samples, claim your words"
7. [Play Speaker A sample] "Jeff clicks 'That's me!'"
8. [Show results] "Jeff: walao (10), lah (15). Alice: sia (8)"
9. [Show Wrapped mockup] "Weekly stats: You said lah 247 times!"

---

## Common Issues

| Problem | Solution |
|---------|----------|
| pyannote auth error | Set `HUGGINGFACE_TOKEN` in `.env` |
| MERaLiON OOM | Reduce batch size or use Colab |
| Poor diarization | Check audio quality, reduce background noise |
| Slow processing | Use GPU, or offload to Colab |
| Claiming not working | Verify sample audio URLs accessible from mobile |

---

## Resources

**Models:**
- MERaLiON-2-10B-ASR: https://huggingface.co/MERaLiON/MERaLiON-2-10B-ASR
- pyannote diarization: https://huggingface.co/pyannote/speaker-diarization-3.1

**Documentation:**
- FastAPI: https://fastapi.tiangolo.com/
- React Native: https://reactnative.dev/
- Expo: https://docs.expo.dev/
- Supabase: https://supabase.com/docs

**Research Papers:**
- MERaLiON-AudioLLM: https://arxiv.org/abs/2412.09818

---

*Last updated: January 18, 2026*

---

**Quick Commands:**

```bash
# Start backend
cd backend && uvicorn main:app --reload --port 8000

# Start mobile
cd mobile && npm start

# Test models
python scripts/test_meralion.py
python scripts/test_pyannote.py
```
