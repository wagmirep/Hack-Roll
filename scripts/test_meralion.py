"""
test_meralion.py - MERaLiON Model Test Script

PURPOSE:
    Quick test to verify MERaLiON ASR model is working correctly.
    Useful for setup verification and debugging.

REFERENCED BY:
    - Development setup checklist
    - CI/CD pipeline (optional smoke test)

REFERENCES:
    - backend/services/transcription.py - Uses same approach

USAGE:
    python scripts/test_meralion.py
    python scripts/test_meralion.py --audio path/to/test.wav
    python scripts/test_meralion.py --text "test expected output"

TESTS:
    1. Model loading - Can load from HuggingFace
    2. Basic transcription - Transcribes sample audio
    3. Singlish detection - Detects target words
    4. Post-processing - Corrections applied correctly

EXPECTED OUTPUT:
    Loading MERaLiON-2-10B-ASR...
    Model loaded successfully!

    Testing transcription...
    Input: test_audio.wav (5.2s)
    Output: "walao why you do this lah"

    Target words detected:
    - walao: 1
    - lah: 1

    Test PASSED!

REQUIREMENTS:
    - GPU with 8GB+ VRAM (or CPU with patience)
    - transformers, torch installed
    - Test audio file (or uses bundled sample)
"""
