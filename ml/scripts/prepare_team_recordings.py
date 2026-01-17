"""
prepare_team_recordings.py - Team Recording Data Preparation

PURPOSE:
    Process team voice recordings for LoRA fine-tuning on Singlish words.
    Simplified pipeline for hackathon - uses MERaLiON for auto-transcription
    with manual correction workflow.

WORKFLOW:
    1. Place audio files in ml/data/team_recordings/audio/
    2. Run script with --auto-transcribe to generate initial transcripts
    3. Manually correct transcripts in ml/data/team_recordings/transcripts/
    4. Run script with --process to create training splits

USAGE:
    # Step 1: Auto-transcribe recordings
    python prepare_team_recordings.py --auto-transcribe

    # Step 2: Manually correct transcripts in ml/data/team_recordings/transcripts/

    # Step 3: Process and create splits
    python prepare_team_recordings.py --process --test-ratio 0.15

    # Or do everything if transcripts already exist:
    python prepare_team_recordings.py --process

OUTPUT FORMAT:
    ml/data/splits/
    ├── train.json
    ├── val.json
    └── test.json

    Each JSON contains list of:
    {
        "audio_path": "path/to/audio.wav",
        "transcript": "corrected transcript text",
        "duration": 5.2,
        "speaker": "nickolas",
        "target_words": ["lah", "walao"]
    }
"""

import argparse
import json
import os
import random
from pathlib import Path
from typing import Optional
import warnings

# Audio processing
try:
    import librosa
    import soundfile as sf
    AUDIO_LIBS_AVAILABLE = True
except ImportError:
    AUDIO_LIBS_AVAILABLE = False
    warnings.warn("librosa/soundfile not installed. Audio processing disabled.")

# ASR for auto-transcription
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    warnings.warn("transformers not installed. Auto-transcription disabled.")


# =============================================================================
# CONFIGURATION
# =============================================================================

TARGET_WORDS = [
    # Particles (most frequent in Singlish)
    'lah', 'lor', 'leh', 'meh', 'sia', 'hor', 'ah', 'one', 'mah',
    # Exclamations
    'walao', 'wah', 'aiyo', 'alamak',
    # Common Singlish words
    'can', 'cannot', 'paiseh', 'shiok', 'sian', 'jialat', 'chope',
    'kiasu', 'kiasi', 'blur', 'atas', 'cheem', 'kaypoh', 'steady'
]

# Audio requirements
SAMPLE_RATE = 16000  # 16kHz mono
MIN_DURATION = 1.0   # seconds
MAX_DURATION = 30.0  # seconds

# Paths
BASE_DIR = Path(__file__).parent.parent
RECORDINGS_DIR = BASE_DIR / "data" / "team_recordings"
AUDIO_DIR = RECORDINGS_DIR / "audio"
TRANSCRIPT_DIR = RECORDINGS_DIR / "transcripts"
SPLITS_DIR = BASE_DIR / "data" / "splits"


# =============================================================================
# AUDIO UTILITIES
# =============================================================================

def get_audio_duration(audio_path: Path) -> float:
    """Get duration of audio file in seconds."""
    if not AUDIO_LIBS_AVAILABLE:
        raise RuntimeError("librosa not installed")
    y, sr = librosa.load(audio_path, sr=None)
    return len(y) / sr


def convert_to_16khz_mono(input_path: Path, output_path: Path) -> None:
    """Convert audio to 16kHz mono WAV format."""
    if not AUDIO_LIBS_AVAILABLE:
        raise RuntimeError("librosa/soundfile not installed")
    y, sr = librosa.load(input_path, sr=SAMPLE_RATE, mono=True)
    sf.write(output_path, y, SAMPLE_RATE)


def validate_audio(audio_path: Path) -> tuple[bool, str]:
    """Validate audio file meets requirements."""
    if not audio_path.exists():
        return False, f"File not found: {audio_path}"

    try:
        duration = get_audio_duration(audio_path)
        if duration < MIN_DURATION:
            return False, f"Too short ({duration:.1f}s < {MIN_DURATION}s)"
        if duration > MAX_DURATION:
            return False, f"Too long ({duration:.1f}s > {MAX_DURATION}s)"
        return True, f"OK ({duration:.1f}s)"
    except Exception as e:
        return False, f"Error loading audio: {e}"


# =============================================================================
# TRANSCRIPTION
# =============================================================================

def load_transcriber():
    """Load MERaLiON ASR model for auto-transcription."""
    if not TRANSFORMERS_AVAILABLE:
        raise RuntimeError("transformers not installed")

    print("Loading MERaLiON-2-10B-ASR model...")
    print("(This may take a few minutes on first run)")

    transcriber = pipeline(
        "automatic-speech-recognition",
        model="MERaLiON/MERaLiON-2-10B-ASR",
        device="cuda"  # Change to "cpu" if no GPU
    )
    return transcriber


def auto_transcribe(audio_path: Path, transcriber) -> str:
    """Transcribe audio file using MERaLiON."""
    result = transcriber(str(audio_path))
    return result['text'].strip()


# =============================================================================
# DATA PROCESSING
# =============================================================================

def extract_target_words(transcript: str) -> list[str]:
    """Extract target Singlish words from transcript."""
    transcript_lower = transcript.lower()
    found = []
    for word in TARGET_WORDS:
        if word in transcript_lower:
            found.append(word)
    return found


def parse_speaker_from_filename(filename: str) -> str:
    """
    Extract speaker name from filename.
    Expected format: speakername_001.wav or speakername_description.wav
    """
    stem = Path(filename).stem
    # Take first part before underscore
    parts = stem.split('_')
    return parts[0].lower()


def create_manifest_entry(
    audio_path: Path,
    transcript: str,
    speaker: Optional[str] = None
) -> dict:
    """Create a manifest entry for one audio sample."""
    duration = get_audio_duration(audio_path)

    if speaker is None:
        speaker = parse_speaker_from_filename(audio_path.name)

    return {
        "audio_path": str(audio_path.absolute()),
        "transcript": transcript,
        "duration": round(duration, 2),
        "speaker": speaker,
        "target_words": extract_target_words(transcript)
    }


# =============================================================================
# MAIN WORKFLOW
# =============================================================================

def setup_directories():
    """Create necessary directories if they don't exist."""
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)
    SPLITS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Audio directory: {AUDIO_DIR}")
    print(f"Transcript directory: {TRANSCRIPT_DIR}")
    print(f"Splits directory: {SPLITS_DIR}")


def run_auto_transcribe():
    """Auto-transcribe all audio files without existing transcripts."""
    setup_directories()

    audio_files = list(AUDIO_DIR.glob("*.wav")) + list(AUDIO_DIR.glob("*.mp3"))

    if not audio_files:
        print(f"\nNo audio files found in {AUDIO_DIR}")
        print("Please add your team recordings (.wav or .mp3) to this directory.")
        print("\nExpected filename format: speakername_001.wav")
        print("Examples: nickolas_001.wav, winston_natural_01.wav")
        return

    print(f"\nFound {len(audio_files)} audio files")

    # Find files needing transcription
    needs_transcription = []
    for audio_file in audio_files:
        transcript_file = TRANSCRIPT_DIR / f"{audio_file.stem}.txt"
        if not transcript_file.exists():
            needs_transcription.append(audio_file)

    if not needs_transcription:
        print("All files already have transcripts. Nothing to do.")
        return

    print(f"{len(needs_transcription)} files need transcription")

    # Load model and transcribe
    transcriber = load_transcriber()

    for i, audio_file in enumerate(needs_transcription, 1):
        print(f"\n[{i}/{len(needs_transcription)}] Transcribing: {audio_file.name}")

        # Validate audio
        valid, msg = validate_audio(audio_file)
        if not valid:
            print(f"  SKIP: {msg}")
            continue

        # Transcribe
        try:
            transcript = auto_transcribe(audio_file, transcriber)
            print(f"  Result: {transcript[:80]}{'...' if len(transcript) > 80 else ''}")

            # Save transcript
            transcript_file = TRANSCRIPT_DIR / f"{audio_file.stem}.txt"
            transcript_file.write_text(transcript, encoding='utf-8')
            print(f"  Saved: {transcript_file.name}")

        except Exception as e:
            print(f"  ERROR: {e}")

    print(f"\n{'='*60}")
    print("AUTO-TRANSCRIPTION COMPLETE")
    print(f"{'='*60}")
    print(f"\nTranscripts saved to: {TRANSCRIPT_DIR}")
    print("\nNEXT STEPS:")
    print("1. Review and correct transcripts in the transcripts/ folder")
    print("2. Ensure Singlish words are spelled correctly:")
    print(f"   Target words: {', '.join(TARGET_WORDS[:10])}...")
    print("3. Run: python prepare_team_recordings.py --process")


def run_process(test_ratio: float = 0.15, val_ratio: float = 0.10):
    """Process corrected transcripts and create train/val/test splits."""
    setup_directories()

    # Find all audio files with matching transcripts
    audio_files = list(AUDIO_DIR.glob("*.wav")) + list(AUDIO_DIR.glob("*.mp3"))

    samples = []
    skipped = []

    print(f"\nProcessing {len(audio_files)} audio files...")

    for audio_file in audio_files:
        transcript_file = TRANSCRIPT_DIR / f"{audio_file.stem}.txt"

        # Check transcript exists
        if not transcript_file.exists():
            skipped.append((audio_file.name, "No transcript"))
            continue

        # Validate audio
        valid, msg = validate_audio(audio_file)
        if not valid:
            skipped.append((audio_file.name, msg))
            continue

        # Read transcript
        transcript = transcript_file.read_text(encoding='utf-8').strip()
        if not transcript:
            skipped.append((audio_file.name, "Empty transcript"))
            continue

        # Create entry
        entry = create_manifest_entry(audio_file, transcript)
        samples.append(entry)

    print(f"\nProcessed: {len(samples)} samples")
    print(f"Skipped: {len(skipped)} files")

    if skipped:
        print("\nSkipped files:")
        for name, reason in skipped[:10]:
            print(f"  - {name}: {reason}")
        if len(skipped) > 10:
            print(f"  ... and {len(skipped) - 10} more")

    if not samples:
        print("\nNo valid samples to process!")
        return

    # Analyze target word coverage
    word_counts = {}
    for sample in samples:
        for word in sample['target_words']:
            word_counts[word] = word_counts.get(word, 0) + 1

    print(f"\nTarget word coverage:")
    for word in sorted(word_counts.keys(), key=lambda w: word_counts[w], reverse=True):
        print(f"  {word}: {word_counts[word]} samples")

    missing_words = set(TARGET_WORDS) - set(word_counts.keys())
    if missing_words:
        print(f"\nWARNING: Missing words (no samples): {', '.join(missing_words)}")

    # Create splits
    random.seed(42)  # Reproducible splits
    random.shuffle(samples)

    n_test = max(1, int(len(samples) * test_ratio))
    n_val = max(1, int(len(samples) * val_ratio))
    n_train = len(samples) - n_test - n_val

    test_samples = samples[:n_test]
    val_samples = samples[n_test:n_test + n_val]
    train_samples = samples[n_test + n_val:]

    # Save splits
    for split_name, split_data in [
        ('train', train_samples),
        ('val', val_samples),
        ('test', test_samples)
    ]:
        output_path = SPLITS_DIR / f"{split_name}.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(split_data, f, indent=2, ensure_ascii=False)
        print(f"\nSaved {split_name}.json: {len(split_data)} samples")

    print(f"\n{'='*60}")
    print("PROCESSING COMPLETE")
    print(f"{'='*60}")
    print(f"\nSplits saved to: {SPLITS_DIR}")
    print(f"  - train.json: {len(train_samples)} samples")
    print(f"  - val.json: {len(val_samples)} samples")
    print(f"  - test.json: {len(test_samples)} samples")
    print(f"\nTotal duration: {sum(s['duration'] for s in samples):.1f} seconds")
    print(f"Average duration: {sum(s['duration'] for s in samples) / len(samples):.1f} seconds")


def show_stats():
    """Show current data statistics."""
    setup_directories()

    audio_files = list(AUDIO_DIR.glob("*.wav")) + list(AUDIO_DIR.glob("*.mp3"))
    transcript_files = list(TRANSCRIPT_DIR.glob("*.txt"))

    print(f"\nData Statistics:")
    print(f"  Audio files: {len(audio_files)}")
    print(f"  Transcripts: {len(transcript_files)}")

    # Check splits
    for split in ['train', 'val', 'test']:
        split_path = SPLITS_DIR / f"{split}.json"
        if split_path.exists():
            with open(split_path) as f:
                data = json.load(f)
            print(f"  {split}.json: {len(data)} samples")


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Prepare team recordings for LoRA fine-tuning",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-transcribe new recordings
  python prepare_team_recordings.py --auto-transcribe

  # Process corrected transcripts into splits
  python prepare_team_recordings.py --process

  # Show current data stats
  python prepare_team_recordings.py --stats

Workflow:
  1. Add audio files to ml/data/team_recordings/audio/
     Filename format: speakername_001.wav (e.g., nickolas_001.wav)

  2. Run --auto-transcribe to generate initial transcripts

  3. Manually correct transcripts in ml/data/team_recordings/transcripts/
     Ensure Singlish words are spelled correctly!

  4. Run --process to create train/val/test splits
        """
    )

    parser.add_argument(
        '--auto-transcribe',
        action='store_true',
        help='Auto-transcribe audio files using MERaLiON'
    )
    parser.add_argument(
        '--process',
        action='store_true',
        help='Process transcripts and create train/val/test splits'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show current data statistics'
    )
    parser.add_argument(
        '--test-ratio',
        type=float,
        default=0.15,
        help='Ratio of data for test set (default: 0.15)'
    )
    parser.add_argument(
        '--val-ratio',
        type=float,
        default=0.10,
        help='Ratio of data for validation set (default: 0.10)'
    )

    args = parser.parse_args()

    if args.stats:
        show_stats()
    elif args.auto_transcribe:
        run_auto_transcribe()
    elif args.process:
        run_process(test_ratio=args.test_ratio, val_ratio=args.val_ratio)
    else:
        # Default: show help and setup directories
        setup_directories()
        print("\nTeam Recordings Data Preparation")
        print("="*40)
        print(f"\nTarget words ({len(TARGET_WORDS)}):")
        print(f"  {', '.join(TARGET_WORDS)}")
        print("\nRun with --help for usage instructions")
        parser.print_help()


if __name__ == "__main__":
    main()
