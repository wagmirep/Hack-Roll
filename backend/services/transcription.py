"""
services/transcription.py - MERaLiON Transcription Service

PURPOSE:
    Wrapper service for MERaLiON-2-10B-ASR speech-to-text model.
    Transcribes Singlish audio segments to text.

RESPONSIBILITIES:
    - Load MERaLiON ASR model from HuggingFace
    - Transcribe audio segments to text
    - Apply post-processing corrections for Singlish words
    - Count target Singlish words in transcription
    - Cache model for reuse

REFERENCED BY:
    - processor.py - Called for each speaker segment

REFERENCES:
    - config.py - Model configuration
    - ml/outputs/ - Fine-tuned LoRA adapters (post-hackathon)

MODEL:
    MERaLiON/MERaLiON-2-10B-ASR (HuggingFace)
    - Input: 16kHz mono audio, max 30s chunks
    - Output: Text transcription
    - Performance: 85-90% accuracy on Singlish particles

FUNCTIONS:
    - get_transcriber() -> Pipeline
        Returns cached transformers pipeline instance

    - transcribe_audio(audio_path: str) -> str
        Transcribe audio file to text

    - transcribe_segment(audio_bytes: bytes) -> str
        Transcribe audio bytes directly

    - apply_corrections(text: str) -> str
        Apply post-processing corrections
        e.g., "while up" -> "walao", "wa lao" -> "walao"

    - count_target_words(text: str) -> Dict[str, int]
        Count occurrences of target Singlish words
        Returns: {'walao': 2, 'lah': 5, 'sia': 1}

CORRECTIONS DICTIONARY:
    {
        'while up': 'walao',
        'wa lao': 'walao',
        'wah lao': 'walao',
        'cheap buy': 'cheebai',
        'chee bye': 'cheebai',
        'lunch hour': 'lanjiao',
        'lan jiao': 'lanjiao',
        'la': 'lah',
        'low': 'lor',
        'leh': 'lah',
        'seh': 'sia',
        ...
    }

TARGET_WORDS:
    ['walao', 'cheebai', 'lanjiao', 'lah', 'lor', 'sia', 'meh', 'can', 'paiseh', 'shiok', 'sian']
"""
