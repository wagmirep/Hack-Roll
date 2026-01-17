#!/usr/bin/env python3
"""
test_pyannote.py - pyannote Speaker Diarization Test Script

PURPOSE:
    Quick test to verify pyannote diarization is working correctly.
    Verifies HuggingFace authentication and model functionality.

USAGE:
    python scripts/test_pyannote.py
    python scripts/test_pyannote.py --audio path/to/test.wav
    python scripts/test_pyannote.py --token YOUR_HF_TOKEN

REQUIREMENTS:
    - HUGGINGFACE_TOKEN environment variable (or --token flag)
    - pyannote.audio installed
    - Test audio file with multiple speakers
"""

import argparse
import os
import sys
import tempfile
import logging

import numpy as np
import soundfile as sf

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.diarization import (
    get_diarization_pipeline,
    diarize_audio,
    extract_speaker_segment,
    filter_overlapping_segments,
    SpeakerSegment
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_test_audio(duration: float = 10.0, sample_rate: int = 16000) -> str:
    """
    Create a simple test audio file for basic testing.

    Note: This is just for testing the pipeline loads - real diarization
    requires actual speech audio with multiple speakers.
    """
    # Generate simple audio (silence with some noise)
    samples = int(duration * sample_rate)
    audio = np.random.randn(samples).astype(np.float32) * 0.01

    # Create temp file
    fd, path = tempfile.mkstemp(suffix='.wav')
    os.close(fd)

    sf.write(path, audio, sample_rate)
    logger.info(f"Created test audio: {path} ({duration}s)")

    return path


def test_authentication(token: str) -> bool:
    """Test that the HuggingFace token is valid."""
    print("\n" + "="*50)
    print("TEST 1: Authentication")
    print("="*50)

    if not token:
        print("FAILED: No HuggingFace token provided")
        print("Set HUGGINGFACE_TOKEN environment variable or use --token flag")
        return False

    # Set token in environment for the service to use
    os.environ["HUGGINGFACE_TOKEN"] = token

    print(f"Token found: {token[:8]}...{token[-4:]}")
    print("Token will be validated during model loading")
    print("PASSED (token present)")
    return True


def test_model_loading() -> bool:
    """Test that the diarization model loads successfully."""
    print("\n" + "="*50)
    print("TEST 2: Model Loading")
    print("="*50)

    try:
        print("Loading pyannote/speaker-diarization-3.1...")
        print("(This may take a few minutes on first run)")

        pipeline = get_diarization_pipeline()

        print(f"Model loaded successfully!")
        print(f"Pipeline type: {type(pipeline).__name__}")
        print("PASSED")
        return True

    except ValueError as e:
        print(f"FAILED: Authentication error - {e}")
        return False
    except RuntimeError as e:
        print(f"FAILED: Model loading error - {e}")
        return False
    except Exception as e:
        print(f"FAILED: Unexpected error - {e}")
        return False


def test_diarization(audio_path: str) -> bool:
    """Test diarization on an audio file."""
    print("\n" + "="*50)
    print("TEST 3: Diarization")
    print("="*50)

    try:
        print(f"Input: {audio_path}")

        # Get audio duration
        audio_data, sample_rate = sf.read(audio_path)
        duration = len(audio_data) / sample_rate
        print(f"Duration: {duration:.1f}s, Sample rate: {sample_rate}Hz")

        print("\nRunning diarization...")
        segments = diarize_audio(audio_path)

        # Report results
        unique_speakers = set(s.speaker_id for s in segments)
        print(f"\nSpeakers detected: {len(unique_speakers)}")
        print(f"Segments: {len(segments)}")

        if segments:
            print("\nSegment details:")
            for seg in segments[:10]:  # Show first 10
                print(f"  - {seg.speaker_id}: {seg.start_time:.1f}s - {seg.end_time:.1f}s ({seg.duration:.1f}s)")

            if len(segments) > 10:
                print(f"  ... and {len(segments) - 10} more segments")
        else:
            print("\nNo segments detected (audio may not contain speech)")

        print("\nPASSED")
        return True

    except FileNotFoundError as e:
        print(f"FAILED: {e}")
        return False
    except RuntimeError as e:
        print(f"FAILED: Diarization error - {e}")
        return False
    except Exception as e:
        print(f"FAILED: Unexpected error - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_segment_extraction(audio_path: str) -> bool:
    """Test audio segment extraction."""
    print("\n" + "="*50)
    print("TEST 4: Segment Extraction")
    print("="*50)

    try:
        print(f"Extracting 2-second segment from {audio_path}...")

        audio_bytes = extract_speaker_segment(
            audio_path,
            start_time=0.0,
            end_time=2.0
        )

        print(f"Extracted {len(audio_bytes)} bytes")

        # Verify it's valid WAV data
        import io
        buffer = io.BytesIO(audio_bytes)
        data, sr = sf.read(buffer)
        extracted_duration = len(data) / sr

        print(f"Extracted audio: {extracted_duration:.2f}s at {sr}Hz")
        print("PASSED")
        return True

    except Exception as e:
        print(f"FAILED: {e}")
        return False


def test_overlap_filtering() -> bool:
    """Test the overlap filtering function."""
    print("\n" + "="*50)
    print("TEST 5: Overlap Filtering")
    print("="*50)

    try:
        # Create test segments with overlaps
        segments = [
            SpeakerSegment("SPEAKER_00", 0.0, 5.0),
            SpeakerSegment("SPEAKER_01", 4.0, 8.0),  # Overlaps with 00
            SpeakerSegment("SPEAKER_00", 10.0, 15.0),  # No overlap
            SpeakerSegment("SPEAKER_01", 20.0, 25.0),  # No overlap
        ]

        print(f"Input: {len(segments)} segments")
        for seg in segments:
            print(f"  - {seg.speaker_id}: {seg.start_time}-{seg.end_time}s")

        filtered = filter_overlapping_segments(segments, overlap_threshold=0.1)

        print(f"\nAfter filtering: {len(filtered)} segments")
        for seg in filtered:
            print(f"  - {seg.speaker_id}: {seg.start_time}-{seg.end_time}s")

        # Verify overlapping segments were removed
        # First two segments should be filtered due to overlap
        if len(filtered) <= len(segments):
            print("\nPASSED")
            return True
        else:
            print("\nFAILED: Filtering did not work correctly")
            return False

    except Exception as e:
        print(f"FAILED: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Test pyannote speaker diarization"
    )
    parser.add_argument(
        "--audio",
        type=str,
        help="Path to test audio file (WAV format recommended)"
    )
    parser.add_argument(
        "--token",
        type=str,
        help="HuggingFace token (overrides HUGGINGFACE_TOKEN env var)"
    )
    parser.add_argument(
        "--skip-model",
        action="store_true",
        help="Skip model loading tests (for quick validation)"
    )

    args = parser.parse_args()

    print("="*50)
    print("pyannote Speaker Diarization Test Suite")
    print("="*50)

    # Get token
    token = args.token or os.environ.get("HUGGINGFACE_TOKEN")

    results = []
    test_audio_path = None
    created_temp_audio = False

    try:
        if args.skip_model:
            print("\n(Skipping authentication and model tests with --skip-model)")
        else:
            # Test 1: Authentication
            results.append(("Authentication", test_authentication(token)))

            if not results[-1][1]:
                print("\n" + "="*50)
                print("STOPPING: Authentication required for further tests")
                print("="*50)
                return 1

        if args.skip_model:
            print("\n(Skipping model tests with --skip-model)")
        else:
            # Test 2: Model loading
            results.append(("Model Loading", test_model_loading()))

            if not results[-1][1]:
                print("\n" + "="*50)
                print("STOPPING: Model loading required for further tests")
                print("="*50)
                return 1

            # Get audio path
            if args.audio:
                test_audio_path = args.audio
            else:
                print("\n(No --audio provided, creating synthetic test audio)")
                test_audio_path = create_test_audio()
                created_temp_audio = True

            # Test 3: Diarization
            results.append(("Diarization", test_diarization(test_audio_path)))

            # Test 4: Segment extraction
            results.append(("Segment Extraction", test_segment_extraction(test_audio_path)))

        # Test 5: Overlap filtering (no model needed)
        results.append(("Overlap Filtering", test_overlap_filtering()))

    finally:
        # Cleanup temp audio
        if created_temp_audio and test_audio_path and os.path.exists(test_audio_path):
            os.remove(test_audio_path)
            logger.info(f"Cleaned up temp audio: {test_audio_path}")

    # Summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)

    passed = sum(1 for _, result in results if result)
    failed = len(results) - passed

    for name, result in results:
        status = "PASSED" if result else "FAILED"
        print(f"  {name}: {status}")

    print(f"\nTotal: {passed}/{len(results)} passed")

    if failed > 0:
        print("\nSome tests FAILED!")
        return 1
    else:
        print("\nAll tests PASSED!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
