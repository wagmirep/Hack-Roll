# LahStats ML Services — Roadmap

**Milestone:** v1.0 — Working ML Pipeline
**Status:** In Progress (Phases 1-3 Complete)

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
| 1 | Model Setup & Validation | ✅ Complete | — |
| 2 | Speaker Diarization Service | ✅ Complete | Phase 1 |
| 3 | ASR Transcription Service | ✅ Complete | Phase 1 |
| 4 | Processing Pipeline Integration | Not Started | Phase 2, 3 |

**Notes:**
- Phases 1-3 completed via parallel agent development (4 agents)
- Phase 4 requires both services complete — ready to start
- Fine-tuning data prep also complete (Agent 4): `ml/scripts/prepare_singlish_data.py`, `ml/scripts/filter_imda.py`
- 95 unit tests passing across backend and ML

---

*Created: 2026-01-17*
*Updated: 2026-01-17 — Phases 1-3 complete*
*Milestone: v1.0*
