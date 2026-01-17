"""
services/transcription.py - MERaLiON Transcription Service

Wrapper service for MERaLiON ASR speech-to-text model.
Transcribes Singlish audio segments to text.

OPTIMIZATION: Uses MERaLiON-2-3B (lightweight) instead of 10B for faster CPU inference.
- 3B params vs 10B = ~3x smaller, ~3-4x faster on CPU
- Singlish WER: 18% (vs 12% for 10B-ASR) - acceptable for hackathon
- Added INT8 dynamic quantization for additional CPU speedup
"""

import os
import re
import logging
from typing import Dict, Optional, Tuple
from threading import Lock

logger = logging.getLogger(__name__)

# =============================================================================
# MODEL CONFIGURATION
# =============================================================================

# Use lightweight 3B model for faster CPU inference
# Trade-off: ~6% more errors but 3-4x faster
MODEL_NAME = "MERaLiON/MERaLiON-2-3B"
SAMPLE_RATE = 16000  # Expected input sample rate

# CPU Optimization settings
ENABLE_QUANTIZATION = True  # INT8 dynamic quantization for CPU
ENABLE_TORCH_COMPILE = True  # torch.compile() for faster inference
NUM_THREADS = None  # None = auto-detect, or set specific number

# =============================================================================
# MODEL SINGLETON
# =============================================================================

_model = None
_processor = None
_model_lock = Lock()

# Backward compatibility alias for tests
_transcriber = None  # Will be set to (model, processor) tuple when loaded


def _optimize_for_cpu(model):
    """
    Apply CPU-specific optimizations to the model.

    - Dynamic INT8 quantization (2x speedup on CPU)
    - torch.compile() if available (10-30% speedup)
    - Thread optimization
    """
    import torch

    # Set optimal thread count
    if NUM_THREADS:
        torch.set_num_threads(NUM_THREADS)
    else:
        # Use all available cores
        import multiprocessing
        cores = multiprocessing.cpu_count()
        torch.set_num_threads(cores)
        logger.info(f"Set torch threads to {cores}")

    # Enable torch inference optimizations
    torch.set_grad_enabled(False)

    # Apply INT8 dynamic quantization for CPU
    if ENABLE_QUANTIZATION:
        try:
            logger.info("Applying INT8 dynamic quantization for CPU...")
            model = torch.quantization.quantize_dynamic(
                model,
                {torch.nn.Linear},  # Quantize linear layers
                dtype=torch.qint8
            )
            logger.info("INT8 quantization applied successfully")
        except Exception as e:
            logger.warning(f"Quantization failed, using unquantized model: {e}")

    # Apply torch.compile() for additional speedup
    if ENABLE_TORCH_COMPILE:
        try:
            if hasattr(torch, 'compile'):
                logger.info("Applying torch.compile() optimization...")
                model = torch.compile(model, mode="reduce-overhead")
                logger.info("torch.compile() applied successfully")
        except Exception as e:
            logger.warning(f"torch.compile() failed, using uncompiled model: {e}")

    return model


def get_transcriber():
    """
    Get or create the MERaLiON model and processor instances.

    Uses singleton pattern to avoid reloading the model.
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

            # Load processor
            _processor = AutoProcessor.from_pretrained(
                MODEL_NAME,
                trust_remote_code=True
            )

            # Check for GPU
            if torch.cuda.is_available():
                total_mem_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
                logger.info(f"GPU available: {total_mem_gb:.1f}GB")

                # 3B model fits easily on most GPUs
                _model = AutoModelForSpeechSeq2Seq.from_pretrained(
                    MODEL_NAME,
                    torch_dtype=torch.float16,
                    trust_remote_code=True,
                    attn_implementation="eager",
                ).to("cuda")
                logger.info("Model loaded on GPU (float16)")
            else:
                logger.info("No GPU available, loading for CPU inference...")

                # Load in float32 for CPU (required for quantization)
                _model = AutoModelForSpeechSeq2Seq.from_pretrained(
                    MODEL_NAME,
                    torch_dtype=torch.float32,
                    trust_remote_code=True,
                    attn_implementation="eager",
                )

                # Apply CPU optimizations
                _model = _optimize_for_cpu(_model)
                logger.info("Model loaded on CPU with optimizations")

            # Set to eval mode
            _model.eval()

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

    # MERaLiON uses a chat-style interface with prompt template
    prompt_template = "Instruction: {query} \nFollow the text instruction based on the following audio: <SpeechHere>"
    transcribe_prompt = "Please transcribe this speech."

    conversation = [[{"role": "user", "content": prompt_template.format(query=transcribe_prompt)}]]
    chat_prompt = processor.tokenizer.apply_chat_template(
        conversation=conversation,
        tokenize=False,
        add_generation_prompt=True
    )

    # Process audio through processor
    inputs = processor(text=chat_prompt, audios=[audio_data])

    # Move inputs to model device and dtype
    device = next(model.parameters()).device
    dtype = next(model.parameters()).dtype

    def move_to_device(v):
        if not hasattr(v, 'to'):
            return v
        v = v.to(device)
        # Only convert floating point tensors to model dtype
        if v.is_floating_point() and dtype in [torch.float16, torch.bfloat16]:
            v = v.to(dtype)
        return v

    inputs = {k: move_to_device(v) for k, v in inputs.items()}

    # Generate transcription with inference mode for speed
    with torch.inference_mode():
        generated_ids = model.generate(
            **inputs,
            max_new_tokens=256,
            do_sample=False,  # Greedy decoding is faster
        )

    # Decode - skip the input tokens
    input_len = inputs['input_ids'].size(1)
    generated_ids = generated_ids[:, input_len:]
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
        import time

        # Load audio file
        start = time.time()
        audio_data, sr = librosa.load(audio_path, sr=SAMPLE_RATE)
        load_time = time.time() - start

        # Transcribe
        start = time.time()
        text = _transcribe_audio_array(audio_data, SAMPLE_RATE)
        transcribe_time = time.time() - start

        audio_duration = len(audio_data) / SAMPLE_RATE
        logger.info(f"Transcription complete: {len(text)} chars")
        logger.info(f"  Audio: {audio_duration:.1f}s, Load: {load_time:.1f}s, Transcribe: {transcribe_time:.1f}s")
        logger.info(f"  Real-time factor: {transcribe_time / audio_duration:.2f}x")

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
    # Check both new API (_model, _processor) and legacy _transcriber
    return (_model is not None and _processor is not None) or _transcriber is not None


def unload_model() -> None:
    """
    Unload the transcription model to free memory.

    Useful for testing or when switching between models.
    """
    global _model, _processor, _transcriber

    with _model_lock:
        if _model is not None or _transcriber is not None:
            logger.info("Unloading MERaLiON model")
            if _model is not None:
                del _model
            if _processor is not None:
                del _processor
            _model = None
            _processor = None
            _transcriber = None

            # Force garbage collection
            import gc
            import torch
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()


def get_model_info() -> Dict[str, str]:
    """Return info about the loaded model."""
    return {
        "model_name": MODEL_NAME,
        "quantization_enabled": ENABLE_QUANTIZATION,
        "torch_compile_enabled": ENABLE_TORCH_COMPILE,
        "is_loaded": is_model_loaded(),
    }


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
    'leh': 'lah',
    'ler': 'lah',
    'seh': 'sia',
    'mah': 'meh',
    'huh': 'hor',
    'arh': 'ah',
    'shio': 'shiok',  # Needs word boundary to avoid shiok → shiokk
}

# Target Singlish words to count
TARGET_WORDS = [
    # Vulgar
    'walao', 'cheebai', 'lanjiao', 'kanina', 'nabei',
    # Particles
    'lah', 'lor', 'sia', 'meh', 'leh', 'hor', 'ah', 'one', 'what', 'lei', 'ma',
    # Exclamations
    'wah', 'eh', 'aiyo', 'aiyah', 'alamak',
    # Colloquial
    'can', 'cannot', 'paiseh', 'shiok', 'sian', 'bodoh', 'kiasu', 'kiasi',
    'bojio', 'suaku', 'lepak', 'blur', 'goondu',
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
