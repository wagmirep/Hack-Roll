"""
services/transcription.py - MERaLiON Transcription Service

Wrapper service for MERaLiON-2-10B-ASR speech-to-text model.
Transcribes Singlish audio segments to text.

Agent 2 scope: Model loading and transcription only.
Post-processing (corrections, word counting) handled by Agent 3.
"""

import os
import re
import logging
from typing import Dict, Optional
from threading import Lock

logger = logging.getLogger(__name__)

# =============================================================================
# MODEL SINGLETON (Agent 2)
# =============================================================================

_transcriber = None
_transcriber_lock = Lock()

# Model configuration
MODEL_NAME = "MERaLiON/MERaLiON-2-10B-ASR"
SAMPLE_RATE = 16000  # Expected input sample rate


def get_transcriber():
    """
    Get or create the MERaLiON transcriber pipeline instance.

    Uses singleton pattern to avoid reloading the 10B parameter model.
    Thread-safe initialization.

    Returns:
        transformers.Pipeline: The ASR pipeline instance

    Raises:
        RuntimeError: If model fails to load
    """
    global _transcriber

    if _transcriber is not None:
        return _transcriber

    with _transcriber_lock:
        # Double-check after acquiring lock
        if _transcriber is not None:
            return _transcriber

        logger.info(f"Loading MERaLiON ASR model: {MODEL_NAME}")

        try:
            from transformers import pipeline
            import torch

            # Check GPU memory to decide loading strategy
            use_device_map = False
            if torch.cuda.is_available():
                total_mem_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
                logger.info(f"GPU memory: {total_mem_gb:.1f}GB")
                # MERaLiON-2-10B needs ~20GB in fp16, use device_map for smaller GPUs
                if total_mem_gb < 20:
                    use_device_map = True
                    logger.info("Using device_map='auto' for CPU offloading (GPU < 20GB)")
                else:
                    logger.info("Using full GPU inference")
            else:
                logger.warning("CUDA not available, using CPU (will be slow)")

            if use_device_map:
                # Use device_map for automatic CPU/GPU split
                _transcriber = pipeline(
                    "automatic-speech-recognition",
                    model=MODEL_NAME,
                    device_map="auto",
                    torch_dtype=torch.float16,
                    trust_remote_code=True,
                    model_kwargs={"attn_implementation": "eager"},
                )
            else:
                # Standard loading (full GPU or CPU)
                device = 0 if torch.cuda.is_available() else -1
                _transcriber = pipeline(
                    "automatic-speech-recognition",
                    model=MODEL_NAME,
                    device=device,
                    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                    trust_remote_code=True,
                    model_kwargs={"attn_implementation": "eager"},
                )

            logger.info("MERaLiON model loaded successfully")
            return _transcriber

        except Exception as e:
            logger.error(f"Failed to load MERaLiON model: {e}")
            raise RuntimeError(f"Failed to load transcription model: {e}") from e


def transcribe_audio(audio_path: str) -> str:
    """
    Transcribe audio file to text using MERaLiON ASR.

    Args:
        audio_path: Path to audio file (16kHz mono WAV recommended)

    Returns:
        Raw transcription text

    Raises:
        FileNotFoundError: If audio file doesn't exist
        RuntimeError: If transcription fails
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    logger.info(f"Transcribing audio: {audio_path}")

    try:
        transcriber = get_transcriber()

        # Run transcription
        result = transcriber(audio_path)

        text = result.get("text", "")
        logger.info(f"Transcription complete: {len(text)} characters")

        return text.strip()

    except Exception as e:
        logger.error(f"Transcription failed for {audio_path}: {e}")
        raise RuntimeError(f"Transcription failed: {e}") from e


def transcribe_segment(audio_bytes: bytes, sample_rate: int = SAMPLE_RATE) -> str:
    """
    Transcribe audio bytes directly without saving to file.

    Args:
        audio_bytes: Raw audio data
        sample_rate: Sample rate of the audio (default: 16000)

    Returns:
        Raw transcription text

    Raises:
        RuntimeError: If transcription fails
    """
    import io
    import numpy as np

    try:
        import soundfile as sf

        # Read audio bytes
        audio_data, sr = sf.read(io.BytesIO(audio_bytes))

        # Ensure mono
        if len(audio_data.shape) > 1:
            audio_data = audio_data.mean(axis=1)

        # Resample if needed
        if sr != sample_rate:
            import librosa
            audio_data = librosa.resample(audio_data, orig_sr=sr, target_sr=sample_rate)

        transcriber = get_transcriber()

        # Create input dict for pipeline
        inputs = {
            "raw": audio_data.astype(np.float32),
            "sampling_rate": sample_rate
        }

        result = transcriber(inputs)
        text = result.get("text", "")

        return text.strip()

    except Exception as e:
        logger.error(f"Segment transcription failed: {e}")
        raise RuntimeError(f"Segment transcription failed: {e}") from e


def is_model_loaded() -> bool:
    """Check if the transcription model is currently loaded."""
    return _transcriber is not None


def unload_model() -> None:
    """
    Unload the transcription model to free memory.

    Useful for testing or when switching between models.
    """
    global _transcriber

    with _transcriber_lock:
        if _transcriber is not None:
            logger.info("Unloading MERaLiON model")
            del _transcriber
            _transcriber = None

            # Force garbage collection
            import gc
            import torch
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()


# =============================================================================
# SINGLISH POST-PROCESSING CORRECTIONS (Agent 3)
# =============================================================================
#
# These dictionaries correct common ASR (Automatic Speech Recognition)
# misrecognitions of Singlish words. MERaLiON may transcribe Singlish slang
# as similar-sounding English words/phrases.
#
# HOW TO EXTEND:
# --------------
# When testing reveals new mistranscriptions, add them to the appropriate dict:
#
# 1. CORRECTIONS - For multi-word phrases OR unique single words
#    Example: 'cheap buy': 'cheebai'  (ASR heard "cheap buy" for "cheebai")
#    - Matched via simple substring replacement (case-insensitive)
#    - Longer phrases are matched first to avoid partial matches
#
# 2. WORD_CORRECTIONS - For single words that might appear inside other words
#    Example: 'la': 'lah'  (but don't change "salah" or "malaysia")
#    - Matched with word boundary checking (\b regex)
#    - Use this when the misheard word is a common English word/substring
#
# After adding corrections, also add the target word to TARGET_WORDS list
# if you want to count its occurrences.
#
# =============================================================================

# Corrections dictionary for common ASR misrecognitions
# Maps misrecognized phrases -> correct Singlish word
CORRECTIONS: Dict[str, str] = {
    # Walao variations (multi-word first)
    'while up': 'walao',
    'wah lao': 'walao',
    'wa lao': 'walao',
    'wah low': 'walao',
    'wa low': 'walao',
    'while ah': 'walao',
    'wah lau': 'walao',
    'wa lau': 'walao',
    # Vulgar - cheebai variations
    'cheap buy': 'cheebai',
    'chee bye': 'cheebai',
    'chi bye': 'cheebai',
    'chee bai': 'cheebai',
    'chi bai': 'cheebai',
    # Vulgar - lanjiao variations
    'lunch hour': 'lanjiao',
    'lan jiao': 'lanjiao',
    'lan chow': 'lanjiao',
    'lan chiao': 'lanjiao',
    # Paiseh variations
    'pie say': 'paiseh',
    'pai seh': 'paiseh',
    'pie seh': 'paiseh',
    'pai say': 'paiseh',
    # Shiok variations
    'shook': 'shiok',
    'she ok': 'shiok',
    # Sia variations
    'see ya': 'sia',
    'see ah': 'sia',
    # Sian variations
    'see an': 'sian',
    'si an': 'sian',
    # Particle variations (single word - more careful matching needed)
    'lah ': 'lah ',  # Keep space to preserve word boundary
    'lor ': 'lor ',
    'loh': 'lor',
    'leh': 'lah',
}

# Single-word corrections with word boundary checking
# Use for words that could appear as substrings in other words
# e.g., 'la' -> 'lah' but don't affect 'salah' or 'malaysia'
WORD_CORRECTIONS: Dict[str, str] = {
    'la': 'lah',
    'low': 'lor',
    'loh': 'lor',
    'leh': 'lah',
    'seh': 'sia',
}

# Target Singlish words to count in transcriptions
# Add new words here when you want to track their usage
# Words are matched case-insensitively with word boundary detection
TARGET_WORDS = [
    # Vulgar/Expletives
    'walao',
    'cheebai',
    'lanjiao',
    # Particles
    'lah',
    'lor',
    'sia',
    'meh',
    'leh',
    'hor',
    'ah',
    # Colloquial expressions
    'can',
    'paiseh',
    'shiok',
    'sian',
    'alamak',
    'aiyo',
    'bodoh',
    'kiasu',
    'kiasi',
    'bojio',
]


def apply_corrections(text: str) -> str:
    """
    Apply post-processing corrections to transcribed text.

    Handles common ASR misrecognitions of Singlish words.
    Case-insensitive matching with case-preserving replacement.

    Args:
        text: Raw transcription text from ASR model

    Returns:
        Corrected text with Singlish words properly spelled

    Examples:
        >>> apply_corrections("while up why you do that")
        'walao why you do that'
        >>> apply_corrections("wa lao eh this is shook")
        'walao eh this is shiok'
    """
    if not text:
        return text

    result = text

    # Apply multi-word corrections first (case-insensitive)
    # Sort by length descending to match longer phrases first
    sorted_corrections = sorted(CORRECTIONS.items(), key=lambda x: len(x[0]), reverse=True)

    for wrong, correct in sorted_corrections:
        # Case-insensitive replacement
        pattern = re.compile(re.escape(wrong), re.IGNORECASE)
        result = pattern.sub(correct, result)

    # Apply single-word corrections with word boundary checking
    for wrong, correct in WORD_CORRECTIONS.items():
        # Match whole words only (word boundaries)
        pattern = re.compile(r'\b' + re.escape(wrong) + r'\b', re.IGNORECASE)
        result = pattern.sub(correct, result)

    return result


def count_target_words(text: str) -> Dict[str, int]:
    """
    Count occurrences of target Singlish words in text.

    Case-insensitive matching with word boundary detection.
    Only counts whole words, not substrings (e.g., "salah" won't count as "lah").

    Args:
        text: Text to analyze (should be corrected first via apply_corrections)

    Returns:
        Dictionary mapping word -> count for words that appear at least once

    Examples:
        >>> count_target_words("walao sia this is shiok")
        {'walao': 1, 'sia': 1, 'shiok': 1}
        >>> count_target_words("lah lah lah you know lah")
        {'lah': 4}
        >>> count_target_words("hello how are you")
        {}
    """
    if not text:
        return {}

    # Normalize text for counting
    normalized = text.lower()

    counts: Dict[str, int] = {}

    for word in TARGET_WORDS:
        # Match whole words only with word boundaries
        # Handle punctuation by using a pattern that allows punctuation at boundaries
        pattern = re.compile(r'(?<![a-zA-Z])' + re.escape(word) + r'(?![a-zA-Z])', re.IGNORECASE)
        matches = pattern.findall(normalized)

        if matches:
            counts[word] = len(matches)

    return counts


def process_transcription(text: str) -> tuple[str, Dict[str, int]]:
    """
    Convenience function that applies corrections and counts words in one step.

    Args:
        text: Raw transcription text from ASR model

    Returns:
        Tuple of (corrected_text, word_counts)

    Example:
        >>> process_transcription("while up that's shook la")
        ('walao that's shiok lah', {'walao': 1, 'shiok': 1, 'lah': 1})
    """
    corrected = apply_corrections(text)
    counts = count_target_words(corrected)
    return corrected, counts
