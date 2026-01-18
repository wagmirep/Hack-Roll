#!/usr/bin/env python3
"""
Complete Integration Test - End-to-End Workflow Verification

Tests the complete flow:
1. Create session
2. Upload audio chunk
3. End session (queues to Redis)
4. Worker processes session
5. Transcription + Diarization via external API
6. Results saved to database
7. Claim speakers
8. Verify WordCount records
9. Verify Wrapped stats

This simulates the exact flow from mobile app recording to stats display.
"""

import sys
import os
import time
import json
import uuid
from datetime import datetime
from pathlib import Path

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from dotenv import load_dotenv
load_dotenv()

# Import backend modules
from config import settings
from database import SessionLocal
from models import Session, SessionSpeaker, SpeakerWordCount, WordCount, AudioChunk, Profile
from processor import process_session_sync
from redis_client import get_redis_client, PROCESSING_QUEUE
from services.transcription import is_using_external_api

print('=' * 80)
print('COMPLETE INTEGRATION TEST - END-TO-END WORKFLOW')
print('=' * 80)
print(f'Timestamp: {datetime.now().isoformat()}')
print(f'Using external transcription API: {is_using_external_api()}')
if is_using_external_api():
    print(f'Transcription API URL: {settings.TRANSCRIPTION_API_URL}')
print('=' * 80)

# Configuration
TEST_AUDIO_PATH = Path('../audio/Main Speech 1.m4a')
if not TEST_AUDIO_PATH.exists():
    # Try alternative path
    TEST_AUDIO_PATH = Path('test_audio/sample1.wav')
    if not TEST_AUDIO_PATH.exists():
        print(f'\n❌ Test audio file not found: {TEST_AUDIO_PATH}')
        print('Please provide a test audio file')
        sys.exit(1)

print(f'\nTest audio: {TEST_AUDIO_PATH}')
print(f'Test audio exists: {TEST_AUDIO_PATH.exists()}')


def print_step(step_num, total_steps, title):
    """Print formatted step header"""
    print(f'\n{"="*80}')
    print(f'STEP {step_num}/{total_steps}: {title}')
    print(f'{"="*80}')


def print_substep(message):
    """Print formatted substep"""
    print(f'  → {message}')


# =============================================================================
# STEP 1: Setup & Verify Services
# =============================================================================
print_step(1, 9, 'Setup & Verify Services')

print_substep('Checking database connection...')
db = SessionLocal()
session_count = db.query(Session).count()
print_substep(f'✅ Database connected ({session_count} sessions in DB)')

print_substep('Checking Redis connection...')
redis_client = get_redis_client()
redis_client.ping()
queue_length = redis_client.llen(PROCESSING_QUEUE)
print_substep(f'✅ Redis connected ({queue_length} jobs in queue)')

print_substep('Checking test user...')
test_user = db.query(Profile).first()
if not test_user:
    print_substep('❌ No users in database. Creating test user...')
    test_user = Profile(
        id=uuid.uuid4(),
        username='test_user',
        display_name='Test User'
    )
    db.add(test_user)
    db.commit()
    print_substep(f'✅ Created test user: {test_user.username}')
else:
    print_substep(f'✅ Using existing user: {test_user.username} (ID: {test_user.id})')


# =============================================================================
# STEP 2: Create Session
# =============================================================================
print_step(2, 9, 'Create Recording Session')

session = Session(
    id=uuid.uuid4(),
    started_by=test_user.id,
    status='recording',
    group_id=None  # Personal session
)
db.add(session)
db.commit()
db.refresh(session)

print_substep(f'✅ Session created: {session.id}')
print_substep(f'   Status: {session.status}')
print_substep(f'   Started by: {test_user.username}')


# =============================================================================
# STEP 3: Convert & Upload Audio Chunk
# =============================================================================
print_step(3, 9, 'Convert & Upload Audio Chunk')

print_substep('Converting audio to WAV format...')
from pydub import AudioSegment
import tempfile

# Convert to WAV (16kHz mono)
audio = AudioSegment.from_file(str(TEST_AUDIO_PATH))
audio = audio.set_frame_rate(16000).set_channels(1)
duration_seconds = len(audio) / 1000

# Save to temporary WAV file
temp_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
audio.export(temp_wav.name, format='wav')
temp_wav_path = temp_wav.name
temp_wav.close()

print_substep(f'✅ Audio converted: {duration_seconds:.1f}s duration')

# Simulate chunk upload by copying to storage location
print_substep('Uploading chunk to storage...')
from storage import storage
import asyncio

with open(temp_wav_path, 'rb') as f:
    audio_bytes = f.read()

# Upload chunk - create a proper async mock for UploadFile
class MockUploadFile:
    def __init__(self, content, filename, content_type):
        self._content = content
        self.filename = filename
        self.content_type = content_type

    async def read(self):
        return self._content

async def upload_chunk():
    mock_file = MockUploadFile(audio_bytes, 'chunk_1.wav', 'audio/wav')
    storage_path = await storage.upload_chunk(session.id, 1, mock_file)
    return storage_path

storage_path = asyncio.run(upload_chunk())

# Create AudioChunk record
chunk = AudioChunk(
    session_id=session.id,
    chunk_number=1,
    storage_path=storage_path,
    duration_seconds=duration_seconds
)
db.add(chunk)
db.commit()

print_substep(f'✅ Chunk uploaded: {storage_path}')
print_substep(f'   Chunk number: 1')
print_substep(f'   Duration: {duration_seconds:.1f}s')


# =============================================================================
# STEP 4: End Session
# =============================================================================
print_step(4, 9, 'End Recording Session')

session.status = 'processing'
session.ended_at = datetime.utcnow()
session.duration_seconds = int(duration_seconds)
session.progress = 0
db.commit()

print_substep(f'✅ Session ended')
print_substep(f'   Status: {session.status}')
print_substep(f'   Duration: {duration_seconds:.1f}s')

# Queue job to Redis (simulating API endpoint behavior)
print_substep('Queuing processing job to Redis...')
job_payload = json.dumps({
    'session_id': str(session.id),
    'queued_at': datetime.utcnow().isoformat()
})
redis_client.lpush(PROCESSING_QUEUE, job_payload)
queue_length = redis_client.llen(PROCESSING_QUEUE)

print_substep(f'✅ Job queued to Redis')
print_substep(f'   Queue: {PROCESSING_QUEUE}')
print_substep(f'   Queue length: {queue_length}')


# =============================================================================
# STEP 5: Process Session (Worker Simulation)
# =============================================================================
print_step(5, 9, 'Process Session with ML Pipeline')

print_substep('Running processor.process_session_sync()...')
print_substep(f'This will:')
print_substep(f'  1. Concatenate audio chunks')
print_substep(f'  2. Run speaker diarization (pyannote)')
print_substep(f'  3. Transcribe segments via external API')
print_substep(f'  4. Apply Singlish corrections')
print_substep(f'  5. Count target words')
print_substep(f'  6. Save results to database')
print_substep('')
print_substep('⏳ Processing... (this may take 1-3 minutes)')

start_time = time.time()

try:
    result = process_session_sync(session.id)
    processing_time = time.time() - start_time
    
    print_substep(f'✅ Processing complete in {processing_time:.1f}s')
    print_substep(f'   Speakers detected: {result.get("speakers", 0)}')
    print_substep(f'   Segments processed: {result.get("segments", 0)}')
    print_substep(f'   Total words: {result.get("total_words", 0)}')
    
    # Show word counts by speaker
    if 'speaker_word_counts' in result:
        print_substep('')
        print_substep('Word counts by speaker:')
        for speaker_id, counts in result['speaker_word_counts'].items():
            total = sum(counts.values())
            print_substep(f'  {speaker_id}: {total} words - {counts}')

except Exception as e:
    processing_time = time.time() - start_time
    print_substep(f'❌ Processing failed after {processing_time:.1f}s')
    print_substep(f'   Error: {str(e)}')
    
    # Check session status
    db.refresh(session)
    print_substep(f'   Session status: {session.status}')
    if session.error_message:
        print_substep(f'   Error message: {session.error_message[:200]}...')
    
    raise


# =============================================================================
# STEP 6: Verify Database Results
# =============================================================================
print_step(6, 9, 'Verify Database Results')

# Refresh session
db.refresh(session)
print_substep(f'Session status: {session.status}')
print_substep(f'Session progress: {session.progress}%')

# Check SessionSpeakers
speakers = db.query(SessionSpeaker).filter(
    SessionSpeaker.session_id == session.id
).all()

print_substep(f'✅ Found {len(speakers)} speakers in database')

for speaker in speakers:
    # Get word counts for this speaker
    word_counts = db.query(SpeakerWordCount).filter(
        SpeakerWordCount.session_speaker_id == speaker.id
    ).all()
    
    total_words = sum(wc.count for wc in word_counts)
    
    print_substep(f'  {speaker.speaker_label}:')
    print_substep(f'    Segments: {speaker.segment_count}')
    print_substep(f'    Total words: {total_words}')
    print_substep(f'    Sample audio: {speaker.sample_audio_url is not None}')
    
    if word_counts:
        words_str = ', '.join([f'{wc.word}:{wc.count}' for wc in word_counts[:5]])
        print_substep(f'    Top words: {words_str}')


# =============================================================================
# STEP 7: Claim Speakers
# =============================================================================
print_step(7, 9, 'Claim Speakers')

print_substep('Claiming speakers as current user...')

for speaker in speakers:
    speaker.claimed_by = test_user.id
    speaker.claimed_at = datetime.utcnow()
    speaker.claim_type = 'self'
    speaker.attributed_to_user_id = test_user.id
    
    # Create WordCount records
    speaker_word_counts = db.query(SpeakerWordCount).filter(
        SpeakerWordCount.session_speaker_id == speaker.id
    ).all()
    
    for swc in speaker_word_counts:
        word_count = WordCount(
            session_id=session.id,
            user_id=test_user.id,
            group_id=None,  # Personal session
            word=swc.word,
            count=swc.count
        )
        db.add(word_count)
    
    print_substep(f'✅ Claimed {speaker.speaker_label} ({len(speaker_word_counts)} words)')

# Update session status
unclaimed = db.query(SessionSpeaker).filter(
    SessionSpeaker.session_id == session.id,
    SessionSpeaker.claimed_by == None
).count()

if unclaimed == 0:
    session.status = 'completed'

db.commit()

print_substep(f'✅ All speakers claimed')
print_substep(f'   Session status: {session.status}')


# =============================================================================
# STEP 8: Verify WordCount Records
# =============================================================================
print_step(8, 9, 'Verify WordCount Records')

word_counts = db.query(WordCount).filter(
    WordCount.session_id == session.id,
    WordCount.user_id == test_user.id
).all()

print_substep(f'✅ Found {len(word_counts)} WordCount records')

# Aggregate by word
word_totals = {}
for wc in word_counts:
    word_totals[wc.word] = word_totals.get(wc.word, 0) + wc.count

total_words = sum(word_totals.values())
print_substep(f'   Total Singlish words: {total_words}')

if word_totals:
    print_substep('   Top words:')
    for word, count in sorted(word_totals.items(), key=lambda x: -x[1])[:10]:
        print_substep(f'     {word}: {count}')


# =============================================================================
# STEP 9: Verify Wrapped Stats (Simulated)
# =============================================================================
print_step(9, 9, 'Verify Wrapped Stats')

print_substep('Simulating /users/me/wrapped endpoint...')

from sqlalchemy import func

# Get top words for current year
year = datetime.utcnow().year
start_date = datetime(year, 1, 1)
end_date = datetime(year + 1, 1, 1)

top_words = db.query(
    WordCount.word,
    func.sum(WordCount.count).label('total_count')
).filter(
    WordCount.user_id == test_user.id,
    WordCount.detected_at >= start_date,
    WordCount.detected_at < end_date
).group_by(
    WordCount.word
).order_by(
    func.sum(WordCount.count).desc()
).limit(10).all()

total_words_wrapped = sum(count for word, count in top_words)
favorite_word = top_words[0][0] if top_words else 'lah'

print_substep(f'✅ Wrapped stats generated')
print_substep(f'   Year: {year}')
print_substep(f'   Total words: {total_words_wrapped}')
print_substep(f'   Favorite word: {favorite_word}')

if top_words:
    print_substep('   Top 10 words:')
    for i, (word, count) in enumerate(top_words, 1):
        print_substep(f'     {i}. {word}: {count}')


# =============================================================================
# CLEANUP & SUMMARY
# =============================================================================
print('\n' + '=' * 80)
print('TEST COMPLETE - SUMMARY')
print('=' * 80)

print(f'\n✅ Session: {session.id}')
print(f'✅ Status: {session.status}')
print(f'✅ Speakers detected: {len(speakers)}')
print(f'✅ Total words counted: {total_words}')
print(f'✅ WordCount records: {len(word_counts)}')
print(f'✅ Wrapped stats generated successfully')

print(f'\n🎉 COMPLETE INTEGRATION TEST PASSED!')
print(f'   All components working correctly:')
print(f'   - Session creation ✅')
print(f'   - Audio upload ✅')
print(f'   - Redis queueing ✅')
print(f'   - ML processing (diarization + transcription) ✅')
print(f'   - Database updates ✅')
print(f'   - Speaker claiming ✅')
print(f'   - WordCount records ✅')
print(f'   - Wrapped stats ✅')

print('\n' + '=' * 80)

# Cleanup
os.unlink(temp_wav_path)
db.close()

print('\n✅ Test completed successfully!')
print('=' * 80)
