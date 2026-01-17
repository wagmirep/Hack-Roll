# LahStats ML Agents — Parallel Development Guide

**Created:** 2026-01-17
**Coordinator:** Nickolas (you)
**Merge Strategy:** Rolling (merge each agent's work as completed)

---

## Overview

4 Claude agents working in parallel on the ML pipeline. Each agent has an isolated git worktree to avoid conflicts.

| Agent | Branch | Worktree Directory | Focus |
|-------|--------|-------------------|-------|
| 1 | `diarization` | `Hack-Roll-diarization` | Speaker diarization service |
| 2 | `transcription` | `Hack-Roll-transcription` | MERaLiON ASR wrapper |
| 3 | `singlish-nlp` | `Hack-Roll-singlish-nlp` | Corrections + word counting |
| 4 | `data-prep` | `Hack-Roll-data-prep` | Training data for fine-tuning |

---

## Agent 1: Diarization Service

**Worktree:** `C:\Users\nicko\Desktop\wagmi\Hack-Roll-diarization`
**Branch:** `diarization`

### Scope
Implement the speaker diarization service using pyannote.

### Files to Modify
- `backend/services/diarization.py` — **PRIMARY**: Full implementation
- `scripts/test_pyannote.py` — Test script for the model
- `backend/requirements.txt` — Uncomment pyannote dependencies

### Deliverables
1. Model loading with singleton caching (avoid reloading 10B params)
2. `diarize_audio(audio_path: str) -> List[SpeakerSegment]`
   - Returns list of segments with speaker_id, start_time, end_time
3. `extract_speaker_segment(audio_path: str, start: float, end: float) -> bytes`
   - Extracts audio clip for a segment
4. Handle overlapping speech (filter or flag)

### Technical Details
```python
# Model: pyannote/speaker-diarization-3.1
# Requires: HUGGINGFACE_TOKEN env var (user accepted license)
# Input: Audio file path (16kHz mono WAV)
# Output: Timeline with speaker labels

from pyannote.audio import Pipeline

pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization-3.1",
    use_auth_token=os.environ["HUGGINGFACE_TOKEN"]
)
result = pipeline(audio_path)
for turn, _, speaker in result.itertracks(yield_label=True):
    # turn.start, turn.end, speaker (e.g., "SPEAKER_00")
```

### Dependencies
```
pyannote.audio>=3.1.0
torch>=2.0.0
torchaudio>=2.0.0
```

### Success Criteria
- [ ] `scripts/test_pyannote.py` runs successfully on sample audio
- [ ] Returns correct speaker segments for 2+ speaker audio
- [ ] Model loads once and is cached for subsequent calls

### Do NOT Touch
- `backend/services/transcription.py` (Agent 2's domain)
- `backend/processor.py` (integration happens after merge)
- Any mobile/ files

---

## Agent 2: Transcription Service

**Worktree:** `C:\Users\nicko\Desktop\wagmi\Hack-Roll-transcription`
**Branch:** `transcription`

### Scope
Implement the MERaLiON ASR wrapper for speech-to-text.

### Files to Modify
- `backend/services/transcription.py` — **PRIMARY**: Model loading + transcription only
- `scripts/test_meralion.py` — Test script for the model
- `backend/requirements.txt` — Uncomment transformers dependencies

### Deliverables
1. Model loading with singleton caching
2. `transcribe_audio(audio_path: str) -> str`
   - Returns raw transcription text
   - Handles 16kHz mono WAV input

### Technical Details
```python
# Model: MERaLiON/MERaLiON-2-10B-ASR
# Input: Audio file path (16kHz mono WAV, max 30s chunks)
# Output: Raw text transcription

from transformers import pipeline

transcriber = pipeline(
    "automatic-speech-recognition",
    model="MERaLiON/MERaLiON-2-10B-ASR",
    device=0  # GPU
)
result = transcriber(audio_path)
text = result['text']
```

### Dependencies
```
transformers>=4.35.0
torch>=2.0.0
librosa>=0.10.0
soundfile>=0.12.0
```

### Success Criteria
- [ ] `scripts/test_meralion.py` runs successfully on sample audio
- [ ] Transcribes Singlish audio to text
- [ ] Model loads once and is cached

### Do NOT Touch
- `backend/services/diarization.py` (Agent 1's domain)
- Post-processing corrections (Agent 3's domain)
- Word counting (Agent 3's domain)
- `backend/processor.py` (integration happens after merge)

---

## Agent 3: Singlish NLP (Corrections + Counting)

**Worktree:** `C:\Users\nicko\Desktop\wagmi\Hack-Roll-singlish-nlp`
**Branch:** `singlish-nlp`

### Scope
Implement post-processing corrections and word counting logic.

### Files to Modify
- `backend/services/transcription.py` — Add `apply_corrections()` and `count_target_words()` functions
- `backend/tests/test_word_counting.py` — Unit tests for corrections and counting

### Deliverables
1. `apply_corrections(text: str) -> str`
   - Applies Singlish corrections dictionary
   - Handles case-insensitive matching
   - Returns corrected text
2. `count_target_words(text: str) -> Dict[str, int]`
   - Counts occurrences of target Singlish words
   - Returns dict like `{'walao': 3, 'lah': 5}`

### Technical Details
```python
# Corrections dictionary (expand as needed)
CORRECTIONS = {
    'while up': 'walao',
    'wa lao': 'walao',
    'wah lao': 'walao',
    'cheap buy': 'cheebai',
    'chee bye': 'cheebai',
    'lunch hour': 'lanjiao',
    'lan jiao': 'lanjiao',
    'la': 'lah',
    'low': 'lor',
    'loh': 'lor',
    'see ya': 'sia',
    'shook': 'shiok',
    'pie say': 'paiseh',
    'pai seh': 'paiseh',
}

# Target words to count
TARGET_WORDS = [
    'walao', 'cheebai', 'lanjiao',  # Vulgar
    'lah', 'lor', 'sia', 'meh',      # Particles
    'can', 'paiseh', 'shiok', 'sian' # Colloquial
]
```

### Dependencies
```
# No additional dependencies - pure Python
```

### Success Criteria
- [ ] All test cases in `test_word_counting.py` pass
- [ ] Corrections handle common ASR misrecognitions
- [ ] Word counting is case-insensitive and accurate

### Do NOT Touch
- Model loading code (Agent 2's domain)
- `backend/services/diarization.py` (Agent 1's domain)
- `backend/processor.py` (integration happens after merge)

### Important Note
Agent 2 will create the base `transcription.py` with model code. Your corrections and counting functions should be additive — they can coexist. When merging, the file will have both model code (from Agent 2) and your NLP functions.

---

## Agent 4: Data Preparation

**Worktree:** `C:\Users\nicko\Desktop\wagmi\Hack-Roll-data-prep`
**Branch:** `data-prep`

### Scope
Prepare training data for MERaLiON fine-tuning on Singlish vocabulary.

### Files to Modify
- `ml/scripts/prepare_singlish_data.py` — Data preparation script
- `ml/scripts/filter_imda.py` — Filter IMDA corpus for Singlish samples
- `ml/data/` — Output directory for processed data

### Deliverables
1. Script to filter IMDA National Speech Corpus for Singlish-heavy samples
2. Script to prepare training data in format MERaLiON expects
3. Data manifest files for fine-tuning

### Technical Details
```python
# IMDA National Speech Corpus filtering criteria:
# - Contains target Singlish words in transcript
# - Clear audio quality (no heavy background noise)
# - Speaker variety (multiple speakers, demographics)

# Output format for fine-tuning:
# - Audio: 16kHz mono WAV
# - Transcripts: JSON with {audio_path, text, duration}
```

### Data Sources
- IMDA National Speech Corpus: https://www.imda.gov.sg/how-we-can-help/national-speech-corpus
- Singlish recordings (if available)

### Success Criteria
- [ ] Filter script identifies Singlish-heavy samples
- [ ] Data manifest generated for fine-tuning
- [ ] Audio files in correct format (16kHz mono)

### Do NOT Touch
- `backend/` files (other agents' domain)
- Model inference code

---

## Merge Order & Integration

### Recommended Merge Sequence

1. **Merge Agent 2 (transcription) first** — Base model code
2. **Merge Agent 3 (singlish-nlp) second** — Adds to transcription.py
3. **Merge Agent 1 (diarization) third** — Independent service
4. **Agent 4 (data-prep)** — Can merge anytime, independent

### After All Merges: Integration Task

Once Agents 1-3 are merged into `ml`, the coordinator (you or a 5th session) implements:

**File:** `backend/processor.py`

```python
async def process_session(session_id: str) -> ProcessingResult:
    # 1. Concatenate audio chunks
    full_audio = concatenate_chunks(session_id)

    # 2. Run diarization (Agent 1's code)
    segments = diarize_audio(full_audio)

    # 3. For each segment (Agent 2 + 3's code)
    for segment in segments:
        clip = extract_speaker_segment(full_audio, segment.start, segment.end)
        text = transcribe_audio(clip)
        corrected = apply_corrections(text)
        counts = count_target_words(corrected)

    # 4. Generate sample clips, aggregate results
    # 5. Return structured data for database
```

---

## How to Start Each Agent

### Terminal 1 (Agent 1 - Diarization)
```bash
cd C:\Users\nicko\Desktop\wagmi\Hack-Roll-diarization
claude
# Prompt: "Read .planning/AGENTS.md and implement Agent 1 (Diarization Service)"
```

### Terminal 2 (Agent 2 - Transcription)
```bash
cd C:\Users\nicko\Desktop\wagmi\Hack-Roll-transcription
claude
# Prompt: "Read .planning/AGENTS.md and implement Agent 2 (Transcription Service)"
```

### Terminal 3 (Agent 3 - Singlish NLP)
```bash
cd C:\Users\nicko\Desktop\wagmi\Hack-Roll-singlish-nlp
claude
# Prompt: "Read .planning/AGENTS.md and implement Agent 3 (Singlish NLP)"
```

### Terminal 4 (Agent 4 - Data Prep)
```bash
cd C:\Users\nicko\Desktop\wagmi\Hack-Roll-data-prep
claude
# Prompt: "Read .planning/AGENTS.md and implement Agent 4 (Data Preparation)"
```

---

## Merging Workflow

When an agent completes their work:

```bash
# From main worktree (Hack-Roll)
cd C:\Users\nicko\Desktop\wagmi\Hack-Roll

# Merge completed branch into ml
git checkout ml
git merge <branch-name> --no-ff -m "Merge <agent> work"

# Example: Merge transcription
git merge transcription --no-ff -m "Merge Agent 2: transcription service"
```

### Conflict Resolution
If conflicts occur (unlikely with this split):
1. Both agents modified same file → Manual resolution
2. Prefer the more complete implementation
3. Combine additive changes (e.g., Agent 2 + Agent 3 in transcription.py)

---

## Communication

Agents should NOT communicate with each other directly. The coordinator (Nickolas) handles:
- Reviewing completed work
- Triggering merges
- Resolving any integration issues
- Implementing `processor.py` after merges

---

*Created: 2026-01-17*
*Last updated: 2026-01-17*
