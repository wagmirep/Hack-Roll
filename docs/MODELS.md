# AI Models Guide

## MERaLiON-2-10B-ASR

**Purpose:** Transcribe Singlish speech to text

**Model:** `MERaLiON/MERaLiON-2-10B-ASR` (HuggingFace)

**Usage:**
```python
from transformers import pipeline

transcriber = pipeline(
    "automatic-speech-recognition",
    model="MERaLiON/MERaLiON-2-10B-ASR",
    device=0  # GPU
)

result = transcriber("audio.wav", return_timestamps=True)
print(result['text'])
```

**Specifications:**
- Input: 16kHz mono audio, max 30s chunks
- Output: Text transcription
- Performance: 85-90% accuracy on Singlish particles
- Pre-trained: No fine-tuning needed for hackathon

**Limitations:**
- May misinterpret vulgar slang (e.g., "walao" → "while up")
- Solution: Post-processing corrections dictionary

## pyannote Speaker Diarization

**Purpose:** Segment audio by speaker ("who spoke when")

**Model:** `pyannote/speaker-diarization-3.1`

**Setup:**
```python
from pyannote.audio import Pipeline

# Requires HuggingFace token
diarization = Pipeline.from_pretrained(
    "pyannote/speaker-diarization-3.1",
    use_auth_token="YOUR_HF_TOKEN"
)
```

**Usage:**
```python
result = diarization("full_audio.wav")

for turn, _, speaker in result.itertracks(yield_label=True):
    print(f"{speaker}: {turn.start:.1f}s - {turn.end:.1f}s")
```

**Output Format:**
```
SPEAKER_00: 0.0s - 5.2s
SPEAKER_01: 5.2s - 12.8s
SPEAKER_00: 12.8s - 18.5s
```

**Specifications:**
- Input: Full session audio (any length)
- Output: Time-stamped speaker segments
- Accuracy: 85-90% in good conditions

**Requirements:**
- Quiet environment
- Clear speech
- Minimal overlapping speech

---

## Diarization Service Implementation

> **File:** `backend/services/diarization.py`
> **Implemented:** 2026-01-17 (Agent 1)

### Why This Design

1. **Singleton Pattern for Model Loading**
   - The pyannote model is ~2GB and takes 10-30 seconds to load
   - Loading once and caching avoids repeated startup delays
   - Thread-safe double-checked locking prevents race conditions in concurrent requests

2. **GPU Auto-Detection**
   - Automatically moves model to CUDA if available
   - Falls back to CPU gracefully (slower but functional)
   - No manual configuration required

3. **Minimum Segment Filtering (0.5s default)**
   - Very short segments are often noise or breathing
   - Filtering improves transcription quality downstream
   - Configurable threshold for different use cases

4. **Overlap Filtering**
   - Overlapping speech is hard to transcribe accurately
   - Segments with >30% overlap are filtered out
   - Improves overall transcription quality at cost of some data loss

5. **WAV Bytes Output**
   - `extract_speaker_segment()` returns bytes, not file paths
   - Enables direct upload to S3 without temp files
   - Memory-efficient for short clips (5-30 seconds)

### API Reference

```python
from services.diarization import (
    diarize_audio,
    extract_speaker_segment,
    filter_overlapping_segments,
    get_all_speaker_samples,
    SpeakerSegment
)
```

#### `diarize_audio(audio_path, min_segment_duration=0.5)`

Run speaker diarization on an audio file.

```python
segments = diarize_audio("recording.wav")
# Returns: [
#   SpeakerSegment(speaker_id="SPEAKER_00", start_time=0.0, end_time=5.2),
#   SpeakerSegment(speaker_id="SPEAKER_01", start_time=5.2, end_time=12.8),
#   ...
# ]

for seg in segments:
    print(f"{seg.speaker_id}: {seg.start_time:.1f}s - {seg.end_time:.1f}s")
    print(f"  Duration: {seg.duration:.1f}s")
    print(f"  Dict: {seg.to_dict()}")
```

#### `extract_speaker_segment(audio_path, start_time, end_time, output_path=None)`

Extract a time range from audio file as WAV bytes.

```python
# Get bytes directly (for S3 upload)
clip_bytes = extract_speaker_segment("recording.wav", 0.0, 5.0)
s3.put_object(Body=clip_bytes, Bucket="bucket", Key="clip.wav")

# Or save to file
extract_speaker_segment("recording.wav", 0.0, 5.0, output_path="clip.wav")
```

#### `filter_overlapping_segments(segments, overlap_threshold=0.3)`

Remove segments with significant speaker overlap.

```python
clean_segments = filter_overlapping_segments(segments, overlap_threshold=0.3)
# Segments with >30% overlap are removed
```

#### `get_all_speaker_samples(audio_path, segments, sample_duration=5.0)`

Get representative audio samples for each speaker (for claiming UI).

```python
samples = get_all_speaker_samples("recording.wav", segments)
# Returns: {
#   "SPEAKER_00": b"RIFF...(wav bytes)...",
#   "SPEAKER_01": b"RIFF...(wav bytes)...",
# }

# Save samples for claiming UI
for speaker_id, audio_bytes in samples.items():
    upload_to_s3(f"samples/{session_id}/{speaker_id}.wav", audio_bytes)
```

### Integration with Processor

```python
# In processor.py (after all agents merged)
from services.diarization import diarize_audio, extract_speaker_segment, filter_overlapping_segments
from services.transcription import transcribe_audio, apply_corrections, count_target_words

async def process_session(session_id: str):
    audio_path = get_session_audio(session_id)

    # 1. Diarize
    segments = diarize_audio(audio_path)
    segments = filter_overlapping_segments(segments)

    # 2. Transcribe each segment
    results = []
    for seg in segments:
        clip = extract_speaker_segment(audio_path, seg.start_time, seg.end_time)
        text = transcribe_audio(clip)
        text = apply_corrections(text)
        counts = count_target_words(text)
        results.append({
            "speaker": seg.speaker_id,
            "start": seg.start_time,
            "end": seg.end_time,
            "words": counts
        })

    return results
```

### Testing

```bash
# Full test suite
python scripts/test_pyannote.py --token YOUR_HF_TOKEN

# With custom audio
python scripts/test_pyannote.py --audio path/to/multi_speaker.wav

# Quick validation (skip model loading)
python scripts/test_pyannote.py --skip-model
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `HUGGINGFACE_TOKEN` | Yes | HuggingFace token with pyannote model access |

**Getting the token:**
1. Create account at https://huggingface.co
2. Accept pyannote model terms at https://huggingface.co/pyannote/speaker-diarization-3.1
3. Generate token at https://huggingface.co/settings/tokens
4. Set `HUGGINGFACE_TOKEN` in `.env`

---

## Post-Processing

**Corrections Dictionary:**
```python
CORRECTIONS = {
    # Vulgar Singlish
    'while up': 'walao',
    'wa lao': 'walao',
    'cheap buy': 'cheebai',
    'lunch hour': 'lanjiao',

    # Particles
    'la': 'lah',
    'low': 'lor',
    'yeah': 'sia',
    'may': 'meh',
}

def apply_corrections(text):
    for wrong, correct in CORRECTIONS.items():
        text = text.replace(wrong, correct)
    return text
```

**Target Words:**
```python
TARGET_WORDS = [
    # Vulgar
    'walao', 'cheebai', 'lanjiao',

    # Particles
    'lah', 'lor', 'sia', 'meh',

    # Colloquial
    'can', 'paiseh', 'shiok', 'sian', 'steady'
]
```

## Processing Pipeline

```python
async def process_session(session_id):
    # 1. Concatenate audio chunks
    full_audio = concatenate_chunks(session_id)

    # 2. Speaker diarization
    segments = diarization_pipeline(full_audio)

    # 3. Transcribe each segment
    for segment in segments:
        audio_chunk = extract_audio(full_audio, segment.start, segment.end)
        text = transcriber(audio_chunk)['text']

        # 4. Post-processing
        corrected = apply_corrections(text)
        words = count_target_words(corrected)

        # 5. Save to database
        save_speaker_data(segment.speaker, words)

    # 6. Generate claiming samples
    generate_samples(session_id)
```

## Performance Tips

1. **Use GPU:** Both models benefit significantly from GPU
2. **Batch processing:** Process multiple segments together
3. **Audio quality:** 16kHz is optimal for MERaLiON
4. **Redis queue:** Offload processing to background worker
5. **Caching:** Cache corrections dictionary lookup

## Resources

- MERaLiON Paper: https://arxiv.org/abs/2412.09818
- pyannote Docs: https://github.com/pyannote/pyannote-audio
- HuggingFace Token: https://huggingface.co/settings/tokens
