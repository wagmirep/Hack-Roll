# ML Training Pipeline

This directory contains the machine learning pipeline for fine-tuning MERaLiON-2-10B-ASR on Singlish speech data using LoRA (Low-Rank Adaptation).

## Overview

The pipeline prepares training data from the IMDA National Speech Corpus, filtering for Singlish-heavy samples, and formats them for LoRA fine-tuning.

```
IMDA Corpus → filter_imda.py → filtered_samples.json → prepare_singlish_data.py → Training Data
```

## Directory Structure

```
ml/
├── configs/
│   ├── lora_config.yaml       # LoRA adapter hyperparameters
│   └── training_config.yaml   # Training settings
├── data/
│   ├── raw/                   # Raw/filtered IMDA samples
│   ├── processed/             # Converted 16kHz mono WAV files
│   │   ├── audio/             # Processed audio files
│   │   ├── manifest.json      # Full dataset manifest
│   │   └── dataset/           # HuggingFace format splits
│   └── splits/                # Train/val/test JSON files
├── scripts/
│   ├── filter_imda.py         # Filter IMDA for Singlish samples
│   ├── prepare_singlish_data.py  # Prepare training data
│   ├── prepare_imda_data.py   # Wrapper script (runs both above)
│   ├── train_lora.py          # LoRA fine-tuning (stub)
│   ├── evaluate.py            # Model evaluation (stub)
│   └── export_model.py        # Export trained adapters (stub)
├── tests/
│   ├── test_data_processing.py   # Data pipeline tests
│   └── test_evaluation.py        # Evaluation tests (stub)
├── checkpoints/               # Training checkpoints
├── outputs/                   # Final trained adapters
└── requirements.txt           # Python dependencies
```

## Quick Start

### 1. Install Dependencies

```bash
# For GPU support, install PyTorch first:
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118

# Then install ML dependencies:
pip install -r ml/requirements.txt
```

### 2. Prepare Training Data

**Option A: Full Pipeline (with IMDA corpus)**

```bash
python ml/scripts/prepare_imda_data.py --imda-path /path/to/imda
```

**Option B: Step by Step**

```bash
# Step 1: Filter IMDA corpus for Singlish samples
python ml/scripts/filter_imda.py \
    --imda-path /path/to/imda \
    --output ml/data/raw/filtered_samples.json \
    --min-word-count 1

# Step 2: Prepare training data (convert audio, create splits)
python ml/scripts/prepare_singlish_data.py \
    --input ml/data/raw/filtered_samples.json \
    --output ml/data/processed
```

**Option C: Custom Recordings (no IMDA)**

```bash
# Create a template manifest for your own recordings
python ml/scripts/filter_imda.py --create-template

# Or prepare from audio/transcript directories
python ml/scripts/prepare_singlish_data.py \
    --audio-dir /path/to/audio \
    --transcript-dir /path/to/transcripts \
    --input dummy.json
```

### 3. Run Tests

```bash
python -m pytest ml/tests/ -v
```

## Data Preparation Scripts

### filter_imda.py

Filters the IMDA National Speech Corpus for Singlish-heavy samples.

**Features:**
- Detects 40+ Singlish words/expressions (particles, vulgar, colloquial)
- Filters by duration (1-30 seconds)
- Case-insensitive matching with word boundaries
- Outputs word distribution statistics

**Target Words:**
- **Particles:** lah, lor, leh, sia, meh, hor, ah
- **Vulgar:** walao, cheebai, lanjiao
- **Colloquial:** paiseh, shiok, sian, kiasu, kaypoh, bo jio, jialat, etc.

**Usage:**
```bash
python ml/scripts/filter_imda.py --imda-path /path/to/imda --output filtered.json

# Options:
#   --min-duration    Minimum audio length (default: 1.0s)
#   --max-duration    Maximum audio length (default: 30.0s)
#   --min-word-count  Minimum Singlish words per sample (default: 1)
#   --create-template Create manifest template for manual recording
```

### prepare_singlish_data.py

Converts filtered samples to MERaLiON training format.

**Features:**
- Converts audio to 16kHz mono WAV (required by Whisper/MERaLiON)
- Creates 80/10/10 train/val/test splits
- Generates HuggingFace-compatible JSONL files
- Reproducible splits with seed parameter

**Usage:**
```bash
python ml/scripts/prepare_singlish_data.py --input filtered.json --output ml/data/processed

# Options:
#   --train-ratio     Training set ratio (default: 0.8)
#   --val-ratio       Validation set ratio (default: 0.1)
#   --test-ratio      Test set ratio (default: 0.1)
#   --seed            Random seed for reproducibility (default: 42)
#   --skip-conversion Skip audio conversion if already 16kHz mono
```

## Configuration

### lora_config.yaml

LoRA adapter settings based on research findings:

| Parameter | Value | Notes |
|-----------|-------|-------|
| rank (r) | 32 | Balanced for ~1000 samples |
| lora_alpha | 64 | 2x rank (standard practice) |
| target_modules | q_proj, v_proj | Minimal effective set |
| lora_dropout | 0.05 | Light regularization |
| bias | none | More stable training |

### training_config.yaml

Training hyperparameters:

| Parameter | Value | Notes |
|-----------|-------|-------|
| epochs | 3 | Prevents overfitting on small data |
| batch_size | 4 | Reduce if OOM |
| learning_rate | 1e-4 | Higher than full fine-tuning |
| fp16 | true | Memory optimization |
| gradient_checkpointing | true | Trades compute for memory |
| load_in_8bit | true | Enables training on 16GB GPU |

## Output Formats

### Manifest (manifest.json)

```json
{
  "total_samples": 1000,
  "total_duration_seconds": 5000.0,
  "samples": [
    {
      "sample_id": "sample_001",
      "audio_path": "audio/sample_001.wav",
      "transcript": "Wah lao eh, this one damn shiok sia!",
      "duration_seconds": 5.0,
      "singlish_words": ["walao", "shiok", "sia"]
    }
  ]
}
```

### Split Files (train.json, val.json, test.json)

```json
{
  "split_name": "train",
  "total_samples": 800,
  "total_duration_seconds": 4000.0,
  "samples": [...]
}
```

### HuggingFace Format (dataset/train/train.jsonl)

```jsonl
{"audio": "/path/to/sample_001.wav", "transcript": "Wah lao...", "duration": 5.0}
{"audio": "/path/to/sample_002.wav", "transcript": "Cannot lah...", "duration": 4.0}
```

Load with:
```python
from datasets import load_dataset
dataset = load_dataset('json', data_files={'train': 'ml/data/processed/dataset/train/train.jsonl'})
```

## Expected Results

For ~1000 samples:

| Metric | Expected |
|--------|----------|
| Trainable params | ~1% of model |
| Training time (T4) | 2-3 hours |
| Training time (A100) | 30-60 minutes |
| WER improvement | 5-15% on target words |
| Checkpoint size | ~50-100MB |

## References

- [MERaLiON-2-10B-ASR](https://huggingface.co/MERaLiON/MERaLiON-2-10B-ASR)
- [IMDA National Speech Corpus](https://www.imda.gov.sg/how-we-can-help/national-speech-corpus)
- [HuggingFace PEFT Documentation](https://huggingface.co/docs/peft)
- [LoRA Fine-tuning Research](.planning/phases/lora-finetuning/RESEARCH.md)
