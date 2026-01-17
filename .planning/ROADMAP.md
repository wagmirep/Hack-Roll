# LahStats ML Services — Roadmap

**Milestone:** v1.0 — Working ML Pipeline
**Status:** Not Started

---

## Phase 1: Model Setup & Validation

**Goal:** Get both ML models loading and running locally

**Delivers:**
- Dependencies installed and working
- pyannote model loads with HuggingFace auth
- MERaLiON model loads via transformers
- Test scripts verify both models work

**Key files:**
- `backend/requirements.txt` (uncomment dependencies)
- `scripts/test_pyannote.py`
- `scripts/test_meralion.py`

**Success:** Both test scripts run successfully on sample audio

---

## Phase 2: Speaker Diarization Service

**Goal:** Implement pyannote wrapper that segments audio by speaker

**Delivers:**
- `backend/services/diarization.py` fully implemented
- Model loading with caching (singleton pattern)
- `diarize_audio(path)` → returns speaker segments
- `extract_speaker_segment(audio, start, end)` → extracts clip
- Handles overlapping speech (filter or flag)

**Key files:**
- `backend/services/diarization.py`

**Success:** Given test audio with 2+ speakers, returns correct time-stamped segments

---

## Phase 3: ASR Transcription Service

**Goal:** Implement MERaLiON wrapper with Singlish corrections

**Delivers:**
- `backend/services/transcription.py` fully implemented
- Model loading with caching
- `transcribe_audio(path)` → returns text
- `apply_corrections(text)` → fixes Singlish misrecognitions
- `count_target_words(text)` → returns word counts dict

**Key files:**
- `backend/services/transcription.py`

**Success:** Transcribes Singlish audio, corrections work, word counts accurate

---

## Phase 4: Processing Pipeline Integration

**Goal:** Wire diarization + transcription into processor.py

**Delivers:**
- `backend/processor.py` fully implemented
- `process_session(session_id)` orchestrates full pipeline:
  1. Concatenate audio chunks
  2. Run diarization → speaker segments
  3. For each segment: transcribe → correct → count words
  4. Generate 5-second sample clips per speaker
  5. Return structured results for database storage

**Key files:**
- `backend/processor.py`

**Success:** End-to-end: audio in → speaker-attributed word counts out

---

## Phase Summary

| Phase | Name | Status | Dependency |
|-------|------|--------|------------|
| 1 | Model Setup & Validation | Not Started | — |
| 2 | Speaker Diarization Service | Not Started | Phase 1 |
| 3 | ASR Transcription Service | Not Started | Phase 1 |
| 4 | Processing Pipeline Integration | Not Started | Phase 2, 3 |

**Notes:**
- Phases 2 and 3 can run in parallel after Phase 1
- Phase 4 requires both services complete
- Fine-tuning is OUT OF SCOPE (doing separately)

---

*Created: 2026-01-17*
*Milestone: v1.0*
