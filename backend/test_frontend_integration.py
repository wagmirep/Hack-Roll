"""
test_frontend_integration.py - Frontend-Backend Integration Test

PURPOSE:
    Validate complete flow from chunk upload to results retrieval.
    Simulates what the mobile app does to ensure compatibility.

USAGE:
    1. Start backend: cd backend && uvicorn main:app
    2. Start worker: cd backend && python worker.py
    3. Get auth token from Supabase or use existing one
    4. Set token: export AUTH_TOKEN="your-jwt-token"
    5. Run test: python test_frontend_integration.py

REQUIREMENTS:
    - Backend running on localhost:8000
    - Background worker running
    - Valid JWT token from Supabase authentication
    
NOTE:
    Authentication is handled by Supabase, not the backend.
    Login via Supabase Auth, then use the JWT token here.
"""

import requests
import time
import os
import json
from pathlib import Path
from typing import Dict, Optional

# Configuration
API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "")

# Test audio file path (create a small wav file for testing)
TEST_AUDIO_DIR = Path(__file__).parent / "test_audio"


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Print section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")


def print_info(text: str):
    """Print info message"""
    print(f"{Colors.YELLOW}ℹ {text}{Colors.END}")


class IntegrationTest:
    """Integration test runner"""
    
    def __init__(self):
        self.token: Optional[str] = AUTH_TOKEN
        self.session_id: Optional[str] = None
        self.headers: Dict[str, str] = {}
        
    def authenticate(self) -> bool:
        """Verify JWT token works"""
        print_header("Phase 1: Authentication Check")
        
        if not self.token:
            print_error("No AUTH_TOKEN provided!")
            print_info("Please set AUTH_TOKEN environment variable with your Supabase JWT token")
            print_info("Example: export AUTH_TOKEN='eyJhbGc...'")
            return False
        
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            # Test token by calling /auth/me
            response = requests.get(
                f"{API_BASE}/auth/me",
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                username = data.get("profile", {}).get("username", "Unknown")
                print_success(f"Authenticated as: {username}")
                return True
            else:
                print_error(f"Token validation failed: {response.status_code}")
                print_info(f"Response: {response.text}")
                print_info("Make sure your JWT token is valid and not expired")
                return False
                
        except Exception as e:
            print_error(f"Authentication error: {e}")
            print_info("Is the backend running on localhost:8000?")
            return False
    
    def test_session_creation(self) -> bool:
        """Test POST /sessions - Create recording session"""
        print_header("Phase 2: Session Creation")
        
        try:
            response = requests.post(
                f"{API_BASE}/sessions",
                headers=self.headers,
                json={"group_id": None}  # Personal session
            )
            
            if response.status_code == 201:
                data = response.json()
                self.session_id = data["id"]
                
                # Validate response format
                required_fields = ["id", "started_by", "status", "started_at", "progress"]
                missing_fields = [f for f in required_fields if f not in data]
                
                if missing_fields:
                    print_error(f"Missing fields in response: {missing_fields}")
                    return False
                
                # Validate status
                if data["status"] != "recording":
                    print_error(f"Expected status 'recording', got '{data['status']}'")
                    return False
                
                print_success(f"Created session: {self.session_id}")
                print_info(f"Status: {data['status']}, Progress: {data['progress']}%")
                return True
            else:
                print_error(f"Session creation failed: {response.status_code}")
                print_info(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print_error(f"Session creation error: {e}")
            return False
    
    def test_chunk_upload(self, chunk_number: int) -> bool:
        """Test POST /sessions/{id}/chunks - Upload audio chunk"""
        
        try:
            # Use real audio file if available, otherwise generate it
            audio_file_path = TEST_AUDIO_DIR / f"chunk_{chunk_number}.wav"
            
            if not audio_file_path.exists():
                print_info(f"Audio file not found: {audio_file_path}")
                print_info("Run 'python generate_test_audio.py' first to create test audio files")
                print_info("Falling back to minimal WAV file...")
                
                # Create minimal valid WAV file (16kHz, mono, 16-bit, 1 second of silence)
                audio_content = self._create_minimal_wav()
            else:
                # Read real audio file
                with open(audio_file_path, 'rb') as f:
                    audio_content = f.read()
                print_info(f"Using real audio file: {audio_file_path.name} ({len(audio_content)} bytes)")
            
            files = {"file": (f"chunk_{chunk_number}.wav", audio_content, "audio/wav")}
            data = {"duration_seconds": "30.0"}
            
            response = requests.post(
                f"{API_BASE}/sessions/{self.session_id}/chunks",
                headers=self.headers,
                files=files,
                data=data
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Validate response format
                required_fields = ["chunk_number", "uploaded", "storage_path"]
                missing_fields = [f for f in required_fields if f not in result]
                
                if missing_fields:
                    print_error(f"Missing fields in chunk response: {missing_fields}")
                    return False
                
                if result["chunk_number"] != chunk_number:
                    print_error(f"Expected chunk_number {chunk_number}, got {result['chunk_number']}")
                    return False
                
                print_success(f"Uploaded chunk {chunk_number}")
                print_info(f"Storage path: {result['storage_path']}")
                return True
            else:
                print_error(f"Chunk upload failed: {response.status_code}")
                print_info(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print_error(f"Chunk upload error: {e}")
            return False
    
    def _create_minimal_wav(self) -> bytes:
        """
        Create a minimal valid WAV file with correct format.
        
        Format: 16kHz, mono, 16-bit PCM, 1 second of silence
        This matches what the frontend sends and ML pipeline expects.
        
        Returns:
            WAV file as bytes
        """
        import struct
        import io
        
        sample_rate = 16000  # 16 kHz
        channels = 1  # Mono
        bits_per_sample = 16  # 16-bit
        duration = 1  # 1 second
        
        num_samples = sample_rate * duration
        
        # Create WAV file in memory
        wav_buffer = io.BytesIO()
        
        # WAV header
        wav_buffer.write(b'RIFF')
        wav_buffer.write(struct.pack('<I', 36 + num_samples * channels * (bits_per_sample // 8)))
        wav_buffer.write(b'WAVE')
        
        # fmt chunk
        wav_buffer.write(b'fmt ')
        wav_buffer.write(struct.pack('<I', 16))  # fmt chunk size
        wav_buffer.write(struct.pack('<H', 1))   # PCM format
        wav_buffer.write(struct.pack('<H', channels))
        wav_buffer.write(struct.pack('<I', sample_rate))
        wav_buffer.write(struct.pack('<I', sample_rate * channels * (bits_per_sample // 8)))
        wav_buffer.write(struct.pack('<H', channels * (bits_per_sample // 8)))
        wav_buffer.write(struct.pack('<H', bits_per_sample))
        
        # data chunk
        wav_buffer.write(b'data')
        wav_buffer.write(struct.pack('<I', num_samples * channels * (bits_per_sample // 8)))
        
        # Write silence (zeros)
        for _ in range(num_samples):
            wav_buffer.write(struct.pack('<h', 0))
        
        return wav_buffer.getvalue()
    
    def test_session_end(self) -> bool:
        """Test POST /sessions/{id}/end - End recording session"""
        print_header("Phase 4: End Session")
        
        try:
            response = requests.post(
                f"{API_BASE}/sessions/{self.session_id}/end",
                headers=self.headers,
                json={"final_duration_seconds": 90}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Status should now be 'processing'
                if data["status"] not in ["processing", "ready_for_claiming"]:
                    print_error(f"Expected status 'processing', got '{data['status']}'")
                    return False
                
                print_success("Session ended, processing started")
                print_info(f"Status: {data['status']}")
                return True
            else:
                print_error(f"End session failed: {response.status_code}")
                print_info(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print_error(f"End session error: {e}")
            return False
    
    def test_session_status_polling(self, timeout: int = 300) -> bool:
        """Test GET /sessions/{id} - Poll processing status"""
        print_header("Phase 5: Status Polling")
        
        start_time = time.time()
        last_progress = -1
        
        try:
            while time.time() - start_time < timeout:
                response = requests.get(
                    f"{API_BASE}/sessions/{self.session_id}",
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    status = data["status"]
                    progress = data.get("progress", 0)
                    
                    # Print progress updates
                    if progress != last_progress:
                        print_info(f"Status: {status}, Progress: {progress}%")
                        last_progress = progress
                    
                    if status == "ready_for_claiming":
                        print_success("Processing complete!")
                        return True
                    elif status == "failed":
                        error_msg = data.get("error_message", "Unknown error")
                        print_error(f"Processing failed: {error_msg}")
                        return False
                    
                    time.sleep(2)  # Poll every 2 seconds
                else:
                    print_error(f"Status check failed: {response.status_code}")
                    return False
            
            print_error(f"Timeout after {timeout} seconds")
            return False
            
        except Exception as e:
            print_error(f"Status polling error: {e}")
            return False
    
    def test_speakers_list(self) -> bool:
        """Test GET /sessions/{id}/speakers - Get detected speakers"""
        print_header("Phase 6: Retrieve Speakers")
        
        try:
            response = requests.get(
                f"{API_BASE}/sessions/{self.session_id}/speakers",
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "speakers" not in data:
                    print_error("Response missing 'speakers' array")
                    return False
                
                speakers = data["speakers"]
                print_success(f"Found {len(speakers)} speaker(s)")
                
                # Validate each speaker
                for i, speaker in enumerate(speakers):
                    required_fields = ["id", "speaker_label", "segment_count", "word_counts"]
                    missing_fields = [f for f in required_fields if f not in speaker]
                    
                    if missing_fields:
                        print_error(f"Speaker {i} missing fields: {missing_fields}")
                        return False
                    
                    print_info(f"Speaker {speaker['speaker_label']}:")
                    print_info(f"  - Segments: {speaker['segment_count']}")
                    print_info(f"  - Words detected: {len(speaker['word_counts'])}")
                    
                    if speaker['word_counts']:
                        for wc in speaker['word_counts'][:3]:  # Show first 3
                            print_info(f"    • {wc['word']}: {wc['count']}")
                    
                    # Check sample audio URL
                    if speaker.get('sample_audio_url'):
                        print_info(f"  - Sample audio: ✓")
                    else:
                        print_info(f"  - Sample audio: ✗ (may be null for test data)")
                
                return len(speakers) > 0
            else:
                print_error(f"Get speakers failed: {response.status_code}")
                print_info(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print_error(f"Get speakers error: {e}")
            return False
    
    def test_claim_speaker(self, speaker_id: str) -> bool:
        """Test POST /sessions/{id}/claim - Claim speaker identity"""
        print_header("Phase 7: Claim Speaker")
        
        try:
            response = requests.post(
                f"{API_BASE}/sessions/{self.session_id}/claim",
                headers=self.headers,
                json={
                    "speaker_id": speaker_id,
                    "claim_type": "self"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                print_success("Speaker claimed successfully")
                print_info(f"Message: {data.get('message', 'N/A')}")
                return True
            else:
                print_error(f"Claim speaker failed: {response.status_code}")
                print_info(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print_error(f"Claim speaker error: {e}")
            return False
    
    def test_session_results(self) -> bool:
        """Test GET /sessions/{id}/results - Get final results"""
        print_header("Phase 8: Retrieve Results")
        
        try:
            response = requests.get(
                f"{API_BASE}/sessions/{self.session_id}/results",
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                
                required_fields = ["session_id", "status", "users", "all_claimed"]
                missing_fields = [f for f in required_fields if f not in data]
                
                if missing_fields:
                    print_error(f"Results missing fields: {missing_fields}")
                    return False
                
                print_success("Retrieved results")
                print_info(f"Users: {len(data['users'])}")
                print_info(f"All claimed: {data['all_claimed']}")
                
                for user in data['users']:
                    username = user.get('username') or user.get('guest_name', 'Unknown')
                    print_info(f"  - {username}: {user['total_words']} total words")
                
                return True
            else:
                print_error(f"Get results failed: {response.status_code}")
                print_info(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print_error(f"Get results error: {e}")
            return False
    
    def validate_audio_format(self) -> bool:
        """Validate test audio files match expected format"""
        print_header("Phase 0: Audio Format Validation")
        
        # Check if test audio directory exists
        if not TEST_AUDIO_DIR.exists():
            print_info(f"Test audio directory not found: {TEST_AUDIO_DIR}")
            print_info("Will use minimal WAV files (silence)")
            print_info("For better testing, run: python generate_test_audio.py")
            return True
        
        # Check for audio files
        audio_files = list(TEST_AUDIO_DIR.glob("chunk_*.wav"))
        if not audio_files:
            print_info("No chunk audio files found")
            print_info("Will use minimal WAV files (silence)")
            return True
        
        print_success(f"Found {len(audio_files)} test audio files")
        
        # Validate format of first file
        try:
            import wave
            test_file = audio_files[0]
            
            with wave.open(str(test_file), 'r') as wav:
                channels = wav.getnchannels()
                sample_width = wav.getsampwidth()
                framerate = wav.getframerate()
                
                print_info(f"Audio format: {framerate}Hz, {channels}ch, {sample_width*8}-bit")
                
                # Validate against expected format
                expected_rate = 16000
                expected_channels = 1
                expected_width = 2  # 16-bit = 2 bytes
                
                if framerate != expected_rate:
                    print_error(f"Wrong sample rate: {framerate} (expected {expected_rate})")
                    return False
                
                if channels != expected_channels:
                    print_error(f"Wrong channels: {channels} (expected {expected_channels})")
                    return False
                
                if sample_width != expected_width:
                    print_error(f"Wrong bit depth: {sample_width*8} (expected {expected_width*8})")
                    return False
                
                print_success("✓ Audio format matches frontend/ML pipeline requirements")
                print_info("  - 16000 Hz (16 kHz)")
                print_info("  - Mono (1 channel)")
                print_info("  - 16-bit PCM")
                return True
                
        except Exception as e:
            print_error(f"Audio validation error: {e}")
            print_info("Will continue with minimal WAV files")
            return True
    
    def run_full_test(self) -> bool:
        """Run complete integration test"""
        print_header("🚀 LahStats Frontend-Backend Integration Test")
        print_info(f"API Base: {API_BASE}")
        print_info(f"Auth Token: {'✓ Provided' if AUTH_TOKEN else '✗ Missing'}")
        
        # Phase 0: Validate audio format
        self.validate_audio_format()
        
        # Phase 1: Authentication check
        if not self.authenticate():
            return False
        
        # Phase 2: Create session
        if not self.test_session_creation():
            return False
        
        # Phase 3: Upload chunks
        print_header("Phase 3: Upload Audio Chunks")
        for i in range(1, 4):  # Upload 3 chunks
            if not self.test_chunk_upload(i):
                return False
            time.sleep(0.5)  # Brief delay between uploads
        
        # Phase 4: End session
        if not self.test_session_end():
            return False
        
        # Phase 5: Poll status
        print_info("⏳ Waiting for processing (this may take 1-2 minutes)...")
        if not self.test_session_status_polling():
            return False
        
        # Phase 6: Get speakers
        if not self.test_speakers_list():
            return False
        
        # Phase 7: Claim first speaker (if any)
        try:
            response = requests.get(
                f"{API_BASE}/sessions/{self.session_id}/speakers",
                headers=self.headers
            )
            if response.status_code == 200:
                speakers = response.json()["speakers"]
                if speakers:
                    first_speaker_id = speakers[0]["id"]
                    if not self.test_claim_speaker(first_speaker_id):
                        return False
                else:
                    print_info("No speakers to claim (test data may not have speech)")
        except:
            pass
        
        # Phase 8: Get results
        if not self.test_session_results():
            return False
        
        # Success!
        print_header("✅ All Tests Passed!")
        print_success("Frontend-Backend integration is working correctly")
        return True


def main():
    """Main entry point"""
    test = IntegrationTest()
    success = test.run_full_test()
    
    if success:
        print(f"\n{Colors.GREEN}{Colors.BOLD}{'='*70}")
        print("SUCCESS: Integration test passed!")
        print(f"{'='*70}{Colors.END}\n")
        exit(0)
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}{'='*70}")
        print("FAILED: Integration test failed!")
        print(f"{'='*70}{Colors.END}\n")
        exit(1)


if __name__ == "__main__":
    main()
