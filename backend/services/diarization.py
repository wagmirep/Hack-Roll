"""
services/diarization.py - Speaker Diarization Service

PURPOSE:
    Wrapper service for pyannote speaker diarization model.
    Segments audio into speaker-attributed time ranges.

RESPONSIBILITIES:
    - Load pyannote/speaker-diarization-3.1 model
    - Process audio files to identify speakers
    - Return time-stamped speaker segments
    - Handle overlapping speech detection
    - Cache model for reuse across sessions

REFERENCED BY:
    - processor.py - Called during session processing

REFERENCES:
    - config.py - HUGGINGFACE_TOKEN for model authentication
    - storage.py - Audio file access

MODEL:
    pyannote/speaker-diarization-3.1
    - Input: Audio file path (16kHz mono recommended)
    - Output: List of (start_time, end_time, speaker_id) tuples
    - Authentication: Requires HuggingFace token

EXPECTED ACCURACY:
    85-90% in good acoustic conditions
    Degrades with: background noise, overlapping speech, similar voices
"""

import os
import logging
from dataclasses import dataclass
from typing import List, Optional
from threading import Lock

# Initialize logger FIRST - before any code that might use it
logger = logging.getLogger(__name__)

# =============================================================================
# PyTorch 2.6+ COMPATIBILITY FIX
# =============================================================================
# PyTorch 2.6 changed default weights_only=True in torch.load(), which breaks
# pyannote model loading. We need to add pyannote classes to the safe globals
# whitelist BEFORE any model loading occurs.

import torch
import torch.serialization

# Step 1: Import pyannote modules and add their classes to safe globals
# This MUST happen before any model loading
try:
    from torch.serialization import add_safe_globals
    
    # Add TorchVersion to safe globals (required for some model files)
    try:
        add_safe_globals([torch.torch_version.TorchVersion])
    except (AttributeError, TypeError):
        pass
    
    # Import pyannote classes and add them to safe globals
    try:
        import pyannote.audio.core.task
        import pyannote.audio.core.model
        
        # Collect all classes from pyannote.audio.core.task
        pyannote_classes = []
        for attr_name in dir(pyannote.audio.core.task):
            attr = getattr(pyannote.audio.core.task, attr_name, None)
            if isinstance(attr, type):
                pyannote_classes.append(attr)
        
        # Specifically ensure Specifications is included
        if hasattr(pyannote.audio.core.task, 'Specifications'):
            if pyannote.audio.core.task.Specifications not in pyannote_classes:
                pyannote_classes.append(pyannote.audio.core.task.Specifications)
        
        # Add Model class if available
        if hasattr(pyannote.audio.core.model, 'Model'):
            pyannote_classes.append(pyannote.audio.core.model.Model)
        
        # Add all collected classes to safe globals
        if pyannote_classes:
            add_safe_globals(pyannote_classes)
            logger.info(f"Added {len(pyannote_classes)} pyannote classes to torch safe globals")
            
    except ImportError as e:
        logger.warning(f"Could not import pyannote for safe globals setup: {e}")
        
except ImportError:
    logger.info("torch.serialization.add_safe_globals not available (older PyTorch version)")

# Step 2: AGGRESSIVELY patch torch.load to ALWAYS use weights_only=False
# This is necessary because pyannote/lightning may explicitly pass weights_only=True
_original_torch_load = torch.load

def _patched_torch_load(*args, **kwargs):
    """Patched torch.load that FORCES weights_only=False for pyannote compatibility."""
    # ALWAYS override weights_only to False, regardless of what was passed
    kwargs['weights_only'] = False
    return _original_torch_load(*args, **kwargs)

torch.load = _patched_torch_load

# Also patch torch.serialization.load which is used internally
_original_serialization_load = torch.serialization.load

def _patched_serialization_load(*args, **kwargs):
    """Patched serialization.load that FORCES weights_only=False."""
    kwargs['weights_only'] = False
    return _original_serialization_load(*args, **kwargs)

torch.serialization.load = _patched_serialization_load

# Step 3: Patch lightning.fabric if present (pyannote uses pytorch-lightning)
try:
    import lightning.fabric.utilities.cloud_io as cloud_io
    if hasattr(cloud_io, '_load'):
        _original_lightning_load = cloud_io._load
        
        def _patched_lightning_load(f, map_location=None, weights_only=None):
            # Always use weights_only=False for pyannote models
            return _original_torch_load(f, map_location=map_location, weights_only=False)
        
        cloud_io._load = _patched_lightning_load
        logger.info("Patched lightning cloud_io._load for PyTorch 2.6 compatibility")
except (ImportError, AttributeError):
    pass  # Lightning not installed or different version

# Step 4: Patch huggingface_hub's torch loading if present
try:
    import huggingface_hub.serialization._torch as hf_torch
    if hasattr(hf_torch, '_load_state_dict_from_file'):
        _original_hf_load = hf_torch._load_state_dict_from_file
        
        def _patched_hf_load(filename, **kwargs):
            kwargs['weights_only'] = False
            return _original_hf_load(filename, **kwargs)
        
        hf_torch._load_state_dict_from_file = _patched_hf_load
        logger.info("Patched huggingface_hub torch loading for PyTorch 2.6 compatibility")
except (ImportError, AttributeError):
    pass
# =============================================================================

# Import other dependencies
import soundfile as sf
import numpy as np

# Model singleton - cached after first load
_pipeline = None
_pipeline_lock = Lock()

# Model configuration
MODEL_NAME = "pyannote/speaker-diarization-3.1"


@dataclass
class SpeakerSegment:
    """Represents a single speaker segment in the audio."""
    speaker_id: str  # e.g., "SPEAKER_00", "SPEAKER_01"
    start_time: float  # Start time in seconds
    end_time: float  # End time in seconds

    @property
    def duration(self) -> float:
        """Duration of the segment in seconds."""
        return self.end_time - self.start_time

    def to_dict(self) -> dict:
        """Convert to dictionary format."""
        return {
            "speaker": self.speaker_id,
            "start": self.start_time,
            "end": self.end_time,
            "duration": self.duration
        }


def get_diarization_pipeline():
    """
    Get the pyannote diarization pipeline, loading it if necessary.

    Uses singleton pattern to avoid reloading the large model.
    Thread-safe for concurrent access.

    Returns:
        Pipeline: The pyannote diarization pipeline

    Raises:
        ValueError: If HUGGINGFACE_TOKEN is not set
        RuntimeError: If model fails to load
    """
    global _pipeline

    if _pipeline is not None:
        return _pipeline

    with _pipeline_lock:
        # Double-check after acquiring lock
        if _pipeline is not None:
            return _pipeline

        # Get HuggingFace token from environment
        hf_token = os.environ.get("HUGGINGFACE_TOKEN")
        if not hf_token:
            raise ValueError(
                "HUGGINGFACE_TOKEN environment variable is required. "
                "Get your token from https://huggingface.co/settings/tokens "
                "and accept the pyannote model terms."
            )

        logger.info(f"Loading diarization model: {MODEL_NAME}")

        try:
            from pyannote.audio import Pipeline
            
            # Ensure pyannote classes are in safe globals (may have been added at module load)
            # Re-add here in case module was imported before torch was configured
            try:
                from torch.serialization import add_safe_globals
                import pyannote.audio.core.task
                
                pyannote_classes = []
                for attr_name in dir(pyannote.audio.core.task):
                    attr = getattr(pyannote.audio.core.task, attr_name, None)
                    if isinstance(attr, type):
                        pyannote_classes.append(attr)
                
                if pyannote_classes:
                    add_safe_globals(pyannote_classes)
                    logger.info(f"Re-added {len(pyannote_classes)} pyannote classes to safe globals before loading")
            except ImportError:
                pass  # Older PyTorch without add_safe_globals
            
            # Load the pipeline - our patched torch.load will handle weights_only
            logger.info("Loading pipeline from pretrained model...")
            pipeline = Pipeline.from_pretrained(
                MODEL_NAME,
                token=hf_token
            )
            logger.info("Pipeline loaded successfully")

            # Move to GPU if available
            if torch.cuda.is_available():
                pipeline = pipeline.to(torch.device("cuda"))
                logger.info("Diarization pipeline moved to GPU")
            else:
                logger.info("Running diarization on CPU (GPU not available)")

            _pipeline = pipeline
            logger.info("Diarization pipeline loaded successfully")

            return _pipeline

        except Exception as e:
            logger.error(f"Failed to load diarization pipeline: {e}")
            raise RuntimeError(f"Failed to load diarization model: {e}")


def diarize_audio(audio_path: str, min_segment_duration: float = 0.5) -> List[SpeakerSegment]:
    """
    Run speaker diarization on an audio file.

    Args:
        audio_path: Path to the audio file (16kHz mono WAV recommended)
        min_segment_duration: Minimum segment duration in seconds (default 0.5s)

    Returns:
        List of SpeakerSegment objects sorted by start time

    Raises:
        FileNotFoundError: If audio file doesn't exist
        RuntimeError: If diarization fails
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    logger.info(f"Running diarization on: {audio_path}")

    try:
        pipeline = get_diarization_pipeline()

        # Preload audio with soundfile to bypass torchcodec requirement on Windows
        # pyannote 4.x accepts {'waveform': tensor, 'sample_rate': int} format
        audio_data, sample_rate = sf.read(audio_path)

        # Convert to torch tensor: (channels, samples) format
        if audio_data.ndim == 1:
            # Mono audio - add channel dimension
            waveform = torch.from_numpy(audio_data).float().unsqueeze(0)
        else:
            # Multi-channel - transpose to (channels, samples)
            waveform = torch.from_numpy(audio_data.T).float()

        # Create audio input dict for pyannote
        audio_input = {"waveform": waveform, "sample_rate": sample_rate}

        logger.info(f"Audio loaded: {waveform.shape}, {sample_rate}Hz")

        # Run diarization with preloaded audio
        diarization_result = pipeline(audio_input)

        # Convert to SpeakerSegment objects
        # pyannote 4.x returns DiarizeOutput, access speaker_diarization Annotation
        annotation = getattr(diarization_result, 'speaker_diarization', diarization_result)

        segments = []
        for turn, _, speaker in annotation.itertracks(yield_label=True):
            duration = turn.end - turn.start

            # Skip very short segments (likely noise)
            if duration < min_segment_duration:
                logger.debug(f"Skipping short segment: {speaker} ({duration:.2f}s)")
                continue

            segment = SpeakerSegment(
                speaker_id=speaker,
                start_time=round(turn.start, 3),
                end_time=round(turn.end, 3)
            )
            segments.append(segment)

        # Sort by start time
        segments.sort(key=lambda s: s.start_time)

        # Log summary
        unique_speakers = set(s.speaker_id for s in segments)
        logger.info(
            f"Diarization complete: {len(segments)} segments, "
            f"{len(unique_speakers)} speakers detected"
        )

        return segments

    except Exception as e:
        logger.error(f"Diarization failed: {e}")
        raise RuntimeError(f"Diarization failed: {e}")


def extract_speaker_segment(
    audio_path: str,
    start_time: float,
    end_time: float,
    output_path: Optional[str] = None
) -> bytes:
    """
    Extract a specific time range from an audio file.

    Args:
        audio_path: Path to the source audio file
        start_time: Start time in seconds
        end_time: End time in seconds
        output_path: Optional path to save the extracted segment

    Returns:
        Extracted audio as WAV bytes

    Raises:
        FileNotFoundError: If audio file doesn't exist
        ValueError: If time range is invalid
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    if start_time < 0:
        raise ValueError("start_time must be non-negative")

    if end_time <= start_time:
        raise ValueError("end_time must be greater than start_time")

    # Read audio file
    audio_data, sample_rate = sf.read(audio_path)

    # Convert time to sample indices
    start_sample = int(start_time * sample_rate)
    end_sample = int(end_time * sample_rate)

    # Clamp to valid range
    end_sample = min(end_sample, len(audio_data))

    if start_sample >= len(audio_data):
        raise ValueError(f"start_time {start_time}s exceeds audio duration")

    # Extract segment
    segment_data = audio_data[start_sample:end_sample]

    # Write to bytes buffer or file
    import io
    buffer = io.BytesIO()
    sf.write(buffer, segment_data, sample_rate, format='WAV')
    audio_bytes = buffer.getvalue()

    # Optionally save to file
    if output_path:
        sf.write(output_path, segment_data, sample_rate)
        logger.debug(f"Saved segment to: {output_path}")

    return audio_bytes


def filter_overlapping_segments(
    segments: List[SpeakerSegment],
    overlap_threshold: float = 0.3
) -> List[SpeakerSegment]:
    """
    Filter out segments that overlap significantly with other speakers.

    Overlapping speech is often harder to transcribe accurately,
    so we filter these segments out for better transcription quality.

    Args:
        segments: List of speaker segments
        overlap_threshold: Maximum overlap ratio allowed (0.0 to 1.0)

    Returns:
        Filtered list of non-overlapping segments
    """
    if not segments:
        return []

    # Sort by start time
    sorted_segments = sorted(segments, key=lambda s: s.start_time)
    filtered = []

    for i, segment in enumerate(sorted_segments):
        is_overlapping = False

        # Check overlap with adjacent segments
        for j, other in enumerate(sorted_segments):
            if i == j:
                continue

            # Calculate overlap
            overlap_start = max(segment.start_time, other.start_time)
            overlap_end = min(segment.end_time, other.end_time)

            if overlap_start < overlap_end:
                overlap_duration = overlap_end - overlap_start
                overlap_ratio = overlap_duration / segment.duration

                if overlap_ratio > overlap_threshold:
                    is_overlapping = True
                    logger.debug(
                        f"Segment {segment.speaker_id} "
                        f"({segment.start_time:.1f}-{segment.end_time:.1f}s) "
                        f"overlaps {overlap_ratio:.0%} with {other.speaker_id}"
                    )
                    break

        if not is_overlapping:
            filtered.append(segment)

    removed_count = len(segments) - len(filtered)
    if removed_count > 0:
        logger.info(f"Filtered out {removed_count} overlapping segments")

    return filtered


def get_speaker_sample(
    audio_path: str,
    segments: List[SpeakerSegment],
    speaker_id: str,
    sample_duration: float = 5.0
) -> Optional[bytes]:
    """
    Get a representative audio sample for a specific speaker.

    Finds the longest clean segment for the speaker and extracts
    a sample clip (up to sample_duration seconds).

    Args:
        audio_path: Path to the audio file
        segments: List of all speaker segments
        speaker_id: The speaker ID to get sample for
        sample_duration: Maximum sample duration in seconds

    Returns:
        Audio bytes for the sample, or None if speaker not found
    """
    # Get segments for this speaker
    speaker_segments = [s for s in segments if s.speaker_id == speaker_id]

    if not speaker_segments:
        logger.warning(f"No segments found for speaker: {speaker_id}")
        return None

    # Find the longest segment (most representative)
    longest_segment = max(speaker_segments, key=lambda s: s.duration)

    # Calculate sample range
    sample_end = min(
        longest_segment.start_time + sample_duration,
        longest_segment.end_time
    )

    return extract_speaker_segment(
        audio_path,
        longest_segment.start_time,
        sample_end
    )


def get_all_speaker_samples(
    audio_path: str,
    segments: List[SpeakerSegment],
    sample_duration: float = 5.0
) -> dict:
    """
    Get audio samples for all detected speakers.

    Args:
        audio_path: Path to the audio file
        segments: List of all speaker segments
        sample_duration: Maximum sample duration per speaker

    Returns:
        Dict mapping speaker_id to audio bytes
    """
    unique_speakers = set(s.speaker_id for s in segments)
    samples = {}

    for speaker_id in unique_speakers:
        sample = get_speaker_sample(
            audio_path, segments, speaker_id, sample_duration
        )
        if sample:
            samples[speaker_id] = sample

    return samples
