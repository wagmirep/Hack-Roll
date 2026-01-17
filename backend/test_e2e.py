"""Quick E2E test with diarization."""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from dotenv import load_dotenv
load_dotenv()

print('='*60)
print('FULL E2E TEST WITH DIARIZATION')
print('='*60)

# Test with Main Speech 1.m4a
print('\nTesting: Main Speech 1.m4a')
print('-'*60)

# Step 1: Check services
print('[1/4] Loading services...')
from services.transcription import transcribe_audio, apply_corrections, count_target_words, is_using_external_api
from services.diarization import diarize_audio, extract_speaker_segment
print(f'      External API: {is_using_external_api()}')
print('      Services loaded!')

# Step 2: Convert audio to WAV for diarization
print('\n[2/4] Converting audio to WAV...')
from pydub import AudioSegment
import tempfile
import os

audio = AudioSegment.from_file('../audio/Main Speech 1.m4a')
audio = audio.set_frame_rate(16000).set_channels(1)

temp_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
audio.export(temp_wav.name, format='wav')
temp_wav.close()
print(f'      Duration: {len(audio)/1000:.1f}s')

# Step 3: Run diarization
print('\n[3/4] Running speaker diarization...')
import time
start = time.time()
segments = diarize_audio(temp_wav.name)
print(f'      Completed in {time.time()-start:.1f}s')
print(f'      Found {len(segments)} segments')

speakers = set(s.speaker_id for s in segments)
print(f'      Speakers: {list(speakers)}')

print('\n      Segments:')
for i, seg in enumerate(segments[:10]):
    print(f'        {i+1}. {seg.speaker_id}: {seg.start_time:.1f}s - {seg.end_time:.1f}s ({seg.duration:.1f}s)')
if len(segments) > 10:
    print(f'        ... and {len(segments)-10} more')

# Step 4: Transcribe each segment
print('\n[4/4] Transcribing segments...')
results = {}

for i, seg in enumerate(segments):
    segment_bytes = extract_speaker_segment(temp_wav.name, seg.start_time, seg.end_time)

    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        f.write(segment_bytes)
        seg_path = f.name

    try:
        raw_text = transcribe_audio(seg_path)
        corrected = apply_corrections(raw_text)
        counts = count_target_words(corrected)

        speaker = seg.speaker_id
        if speaker not in results:
            results[speaker] = {}
        for word, count in counts.items():
            results[speaker][word] = results[speaker].get(word, 0) + count

        print(f'      Segment {i+1}/{len(segments)} ({seg.speaker_id}): {counts}')
    finally:
        os.unlink(seg_path)

os.unlink(temp_wav.name)

# Print results
print('\n' + '='*60)
print('RESULTS BY SPEAKER')
print('='*60)

for speaker_id, word_counts in sorted(results.items()):
    total = sum(word_counts.values())
    print(f'\n{speaker_id}: {total} Singlish words')
    if word_counts:
        for word, count in sorted(word_counts.items(), key=lambda x: -x[1]):
            print(f'  {word}: {count}')

print('\n' + '='*60)
grand_total = sum(sum(c.values()) for c in results.values())
print(f'GRAND TOTAL: {grand_total} Singlish words')
print('='*60)
