"""
filter_imda.py - IMDA National Speech Corpus Filtering

PURPOSE:
    Filter the IMDA National Speech Corpus to extract Singlish-heavy samples
    for LoRA fine-tuning on MERaLiON-2-10B-ASR.

RESPONSIBILITIES:
    - Load IMDA corpus transcripts and audio metadata
    - Identify samples containing target Singlish words
    - Filter by audio quality and duration
    - Export filtered samples list

USAGE:
    python filter_imda.py --imda-path /path/to/imda --output ml/data/raw/filtered_samples.json
    python filter_imda.py --imda-path /path/to/imda --min-word-count 2 --output filtered.json

REFERENCES:
    - IMDA National Speech Corpus: https://www.imda.gov.sg/how-we-can-help/national-speech-corpus
    - prepare_singlish_data.py - Uses filtered samples for training data prep
"""

import argparse
import json
import os
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Optional, Set
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# =============================================================================
# TARGET WORDS
# =============================================================================

# Singlish particles and expressions to look for
TARGET_WORDS = [
    # Vulgar expressions (often misrecognized by ASR)
    'walao', 'wah lao', 'wa lao',
    'cheebai', 'chee bai', 'chee bye',
    'lanjiao', 'lan jiao',

    # Common particles
    'lah', 'la',
    'lor', 'loh',
    'leh',
    'sia', 'siah',
    'meh',
    'hor',
    'ah',
    'one',  # as sentence-final particle

    # Colloquial expressions
    'paiseh', 'pai seh',
    'shiok',
    'sian',
    'bo jio',
    'can',  # as standalone affirmative
    'cannot',
    'liddat', 'like that',
    'atas',
    'chope',
    'kiasu',
    'kaypoh', 'kaypo',
    'lepak',
    'makan',
    'steady',
    'jialat',
    'sabo',
    'gong',
    'blur',
    'heng',
    'suay',
    'chiong',
    'bo bian',
    'ownself',
]

# Normalize target words for matching
TARGET_WORDS_NORMALIZED = set(word.lower().replace(' ', '') for word in TARGET_WORDS)


@dataclass
class AudioSample:
    """Represents a single audio sample from IMDA corpus."""
    sample_id: str
    audio_path: str
    transcript: str
    duration_seconds: float
    speaker_id: Optional[str] = None
    channel: Optional[str] = None
    singlish_words_found: Optional[List[str]] = None
    singlish_word_count: int = 0


@dataclass
class FilterConfig:
    """Configuration for IMDA filtering."""
    min_duration: float = 1.0  # seconds
    max_duration: float = 30.0  # seconds
    min_word_count: int = 1  # minimum Singlish words per sample
    language_codes: Optional[List[str]] = None  # ['ENGLISH'] or None for all
    exclude_speakers: Optional[List[str]] = None


def normalize_text(text: str) -> str:
    """Normalize text for Singlish word matching."""
    # Lowercase and remove extra whitespace
    text = text.lower().strip()
    text = re.sub(r'\s+', ' ', text)
    return text


def find_singlish_words(text: str) -> List[str]:
    """
    Find Singlish words/expressions in text.

    Returns list of matched Singlish words.
    """
    found = []
    normalized = normalize_text(text)

    # Check for each target word
    for word in TARGET_WORDS:
        word_lower = word.lower()
        # Use word boundary matching to avoid partial matches
        # For multi-word expressions, check exact match
        if ' ' in word_lower:
            if word_lower in normalized:
                found.append(word_lower.replace(' ', ''))
        else:
            # Single word - use word boundaries
            pattern = rf'\b{re.escape(word_lower)}\b'
            if re.search(pattern, normalized):
                found.append(word_lower)

    return list(set(found))  # deduplicate


def check_audio_quality(audio_path: str, min_snr_db: float = 15.0) -> bool:
    """
    Check if audio file meets quality requirements.

    Note: This is a placeholder. For hackathon, we skip SNR checking
    and assume IMDA corpus has decent quality.
    """
    # For hackathon: assume IMDA corpus audio is good quality
    # In production, would compute SNR using librosa/scipy
    return True


def get_audio_duration(audio_path: str) -> Optional[float]:
    """
    Get audio duration in seconds.

    Tries multiple methods:
    1. librosa (most accurate)
    2. soundfile (fast)
    3. File size estimation (fallback)
    """
    try:
        import librosa
        duration = librosa.get_duration(path=audio_path)
        return duration
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"librosa failed for {audio_path}: {e}")

    try:
        import soundfile as sf
        with sf.SoundFile(audio_path) as f:
            return len(f) / f.samplerate
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"soundfile failed for {audio_path}: {e}")

    # Fallback: estimate from file size (assuming 16kHz, 16-bit mono)
    try:
        file_size = os.path.getsize(audio_path)
        # 16kHz * 2 bytes/sample = 32000 bytes/second for raw audio
        # WAV has ~44 byte header, but close enough for estimation
        estimated_duration = file_size / 32000
        return estimated_duration
    except Exception:
        return None


def load_imda_manifest(imda_path: str) -> List[Dict]:
    """
    Load IMDA corpus manifest.

    IMDA corpus structure varies by version. This handles common formats:
    - manifest.json
    - segments.json
    - Individual transcript files with audio
    """
    imda_path = Path(imda_path)

    # Try common manifest file names
    for manifest_name in ['manifest.json', 'segments.json', 'metadata.json', 'index.json']:
        manifest_path = imda_path / manifest_name
        if manifest_path.exists():
            logger.info(f"Found manifest: {manifest_path}")
            with open(manifest_path, 'r', encoding='utf-8') as f:
                return json.load(f)

    # Try loading from transcript files
    samples = []
    transcript_patterns = ['*.txt', '*.TextGrid', '*.json']

    for pattern in transcript_patterns:
        for transcript_file in imda_path.rglob(pattern):
            # Skip non-transcript files
            if transcript_file.name in ['manifest.json', 'metadata.json']:
                continue

            # Look for corresponding audio file
            audio_extensions = ['.wav', '.flac', '.mp3']
            audio_file = None
            for ext in audio_extensions:
                potential_audio = transcript_file.with_suffix(ext)
                if potential_audio.exists():
                    audio_file = potential_audio
                    break

            if audio_file:
                try:
                    if pattern == '*.json':
                        with open(transcript_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            transcript = data.get('transcript', data.get('text', ''))
                    else:
                        with open(transcript_file, 'r', encoding='utf-8') as f:
                            transcript = f.read().strip()

                    samples.append({
                        'sample_id': transcript_file.stem,
                        'audio_path': str(audio_file),
                        'transcript': transcript,
                    })
                except Exception as e:
                    logger.warning(f"Failed to load {transcript_file}: {e}")

    logger.info(f"Found {len(samples)} samples from transcript files")
    return samples


def create_sample_manifest(samples: List[Dict], output_dir: str) -> None:
    """
    Create a template manifest for manual sample collection.

    Use this when IMDA corpus is not available and you want to
    record your own Singlish samples.
    """
    template = {
        "samples": [
            {
                "sample_id": "sample_001",
                "audio_path": "audio/sample_001.wav",
                "transcript": "Wah lao eh, this one damn shiok sia!",
                "duration_seconds": 5.0,
                "speaker_id": "speaker_01"
            },
            {
                "sample_id": "sample_002",
                "audio_path": "audio/sample_002.wav",
                "transcript": "Cannot lah, I very sian already.",
                "duration_seconds": 4.0,
                "speaker_id": "speaker_02"
            }
        ],
        "instructions": {
            "audio_format": "WAV, 16kHz, mono",
            "min_duration": "1 second",
            "max_duration": "30 seconds",
            "content": "Natural Singlish conversation with target words",
            "target_words": TARGET_WORDS[:20]  # Sample of target words
        }
    }

    output_path = Path(output_dir) / 'sample_manifest_template.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(template, f, indent=2)

    logger.info(f"Created sample manifest template: {output_path}")


def filter_samples(
    samples: List[Dict],
    config: FilterConfig
) -> List[AudioSample]:
    """
    Filter samples based on Singlish content and audio requirements.

    Args:
        samples: List of sample dictionaries from manifest
        config: Filtering configuration

    Returns:
        List of AudioSample objects that pass all filters
    """
    filtered = []
    stats = {
        'total': len(samples),
        'no_singlish': 0,
        'too_short': 0,
        'too_long': 0,
        'audio_missing': 0,
        'low_quality': 0,
        'passed': 0
    }

    for sample in samples:
        sample_id = sample.get('sample_id', sample.get('id', 'unknown'))
        audio_path = sample.get('audio_path', sample.get('audio', ''))
        transcript = sample.get('transcript', sample.get('text', ''))

        # Check for Singlish words
        singlish_words = find_singlish_words(transcript)
        if len(singlish_words) < config.min_word_count:
            stats['no_singlish'] += 1
            continue

        # Check audio file exists
        if not os.path.exists(audio_path):
            stats['audio_missing'] += 1
            continue

        # Check duration
        duration = sample.get('duration_seconds') or get_audio_duration(audio_path)
        if duration is None:
            stats['audio_missing'] += 1
            continue

        if duration < config.min_duration:
            stats['too_short'] += 1
            continue

        if duration > config.max_duration:
            stats['too_long'] += 1
            continue

        # Check audio quality (placeholder for now)
        if not check_audio_quality(audio_path):
            stats['low_quality'] += 1
            continue

        # Passed all filters
        stats['passed'] += 1
        filtered.append(AudioSample(
            sample_id=sample_id,
            audio_path=audio_path,
            transcript=transcript,
            duration_seconds=duration,
            speaker_id=sample.get('speaker_id'),
            channel=sample.get('channel'),
            singlish_words_found=singlish_words,
            singlish_word_count=len(singlish_words)
        ))

    # Log statistics
    logger.info("=== Filtering Statistics ===")
    logger.info(f"Total samples: {stats['total']}")
    logger.info(f"No Singlish words: {stats['no_singlish']}")
    logger.info(f"Too short (<{config.min_duration}s): {stats['too_short']}")
    logger.info(f"Too long (>{config.max_duration}s): {stats['too_long']}")
    logger.info(f"Audio missing: {stats['audio_missing']}")
    logger.info(f"Low quality: {stats['low_quality']}")
    logger.info(f"PASSED: {stats['passed']}")

    return filtered


def analyze_word_distribution(samples: List[AudioSample]) -> Dict[str, int]:
    """Analyze distribution of Singlish words in filtered samples."""
    word_counts = {}

    for sample in samples:
        for word in (sample.singlish_words_found or []):
            word_counts[word] = word_counts.get(word, 0) + 1

    # Sort by frequency
    sorted_counts = dict(sorted(word_counts.items(), key=lambda x: x[1], reverse=True))
    return sorted_counts


def save_filtered_samples(
    samples: List[AudioSample],
    output_path: str,
    word_distribution: Optional[Dict[str, int]] = None
) -> None:
    """Save filtered samples to JSON file."""
    output = {
        'total_samples': len(samples),
        'samples': [asdict(s) for s in samples],
    }

    if word_distribution:
        output['word_distribution'] = word_distribution

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved {len(samples)} filtered samples to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Filter IMDA National Speech Corpus for Singlish-heavy samples'
    )
    parser.add_argument(
        '--imda-path',
        type=str,
        required=True,
        help='Path to IMDA corpus directory'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='ml/data/raw/filtered_samples.json',
        help='Output path for filtered samples JSON'
    )
    parser.add_argument(
        '--min-duration',
        type=float,
        default=1.0,
        help='Minimum audio duration in seconds (default: 1.0)'
    )
    parser.add_argument(
        '--max-duration',
        type=float,
        default=30.0,
        help='Maximum audio duration in seconds (default: 30.0)'
    )
    parser.add_argument(
        '--min-word-count',
        type=int,
        default=1,
        help='Minimum Singlish words per sample (default: 1)'
    )
    parser.add_argument(
        '--create-template',
        action='store_true',
        help='Create a sample manifest template for manual recording'
    )

    args = parser.parse_args()

    # Create template if requested
    if args.create_template:
        create_sample_manifest([], Path(args.output).parent)
        return

    # Load IMDA manifest
    logger.info(f"Loading IMDA corpus from: {args.imda_path}")
    samples = load_imda_manifest(args.imda_path)

    if not samples:
        logger.error("No samples found in IMDA corpus!")
        logger.info("Use --create-template to create a manifest template for manual recording")
        return

    logger.info(f"Loaded {len(samples)} samples from IMDA corpus")

    # Filter samples
    config = FilterConfig(
        min_duration=args.min_duration,
        max_duration=args.max_duration,
        min_word_count=args.min_word_count
    )

    filtered = filter_samples(samples, config)

    if not filtered:
        logger.warning("No samples passed filtering!")
        return

    # Analyze word distribution
    word_dist = analyze_word_distribution(filtered)
    logger.info("\n=== Singlish Word Distribution ===")
    for word, count in list(word_dist.items())[:20]:
        logger.info(f"  {word}: {count}")

    # Save results
    save_filtered_samples(filtered, args.output, word_dist)


if __name__ == '__main__':
    main()
