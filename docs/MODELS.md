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
