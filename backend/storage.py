"""
storage.py - Audio File Storage Utilities

PURPOSE:
    Handle all audio file storage operations with AWS S3 or compatible storage.
    Manages upload, download, and URL generation for audio files.

RESPONSIBILITIES:
    - Upload audio chunks to S3
    - Download audio files for processing
    - Generate presigned URLs for audio playback
    - Concatenate audio chunks into full session file
    - Store and retrieve speaker sample clips
    - Clean up temporary files

REFERENCED BY:
    - routers/sessions.py - Audio chunk upload endpoint
    - processor.py - Downloading chunks for processing, saving samples
    - services/diarization.py - Accessing audio files

REFERENCES:
    - config.py - S3_BUCKET, AWS credentials

FUNCTIONS:
    - upload_chunk(session_id, chunk_number, audio_data) -> str (S3 key)
    - download_chunk(s3_key) -> bytes
    - get_chunks_for_session(session_id) -> List[str] (S3 keys)
    - concatenate_audio(chunk_keys) -> str (path to merged file)
    - upload_speaker_sample(session_id, speaker_id, audio_data) -> str (URL)
    - get_presigned_url(s3_key, expiry=3600) -> str
    - cleanup_temp_files(session_id) -> None

STORAGE STRUCTURE:
    s3://lahstats-audio/
    ├── sessions/{session_id}/
    │   ├── chunks/
    │   │   ├── 001.wav
    │   │   ├── 002.wav
    │   │   └── ...
    │   ├── full_audio.wav
    │   └── samples/
    │       ├── SPEAKER_00.wav
    │       └── SPEAKER_01.wav
"""
