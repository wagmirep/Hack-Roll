"""
services/transcription.py - MERaLiON Transcription Service

Wrapper service for MERaLiON-2-10B-ASR speech-to-text model.
Transcribes Singlish audio segments to text.

Agent 2 scope: Model loading and transcription only.
Post-processing (corrections, word counting) handled by Agent 3.
"""

import os
import re
import logging
from typing import Dict, Optional, Tuple
from threading import Lock

logger = logging.getLogger(__name__)

# =============================================================================
# MODEL SINGLETON (Agent 2)
# =============================================================================

_model = None
_processor = None
_model_lock = Lock()

# Model configuration
MODEL_NAME = "MERaLiON/MERaLiON-2-10B-ASR"
SAMPLE_RATE = 16000  # Expected input sample rate


def get_transcriber():
    """
    Get or create the MERaLiON model and processor instances.

    Uses singleton pattern to avoid reloading the 10B parameter model.
    Thread-safe initialization.

    Returns:
        tuple: (model, processor) instances

    Raises:
        RuntimeError: If model fails to load
    """
    global _model, _processor

    if _model is not None and _processor is not None:
        return _model, _processor

    with _model_lock:
        # Double-check after acquiring lock
        if _model is not None and _processor is not None:
            return _model, _processor

        logger.info(f"Loading MERaLiON ASR model: {MODEL_NAME}")

        try:
            from transformers import AutoProcessor, AutoModelForSpeechSeq2Seq
            import torch

            # Check GPU memory to decide loading strategy
            use_device_map = False
            if torch.cuda.is_available():
                total_mem_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
                logger.info(f"GPU memory: {total_mem_gb:.1f}GB")
                # MERaLiON-2-10B needs ~20GB in fp16, use device_map for smaller GPUs
                if total_mem_gb < 20:
                    use_device_map = True
                    logger.info("Using device_map='auto' for CPU offloading (GPU < 20GB)")
                else:
                    logger.info("Using full GPU inference")
            else:
                logger.warning("CUDA not available, using CPU (will be slow)")

            # Load processor
            _processor = AutoProcessor.from_pretrained(
                MODEL_NAME,
                trust_remote_code=True
            )

            # Load model with appropriate device strategy
            if use_device_map:
                _model = AutoModelForSpeechSeq2Seq.from_pretrained(
                    MODEL_NAME,
                    torch_dtype=torch.float16,
                    device_map="auto",
                    trust_remote_code=True,
                    attn_implementation="eager",
                )
            else:
                _model = AutoModelForSpeechSeq2Seq.from_pretrained(
                    MODEL_NAME,
                    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                    trust_remote_code=True,
                    attn_implementation="eager",
                )
                if torch.cuda.is_available():
                    _model = _model.to("cuda")

            logger.info("MERaLiON model loaded successfully")
            return _model, _processor

        except Exception as e:
            logger.error(f"Failed to load MERaLiON model: {e}")
            raise RuntimeError(f"Failed to load transcription model: {e}") from e


def _clean_model_output(text: str) -> str:
    """
    Clean raw model output by removing prompt templates and artifacts.

    MERaLiON outputs include the chat template, speaker markers, and
    sometimes bracketed words that need to be cleaned before processing.

    Args:
        text: Raw model output

    Returns:
        Cleaned transcription text
    """
    if not text:
        return text

    result = text

    # Remove everything up to and including "model\n" (chat template prefix)
    if "model\n" in result:
        result = result.split("model\n", 1)[-1]

    # Remove speaker markers like <Speaker1>:, <Speaker2>:, etc.
    result = re.sub(r'<Speaker\d+>:\s*', '', result)

    # Remove <SpeechHere> tags
    result = re.sub(r'<SpeechHere>', '', result)

    # Clean bracketed words: !(walao)! -> walao, (lah) -> lah
    result = re.sub(r'!\(([^)]+)\)!', r'\1', result)  # !(word)! -> word
    result = re.sub(r'\(([a-zA-Z]+)\)', r'\1', result)  # (word) -> word

    # Remove filler markers
    result = re.sub(r'\(err\)', '', result, flags=re.IGNORECASE)
    result = re.sub(r'\(uh\)', '', result, flags=re.IGNORECASE)
    result = re.sub(r'\(um\)', '', result, flags=re.IGNORECASE)

    # Clean up extra whitespace
    result = re.sub(r'\s+', ' ', result).strip()

    return result


def _transcribe_audio_array(audio_data, sample_rate: int = SAMPLE_RATE) -> str:
    """
    Internal function to transcribe audio array using model directly.

    Args:
        audio_data: numpy array of audio samples
        sample_rate: Sample rate of the audio

    Returns:
        Transcription text
    """
    import torch
    import numpy as np

    model, processor = get_transcriber()

    # Ensure float32 numpy array
    if not isinstance(audio_data, np.ndarray):
        audio_data = np.array(audio_data)
    audio_data = audio_data.astype(np.float32)

    # MERaLiON-2-10B-ASR uses a chat-style interface with prompt template
    # The processor expects: text (chat prompt) and audios (list of arrays)
    prompt_template = "Instruction: {query} \nFollow the text instruction based on the following audio: <SpeechHere>"
    transcribe_prompt = "Please transcribe this speech."

    conversation = [[{"role": "user", "content": prompt_template.format(query=transcribe_prompt)}]]
    chat_prompt = processor.tokenizer.apply_chat_template(
        conversation=conversation,
        tokenize=False,
        add_generation_prompt=True
    )

    # Process audio through processor
    # Note: audios must be a list of audio arrays
    inputs = processor(text=chat_prompt, audios=[audio_data])

    # Move inputs to model device and dtype
    # Model is loaded in float16, so inputs must match
    device = next(model.parameters()).device
    dtype = next(model.parameters()).dtype  # Usually float16

    def move_to_device(v):
        if not hasattr(v, 'to'):
            return v
        v = v.to(device)
        # Only convert floating point tensors to model dtype
        if v.is_floating_point():
            v = v.to(dtype)
        return v

    inputs = {k: move_to_device(v) for k, v in inputs.items()}

    # Generate transcription
    with torch.no_grad():
        generated_ids = model.generate(**inputs, max_new_tokens=256)

    # Decode
    transcription = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

    # Clean model output artifacts
    transcription = _clean_model_output(transcription)

    return transcription.strip()


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
        import librosa

        # Load audio file
        audio_data, sr = librosa.load(audio_path, sr=SAMPLE_RATE)

        text = _transcribe_audio_array(audio_data, SAMPLE_RATE)
        logger.info(f"Transcription complete: {len(text)} characters")

        return text

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

        text = _transcribe_audio_array(audio_data, sample_rate)

        return text.strip()

    except Exception as e:
        logger.error(f"Segment transcription failed: {e}")
        raise RuntimeError(f"Segment transcription failed: {e}") from e


def is_model_loaded() -> bool:
    """Check if the transcription model is currently loaded."""
    return _model is not None and _processor is not None


def unload_model() -> None:
    """
    Unload the transcription model to free memory.

    Useful for testing or when switching between models.
    """
    global _model, _processor

    with _model_lock:
        if _model is not None:
            logger.info("Unloading MERaLiON model")
            del _model
            del _processor
            _model = None
            _processor = None

            # Force garbage collection
            import gc
            import torch
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()


# =============================================================================
# SINGLISH POST-PROCESSING CORRECTIONS (Agent 3)
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
    # =========================================================================
    # WALAO VARIATIONS (17 patterns)
    # =========================================================================
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

    # =========================================================================
    # VULGAR - CHEEBAI VARIATIONS (10 patterns)
    # =========================================================================
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

    # =========================================================================
    # VULGAR - LANJIAO VARIATIONS (8 patterns)
    # =========================================================================
    'lunch hour': 'lanjiao',
    'lan jiao': 'lanjiao',
    'lan chow': 'lanjiao',
    'lan chiao': 'lanjiao',
    'lun jiao': 'lanjiao',
    'lan chio': 'lanjiao',
    'lunchow': 'lanjiao',
    'lan jio': 'lanjiao',

    # =========================================================================
    # VULGAR - KANINA VARIATIONS (6 patterns)
    # =========================================================================
    'can nina': 'kanina',
    'kar ni na': 'kanina',
    'ka ni na': 'kanina',
    'car nina': 'kanina',
    'knn': 'kanina',
    'k n n': 'kanina',

    # =========================================================================
    # VULGAR - NABEI VARIATIONS (5 patterns)
    # =========================================================================
    'nah bay': 'nabei',
    'na bei': 'nabei',
    'nah bei': 'nabei',
    'na beh': 'nabei',
    'nah beh': 'nabei',

    # =========================================================================
    # PAISEH VARIATIONS (7 patterns)
    # =========================================================================
    'pie say': 'paiseh',
    'pai seh': 'paiseh',
    'pie seh': 'paiseh',
    'pai say': 'paiseh',
    'pie se': 'paiseh',
    'pai se': 'paiseh',
    'paise': 'paiseh',

    # =========================================================================
    # SHIOK VARIATIONS (5 patterns)
    # =========================================================================
    'shook': 'shiok',
    'she ok': 'shiok',
    'shoe ok': 'shiok',
    'shi ok': 'shiok',
    'shio': 'shiok',

    # =========================================================================
    # ALAMAK VARIATIONS (5 patterns)
    # =========================================================================
    'ala mak': 'alamak',
    'allah mak': 'alamak',
    'a la mak': 'alamak',
    'allamak': 'alamak',
    'aller mak': 'alamak',

    # =========================================================================
    # AIYO/AIYAH VARIATIONS (8 patterns)
    # =========================================================================
    'ai yo': 'aiyo',
    'ai yoh': 'aiyo',
    'aiya': 'aiyah',
    'ai ya': 'aiyah',
    'eye yo': 'aiyo',
    'aye yo': 'aiyo',
    'ai yah': 'aiyah',
    'eye yah': 'aiyah',

    # =========================================================================
    # JIALAT VARIATIONS (5 patterns)
    # =========================================================================
    'jia lat': 'jialat',
    'gia lat': 'jialat',
    'jia lut': 'jialat',
    'jee ah lat': 'jialat',
    'gia lut': 'jialat',

    # =========================================================================
    # BOJIO VARIATIONS (5 patterns)
    # =========================================================================
    'bo jio': 'bojio',
    'boh jio': 'bojio',
    'bo gio': 'bojio',
    'never jio': 'bojio',
    'boh gio': 'bojio',

    # =========================================================================
    # SIA VARIATIONS (4 patterns)
    # =========================================================================
    'see ya': 'sia',
    'see ah': 'sia',
    'siah': 'sia',
    'si ah': 'sia',

    # =========================================================================
    # SIAN VARIATIONS (4 patterns)
    # =========================================================================
    'see an': 'sian',
    'si an': 'sian',
    'see en': 'sian',
    'si en': 'sian',

    # =========================================================================
    # OTHER SINGLISH WORDS
    # =========================================================================
    # Kiasu/Kiasi
    'kia su': 'kiasu',
    'key ah su': 'kiasu',
    'kia si': 'kiasi',
    'key ah si': 'kiasi',

    # Bodoh
    'boh doh': 'bodoh',
    'bo doh': 'bodoh',

    # Suaku
    'sua ku': 'suaku',
    'swah ku': 'suaku',

    # Lepak
    'le pak': 'lepak',
    'lay pak': 'lepak',

    # Chope
    'chop': 'chope',

    # Makan
    'ma kan': 'makan',

    # Gostan
    'go stan': 'gostan',
    'go stun': 'gostan',

    # Sibei
    'si bei': 'sibei',
    'see bay': 'sibei',
    'si bay': 'sibei',

    # Atas
    'ah tas': 'atas',
    'ar tas': 'atas',

    # Kaypoh
    'kay poh': 'kaypoh',
    'kae poh': 'kaypoh',
    'kpo': 'kaypoh',

    # Steady
    'steady pom pi pi': 'steady',

    # Goondu
    'goon du': 'goondu',
    'gun du': 'goondu',
}

# Single-word corrections with word boundary checking
# Use for words that could appear as substrings in other words
# e.g., 'la' -> 'lah' but don't affect 'salah' or 'malaysia'
WORD_CORRECTIONS: Dict[str, str] = {
    'la': 'lah',
    'laa': 'lah',
    'laaa': 'lah',
    'low': 'lor',
    'loh': 'lor',
    'leh': 'lah',
    'ler': 'lah',
    'seh': 'sia',
    'mah': 'meh',
    'huh': 'hor',
    'arh': 'ah',
}

# Target Singlish words to count in transcriptions
# Add new words here when you want to track their usage
# Words are matched case-insensitively with word boundary detection
TARGET_WORDS = [
    # =========================================================================
    # VULGAR/EXPLETIVES
    # =========================================================================
    'walao',
    'cheebai',
    'lanjiao',
    'kanina',
    'nabei',

    # =========================================================================
    # PARTICLES (sentence-ending words)
    # =========================================================================
    'lah',
    'lor',
    'sia',
    'meh',
    'leh',
    'hor',
    'ah',
    'one',      # "confirm good one"
    'what',     # "cannot what"
    'lei',
    'ma',

    # =========================================================================
    # EXCLAMATIONS
    # =========================================================================
    'wah',
    'eh',
    'aiyo',
    'aiyah',
    'alamak',

    # =========================================================================
    # COLLOQUIAL EXPRESSIONS
    # =========================================================================
    'can',      # "can or not"
    'cannot',
    'paiseh',
    'shiok',
    'sian',
    'bodoh',
    'kiasu',
    'kiasi',
    'bojio',
    'suaku',
    'lepak',
    'blur',     # "blur like sotong"
    'goondu',

    # =========================================================================
    # ACTIONS/VERBS
    # =========================================================================
    'chope',    # reserve seat
    'kena',     # get (negative)
    'makan',    # eat
    'tahan',    # endure
    'gostan',   # reverse
    'cabut',    # run away
    'sabo',     # sabotage
    'arrow',    # assign task to someone

    # =========================================================================
    # INTENSIFIERS
    # =========================================================================
    'sibei',    # very (vulgar)
    'buay',     # cannot/not
    'jialat',   # serious/terrible

    # =========================================================================
    # FOOD/DRINK (common Singlish terms)
    # =========================================================================
    'kopi',     # coffee
    'teh',      # tea
    'peng',     # iced

    # =========================================================================
    # MISCELLANEOUS
    # =========================================================================
    'atas',     # high class
    'kaypoh',   # busybody
    'steady',   # cool/reliable
    'power',    # impressive
    'liao',     # already/finished
]


def _normalize_for_matching(text: str) -> str:
    """
    Normalize text before correction matching and word counting.

    Handles model output artifacts like bracketed words.

    Args:
        text: Text to normalize

    Returns:
        Normalized text
    """
    if not text:
        return text

    result = text

    # Remove exclamation brackets: !(walao)! -> walao
    result = re.sub(r'!\(([^)]+)\)!', r'\1', result)

    # Remove parentheses around single words: (lah) -> lah
    result = re.sub(r'\(([a-zA-Z]+)\)', r'\1', result)

    # Normalize multiple spaces
    result = re.sub(r'\s+', ' ', result)

    return result.strip()


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

    # Normalize first
    result = _normalize_for_matching(text)

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
    normalized = _normalize_for_matching(text.lower())

    counts: Dict[str, int] = {}

    for word in TARGET_WORDS:
        # Match whole words only with word boundaries
        # Handle punctuation by using a pattern that allows punctuation at boundaries
        pattern = re.compile(r'(?<![a-zA-Z])' + re.escape(word) + r'(?![a-zA-Z])', re.IGNORECASE)
        matches = pattern.findall(normalized)

        if matches:
            counts[word] = len(matches)

    return counts


def process_transcription(text: str) -> Tuple[str, Dict[str, int]]:
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


def get_all_target_words() -> list:
    """Return list of all target words being tracked."""
    return TARGET_WORDS.copy()


def get_corrections_info() -> Dict[str, int]:
    """Return info about corrections dictionary."""
    return {
        "phrase_corrections": len(CORRECTIONS),
        "word_corrections": len(WORD_CORRECTIONS),
        "target_words": len(TARGET_WORDS),
    }
