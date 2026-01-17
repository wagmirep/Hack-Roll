# Team Recordings

Place your audio recordings here for fine-tuning.

## Directory Structure

```
team_recordings/
├── audio/          # Your .wav or .mp3 files
├── transcripts/    # Auto-generated, then manually corrected
└── README.md       # This file
```

## Filename Convention

**Format:** `speakername_description_number.wav`

**Examples:**
- `nickolas_template_001.wav` - Reading sentence template #1
- `winston_natural_01.wav` - Natural conversation recording
- `harshith_template_042.wav` - Reading sentence template #42

## Workflow

1. **Record audio** → Save to `audio/`
2. **Auto-transcribe:**
   ```bash
   python scripts/prepare_team_recordings.py --auto-transcribe
   ```
3. **Manually correct** transcripts in `transcripts/` folder
4. **Create splits:**
   ```bash
   python scripts/prepare_team_recordings.py --process
   ```

## Audio Requirements

- Format: WAV or MP3 (WAV preferred)
- Sample rate: 16kHz (will be converted automatically)
- Duration: 1-30 seconds per file
- Quality: Clear audio, minimal background noise
