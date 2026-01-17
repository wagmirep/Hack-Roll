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

FUNCTIONS:
    - get_diarization_pipeline() -> Pipeline
        Returns cached pyannote pipeline instance

    - diarize_audio(audio_path: str) -> List[Segment]
        Run diarization on audio file
        Returns: [
            {'start': 0.0, 'end': 5.2, 'speaker': 'SPEAKER_00'},
            {'start': 5.2, 'end': 12.1, 'speaker': 'SPEAKER_01'},
            ...
        ]

    - extract_speaker_segment(audio_path, start, end) -> bytes
        Extract audio segment for a specific time range

    - filter_overlapping_segments(segments) -> List[Segment]
        Remove segments where multiple speakers detected

EXPECTED ACCURACY:
    85-90% in good acoustic conditions
    Degrades with: background noise, overlapping speech, similar voices
"""
