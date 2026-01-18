# Rabak

> "Track your lah, lor, and more"

Singlish word tracking app with AI speaker recognition. One phone records everyone, automatically segments speakers, users claim their words, get Spotify Wrapped-style stats.

## Features

- **One-phone group recording** — Place one phone on the table, record everyone
- **AI speaker diarization** — Automatically identify who spoke when
- **Singlish word detection** — Track particles, expressions, and colloquial terms
- **Claiming UI** — Listen to audio samples, click "That's me!"
- **Spotify Wrapped-style stats** — Weekly/monthly word usage statistics

## Tech Stack

| Component | Technology |
|-----------|------------|
| Mobile | React Native + Expo |
| Backend | FastAPI (Python) |
| ASR | MERaLiON-2-10B-ASR |
| Diarization | pyannote/speaker-diarization-3.1 |
| Database | Supabase (PostgreSQL + Auth) |
| ML Processing | Google Colab |

## Quick Start

### Prerequisites

- Python 3.10+
- CUDA-capable GPU (recommended) or CPU
- HuggingFace account with pyannote model access

### 1. Clone and Setup

```bash
git clone https://github.com/wagmirep/Hack-Roll.git
cd Hack-Roll

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt
```

### 2. Get HuggingFace Token

The pyannote speaker diarization model requires authentication:

1. Create account at https://huggingface.co
2. Accept model terms at https://huggingface.co/pyannote/speaker-diarization-3.1
3. Generate token at https://huggingface.co/settings/tokens
4. Create `.env` file:

```bash
# backend/.env
HUGGINGFACE_TOKEN=hf_your_token_here
```

### 3. Test Models

```bash
# Test MERaLiON transcription
python scripts/test_meralion.py

# Test pyannote diarization
python scripts/test_pyannote.py

# With custom audio
python scripts/test_pyannote.py --audio path/to/multi_speaker.wav
```

### 4. Run Backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

## GPU Setup

Both models benefit significantly from GPU acceleration.

### Option 1: Local NVIDIA GPU

```bash
# Check CUDA availability
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"

# Install CUDA-enabled PyTorch (if needed)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Option 2: Google Colab (Free GPU)

```python
# In Colab notebook
!pip install pyannote.audio transformers torch

import os
os.environ['HUGGINGFACE_TOKEN'] = 'hf_your_token'

# Test diarization
from pyannote.audio import Pipeline
pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization-3.1",
    use_auth_token=os.environ['HUGGINGFACE_TOKEN']
)
```

### Option 3: Cloud GPU (Lambda Labs, RunPod, etc.)

1. Spin up instance with CUDA 11.8+
2. Clone repo and install dependencies
3. Set `HUGGINGFACE_TOKEN` environment variable
4. Run test scripts

## Project Structure

```
Hack-Roll/
├── backend/
│   ├── services/
│   │   ├── diarization.py    # Speaker segmentation (pyannote)
│   │   └── transcription.py  # ASR + corrections (MERaLiON)
│   ├── tests/
│   │   ├── test_transcription.py
│   │   └── test_word_counting.py
│   ├── processor.py          # Pipeline orchestration
│   └── requirements.txt
├── scripts/
│   ├── test_meralion.py      # MERaLiON test suite
│   └── test_pyannote.py      # pyannote test suite
├── mobile/
│   └── src/                  # React Native app
├── docs/
│   └── MODELS.md             # Detailed model documentation
├── .planning/
│   ├── PROJECT.md
│   ├── ROADMAP.md
│   └── AGENTS.md
└── CLAUDE.md                 # AI assistant instructions
```

## Testing

```bash
# Run all backend tests
cd backend && python -m pytest tests/ -v

# Run ML tests
cd ml && python -m pytest tests/ -v

# Current status: 95 tests passing
```

## Target Words

The app tracks these Singlish expressions:

| Category | Words |
|----------|-------|
| Particles | lah, lor, sia, meh, leh, hor, ah |
| Expressions | walao, alamak, aiyo, bojio |
| Colloquial | can, paiseh, shiok, sian, bodoh, kiasu, kiasi |

## Post-Processing Corrections

The ASR may mishear Singlish words. Automatic corrections handle common cases:

| ASR Output | Corrected To |
|------------|--------------|
| "while up" | walao |
| "pie say" | paiseh |
| "shook" | shiok |
| "a llama" | alamak |

See `backend/services/transcription.py` for the full corrections dictionary.

## Roadmap

| Phase | Status |
|-------|--------|
| 1. Model Setup & Validation | Complete |
| 2. Speaker Diarization Service | Complete |
| 3. ASR Transcription Service | Complete |
| 4. Processing Pipeline Integration | Complete |

## Resources

- [MERaLiON Paper](https://arxiv.org/abs/2412.09818)
- [pyannote Documentation](https://github.com/pyannote/pyannote-audio)

## License

MIT
