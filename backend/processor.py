"""
processor.py - Audio Processing Pipeline

PURPOSE:
    Core processing logic for audio sessions. Handles the full pipeline from
    audio concatenation through speaker diarization, transcription, and word counting.

RESPONSIBILITIES:
    - Concatenate uploaded audio chunks into full session audio
    - Run speaker diarization (pyannote) to segment by speaker
    - Transcribe each segment using MERaLiON ASR
    - Apply post-processing corrections for Singlish words
    - Count target words per speaker
    - Generate 5-second sample clips for claiming UI
    - Update session status and progress in database

REFERENCED BY:
    - worker.py - Called by background job worker

REFERENCES:
    - services/diarization.py - Speaker diarization logic
    - services/transcription.py - MERaLiON transcription + corrections
    - storage.py - Audio file storage operations
    - models.py - Database models for sessions/speakers
"""

import os
import io
import uuid
import tempfile
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from decimal import Decimal

import httpx
import numpy as np
import soundfile as sf
from pydub import AudioSegment
from sqlalchemy.orm import Session as DBSession

from database import SessionLocal
from models import Session, SessionSpeaker, SpeakerWordCount, AudioChunk
from storage import storage
from config import settings

from services.diarization import (
    diarize_audio,
    extract_speaker_segment,
    SpeakerSegment,
)
from services.transcription import (
    transcribe_audio,
    apply_corrections,
    count_target_words,
    SAMPLE_RATE,
)
from services.transcription_cache import (
    get_cached_transcriptions,
    get_text_for_time_range,
)

logger = logging.getLogger(__name__)

# Processing stage weights for progress calculation
PROGRESS_STAGES = {
    "concatenating": (0, 10),
    "diarizing": (10, 40),
    "transcribing": (40, 85),
    "saving_results": (85, 95),
    "generating_samples": (95, 100),
}


class ProcessingError(Exception):
    """Custom exception for processing failures"""
    pass


async def process_session(session_id: uuid.UUID) -> Dict:
    """
    Main entry point for processing a recording session.

    Orchestrates the full pipeline:
    1. Concatenate audio chunks
    2. Run speaker diarization
    3. Transcribe each segment
    4. Apply corrections and count words
    5. Save results to database
    6. Generate sample clips for claiming

    Args:
        session_id: UUID of the session to process

    Returns:
        Dict with processing results summary

    Raises:
        ProcessingError: If any stage fails
    """
    db = SessionLocal()
    temp_files = []

    try:
        # Get session from database
        session = db.query(Session).filter(Session.id == session_id).first()
        if not session:
            raise ProcessingError(f"Session not found: {session_id}")

        # Update status to processing
        session.status = "processing"
        session.progress = 0
        db.commit()

        logger.info(f"Starting processing for session {session_id}")

        # Stage 1: Concatenate audio chunks
        update_progress(db, session, "concatenating", 0)
        audio_path, duration = await concatenate_chunks(db, session_id, temp_files)
        session.duration_seconds = int(duration)
        db.commit()
        update_progress(db, session, "concatenating", 100)

        # Stage 2: Run diarization
        update_progress(db, session, "diarizing", 0)
        segments = run_diarization(audio_path)
        update_progress(db, session, "diarizing", 100)

        if not segments:
            logger.warning(f"No speakers detected in session {session_id}")
            session.status = "ready_for_claiming"
            session.progress = 100
            db.commit()
            return {"speakers": 0, "segments": 0, "words": {}}

        # Stage 3: Transcribe segments and count words
        update_progress(db, session, "transcribing", 0)
        speaker_results = await transcribe_and_count(
            audio_path, segments, db, session
        )
        update_progress(db, session, "transcribing", 100)

        # Stage 4: Save results to database
        update_progress(db, session, "saving_results", 0)
        speaker_records = save_speaker_results(
            db, session_id, speaker_results, segments
        )
        update_progress(db, session, "saving_results", 100)

        # Stage 5: Generate and upload sample clips
        update_progress(db, session, "generating_samples", 0)
        await generate_speaker_samples(
            db, session_id, audio_path, speaker_records, segments
        )
        update_progress(db, session, "generating_samples", 100)

        # Upload processed full audio
        with open(audio_path, "rb") as f:
            audio_content = f.read()
        audio_storage_path = await storage.upload_processed_audio(
            session_id, audio_content, "full_audio.wav"
        )
        session.audio_url = storage.get_public_url(audio_storage_path)

        # Mark session as ready for claiming
        session.status = "ready_for_claiming"
        session.progress = 100
        db.commit()

        logger.info(f"Processing complete for session {session_id}")

        # Build summary
        total_words = sum(
            sum(counts.values())
            for counts in speaker_results.values()
        )

        return {
            "speakers": len(speaker_records),  # Use speaker_records which includes all detected speakers
            "segments": len(segments),
            "total_words": total_words,
            "speaker_word_counts": {
                speaker: dict(counts)
                for speaker, counts in speaker_results.items()
            }
        }

    except Exception as e:
        logger.error(f"Processing failed for session {session_id}: {e}")

        # Update session with error
        session = db.query(Session).filter(Session.id == session_id).first()
        if session:
            session.status = "failed"
            session.error_message = str(e)
            db.commit()

        raise ProcessingError(f"Processing failed: {e}") from e

    finally:
        db.close()

        # Cleanup temp files
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file {temp_file}: {e}")


def update_progress(
    db: DBSession,
    session: Session,
    stage: str,
    stage_progress: int
) -> None:
    """Update session progress based on current stage"""
    start, end = PROGRESS_STAGES.get(stage, (0, 100))
    overall = start + (end - start) * stage_progress // 100
    session.progress = overall
    db.commit()


async def concatenate_chunks(
    db: DBSession,
    session_id: uuid.UUID,
    temp_files: List[str]
) -> Tuple[str, float]:
    """
    Download and concatenate all audio chunks for a session.

    Args:
        db: Database session
        session_id: Session UUID
        temp_files: List to track temp files for cleanup

    Returns:
        Tuple of (output_path, duration_seconds)
    """
    # Get chunks from database, ordered by chunk number
    chunks = db.query(AudioChunk).filter(
        AudioChunk.session_id == session_id
    ).order_by(AudioChunk.chunk_number).all()

    if not chunks:
        raise ProcessingError(f"No audio chunks found for session {session_id}")

    logger.info(f"Found {len(chunks)} chunks to concatenate")

    # Download each chunk
    combined = AudioSegment.empty()

    async with httpx.AsyncClient() as client:
        for chunk in chunks:
            # Get public URL for chunk
            chunk_url = storage.get_public_url(chunk.storage_path)

            # Download chunk
            response = await client.get(chunk_url, timeout=60.0)
            if response.status_code != 200:
                raise ProcessingError(
                    f"Failed to download chunk {chunk.chunk_number}: {response.status_code}"
                )

            # Save to temp file (pydub needs file path for some formats)
            temp_chunk = tempfile.NamedTemporaryFile(
                suffix=os.path.splitext(chunk.storage_path)[1],
                delete=False
            )
            temp_chunk.write(response.content)
            temp_chunk.close()
            temp_files.append(temp_chunk.name)

            # Load and append
            try:
                audio_chunk = AudioSegment.from_file(temp_chunk.name)
                combined += audio_chunk
            except Exception as e:
                logger.warning(f"Failed to load chunk {chunk.chunk_number}: {e}")
                continue

    if len(combined) == 0:
        raise ProcessingError("All chunks failed to load")

    # Convert to WAV at correct sample rate
    combined = combined.set_frame_rate(SAMPLE_RATE).set_channels(1)

    # Save concatenated audio
    output_path = tempfile.NamedTemporaryFile(
        suffix=".wav", delete=False
    ).name
    temp_files.append(output_path)

    combined.export(output_path, format="wav")

    duration = len(combined) / 1000.0  # pydub uses milliseconds
    logger.info(f"Concatenated audio: {duration:.1f}s")

    return output_path, duration


def run_diarization(audio_path: str) -> List[SpeakerSegment]:
    """
    Run speaker diarization on audio file.

    Args:
        audio_path: Path to WAV file

    Returns:
        List of SpeakerSegment objects
    """
    logger.info(f"Running diarization on {audio_path}")

    try:
        segments = diarize_audio(audio_path)

        unique_speakers = set(s.speaker_id for s in segments)
        logger.info(
            f"Diarization complete: {len(segments)} segments, "
            f"{len(unique_speakers)} speakers"
        )

        return segments

    except Exception as e:
        logger.error(f"Diarization failed: {e}")
        raise ProcessingError(f"Diarization failed: {e}") from e


async def transcribe_and_count(
    audio_path: str,
    segments: List[SpeakerSegment],
    db: DBSession,
    session: Session
) -> Dict[str, Dict[str, int]]:
    """
    Transcribe each segment and count target words per speaker.

    OPTIMIZED: Uses cached chunk transcriptions when available,
    falls back to direct transcription for uncached segments.
    Parallelizes remaining transcription work.

    Args:
        audio_path: Path to full audio file
        segments: List of speaker segments
        db: Database session (for progress updates)
        session: Session model (for progress updates)

    Returns:
        Dict mapping speaker_id -> {word: count}
    """
    speaker_word_counts: Dict[str, Dict[str, int]] = defaultdict(
        lambda: defaultdict(int)
    )

    total_segments = len(segments)
    session_id = session.id

    # Get cached transcriptions
    cached = get_cached_transcriptions(db, session_id)
    chunks = db.query(AudioChunk).filter(
        AudioChunk.session_id == session_id
    ).order_by(AudioChunk.chunk_number).all()

    logger.info(f"Found {len(cached)} cached chunk transcriptions")

    # Separate segments into cached vs needs-transcription
    cached_segments = []
    uncached_segments = []

    for segment in segments:
        cached_text = get_text_for_time_range(
            cached, chunks, segment.start_time, segment.end_time
        )
        if cached_text:
            cached_segments.append((segment, cached_text))
        else:
            uncached_segments.append(segment)

    logger.info(
        f"Segments: {len(cached_segments)} from cache, "
        f"{len(uncached_segments)} need transcription"
    )

    # Process cached segments (fast - just count words)
    for i, (segment, text) in enumerate(cached_segments):
        corrected = apply_corrections(text)
        word_counts = count_target_words(corrected)

        speaker_id = segment.speaker_id
        for word, count in word_counts.items():
            speaker_word_counts[speaker_id][word] += count

        logger.debug(f"Cached segment ({speaker_id}): {word_counts}")

    # Update progress for cached segments
    cached_progress = len(cached_segments) * 100 // max(total_segments, 1)
    update_progress(db, session, "transcribing", cached_progress)

    # Transcribe uncached segments in parallel
    if uncached_segments:
        async def transcribe_segment(segment: SpeakerSegment) -> Tuple[str, Dict[str, int]]:
            """Transcribe a single segment and return (speaker_id, word_counts)."""
            try:
                segment_bytes = extract_speaker_segment(
                    audio_path, segment.start_time, segment.end_time
                )

                temp_segment = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
                temp_segment.write(segment_bytes)
                temp_segment.close()

                try:
                    # Run synchronous transcription in thread pool
                    raw_text = await asyncio.to_thread(transcribe_audio, temp_segment.name)
                    corrected = apply_corrections(raw_text)
                    word_counts = count_target_words(corrected)
                    return (segment.speaker_id, word_counts)
                finally:
                    os.remove(temp_segment.name)

            except Exception as e:
                logger.warning(f"Failed to transcribe segment ({segment.speaker_id}): {e}")
                return (segment.speaker_id, {})

        # Run transcriptions in parallel (limit concurrency to avoid OOM)
        semaphore = asyncio.Semaphore(3)  # Max 3 concurrent transcriptions

        async def limited_transcribe(segment):
            async with semaphore:
                return await transcribe_segment(segment)

        # Execute in parallel
        results = await asyncio.gather(
            *[limited_transcribe(seg) for seg in uncached_segments],
            return_exceptions=True
        )

        # Aggregate results
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"Parallel transcription error: {result}")
                continue

            speaker_id, word_counts = result
            for word, count in word_counts.items():
                speaker_word_counts[speaker_id][word] += count

            # Update progress
            progress = (len(cached_segments) + i + 1) * 100 // total_segments
            update_progress(db, session, "transcribing", progress)

    update_progress(db, session, "transcribing", 100)

    return {
        speaker: dict(counts)
        for speaker, counts in speaker_word_counts.items()
    }


def save_speaker_results(
    db: DBSession,
    session_id: uuid.UUID,
    speaker_results: Dict[str, Dict[str, int]],
    segments: List[SpeakerSegment] = None
) -> Dict[str, SessionSpeaker]:
    """
    Save speaker and word count results to database.

    Args:
        db: Database session
        session_id: Session UUID
        speaker_results: Dict mapping speaker_id -> {word: count}
        segments: List of speaker segments from diarization (to ensure all speakers are created)

    Returns:
        Dict mapping speaker_id -> SessionSpeaker record
    """
    speaker_records = {}

    # Get all unique speakers from diarization segments
    all_speaker_ids = set(speaker_results.keys())
    if segments:
        for segment in segments:
            all_speaker_ids.add(segment.speaker_id)
    
    logger.info(f"Creating speaker records for {len(all_speaker_ids)} speakers: {all_speaker_ids}")

    for speaker_id in all_speaker_ids:
        word_counts = speaker_results.get(speaker_id, {})
        
        # Count segments for this speaker
        segment_count = 0
        if segments:
            segment_count = sum(1 for s in segments if s.speaker_id == speaker_id)
        
        # Create SessionSpeaker record
        speaker = SessionSpeaker(
            id=uuid.uuid4(),
            session_id=session_id,
            speaker_label=speaker_id,
            segment_count=segment_count if segment_count > 0 else sum(word_counts.values()),
        )
        db.add(speaker)
        db.flush()  # Get the ID

        # Create SpeakerWordCount records
        for word, count in word_counts.items():
            word_count = SpeakerWordCount(
                session_speaker_id=speaker.id,
                word=word,
                count=count
            )
            db.add(word_count)

        speaker_records[speaker_id] = speaker

        logger.info(
            f"Saved speaker {speaker_id}: "
            f"{sum(word_counts.values())} total words"
        )

    db.commit()
    return speaker_records


async def generate_speaker_samples(
    db: DBSession,
    session_id: uuid.UUID,
    audio_path: str,
    speaker_records: Dict[str, SessionSpeaker],
    segments: List[SpeakerSegment],
    sample_duration: float = 5.0
) -> None:
    """
    Generate 5-second sample clips for each speaker for the claiming UI.

    Args:
        db: Database session
        session_id: Session UUID
        audio_path: Path to full audio file
        speaker_records: Dict mapping speaker_id -> SessionSpeaker
        segments: All speaker segments
        sample_duration: Duration of sample clip in seconds
    """
    # Group segments by speaker and find best sample for each
    speaker_segments: Dict[str, List[SpeakerSegment]] = defaultdict(list)
    for segment in segments:
        speaker_segments[segment.speaker_id].append(segment)

    for speaker_id, speaker in speaker_records.items():
        try:
            # Find longest segment for this speaker (most representative)
            segs = speaker_segments.get(speaker_id, [])
            if not segs:
                continue

            best_segment = max(segs, key=lambda s: s.duration)

            # Calculate sample range (up to sample_duration seconds)
            sample_end = min(
                best_segment.start_time + sample_duration,
                best_segment.end_time
            )

            # Extract sample
            sample_bytes = extract_speaker_segment(
                audio_path,
                best_segment.start_time,
                sample_end
            )

            # Upload sample
            sample_filename = f"speaker_{speaker_id}_sample.wav"
            sample_path = await storage.upload_processed_audio(
                session_id, sample_bytes, sample_filename
            )

            # Update speaker record
            speaker.sample_audio_url = storage.get_public_url(sample_path)
            speaker.sample_start_time = Decimal(str(best_segment.start_time))
            speaker.total_duration_seconds = Decimal(
                str(sum(s.duration for s in segs))
            )

            logger.info(
                f"Generated sample for {speaker_id}: "
                f"{best_segment.start_time:.1f}s - {sample_end:.1f}s"
            )

        except Exception as e:
            logger.warning(f"Failed to generate sample for {speaker_id}: {e}")
            continue

    db.commit()


# Synchronous wrapper for use with Redis worker
def process_session_sync(session_id: uuid.UUID) -> Dict:
    """
    Synchronous wrapper for process_session.
    Used by worker.py which may not be async.
    """
    import asyncio
    return asyncio.run(process_session(session_id))
