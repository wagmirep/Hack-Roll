"""
prepare_singlish_data.py - Singlish Training Data Preparation

PURPOSE:
    Prepare filtered Singlish samples for LoRA fine-tuning on MERaLiON-2-10B-ASR.
    Converts audio to correct format and creates HuggingFace-compatible dataset.

RESPONSIBILITIES:
    - Load filtered samples from filter_imda.py output
    - Convert audio to 16kHz mono WAV format
    - Create train/validation/test splits
    - Generate HuggingFace-compatible dataset format
    - Create manifest files for training

USAGE:
    python prepare_singlish_data.py --input ml/data/raw/filtered_samples.json --output ml/data/processed
    python prepare_singlish_data.py --input filtered.json --split-ratio 0.8 0.1 0.1

INPUT FORMAT:
    Filtered samples JSON from filter_imda.py:
    {
        "total_samples": 1000,
        "samples": [
            {
                "sample_id": "sample_001",
                "audio_path": "/path/to/audio.wav",
                "transcript": "Wah lao, this one damn shiok sia!",
                "duration_seconds": 5.0
            },
            ...
        ]
    }

OUTPUT FORMAT:
    ml/data/processed/
    ├── audio/
    │   ├── sample_001.wav  (16kHz mono)
    │   ├── sample_002.wav
    │   └── ...
    ├── manifest.json       # Full dataset manifest
    └── dataset/            # HuggingFace dataset files
        ├── train/
        ├── validation/
        └── test/

    ml/data/splits/
    ├── train.json
    ├── val.json
    └── test.json

REFERENCES:
    - filter_imda.py - Provides filtered samples
    - train_lora.py - Consumes prepared data
    - HuggingFace datasets library
"""

import argparse
import json
import os
import shutil
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import random
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class ProcessedSample:
    """A sample ready for training."""
    sample_id: str
    audio_path: str  # Path to processed 16kHz mono WAV
    transcript: str
    duration_seconds: float
    original_audio_path: Optional[str] = None
    singlish_words: List[str] = field(default_factory=list)


@dataclass
class DatasetSplit:
    """A dataset split (train/val/test)."""
    name: str
    samples: List[ProcessedSample]

    @property
    def total_duration(self) -> float:
        return sum(s.duration_seconds for s in self.samples)


# =============================================================================
# AUDIO PROCESSING
# =============================================================================

def convert_audio_to_training_format(
    input_path: str,
    output_path: str,
    target_sr: int = 16000
) -> bool:
    """
    Convert audio file to training format (16kHz mono WAV).

    Args:
        input_path: Path to input audio file
        output_path: Path to output WAV file
        target_sr: Target sample rate (default 16kHz)

    Returns:
        True if successful, False otherwise
    """
    try:
        import librosa
        import soundfile as sf

        # Load audio
        audio, sr = librosa.load(input_path, sr=target_sr, mono=True)

        # Write as WAV
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        sf.write(output_path, audio, target_sr)

        return True

    except ImportError:
        # Fallback: try to copy if already correct format
        logger.warning("librosa/soundfile not available, attempting direct copy")
        try:
            shutil.copy(input_path, output_path)
            return True
        except Exception as e:
            logger.error(f"Failed to copy audio: {e}")
            return False

    except Exception as e:
        logger.error(f"Failed to convert {input_path}: {e}")
        return False


def validate_audio_format(audio_path: str, expected_sr: int = 16000) -> Tuple[bool, str]:
    """
    Validate that audio file is in correct format.

    Returns:
        (is_valid, message)
    """
    try:
        import librosa
        audio, sr = librosa.load(audio_path, sr=None, mono=False)

        issues = []

        # Check sample rate
        if sr != expected_sr:
            issues.append(f"Sample rate is {sr}Hz, expected {expected_sr}Hz")

        # Check mono
        if len(audio.shape) > 1 and audio.shape[0] > 1:
            issues.append(f"Audio has {audio.shape[0]} channels, expected mono")

        # Check duration
        duration = len(audio) / sr if len(audio.shape) == 1 else len(audio[0]) / sr
        if duration < 0.5:
            issues.append(f"Audio too short ({duration:.2f}s)")
        elif duration > 30:
            issues.append(f"Audio too long ({duration:.2f}s)")

        if issues:
            return False, "; ".join(issues)

        return True, f"Valid ({duration:.2f}s, {sr}Hz, mono)"

    except Exception as e:
        return False, f"Error loading audio: {e}"


# =============================================================================
# DATA LOADING
# =============================================================================

def load_filtered_samples(input_path: str) -> List[Dict]:
    """Load filtered samples from JSON file."""
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Handle list format directly
    if isinstance(data, list):
        return data

    # Handle dict format with 'samples' key
    if isinstance(data, dict):
        if 'samples' in data:
            return data['samples']
        # Maybe the dict itself is a single sample? Return as list
        if 'sample_id' in data or 'audio_path' in data:
            return [data]

    raise ValueError(f"Unknown input format in {input_path}")


def load_custom_samples(audio_dir: str, transcript_dir: str) -> List[Dict]:
    """
    Load samples from separate audio and transcript directories.

    Use this for custom recorded samples.
    """
    audio_path = Path(audio_dir)
    transcript_path = Path(transcript_dir)

    samples = []

    for audio_file in audio_path.glob('*.wav'):
        # Look for matching transcript
        transcript_file = transcript_path / f"{audio_file.stem}.txt"
        if not transcript_file.exists():
            transcript_file = transcript_path / f"{audio_file.stem}.json"

        if transcript_file.exists():
            if transcript_file.suffix == '.json':
                with open(transcript_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    transcript = data.get('transcript', data.get('text', ''))
            else:
                with open(transcript_file, 'r', encoding='utf-8') as f:
                    transcript = f.read().strip()

            samples.append({
                'sample_id': audio_file.stem,
                'audio_path': str(audio_file),
                'transcript': transcript
            })

    return samples


# =============================================================================
# DATASET CREATION
# =============================================================================

def create_train_val_test_split(
    samples: List[ProcessedSample],
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
    test_ratio: float = 0.1,
    seed: int = 42
) -> Tuple[DatasetSplit, DatasetSplit, DatasetSplit]:
    """
    Split samples into train/validation/test sets.

    Args:
        samples: List of processed samples
        train_ratio: Fraction for training (default 0.8)
        val_ratio: Fraction for validation (default 0.1)
        test_ratio: Fraction for testing (default 0.1)
        seed: Random seed for reproducibility

    Returns:
        (train_split, val_split, test_split)
    """
    assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 0.001, \
        "Ratios must sum to 1.0"

    # Shuffle samples
    random.seed(seed)
    shuffled = samples.copy()
    random.shuffle(shuffled)

    # Calculate split indices
    n = len(shuffled)
    train_end = int(n * train_ratio)
    val_end = train_end + int(n * val_ratio)

    train_samples = shuffled[:train_end]
    val_samples = shuffled[train_end:val_end]
    test_samples = shuffled[val_end:]

    return (
        DatasetSplit(name='train', samples=train_samples),
        DatasetSplit(name='validation', samples=val_samples),
        DatasetSplit(name='test', samples=test_samples)
    )


def create_manifest(
    samples: List[ProcessedSample],
    output_path: str,
    base_audio_dir: Optional[str] = None
) -> None:
    """
    Create a manifest JSON file for the dataset.

    Args:
        samples: List of processed samples
        output_path: Path to output manifest file
        base_audio_dir: If provided, make audio paths relative to this directory
    """
    manifest_samples = []

    for sample in samples:
        audio_path = sample.audio_path
        if base_audio_dir:
            audio_path = os.path.relpath(sample.audio_path, base_audio_dir)

        manifest_samples.append({
            'sample_id': sample.sample_id,
            'audio_path': audio_path,
            'transcript': sample.transcript,
            'duration_seconds': sample.duration_seconds,
            'singlish_words': sample.singlish_words
        })

    manifest = {
        'total_samples': len(manifest_samples),
        'total_duration_seconds': sum(s.duration_seconds for s in samples),
        'samples': manifest_samples
    }

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    logger.info(f"Created manifest with {len(samples)} samples: {output_path}")


def create_huggingface_dataset(
    split: DatasetSplit,
    output_dir: str,
    audio_column: str = 'audio',
    text_column: str = 'transcript'
) -> None:
    """
    Create HuggingFace-compatible dataset files for a split.

    Creates JSON Lines file that can be loaded with:
        dataset = load_dataset('json', data_files={'train': 'train.jsonl'})

    Args:
        split: Dataset split
        output_dir: Output directory for dataset files
        audio_column: Name of audio column
        text_column: Name of text column
    """
    output_path = Path(output_dir) / split.name
    output_path.mkdir(parents=True, exist_ok=True)

    # Create JSONL file (HuggingFace preferred format)
    jsonl_path = output_path / f'{split.name}.jsonl'

    with open(jsonl_path, 'w', encoding='utf-8') as f:
        for sample in split.samples:
            record = {
                audio_column: sample.audio_path,
                text_column: sample.transcript,
                'duration': sample.duration_seconds,
                'sample_id': sample.sample_id
            }
            f.write(json.dumps(record, ensure_ascii=False) + '\n')

    logger.info(f"Created {split.name} dataset: {len(split.samples)} samples, "
                f"{split.total_duration:.1f}s total duration")


def save_split_files(
    train_split: DatasetSplit,
    val_split: DatasetSplit,
    test_split: DatasetSplit,
    output_dir: str
) -> None:
    """Save train/val/test split files for training scripts."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    splits = [
        ('train.json', train_split),
        ('val.json', val_split),
        ('test.json', test_split)
    ]

    for filename, split in splits:
        filepath = output_path / filename
        data = {
            'split_name': split.name,
            'total_samples': len(split.samples),
            'total_duration_seconds': split.total_duration,
            'samples': [asdict(s) for s in split.samples]
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved {filename}: {len(split.samples)} samples")


# =============================================================================
# MAIN PROCESSING
# =============================================================================

def process_samples(
    raw_samples: List[Dict],
    output_audio_dir: str,
    skip_conversion: bool = False
) -> List[ProcessedSample]:
    """
    Process raw samples: convert audio and prepare for training.

    Args:
        raw_samples: List of raw sample dictionaries
        output_audio_dir: Directory to save processed audio files
        skip_conversion: If True, skip audio conversion (for already-processed files)

    Returns:
        List of successfully processed samples
    """
    processed = []
    failed = 0

    output_path = Path(output_audio_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for i, sample in enumerate(raw_samples):
        sample_id = sample.get('sample_id', f'sample_{i:04d}')
        audio_path = sample.get('audio_path', sample.get('audio', ''))
        transcript = sample.get('transcript', sample.get('text', ''))

        # Skip if missing required fields
        if not audio_path or not transcript:
            logger.warning(f"Skipping {sample_id}: missing audio_path or transcript")
            failed += 1
            continue

        # Output audio path
        output_audio_path = output_path / f'{sample_id}.wav'

        # Convert audio if needed
        if not skip_conversion:
            if not os.path.exists(audio_path):
                logger.warning(f"Skipping {sample_id}: audio file not found: {audio_path}")
                failed += 1
                continue

            success = convert_audio_to_training_format(audio_path, str(output_audio_path))
            if not success:
                logger.warning(f"Skipping {sample_id}: audio conversion failed")
                failed += 1
                continue
        else:
            # Just copy or use existing path
            if not os.path.exists(output_audio_path):
                shutil.copy(audio_path, output_audio_path)

        # Get duration
        duration = sample.get('duration_seconds')
        if duration is None:
            try:
                import librosa
                duration = librosa.get_duration(path=str(output_audio_path))
            except:
                duration = 0.0

        # Get Singlish words
        singlish_words = sample.get('singlish_words_found', sample.get('singlish_words', []))

        processed.append(ProcessedSample(
            sample_id=sample_id,
            audio_path=str(output_audio_path),
            transcript=transcript,
            duration_seconds=duration,
            original_audio_path=audio_path,
            singlish_words=singlish_words
        ))

        if (i + 1) % 100 == 0:
            logger.info(f"Processed {i + 1}/{len(raw_samples)} samples")

    logger.info(f"Processing complete: {len(processed)} successful, {failed} failed")
    return processed


def print_dataset_stats(
    train_split: DatasetSplit,
    val_split: DatasetSplit,
    test_split: DatasetSplit
) -> None:
    """Print dataset statistics."""
    print("\n" + "="*60)
    print("DATASET STATISTICS")
    print("="*60)

    total_samples = len(train_split.samples) + len(val_split.samples) + len(test_split.samples)
    total_duration = train_split.total_duration + val_split.total_duration + test_split.total_duration

    print(f"\nTotal samples: {total_samples}")
    print(f"Total duration: {total_duration/60:.1f} minutes ({total_duration/3600:.2f} hours)")

    print(f"\nTrain set:")
    print(f"  - Samples: {len(train_split.samples)} ({100*len(train_split.samples)/total_samples:.1f}%)")
    print(f"  - Duration: {train_split.total_duration/60:.1f} minutes")

    print(f"\nValidation set:")
    print(f"  - Samples: {len(val_split.samples)} ({100*len(val_split.samples)/total_samples:.1f}%)")
    print(f"  - Duration: {val_split.total_duration/60:.1f} minutes")

    print(f"\nTest set:")
    print(f"  - Samples: {len(test_split.samples)} ({100*len(test_split.samples)/total_samples:.1f}%)")
    print(f"  - Duration: {test_split.total_duration/60:.1f} minutes")

    # Singlish word coverage
    all_words = set()
    for sample in train_split.samples + val_split.samples + test_split.samples:
        all_words.update(sample.singlish_words)

    print(f"\nSinglish words covered: {len(all_words)}")
    if all_words:
        print(f"  Words: {', '.join(sorted(all_words)[:15])}{'...' if len(all_words) > 15 else ''}")

    print("="*60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description='Prepare Singlish training data for MERaLiON fine-tuning'
    )
    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help='Path to filtered samples JSON (from filter_imda.py)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='ml/data/processed',
        help='Output directory for processed data (default: ml/data/processed)'
    )
    parser.add_argument(
        '--splits-output',
        type=str,
        default='ml/data/splits',
        help='Output directory for train/val/test splits (default: ml/data/splits)'
    )
    parser.add_argument(
        '--train-ratio',
        type=float,
        default=0.8,
        help='Training set ratio (default: 0.8)'
    )
    parser.add_argument(
        '--val-ratio',
        type=float,
        default=0.1,
        help='Validation set ratio (default: 0.1)'
    )
    parser.add_argument(
        '--test-ratio',
        type=float,
        default=0.1,
        help='Test set ratio (default: 0.1)'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for splitting (default: 42)'
    )
    parser.add_argument(
        '--skip-conversion',
        action='store_true',
        help='Skip audio conversion (use if already in correct format)'
    )
    parser.add_argument(
        '--audio-dir',
        type=str,
        help='Custom audio directory (for loading samples from audio/transcript dirs)'
    )
    parser.add_argument(
        '--transcript-dir',
        type=str,
        help='Custom transcript directory (for loading samples from audio/transcript dirs)'
    )

    args = parser.parse_args()

    # Load samples
    logger.info(f"Loading samples from: {args.input}")

    if args.audio_dir and args.transcript_dir:
        raw_samples = load_custom_samples(args.audio_dir, args.transcript_dir)
    else:
        raw_samples = load_filtered_samples(args.input)

    logger.info(f"Loaded {len(raw_samples)} samples")

    if not raw_samples:
        logger.error("No samples loaded!")
        return

    # Process samples (convert audio)
    output_audio_dir = Path(args.output) / 'audio'
    processed_samples = process_samples(
        raw_samples,
        str(output_audio_dir),
        skip_conversion=args.skip_conversion
    )

    if not processed_samples:
        logger.error("No samples were successfully processed!")
        return

    # Create splits
    train_split, val_split, test_split = create_train_val_test_split(
        processed_samples,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        test_ratio=args.test_ratio,
        seed=args.seed
    )

    # Print statistics
    print_dataset_stats(train_split, val_split, test_split)

    # Create output directories
    processed_dir = Path(args.output)
    splits_dir = Path(args.splits_output)
    dataset_dir = processed_dir / 'dataset'

    # Save manifest
    create_manifest(
        processed_samples,
        str(processed_dir / 'manifest.json'),
        base_audio_dir=str(processed_dir)
    )

    # Save split files
    save_split_files(train_split, val_split, test_split, str(splits_dir))

    # Create HuggingFace dataset files
    for split in [train_split, val_split, test_split]:
        create_huggingface_dataset(split, str(dataset_dir))

    logger.info("\nData preparation complete!")
    logger.info(f"Processed audio: {output_audio_dir}")
    logger.info(f"Manifest: {processed_dir / 'manifest.json'}")
    logger.info(f"Split files: {splits_dir}")
    logger.info(f"HuggingFace dataset: {dataset_dir}")


if __name__ == '__main__':
    main()
