# LahStats ML Services — Roadmap

**Milestone:** v1.1 — Performance Optimization
**Status:** Complete (Phase 5 done)

---

## Phase 6: Hackathon Deployment 🚧

**Goal:** Deploy full app for hackathon demo with QR code access

**Status:** Planned (0/3 plans complete)

**Delivers:**
- ⏳ Backend deployed to Fly.io (Plan 06-01)
- ⏳ Expo web frontend deployed to Vercel (Plan 06-02)
- ⏳ QR code for judges to scan (Plan 06-03)

**Key files:**
- `backend/Dockerfile` — Production container
- `backend/fly.toml` — Fly.io config
- `mobile/vercel.json` — Vercel build config (to create)
- `docs/demo-qr.png` — QR code for demo (to create)

**Plans:**
- ⏳ 06-01: Backend Deployment (Fly.io)
- ⏳ 06-02: Frontend Deployment (Vercel)
- ⏳ 06-03: QR Code and Documentation

---

## Phase 5: Batched Transcription ✅

**Goal:** Reduce post-recording wait time from 60-120s to 5-10s

**Status:** Complete

**Delivers:**
- ✅ Background chunk transcription during recording (Plan 05-01)
- ✅ Cache-aware processor for fast post-processing (Plan 05-02)

**Key files:**
- `backend/models.py` — ChunkTranscription model
- `backend/services/transcription_cache.py` — Background transcription cache
- `backend/routers/sessions.py` — Triggers background transcription on upload
- `backend/processor.py` — Cache-aware transcription with parallel fallback

**Plans:**
- ✅ 05-01: Background Chunk Transcription
- ✅ 05-02: Fast Post-Processing

---

# Milestone: v1.0 — Working ML Pipeline ✅

**Status:** Complete (All Phases Done)

---

## Phase 1: Model Setup & Validation ✅

**Goal:** Get both ML models loading and running locally

**Status:** Complete

**Delivers:**
- ✅ Dependencies installed and working
- ✅ pyannote model loads with HuggingFace auth
- ✅ MERaLiON model loads via transformers
- ✅ Test scripts verify both models work

**Key files:**
- `backend/requirements.txt` — Dependencies uncommented and organized
- `scripts/test_pyannote.py` — Full test suite with auth, model loading, diarization tests
- `scripts/test_meralion.py` — Full test suite with model loading, transcription tests

**Completed by:** Agent 1 (diarization), Agent 2 (transcription)

---

## Phase 2: Speaker Diarization Service ✅

**Goal:** Implement pyannote wrapper that segments audio by speaker

**Status:** Complete

**Delivers:**
- ✅ `backend/services/diarization.py` fully implemented (386 lines)
- ✅ Model loading with caching (singleton pattern, thread-safe)
- ✅ `diarize_audio(path)` → returns `List[SpeakerSegment]`
- ✅ `extract_speaker_segment(audio, start, end)` → extracts clip as bytes
- ✅ `filter_overlapping_segments()` → handles overlapping speech
- ✅ `get_speaker_sample()` / `get_all_speaker_samples()` → claiming audio

**Key files:**
- `backend/services/diarization.py`

**Completed by:** Agent 1

---

## Phase 3: ASR Transcription Service ✅

**Goal:** Implement MERaLiON wrapper with Singlish corrections

**Status:** Complete

**Delivers:**
- ✅ `backend/services/transcription.py` fully implemented (407 lines)
- ✅ Model loading with caching (singleton pattern, thread-safe)
- ✅ `transcribe_audio(path)` → returns raw text
- ✅ `transcribe_segment(bytes)` → transcribe from audio bytes
- ✅ `apply_corrections(text)` → fixes Singlish misrecognitions (20+ patterns)
- ✅ `count_target_words(text)` → returns word counts dict (20 target words)
- ✅ `process_transcription(text)` → combined corrections + counting

**Key files:**
- `backend/services/transcription.py`

**Tests:** 64 unit tests passing (test_transcription.py, test_word_counting.py)

**Completed by:** Agent 2 (model code), Agent 3 (NLP corrections)

---

## Phase 4: Processing Pipeline Integration ✅

**Goal:** Wire diarization + transcription into processor.py

**Status:** Complete

**Delivers:**
- ✅ `backend/processor.py` fully implemented (540 lines)
- ✅ `process_session(session_id)` orchestrates full pipeline:
  1. Concatenate audio chunks (`concatenate_chunks()`)
  2. Run diarization → speaker segments (`run_diarization()`)
  3. For each segment: transcribe → correct → count words (`transcribe_and_count()`)
  4. Generate 5-second sample clips per speaker (`generate_speaker_samples()`)
  5. Return structured results for database storage (`save_speaker_results()`)
- ✅ Progress tracking with stage weights (0-100%)
- ✅ Error handling with ProcessingError exceptions
- ✅ Temp file cleanup on completion/failure
- ✅ Sync wrapper for Redis worker (`process_session_sync()`)

**Key files:**
- `backend/processor.py`

**Success:** End-to-end: audio in → speaker-attributed word counts out

---

## Phase Summary

| Phase | Name | Status | Dependency |
|-------|------|--------|------------|
| 1 | Model Setup & Validation | ✅ Complete | — |
| 2 | Speaker Diarization Service | ✅ Complete | Phase 1 |
| 3 | ASR Transcription Service | ✅ Complete | Phase 1 |
| 4 | Processing Pipeline Integration | ✅ Complete | Phase 2, 3 |

**Notes:**
- All phases completed via parallel agent development
- 95+ unit tests passing across backend and ML
- **v1.0 ML Pipeline is feature-complete**

---

*Created: 2026-01-17*
*Updated: 2026-01-18 — v1.1 Performance Optimization complete, batched transcription done*
*Milestone: v1.1*
