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

import re
from typing import Dict


# =============================================================================
# SINGLISH POST-PROCESSING CORRECTIONS
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
