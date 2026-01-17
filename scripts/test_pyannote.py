"""
test_pyannote.py - pyannote Speaker Diarization Test Script

PURPOSE:
    Quick test to verify pyannote diarization is working correctly.
    Verifies HuggingFace authentication and model functionality.

REFERENCED BY:
    - Development setup checklist
    - CI/CD pipeline (optional smoke test)

REFERENCES:
    - backend/services/diarization.py - Uses same approach

USAGE:
    python scripts/test_pyannote.py
    python scripts/test_pyannote.py --audio path/to/test.wav
    python scripts/test_pyannote.py --token YOUR_HF_TOKEN

TESTS:
    1. Authentication - HuggingFace token valid
    2. Model loading - Can load diarization pipeline
    3. Basic diarization - Segments audio by speaker
    4. Output format - Returns expected structure

EXPECTED OUTPUT:
    Authenticating with HuggingFace...
    Token valid!

    Loading pyannote/speaker-diarization-3.1...
    Model loaded successfully!

    Testing diarization...
    Input: test_audio.wav (30.5s)

    Speakers detected: 2
    Segments:
    - SPEAKER_00: 0.0s - 5.2s
    - SPEAKER_01: 5.2s - 12.8s
    - SPEAKER_00: 12.8s - 20.1s
    - SPEAKER_01: 20.1s - 30.5s

    Test PASSED!

REQUIREMENTS:
    - HUGGINGFACE_TOKEN environment variable (or --token flag)
    - pyannote.audio installed
    - Test audio file with multiple speakers

COMMON ERRORS:
    - "Authentication failed" - Check HF token, accept model terms
    - "Model not found" - Ensure pyannote.audio installed correctly
"""
