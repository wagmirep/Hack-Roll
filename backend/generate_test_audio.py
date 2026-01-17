"""
generate_test_audio.py - Generate Test Audio Files

PURPOSE:
    Create realistic test audio files with the exact format the frontend sends
    and the ML pipeline expects.

AUDIO SPECIFICATIONS:
    - Format: WAV (PCM)
    - Sample Rate: 16000 Hz (16 kHz)
    - Channels: 1 (mono)
    - Bit Depth: 16-bit
    - Duration: 30 seconds per chunk (configurable)

USAGE:
    python generate_test_audio.py
"""

import numpy as np
import wave
import struct
from pathlib import Path

# Audio specifications (matches frontend and ML pipeline)
SAMPLE_RATE = 16000  # 16 kHz
CHANNELS = 1  # Mono
SAMPLE_WIDTH = 2  # 16-bit = 2 bytes
DURATION = 30  # seconds per chunk


def generate_sine_wave(frequency: float, duration: float, sample_rate: int = SAMPLE_RATE) -> np.ndarray:
    """
    Generate a sine wave tone.
    
    Args:
        frequency: Frequency in Hz
        duration: Duration in seconds
        sample_rate: Sample rate in Hz
        
    Returns:
        numpy array of audio samples
    """
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    wave = np.sin(2 * np.pi * frequency * t)
    
    # Normalize to 16-bit range
    wave = wave * 32767
    return wave.astype(np.int16)


def generate_speech_like_audio(duration: float, sample_rate: int = SAMPLE_RATE) -> np.ndarray:
    """
    Generate audio that resembles speech patterns.
    Uses multiple frequencies and amplitude modulation to simulate speech.
    
    Args:
        duration: Duration in seconds
        sample_rate: Sample rate in Hz
        
    Returns:
        numpy array of audio samples
    """
    num_samples = int(sample_rate * duration)
    t = np.linspace(0, duration, num_samples, False)
    
    # Create speech-like pattern with multiple harmonics
    # Fundamental frequency around 120-200 Hz (typical human voice)
    fundamental = 150
    
    # Add harmonics (typical of human voice)
    wave = (
        0.5 * np.sin(2 * np.pi * fundamental * t) +
        0.3 * np.sin(2 * np.pi * (2 * fundamental) * t) +
        0.2 * np.sin(2 * np.pi * (3 * fundamental) * t) +
        0.1 * np.sin(2 * np.pi * (4 * fundamental) * t)
    )
    
    # Add amplitude modulation to simulate speech rhythm (3-5 Hz)
    modulation = 0.5 + 0.5 * np.sin(2 * np.pi * 4 * t)
    wave = wave * modulation
    
    # Add some noise for realism
    noise = np.random.normal(0, 0.02, num_samples)
    wave = wave + noise
    
    # Normalize to 16-bit range
    wave = wave / np.max(np.abs(wave))  # Normalize to [-1, 1]
    wave = wave * 32767 * 0.8  # Scale to 80% of max to avoid clipping
    
    return wave.astype(np.int16)


def save_wav_file(filename: str, audio_data: np.ndarray, sample_rate: int = SAMPLE_RATE):
    """
    Save audio data as WAV file with correct format.
    
    Args:
        filename: Output filename
        audio_data: Audio samples as numpy array
        sample_rate: Sample rate in Hz
    """
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(CHANNELS)
        wav_file.setsampwidth(SAMPLE_WIDTH)
        wav_file.setframerate(sample_rate)
        
        # Write audio data
        for sample in audio_data:
            wav_file.writeframes(struct.pack('<h', sample))
    
    print(f"✓ Created: {filename}")
    print(f"  - Duration: {len(audio_data) / sample_rate:.1f}s")
    print(f"  - Sample Rate: {sample_rate} Hz")
    print(f"  - Channels: {CHANNELS} (mono)")
    print(f"  - Bit Depth: {SAMPLE_WIDTH * 8}-bit")
    print(f"  - File Size: {Path(filename).stat().st_size / 1024:.1f} KB")


def create_test_audio_files(output_dir: str = "test_audio"):
    """
    Create a set of test audio files for integration testing.
    
    Args:
        output_dir: Directory to save test files
    """
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    print("=" * 70)
    print("Generating Test Audio Files")
    print("=" * 70)
    print(f"\nOutput directory: {output_path.absolute()}\n")
    
    # Generate 3 chunks of 30 seconds each (simulating 90-second recording)
    for i in range(1, 4):
        print(f"\n--- Chunk {i} ---")
        
        # Generate speech-like audio
        audio_data = generate_speech_like_audio(DURATION, SAMPLE_RATE)
        
        # Save as WAV
        filename = output_path / f"chunk_{i}.wav"
        save_wav_file(str(filename), audio_data, SAMPLE_RATE)
    
    # Also create a single longer file for testing
    print(f"\n--- Full Recording ---")
    full_audio = generate_speech_like_audio(DURATION * 3, SAMPLE_RATE)
    save_wav_file(str(output_path / "full_recording.wav"), full_audio, SAMPLE_RATE)
    
    print("\n" + "=" * 70)
    print("✓ All test audio files created successfully!")
    print("=" * 70)
    print(f"\nFiles created in: {output_path.absolute()}")
    print("\nYou can now use these files for integration testing.")
    print("They match the exact format the frontend sends:")
    print("  - 16000 Hz sample rate")
    print("  - Mono (1 channel)")
    print("  - 16-bit PCM WAV")
    print("\nNote: These are synthetic audio files for testing.")
    print("For real speech detection, use actual voice recordings.")


def validate_audio_format(filename: str) -> bool:
    """
    Validate that an audio file matches expected format.
    
    Args:
        filename: Path to WAV file
        
    Returns:
        True if format is correct, False otherwise
    """
    try:
        with wave.open(filename, 'r') as wav_file:
            channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            framerate = wav_file.getframerate()
            
            print(f"\nValidating: {filename}")
            print(f"  Channels: {channels} (expected: {CHANNELS})")
            print(f"  Sample Width: {sample_width} bytes (expected: {SAMPLE_WIDTH})")
            print(f"  Frame Rate: {framerate} Hz (expected: {SAMPLE_RATE})")
            
            if channels != CHANNELS:
                print(f"  ✗ FAIL: Wrong number of channels")
                return False
            
            if sample_width != SAMPLE_WIDTH:
                print(f"  ✗ FAIL: Wrong sample width")
                return False
            
            if framerate != SAMPLE_RATE:
                print(f"  ✗ FAIL: Wrong sample rate")
                return False
            
            print(f"  ✓ PASS: Format is correct")
            return True
            
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        return False


if __name__ == "__main__":
    # Create test audio files
    create_test_audio_files()
    
    # Validate the created files
    print("\n" + "=" * 70)
    print("Validating Created Files")
    print("=" * 70)
    
    test_dir = Path("test_audio")
    for wav_file in sorted(test_dir.glob("*.wav")):
        validate_audio_format(str(wav_file))
