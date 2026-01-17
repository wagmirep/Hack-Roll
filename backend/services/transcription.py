"""
services/transcription.py - MERaLiON Transcription Service

Wrapper service for MERaLiON-2-10B-ASR speech-to-text model.
Transcribes Singlish audio segments to text.

Agent 2 scope: Model loading and transcription only.
Post-processing (corrections, word counting) handled by Agent 3.
"""

import os
import logging
from typing import Optional
from threading import Lock

logger = logging.getLogger(__name__)

# Model singleton
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

            # Determine device
            if torch.cuda.is_available():
                device = 0  # First GPU
                logger.info("Using CUDA GPU for inference")
            else:
                device = -1  # CPU
                logger.warning("CUDA not available, using CPU (will be slow)")

            _transcriber = pipeline(
                "automatic-speech-recognition",
                model=MODEL_NAME,
                device=device,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
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
