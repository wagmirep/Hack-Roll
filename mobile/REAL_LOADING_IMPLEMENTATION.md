# Real Loading & Data Implementation

## Summary of Changes

Removed all fake/mock data and loading screens from the mobile app. The app now uses real backend data and properly waits for audio processing to complete.

---

## What Was Changed

### 1. ProcessingScreen.tsx - Real Backend Status Polling

**Before (Fake Implementation):**
- Used a fake progress timer that incremented every 100ms
- Completed in ~10 seconds regardless of actual processing status
- Didn't check backend for real status
- Commented-out `useSessionStatus` hook

**After (Real Implementation):**
- Uses `useSessionStatus` hook to poll backend every 2 seconds
- Waits for actual status: `'ready_for_claiming'`, `'completed'`, or `'failed'`
- Shows real progress percentage from backend (0-100%)
- Navigates to Wrapped screen only when processing is actually complete
- Displays error messages if processing fails

**Key Code Changes:**
```typescript
// Real backend status polling
const { status, progress, error, session } = useSessionStatus(sessionId, {
  pollInterval: 2000, // Poll every 2 seconds
  stopOnStatus: ['ready_for_claiming', 'completed', 'failed'],
});

// Navigate when actually complete
useEffect(() => {
  if (status === 'ready_for_claiming' || status === 'completed') {
    console.log('Processing complete! Navigating to Wrapped screen...');
    setTimeout(() => {
      navigation.replace('Wrapped', { sessionId });
    }, 500);
  } else if (status === 'failed') {
    console.error('Session processing failed:', error);
  }
}, [status, sessionId, navigation, progress, error]);
```

---

### 2. WrappedScreen.tsx - Real Session Results Data

**Before (Fake Implementation):**
- Used hardcoded mock data with 6 fake speakers
- Data never changed regardless of actual recording
- No API calls to backend

**After (Real Implementation):**
- Fetches real session results from `/sessions/{sessionId}/results` endpoint
- Shows loading spinner while data is being fetched
- Displays error screen if data fetch fails
- Transforms backend response to match UI format
- Maps real speakers with their actual word counts

**Key Code Changes:**
```typescript
// Fetch session results from backend
useEffect(() => {
  const fetchSessionResults = async () => {
    try {
      const results = await api.sessions.getResults(sessionId);
      
      // Transform backend data to UI format
      const transformedData: WrappedData = {
        singlishWordsCount: results.total_singlish_words || 0,
        totalWords: results.total_words || 0,
        sessionDuration: formatDuration(results.duration_seconds || 0),
        speakers: results.speakers.map((speaker: any) => ({
          id: speaker.speaker_id,
          name: speaker.name || `Speaker ${speaker.speaker_id}`,
          handle: speaker.username ? `@${speaker.username}` : `@speaker${speaker.speaker_id}`,
          totalWords: speaker.total_words || 0,
          topWord: speaker.top_word?.word || 'N/A',
          wordBreakdown: (speaker.word_counts || []).map((wc: any) => ({
            word: wc.word,
            count: wc.count,
          })),
        })),
      };
      
      setData(transformedData);
    } catch (err: any) {
      setError(err.message || 'Failed to load session results');
    }
  };

  fetchSessionResults();
}, [sessionId]);
```

**New UI States:**
1. **Loading State**: Shows spinner and "Loading your Wrapped..." message
2. **Error State**: Shows error message with "Go Back" button
3. **Success State**: Shows actual session data

---

## User Experience Flow

### Before (Fake)
```
Recording → Stop → 
Fake Loading (10 seconds) → 
Wrapped Screen with Mock Data
```

### After (Real)
```
Recording → Stop → 
Real Processing (polls backend every 2s) →
  ↓ status = 'processing', progress updates (0-100%) →
  ↓ status = 'ready_for_claiming' or 'completed' →
Loading Wrapped data from backend →
  ↓ Fetching /sessions/{id}/results →
  ↓ Success →
Wrapped Screen with Real Data
```

---

## Backend Integration

### Processing Status Endpoint
**URL**: `GET /sessions/{sessionId}`

**Response**:
```json
{
  "id": "abc-123",
  "status": "processing",
  "progress": 45,
  "error_message": null
}
```

**Status Values**:
- `"recording"` - Still recording
- `"processing"` - Backend worker is processing audio
- `"ready_for_claiming"` - Processing done, speakers can be claimed
- `"completed"` - Fully complete
- `"failed"` - Processing failed

### Session Results Endpoint
**URL**: `GET /sessions/{sessionId}/results`

**Response**:
```json
{
  "session_id": "abc-123",
  "duration_seconds": 90,
  "total_words": 456,
  "total_singlish_words": 89,
  "speakers": [
    {
      "speaker_id": "SPEAKER_00",
      "name": "Speaker 1",
      "username": null,
      "total_words": 234,
      "top_word": {
        "word": "lah",
        "count": 45
      },
      "word_counts": [
        { "word": "lah", "count": 45 },
        { "word": "walao", "count": 23 }
      ]
    }
  ]
}
```

---

## Testing the Real Flow

### 1. Start Backend Services
```bash
# Terminal 1: Backend API
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000

# Terminal 2: Worker
cd backend
source venv/bin/activate
python worker.py
```

### 2. Record Audio in Mobile App
1. Open mobile app
2. Start recording
3. Wait ~30-60 seconds
4. Stop recording
5. **Watch the processing screen** - you'll see real progress updates
6. When complete, wrapped screen loads with **real data**

### 3. Check Logs

**Backend logs** show:
```
🎙️  NEW SESSION REQUEST
📥 CHUNK UPLOAD REQUEST #1
📥 CHUNK UPLOAD REQUEST #2
🛑 END SESSION REQUEST
📮 Queueing job to Redis...
```

**Worker logs** show:
```
🎬 Processing session: abc-123
📥 Found 2 chunks to concatenate
✅ Concatenated audio: 65.4s
🔊 Running diarization...
📝 Transcribing...
📊 Counting words...
✅ Processing complete!
```

**Mobile app console** shows:
```
ProcessingScreen: status=processing, progress=10
ProcessingScreen: status=processing, progress=50
ProcessingScreen: status=completed, progress=100
Processing complete! Navigating to Wrapped screen...
Fetching results for session: abc-123
Session results: { duration_seconds: 65, total_words: 456, ... }
```

---

## What Happens Now

### ProcessingScreen
- **Polls backend every 2 seconds** to check status
- **Updates progress bar** with real percentage (0-100%)
- **Shows status messages** based on progress:
  - 0-30%: Random Singlish loading messages
  - 30-50%: "Detecting speakers..."
  - 50-70%: "Transcribing conversation..."
  - 70-90%: "Alamak need to analyse word usage..."
  - 90-100%: "Almost ready!"
- **Waits for backend** to finish before navigating
- **Handles errors** gracefully if processing fails

### WrappedScreen
- **Fetches real data** from `/sessions/{id}/results`
- **Shows loading spinner** while fetching
- **Displays actual speakers** detected in the recording
- **Shows real word counts** from transcription
- **Handles errors** if data fetch fails

---

## Expected Processing Time

Based on backend logs and ML model performance:

- **Audio concatenation**: ~2-5 seconds
- **Speaker diarization (pyannote)**: ~20-30 seconds for 60s audio
- **Transcription (MERaLiON)**: ~10-20 seconds
- **Word counting**: ~1-2 seconds
- **Total**: ~30-60 seconds for typical recording

The processing screen will show this progress in real-time!

---

## Debugging Tips

### If Processing Screen Hangs

Check if:
1. **Worker is running**: `ps aux | grep worker.py`
2. **Job was queued**: `redis-cli LRANGE lahstats:processing 0 -1`
3. **Worker logs show errors**: Check Terminal 2

### If Wrapped Screen Shows Error

Check:
1. **Backend API is running**: `curl http://localhost:8000/health`
2. **Session status**: `curl http://localhost:8000/sessions/{id}`
3. **Results exist**: `curl http://localhost:8000/sessions/{id}/results`

### If Data Looks Wrong

Check:
1. **Backend logs** for processing errors
2. **Worker logs** for ML model errors
3. **Database** to verify data was saved: `psql` or Supabase dashboard

---

## Files Changed

1. **`mobile/src/screens/ProcessingScreen.tsx`**
   - Removed fake progress timer
   - Added real `useSessionStatus` hook
   - Added backend status polling logic
   - Added console logging for debugging

2. **`mobile/src/screens/WrappedScreen.tsx`**
   - Removed mock speaker data
   - Added `useEffect` to fetch real data
   - Added loading state UI
   - Added error state UI
   - Transformed backend response to UI format
   - Added helper function `formatDuration`

3. **`mobile/REAL_LOADING_IMPLEMENTATION.md`** (this file)
   - Documentation of changes

---

## Next Steps (If Needed)

1. **Add retry logic** if processing fails
2. **Show estimated time remaining** based on audio duration
3. **Cache results** to avoid re-fetching
4. **Add pull-to-refresh** on Wrapped screen
5. **Add speaker claiming UI** integration

---

**✅ All fake data removed! App now uses 100% real backend data!** 🎉
