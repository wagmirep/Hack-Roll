"""
services/transcription.py - Transcription Service (External API)

Calls external MERaLiON transcription API (Colab notebook via ngrok).
Applies Singlish-specific corrections and counts target words.

SETUP:
    Set TRANSCRIPTION_API_URL environment variable to your Colab ngrok URL.
    Example: TRANSCRIPTION_API_URL=https://xxxx-xxx.ngrok.io
"""

import os
import re
import io
import base64
import logging
from typing import Dict, Optional, Tuple

import httpx

logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

SAMPLE_RATE = 16000  # Expected input sample rate for audio conversion


# =============================================================================
# EXTERNAL API TRANSCRIPTION (Colab notebook)
# =============================================================================

def _get_transcription_api_url() -> Optional[str]:
    """Get external transcription API URL from config."""
    try:
        from config import settings
        return settings.TRANSCRIPTION_API_URL
    except Exception:
        return os.getenv("TRANSCRIPTION_API_URL")


def is_using_external_api() -> bool:
    """Check if external transcription API is configured."""
    url = _get_transcription_api_url()
    return url is not None and len(url) > 0


def _convert_to_wav(audio_path: str) -> bytes:
    """
    Convert audio file to WAV format (16kHz mono) for API compatibility.

    Args:
        audio_path: Path to audio file (any format supported by pydub/ffmpeg)

    Returns:
        WAV audio bytes
    """
    from pydub import AudioSegment

    # Load audio (pydub handles m4a, mp3, wav, etc.)
    audio = AudioSegment.from_file(audio_path)

    # Convert to 16kHz mono
    audio = audio.set_frame_rate(SAMPLE_RATE).set_channels(1)

    # Export as WAV to bytes
    wav_buffer = io.BytesIO()
    audio.export(wav_buffer, format="wav")
    wav_buffer.seek(0)

    return wav_buffer.read()


def transcribe_audio(audio_path: str) -> str:
    """
    Transcribe audio file to text using external MERaLiON API.

    Args:
        audio_path: Path to audio file (16kHz mono WAV recommended)

    Returns:
        Raw transcription text

    Raises:
        FileNotFoundError: If audio file doesn't exist
        RuntimeError: If transcription fails or API not configured
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    api_url = _get_transcription_api_url()
    if not api_url:
        raise RuntimeError(
            "TRANSCRIPTION_API_URL not configured. "
            "Set this environment variable to your Colab ngrok URL."
        )

    transcribe_endpoint = f"{api_url.rstrip('/')}/transcribe"

    logger.info(f"Transcribing audio via external API: {audio_path}")

    try:
        # Convert to WAV format (handles m4a, mp3, etc.)
        audio_bytes = _convert_to_wav(audio_path)
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

        # Call API with generous timeout (model inference can be slow)
        with httpx.Client(timeout=120.0) as client:
            response = client.post(
                transcribe_endpoint,
                json={"audio": audio_b64},
                headers={"Content-Type": "application/json"}
            )

        if response.status_code != 200:
            error_msg = response.text[:500] if response.text else "Unknown error"
            raise RuntimeError(f"API returned {response.status_code}: {error_msg}")

        result = response.json()

        # API returns: {"raw_transcription": ..., "corrected": ..., "word_counts": ...}
        raw_text = result.get("raw_transcription", "")

        logger.info(f"Transcription complete: {len(raw_text)} chars")
        return raw_text

    except httpx.TimeoutException:
        raise RuntimeError(f"External transcription API timed out: {transcribe_endpoint}")
    except httpx.RequestError as e:
        raise RuntimeError(f"External transcription API request failed: {e}")
    except Exception as e:
        raise RuntimeError(f"External transcription failed: {e}")


def transcribe_segment(audio_bytes: bytes, sample_rate: int = SAMPLE_RATE) -> str:
    """
    Transcribe audio bytes directly using external API.

    Args:
        audio_bytes: Raw audio data (WAV format)
        sample_rate: Sample rate of the audio (default: 16000)

    Returns:
        Raw transcription text

    Raises:
        RuntimeError: If transcription fails or API not configured
    """
    api_url = _get_transcription_api_url()
    if not api_url:
        raise RuntimeError(
            "TRANSCRIPTION_API_URL not configured. "
            "Set this environment variable to your Colab ngrok URL."
        )

    transcribe_endpoint = f"{api_url.rstrip('/')}/transcribe"

    try:
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

        with httpx.Client(timeout=120.0) as client:
            response = client.post(
                transcribe_endpoint,
                json={"audio": audio_b64},
                headers={"Content-Type": "application/json"}
            )

        if response.status_code != 200:
            error_msg = response.text[:500] if response.text else "Unknown error"
            raise RuntimeError(f"API returned {response.status_code}: {error_msg}")

        result = response.json()
        return result.get("raw_transcription", "")

    except Exception as e:
        raise RuntimeError(f"External transcription failed: {e}")


# =============================================================================
# SINGLISH POST-PROCESSING CORRECTIONS
# =============================================================================

# Corrections dictionary for common ASR misrecognitions
CORRECTIONS: Dict[str, str] = {
    # Walao variations
    'while up': 'walao',
    'wah lao eh': 'walao',
    'wa lao eh': 'walao',
    'wah lao': 'walao',
    'wa lao': 'walao',
    'wah low': 'walao',
    'wa low': 'walao',
    'while ah': 'walao',
    'wah lau': 'walao',
    'wa lau': 'walao',
    'wah liao': 'walao',
    'wa liao': 'walao',
    'while low': 'walao',
    'wah lei': 'walao',
    'why lao': 'walao',
    'why low': 'walao',
    'wah la': 'walao',
    # Vulgar - cheebai
    'cheap buy': 'cheebai',
    'chee bye': 'cheebai',
    'chi bye': 'cheebai',
    'chee bai': 'cheebai',
    'chi bai': 'cheebai',
    'chee by': 'cheebai',
    'chi by': 'cheebai',
    'cb': 'cheebai',
    'c b': 'cheebai',
    'see bee': 'cheebai',
    # Vulgar - lanjiao
    'lunch hour': 'lanjiao',
    'lan jiao': 'lanjiao',
    'lan chow': 'lanjiao',
    'lan chiao': 'lanjiao',
    'lun jiao': 'lanjiao',
    'lan chio': 'lanjiao',
    'lunchow': 'lanjiao',
    'lan jio': 'lanjiao',
    # Vulgar - kanina
    'can nina': 'kanina',
    'kar ni na': 'kanina',
    'ka ni na': 'kanina',
    'car nina': 'kanina',
    'knn': 'kanina',
    'k n n': 'kanina',
    # Vulgar - nabei
    'nah bay': 'nabei',
    'na bei': 'nabei',
    'nah bei': 'nabei',
    'na beh': 'nabei',
    'nah beh': 'nabei',
    # Paiseh
    'pie say': 'paiseh',
    'pai seh': 'paiseh',
    'pie seh': 'paiseh',
    'pai say': 'paiseh',
    'pie se': 'paiseh',
    'pai se': 'paiseh',
    'paise': 'paiseh',
    # Shiok
    'shook': 'shiok',
    'she ok': 'shiok',
    'shoe ok': 'shiok',
    'shi ok': 'shiok',
    # Alamak
    'ala mak': 'alamak',
    'allah mak': 'alamak',
    'a la mak': 'alamak',
    'allamak': 'alamak',
    'aller mak': 'alamak',
    # Aiyo/Aiyah
    'ai yo': 'aiyo',
    'ai yoh': 'aiyo',
    'aiya': 'aiyah',
    'ai ya': 'aiyah',
    'eye yo': 'aiyo',
    'aye yo': 'aiyo',
    'ai yah': 'aiyah',
    'eye yah': 'aiyah',
    # Jialat
    'jia lat': 'jialat',
    'gia lat': 'jialat',
    'jia lut': 'jialat',
    'jee ah lat': 'jialat',
    'gia lut': 'jialat',
    # Bojio
    'bo jio': 'bojio',
    'boh jio': 'bojio',
    'bo gio': 'bojio',
    'never jio': 'bojio',
    'boh gio': 'bojio',
    # Sia
    'see ya': 'sia',
    'see ah': 'sia',
    'siah': 'sia',
    'si ah': 'sia',
    # Sian
    'see an': 'sian',
    'si an': 'sian',
    'see en': 'sian',
    'si en': 'sian',
    # Other
    'kia su': 'kiasu',
    'key ah su': 'kiasu',
    'kia si': 'kiasi',
    'key ah si': 'kiasi',
    'boh doh': 'bodoh',
    'bo doh': 'bodoh',
    'sua ku': 'suaku',
    'swah ku': 'suaku',
    'le pak': 'lepak',
    'lay pak': 'lepak',
    'chop': 'chope',
    'ma kan': 'makan',
    'go stan': 'gostan',
    'go stun': 'gostan',
    'si bei': 'sibei',
    'see bay': 'sibei',
    'si bay': 'sibei',
    'ah tas': 'atas',
    'ar tas': 'atas',
    'kay poh': 'kaypoh',
    'kae poh': 'kaypoh',
    'kaypo': 'kaypoh',
    'kpo': 'kaypoh',
    'steady pom pi pi': 'steady',
    'goon du': 'goondu',
    'gun du': 'goondu',
}

# Single-word corrections with word boundary checking
WORD_CORRECTIONS: Dict[str, str] = {
    'la': 'lah',
    'laa': 'lah',
    'laaa': 'lah',
    'low': 'lor',
    'loh': 'lor',
    # 'leh' is a distinct particle - don't convert to 'lah'
    'ler': 'lah',
    'seh': 'sia',
    'mah': 'meh',
    # 'huh' is distinct from 'hor' - don't convert
    'arh': 'ah',
    'err': 'eh',  # Model often mishears 'eh' as 'err'
    'shio': 'shiok',  # Needs word boundary to avoid shiok -> shiokk
}

# Target Singlish words to count
TARGET_WORDS = [
    # Vulgar
    'walao', 'cheebai', 'lanjiao', 'kanina', 'nabei',
    # Particles
    'lah', 'lor', 'sia', 'meh', 'leh', 'hor', 'ah', 'one', 'what', 'lei', 'ma',
    # Exclamations
    'wah', 'eh', 'huh', 'aiyo', 'aiyah', 'alamak',
    # Colloquial
    'can', 'cannot', 'paiseh', 'shiok', 'sian', 'bodoh', 'kiasu', 'kiasi',
    'bojio', 'suaku', 'lepak', 'blur', 'goondu', 'cheem', 'chim',
    # Actions
    'chope', 'kena', 'makan', 'tahan', 'gostan', 'cabut', 'sabo', 'arrow',
    # Intensifiers
    'sibei', 'buay', 'jialat',
    # Food/Drink
    'kopi', 'teh', 'peng',
    # Misc
    'atas', 'kaypoh', 'steady', 'power', 'liao',
]


def _normalize_for_matching(text: str) -> str:
    """Normalize text before correction matching."""
    if not text:
        return text
    result = text
    result = re.sub(r'!\(([^)]+)\)!', r'\1', result)
    result = re.sub(r'\(([a-zA-Z]+)\)', r'\1', result)
    result = re.sub(r'\s+', ' ', result)
    return result.strip()


def apply_corrections(text: str) -> str:
    """Apply post-processing corrections to transcribed text."""
    if not text:
        return text

    result = _normalize_for_matching(text)

    # Apply multi-word corrections first (longer phrases first)
    sorted_corrections = sorted(CORRECTIONS.items(), key=lambda x: len(x[0]), reverse=True)
    for wrong, correct in sorted_corrections:
        pattern = re.compile(re.escape(wrong), re.IGNORECASE)
        result = pattern.sub(correct, result)

    # Apply single-word corrections with word boundary checking
    for wrong, correct in WORD_CORRECTIONS.items():
        pattern = re.compile(r'\b' + re.escape(wrong) + r'\b', re.IGNORECASE)
        result = pattern.sub(correct, result)

    return result


def count_target_words(text: str) -> Dict[str, int]:
    """Count occurrences of target Singlish words in text."""
    if not text:
        return {}

    normalized = _normalize_for_matching(text.lower())
    counts: Dict[str, int] = {}

    for word in TARGET_WORDS:
        pattern = re.compile(r'(?<![a-zA-Z])' + re.escape(word) + r'(?![a-zA-Z])', re.IGNORECASE)
        matches = pattern.findall(normalized)
        if matches:
            counts[word] = len(matches)

    return counts


def process_transcription(text: str) -> Tuple[str, Dict[str, int]]:
    """Apply corrections and count words in one step."""
    corrected = apply_corrections(text)
    counts = count_target_words(corrected)
    return corrected, counts
