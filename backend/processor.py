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
    - services/diarization.py - Uses diarization service
    - services/transcription.py - Uses transcription service

REFERENCES:
    - services/diarization.py - Speaker diarization logic
    - services/transcription.py - MERaLiON transcription
    - storage.py - Audio file storage operations
    - models.py - Database models for sessions/speakers
    - database.py - Database session management

KEY FUNCTIONS:
    - process_session(session_id) - Main processing entry point
    - concatenate_chunks(session_id) - Merge audio chunks
    - apply_corrections(text) - Post-process transcription
    - count_target_words(text) - Count Singlish words
    - generate_speaker_samples(segments) - Create claiming audio clips

TARGET_WORDS:
    ['walao', 'cheebai', 'lanjiao', 'lah', 'lor', 'sia', 'meh', 'can', 'paiseh', 'shiok', 'sian']

CORRECTIONS:
    {'while up': 'walao', 'wa lao': 'walao', 'cheap buy': 'cheebai', 'la': 'lah', 'low': 'lor', ...}
"""
