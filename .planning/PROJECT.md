# Rabak ML Services

## What This Is

ML pipeline for LahStats that handles speaker diarization and Singlish speech-to-text transcription. Takes raw audio, segments it by speaker using pyannote, transcribes each segment using MERaLiON ASR, applies Singlish-specific corrections, and counts target words per speaker.

## Core Value

**Working speaker-attributed transcription**: Given group audio, identify who spoke when and what Singlish words they said.

## Requirements

### Validated

- ✓ Project structure scaffolded — existing
- ✓ Codebase mapped — existing

### Complete

- [x] Speaker diarization service (pyannote/speaker-diarization-3.1)
- [x] ASR transcription service (MERaLiON-2-10B-ASR)
- [x] Post-processing corrections for Singlish words
- [x] Word counting for target Singlish vocabulary
- [x] Processing pipeline integration (processor.py)
- [x] Test scripts for model validation
- [x] Batched transcription for faster post-processing

### Out of Scope

- Backend API endpoints — Winston's responsibility
- Mobile app — Harshith/Toshiki's responsibility
- Firebase sync — Winston's responsibility
- Database models/migrations — Winston's responsibility

## Context

**Brownfield project**: Scaffold exists with placeholder files. Implementation needed.

**Key files to implement:**
- `backend/services/diarization.py` - pyannote wrapper
- `backend/services/transcription.py` - MERaLiON wrapper + corrections
- `backend/processor.py` - orchestration pipeline
- `scripts/test_meralion.py` - model testing
- `scripts/test_pyannote.py` - model testing

**Models:**
- MERaLiON-2-10B-ASR: HuggingFace transformers pipeline, 16kHz mono audio
- pyannote/speaker-diarization-3.1: Requires HuggingFace token, returns speaker segments

**Target words:**
```python
TARGET_WORDS = [
    'walao', 'cheebai', 'lanjiao',  # Vulgar
    'lah', 'lor', 'sia', 'meh',      # Particles
    'can', 'paiseh', 'shiok', 'sian' # Colloquial
]
```

**Corrections dictionary** (from CLAUDE.md):
```python
CORRECTIONS = {
    'while up': 'walao',
    'wa lao': 'walao',
    'cheap buy': 'cheebai',
    'lunch hour': 'lanjiao',
    'la': 'lah',
    'low': 'lor',
    # ... more
}
```

## Constraints

- **Tech stack**: Python, transformers, pyannote.audio — matches existing backend
- **Audio format**: 16kHz mono WAV — mobile app sends this format
- **HuggingFace auth**: pyannote requires token acceptance
- **GPU**: Models are large, GPU recommended for inference
- **Integration**: Must work with Winston's backend (processor.py called by worker.py)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Use pre-trained MERaLiON | Post-processing handles edge cases effectively | ✓ Implemented |
| Post-processing corrections | Handles known misrecognitions without fine-tuning | ✓ Implemented |
| Cache model instances | Avoid reloading 10B parameter model per request | ✓ Implemented |
| Batched transcription | Transcribe chunks during recording for faster results | ✓ Implemented |

---
*Last updated: 2026-01-18*
