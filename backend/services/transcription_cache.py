"""
services/transcription_cache.py - Background Chunk Transcription Cache

Transcribes audio chunks as they arrive and caches results.
Used by processor.py to speed up post-recording processing.

PURPOSE:
    - Fire-and-forget background transcription on chunk upload
    - Cache transcription results for fast retrieval after recording ends
    - Provide cache lookup utilities for the processing pipeline

REFERENCED BY:
    - routers/sessions.py - Triggers background transcription on chunk upload
    - processor.py - Uses cached transcriptions to speed up processing

REFERENCES:
    - models.py - ChunkTranscription, AudioChunk
    - database.py - SessionLocal
    - services/transcription.py - transcribe_audio, apply_corrections, count_target_words
"""

import uuid
import logging
import tempfile
import os
from datetime import datetime, timezone
from typing import Optional, Dict, List

from sqlalchemy.orm import Session as DBSession

from models import ChunkTranscription, AudioChunk
from database import SessionLocal
from services.transcription import (
    transcribe_audio,
    apply_corrections,
    count_target_words,
)

logger = logging.getLogger(__name__)


async def transcribe_chunk_background(
    session_id: uuid.UUID,
    chunk_number: int,
    audio_bytes: bytes,
    duration_seconds: float
) -> None:
    """
    Transcribe a chunk in the background and cache the result.

    This is fire-and-forget - errors are logged but don't propagate.
    Called after successful chunk upload.

    Args:
        session_id: Recording session ID
        chunk_number: Chunk sequence number (1-indexed)
        audio_bytes: Raw audio data (WAV format)
        duration_seconds: Duration of the audio chunk
    """
    db = SessionLocal()
    temp_path = None

    try:
        # Check if already transcribed (idempotency)
        existing = db.query(ChunkTranscription).filter(
            ChunkTranscription.session_id == session_id,
            ChunkTranscription.chunk_number == chunk_number
        ).first()

        if existing and existing.transcribed_at:
            logger.debug(f"Chunk {chunk_number} already transcribed, skipping")
            return

        # Save audio to temp file
        temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        temp_path = temp_file.name
        temp_file.write(audio_bytes)
        temp_file.close()

        # Transcribe
        logger.info(f"Background transcribing chunk {chunk_number} for session {session_id}")
        raw_text = transcribe_audio(temp_path)
        corrected_text = apply_corrections(raw_text)
        word_counts = count_target_words(corrected_text)

        # Cache result - upsert pattern
        if existing:
            cache_entry = existing
        else:
            cache_entry = ChunkTranscription(
                session_id=session_id,
                chunk_number=chunk_number
            )
            db.add(cache_entry)

        cache_entry.raw_text = raw_text
        cache_entry.corrected_text = corrected_text
        cache_entry.word_counts = word_counts
        cache_entry.duration_seconds = duration_seconds
        cache_entry.transcribed_at = datetime.now(timezone.utc)
        cache_entry.error_message = None

        db.commit()

        logger.info(
            f"Cached transcription for chunk {chunk_number}: "
            f"{len(corrected_text)} chars, {sum(word_counts.values())} target words"
        )

    except Exception as e:
        logger.error(f"Background transcription failed for chunk {chunk_number}: {e}")

        # Record error in cache
        try:
            cache_entry = db.query(ChunkTranscription).filter(
                ChunkTranscription.session_id == session_id,
                ChunkTranscription.chunk_number == chunk_number
            ).first()

            if not cache_entry:
                cache_entry = ChunkTranscription(
                    session_id=session_id,
                    chunk_number=chunk_number
                )
                db.add(cache_entry)

            cache_entry.error_message = str(e)[:500]
            db.commit()
        except Exception:
            pass  # Don't fail on error logging

    finally:
        db.close()
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass  # Ignore cleanup errors


def get_cached_transcriptions(
    db: DBSession,
    session_id: uuid.UUID
) -> Dict[int, ChunkTranscription]:
    """
    Get all cached transcriptions for a session.

    Args:
        db: Database session
        session_id: Recording session ID

    Returns:
        Dict mapping chunk_number -> ChunkTranscription (only successful transcriptions)
    """
    results = db.query(ChunkTranscription).filter(
        ChunkTranscription.session_id == session_id,
        ChunkTranscription.transcribed_at.isnot(None)  # Only successful transcriptions
    ).all()

    return {ct.chunk_number: ct for ct in results}


def get_text_for_time_range(
    cached: Dict[int, ChunkTranscription],
    chunks: List[AudioChunk],
    start_time: float,
    end_time: float
) -> Optional[str]:
    """
    Get cached transcription text that covers a time range.

    Used by processor.py to map diarized speaker segments to cached chunk text.

    Args:
        cached: Dict of chunk_number -> ChunkTranscription
        chunks: List of AudioChunk records (for timing info)
        start_time: Segment start in seconds
        end_time: Segment end in seconds

    Returns:
        Concatenated corrected text from overlapping chunks, or None if insufficient coverage
    """
    if not chunks:
        return None

    # Build chunk timing map
    chunk_times = []
    current_time = 0.0

    for chunk in sorted(chunks, key=lambda c: c.chunk_number):
        duration = float(chunk.duration_seconds or 30.0)
        chunk_times.append({
            'number': chunk.chunk_number,
            'start': current_time,
            'end': current_time + duration
        })
        current_time += duration

    # Find overlapping chunks
    overlapping_text = []
    coverage = 0.0
    segment_duration = end_time - start_time

    if segment_duration <= 0:
        return None

    for ct in chunk_times:
        # Check overlap
        overlap_start = max(ct['start'], start_time)
        overlap_end = min(ct['end'], end_time)

        if overlap_start < overlap_end:
            overlap_duration = overlap_end - overlap_start
            coverage += overlap_duration

            # Get cached text for this chunk
            if ct['number'] in cached:
                text = cached[ct['number']].corrected_text
                if text:
                    overlapping_text.append(text)

    # Require at least 80% coverage to use cache
    if coverage / segment_duration < 0.8:
        return None

    return " ".join(overlapping_text) if overlapping_text else None


def get_cache_stats(db: DBSession, session_id: uuid.UUID) -> Dict:
    """
    Get statistics about cached transcriptions for a session.

    Useful for debugging and monitoring.

    Args:
        db: Database session
        session_id: Recording session ID

    Returns:
        Dict with cache statistics
    """
    total = db.query(ChunkTranscription).filter(
        ChunkTranscription.session_id == session_id
    ).count()

    successful = db.query(ChunkTranscription).filter(
        ChunkTranscription.session_id == session_id,
        ChunkTranscription.transcribed_at.isnot(None)
    ).count()

    failed = db.query(ChunkTranscription).filter(
        ChunkTranscription.session_id == session_id,
        ChunkTranscription.error_message.isnot(None)
    ).count()

    return {
        'total_chunks': total,
        'successful': successful,
        'failed': failed,
        'pending': total - successful - failed,
        'cache_hit_rate': successful / total if total > 0 else 0.0
    }
