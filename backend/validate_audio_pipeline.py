"""
validate_audio_pipeline.py - Validate Audio Format Compatibility

PURPOSE:
    Ensure audio format compatibility across the entire pipeline:
    1. Frontend audio recording format
    2. Backend API upload handling
    3. Supabase Storage format
    4. ML pipeline processing requirements

USAGE:
    python validate_audio_pipeline.py
"""

import wave
import json
from pathlib import Path
from typing import Dict, List, Tuple

# Expected audio specifications
EXPECTED_FORMAT = {
    "sample_rate": 16000,  # 16 kHz
    "channels": 1,  # Mono
    "sample_width": 2,  # 16-bit = 2 bytes
    "format": "PCM",
    "container": "WAV"
}


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")


def print_success(text: str):
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_error(text: str):
    print(f"{Colors.RED}✗ {text}{Colors.END}")


def print_info(text: str):
    print(f"{Colors.YELLOW}ℹ {text}{Colors.END}")


def validate_wav_format(file_path: Path) -> Tuple[bool, Dict]:
    """
    Validate a WAV file matches expected format.
    
    Returns:
        (is_valid, format_info)
    """
    try:
        with wave.open(str(file_path), 'r') as wav:
            format_info = {
                "sample_rate": wav.getframerate(),
                "channels": wav.getnchannels(),
                "sample_width": wav.getsampwidth(),
                "num_frames": wav.getnframes(),
                "duration": wav.getnframes() / wav.getframerate()
            }
            
            # Check each requirement
            is_valid = True
            issues = []
            
            if format_info["sample_rate"] != EXPECTED_FORMAT["sample_rate"]:
                is_valid = False
                issues.append(f"Sample rate: {format_info['sample_rate']} (expected {EXPECTED_FORMAT['sample_rate']})")
            
            if format_info["channels"] != EXPECTED_FORMAT["channels"]:
                is_valid = False
                issues.append(f"Channels: {format_info['channels']} (expected {EXPECTED_FORMAT['channels']})")
            
            if format_info["sample_width"] != EXPECTED_FORMAT["sample_width"]:
                is_valid = False
                issues.append(f"Bit depth: {format_info['sample_width']*8}-bit (expected {EXPECTED_FORMAT['sample_width']*8}-bit)")
            
            format_info["is_valid"] = is_valid
            format_info["issues"] = issues
            
            return is_valid, format_info
            
    except Exception as e:
        return False, {"error": str(e)}


def check_frontend_config():
    """Check frontend audio recording configuration"""
    print_header("1. Frontend Audio Configuration")
    
    mobile_config_path = Path(__file__).parent.parent / "mobile" / "src" / "hooks" / "useRecording.ts"
    
    if not mobile_config_path.exists():
        print_error(f"Frontend config not found: {mobile_config_path}")
        return False
    
    print_success(f"Found frontend config: {mobile_config_path.name}")
    
    # Read and check configuration
    with open(mobile_config_path, 'r') as f:
        content = f.read()
    
    checks = {
        "sampleRate: 16000": "✓ Sample rate: 16000 Hz",
        "numberOfChannels: 1": "✓ Channels: 1 (mono)",
        "linearPCMBitDepth: 16": "✓ Bit depth: 16-bit",
        "extension: '.wav'": "✓ Format: WAV"
    }
    
    all_found = True
    for check, message in checks.items():
        if check in content:
            print_success(message)
        else:
            print_error(f"Missing: {check}")
            all_found = False
    
    if all_found:
        print_success("\n✓ Frontend configuration matches ML pipeline requirements")
    else:
        print_error("\n✗ Frontend configuration has issues")
    
    return all_found


def check_backend_processing():
    """Check backend processor configuration"""
    print_header("2. Backend Processing Configuration")
    
    # Check transcription service
    transcription_path = Path(__file__).parent / "services" / "transcription.py"
    if not transcription_path.exists():
        print_error(f"Transcription service not found: {transcription_path}")
        return False
    
    print_success(f"Found transcription service: {transcription_path.name}")
    
    with open(transcription_path, 'r') as f:
        content = f.read()
    
    if "SAMPLE_RATE = 16000" in content:
        print_success("✓ Transcription expects 16000 Hz")
    else:
        print_error("✗ Transcription sample rate mismatch")
        return False
    
    # Check processor
    processor_path = Path(__file__).parent / "processor.py"
    if not processor_path.exists():
        print_error(f"Processor not found: {processor_path}")
        return False
    
    print_success(f"Found processor: {processor_path.name}")
    
    with open(processor_path, 'r') as f:
        content = f.read()
    
    if "set_frame_rate(SAMPLE_RATE).set_channels(1)" in content:
        print_success("✓ Processor converts to 16kHz mono")
    else:
        print_error("✗ Processor audio conversion not found")
        return False
    
    print_success("\n✓ Backend processing matches expected format")
    return True


def check_test_audio_files():
    """Check test audio files"""
    print_header("3. Test Audio Files")
    
    test_audio_dir = Path(__file__).parent / "test_audio"
    
    if not test_audio_dir.exists():
        print_info(f"Test audio directory not found: {test_audio_dir}")
        print_info("Run 'python generate_test_audio.py' to create test files")
        return False
    
    print_success(f"Found test audio directory: {test_audio_dir}")
    
    # Find all WAV files
    wav_files = list(test_audio_dir.glob("*.wav"))
    
    if not wav_files:
        print_error("No WAV files found in test_audio directory")
        return False
    
    print_success(f"Found {len(wav_files)} WAV files")
    
    # Validate each file
    all_valid = True
    for wav_file in sorted(wav_files):
        is_valid, format_info = validate_wav_format(wav_file)
        
        if is_valid:
            print_success(f"✓ {wav_file.name}")
            print_info(f"  {format_info['sample_rate']}Hz, {format_info['channels']}ch, "
                      f"{format_info['sample_width']*8}-bit, {format_info['duration']:.1f}s")
        else:
            print_error(f"✗ {wav_file.name}")
            if "error" in format_info:
                print_error(f"  Error: {format_info['error']}")
            else:
                for issue in format_info.get("issues", []):
                    print_error(f"  {issue}")
            all_valid = False
    
    if all_valid:
        print_success("\n✓ All test audio files have correct format")
    else:
        print_error("\n✗ Some test audio files have incorrect format")
    
    return all_valid


def check_database_schema():
    """Check database schema for audio storage"""
    print_header("4. Database Schema")
    
    models_path = Path(__file__).parent / "models.py"
    
    if not models_path.exists():
        print_error(f"Models file not found: {models_path}")
        return False
    
    print_success(f"Found models: {models_path.name}")
    
    with open(models_path, 'r') as f:
        content = f.read()
    
    # Check AudioChunk model
    checks = [
        ("class AudioChunk", "AudioChunk model"),
        ("storage_path = Column(Text", "storage_path column"),
        ("duration_seconds = Column(DECIMAL", "duration_seconds column"),
        ("chunk_number = Column(Integer", "chunk_number column")
    ]
    
    all_found = True
    for check, description in checks:
        if check in content:
            print_success(f"✓ {description} exists")
        else:
            print_error(f"✗ {description} not found")
            all_found = False
    
    if all_found:
        print_success("\n✓ Database schema supports audio chunk storage")
    else:
        print_error("\n✗ Database schema has issues")
    
    return all_found


def generate_compatibility_report():
    """Generate comprehensive compatibility report"""
    print_header("Audio Pipeline Compatibility Report")
    
    results = {
        "frontend_config": check_frontend_config(),
        "backend_processing": check_backend_processing(),
        "test_audio_files": check_test_audio_files(),
        "database_schema": check_database_schema()
    }
    
    print_header("Summary")
    
    for component, is_valid in results.items():
        component_name = component.replace("_", " ").title()
        if is_valid:
            print_success(f"✓ {component_name}: PASS")
        else:
            print_error(f"✗ {component_name}: FAIL")
    
    all_valid = all(results.values())
    
    print("\n" + "=" * 70)
    if all_valid:
        print(f"{Colors.GREEN}{Colors.BOLD}✓ ALL CHECKS PASSED{Colors.END}")
        print(f"{Colors.GREEN}Audio format is compatible across the entire pipeline!{Colors.END}")
    else:
        print(f"{Colors.RED}{Colors.BOLD}✗ SOME CHECKS FAILED{Colors.END}")
        print(f"{Colors.RED}Please fix the issues above before proceeding.{Colors.END}")
    print("=" * 70 + "\n")
    
    # Print expected format
    print_header("Expected Audio Format")
    print(f"Sample Rate:  {EXPECTED_FORMAT['sample_rate']} Hz (16 kHz)")
    print(f"Channels:     {EXPECTED_FORMAT['channels']} (mono)")
    print(f"Bit Depth:    {EXPECTED_FORMAT['sample_width'] * 8}-bit")
    print(f"Format:       {EXPECTED_FORMAT['format']}")
    print(f"Container:    {EXPECTED_FORMAT['container']}")
    print("\nThis format is used by:")
    print("  - Frontend (mobile app recording)")
    print("  - Backend (API upload)")
    print("  - ML Pipeline (diarization + transcription)")
    print("  - Supabase Storage")
    
    return all_valid


if __name__ == "__main__":
    success = generate_compatibility_report()
    exit(0 if success else 1)
