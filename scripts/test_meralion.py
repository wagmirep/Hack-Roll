#!/usr/bin/env python3
"""
test_meralion.py - MERaLiON Model Test Script

Quick test to verify MERaLiON ASR model is working correctly.
Useful for setup verification and debugging.

Usage:
    python scripts/test_meralion.py
    python scripts/test_meralion.py --audio path/to/test.wav
"""

import argparse
import sys
import os
import time
import logging

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_test_audio() -> str:
    """
    Create a simple test audio file for testing.

    Returns:
        Path to the created test audio file
    """
    import numpy as np
    import soundfile as sf
    import tempfile

    # Create a simple 2-second sine wave at 440Hz
    sample_rate = 16000
    duration = 2.0
    t = np.linspace(0, duration, int(sample_rate * duration), dtype=np.float32)
    audio = 0.5 * np.sin(2 * np.pi * 440 * t)

    # Save to temp file
    temp_path = os.path.join(tempfile.gettempdir(), "test_audio_meralion.wav")
    sf.write(temp_path, audio, sample_rate)

    logger.info(f"Created test audio: {temp_path} ({duration}s)")
    return temp_path


def test_model_loading():
    """Test that the model can be loaded."""
    print("\n" + "=" * 50)
    print("TEST 1: Model Loading")
    print("=" * 50)

    try:
        from services.transcription import get_transcriber, is_model_loaded

        print("Loading MERaLiON-2-10B-ASR...")
        start = time.time()

        transcriber = get_transcriber()

        elapsed = time.time() - start
        print(f"Model loaded successfully in {elapsed:.1f}s")

        assert transcriber is not None, "Transcriber is None"
        assert is_model_loaded(), "Model not marked as loaded"

        print("PASSED: Model loading")
        return True

    except Exception as e:
        print(f"FAILED: {e}")
        return False


def test_transcription(audio_path: str):
    """Test transcription on an audio file."""
    print("\n" + "=" * 50)
    print("TEST 2: Audio Transcription")
    print("=" * 50)

    try:
        from services.transcription import transcribe_audio
        import librosa

        # Get audio duration
        duration = librosa.get_duration(path=audio_path)
        print(f"Input: {audio_path}")
        print(f"Duration: {duration:.1f}s")

        print("\nTranscribing...")
        start = time.time()

        text = transcribe_audio(audio_path)

        elapsed = time.time() - start
        print(f"Transcription completed in {elapsed:.1f}s")
        print(f"Output: \"{text}\"")

        if text:
            print("PASSED: Transcription returned text")
        else:
            print("WARNING: Transcription returned empty (may be expected for test audio)")

        return True

    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_segment_transcription():
    """Test transcription from audio bytes."""
    print("\n" + "=" * 50)
    print("TEST 3: Segment Transcription (bytes input)")
    print("=" * 50)

    try:
        from services.transcription import transcribe_segment
        import numpy as np
        import soundfile as sf
        import io

        # Create audio bytes
        sample_rate = 16000
        duration = 1.0
        t = np.linspace(0, duration, int(sample_rate * duration), dtype=np.float32)
        audio = 0.3 * np.sin(2 * np.pi * 440 * t)

        # Convert to bytes
        buffer = io.BytesIO()
        sf.write(buffer, audio, sample_rate, format="WAV")
        audio_bytes = buffer.getvalue()

        print(f"Audio bytes size: {len(audio_bytes)} bytes")

        text = transcribe_segment(audio_bytes)
        print(f"Output: \"{text}\"")

        print("PASSED: Segment transcription works")
        return True

    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_singleton_caching():
    """Test that the model is cached (singleton pattern)."""
    print("\n" + "=" * 50)
    print("TEST 4: Singleton Caching")
    print("=" * 50)

    try:
        from services.transcription import get_transcriber

        # First call (should use cached instance)
        start1 = time.time()
        t1 = get_transcriber()
        elapsed1 = time.time() - start1

        # Second call (should be instant from cache)
        start2 = time.time()
        t2 = get_transcriber()
        elapsed2 = time.time() - start2

        print(f"First get_transcriber(): {elapsed1:.3f}s")
        print(f"Second get_transcriber(): {elapsed2:.3f}s")

        assert t1 is t2, "Transcriber instances are different!"
        assert elapsed2 < 0.1, f"Second call too slow ({elapsed2:.3f}s), caching may not work"

        print("PASSED: Model is cached correctly")
        return True

    except Exception as e:
        print(f"FAILED: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Test MERaLiON ASR model")
    parser.add_argument(
        "--audio",
        type=str,
        help="Path to test audio file (16kHz mono WAV)",
        default=None
    )
    parser.add_argument(
        "--skip-model-test",
        action="store_true",
        help="Skip model loading test (useful if already loaded)"
    )
    args = parser.parse_args()

    print("=" * 50)
    print("MERaLiON ASR Model Test Suite")
    print("=" * 50)

    # Check dependencies
    print("\nChecking dependencies...")
    try:
        import torch
        # PyTorch 2.6+ compatibility fix
        # PyTorch 2.6 changed default weights_only=True in torch.load()
        import torch.torch_version
        torch.serialization.add_safe_globals([torch.torch_version.TorchVersion])

        print(f"  PyTorch: {torch.__version__}")
        print(f"  CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"  CUDA device: {torch.cuda.get_device_name(0)}")
    except ImportError:
        print("  ERROR: PyTorch not installed")
        sys.exit(1)

    try:
        import transformers
        print(f"  Transformers: {transformers.__version__}")
    except ImportError:
        print("  ERROR: Transformers not installed")
        sys.exit(1)

    try:
        import soundfile
        print(f"  SoundFile: installed")
    except ImportError:
        print("  ERROR: SoundFile not installed")
        sys.exit(1)

    results = []

    # Test 1: Model loading
    if not args.skip_model_test:
        results.append(("Model Loading", test_model_loading()))
    else:
        print("\nSkipping model loading test")

    # Prepare test audio
    if args.audio:
        audio_path = args.audio
        if not os.path.exists(audio_path):
            print(f"ERROR: Audio file not found: {audio_path}")
            sys.exit(1)
    else:
        print("\nNo audio file provided, creating test audio...")
        audio_path = create_test_audio()

    # Test 2: Transcription
    results.append(("Transcription", test_transcription(audio_path)))

    # Test 3: Segment transcription
    results.append(("Segment Transcription", test_segment_transcription()))

    # Test 4: Singleton caching
    results.append(("Singleton Caching", test_singleton_caching()))

    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)

    passed = 0
    failed = 0
    for name, result in results:
        status = "PASSED" if result else "FAILED"
        print(f"  {name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1

    print(f"\nTotal: {passed} passed, {failed} failed")

    if failed > 0:
        print("\nSome tests failed. Check output above for details.")
        sys.exit(1)
    else:
        print("\nAll tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
