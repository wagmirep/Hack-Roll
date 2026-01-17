# Integration Map - Latest Changes to Existing App

Visual guide showing how new features connect to your existing architecture.

---

## 🏗️ Current Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         MOBILE APP                               │
│  (React Native + Expo + TypeScript)                             │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Auth Screens │  │ Recording    │  │ Claiming     │          │
│  │ - Login      │  │ - Record     │  │ - Play Audio │          │
│  │ - Signup     │  │ - Upload     │  │ - Claim      │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐                             │
│  │ Results      │  │ Stats        │                             │
│  │ - Leaderboard│  │ - Group Stats│  ← NEW: Add History & Global│
│  └──────────────┘  └──────────────┘                             │
└───────────────────────────┬─────────────────────────────────────┘
                            │ API Client (axios)
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND (FastAPI)                           │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Auth Router  │  │ Sessions     │  │ Stats Router │          │
│  │ - /auth/me   │  │ - /sessions  │  │ - /stats     │          │
│  │ - /auth/...  │  │ - /claim     │  │              │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                   │
│  ┌──────────────────────────────────────────────────────┐       │
│  │              processor.py                             │       │
│  │  (Audio Processing Pipeline)                         │       │
│  │  - Concatenate chunks                                │       │
│  │  - Run diarization                                   │       │
│  │  - Transcribe segments                               │       │
│  │  - Count words                                       │       │
│  └──────────────────────────────────────────────────────┘       │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                    SUPABASE (PostgreSQL)                         │
│  - profiles, groups, sessions, speakers, word_counts            │
└─────────────────────────────────────────────────────────────────┘
```

---

## ✨ NEW: What's Been Added

### 1. Enhanced Backend Services

```
┌─────────────────────────────────────────────────────────────────┐
│                   BACKEND SERVICES (NEW)                         │
│                                                                   │
│  ┌──────────────────────────────────────────────────────┐       │
│  │  services/transcription.py  ✅ PRODUCTION READY       │       │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │       │
│  │  • transcribe_audio(path) → text                     │       │
│  │  • apply_corrections(text) → corrected_text          │       │
│  │  • count_target_words(text) → word_counts            │       │
│  │  • process_transcription(path) → full_result         │       │
│  │                                                       │       │
│  │  Features:                                            │       │
│  │  - MERaLiON-2-10B-ASR model                          │       │
│  │  - GPU auto-detection (CUDA/CPU)                     │       │
│  │  - CPU offloading for small GPUs (T4 16GB works!)    │       │
│  │  - 20+ Singlish correction patterns                  │       │
│  │  - 20 target word counting                           │       │
│  │  - Thread-safe singleton pattern                     │       │
│  └──────────────────────────────────────────────────────┘       │
│                                                                   │
│  ┌──────────────────────────────────────────────────────┐       │
│  │  services/diarization.py  ✅ ALREADY EXISTS          │       │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │       │
│  │  • diarize_audio(path) → speaker_segments            │       │
│  │  • extract_speaker_segment() → audio_bytes           │       │
│  └──────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

### 2. New API Endpoints

```
┌─────────────────────────────────────────────────────────────────┐
│                    NEW ENDPOINTS (READY)                         │
│                                                                   │
│  ┌────────────────────────────────────────────────────┐         │
│  │  GET /sessions/history  ✅ IMPLEMENTED              │         │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │         │
│  │  Query: ?period=week&limit=20                      │         │
│  │  Returns: User's past sessions with details        │         │
│  │                                                     │         │
│  │  Response:                                          │         │
│  │  {                                                  │         │
│  │    "sessions": [                                    │         │
│  │      {                                              │         │
│  │        "session_id": "uuid",                        │         │
│  │        "created_at": "2026-01-17T10:30:00Z",        │         │
│  │        "duration": 180,                             │         │
│  │        "group_name": "My Squad",                    │         │
│  │        "total_words": 45,                           │         │
│  │        "your_words": 23,                            │         │
│  │        "speakers": [...]                            │         │
│  │      }                                              │         │
│  │    ]                                                │         │
│  │  }                                                  │         │
│  └────────────────────────────────────────────────────┘         │
│                                                                   │
│  ┌────────────────────────────────────────────────────┐         │
│  │  GET /stats/global/leaderboard  ✅ IMPLEMENTED      │         │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │         │
│  │  Query: ?period=month&limit=50                     │         │
│  │  Returns: Top users across all groups              │         │
│  │                                                     │         │
│  │  Response:                                          │         │
│  │  {                                                  │         │
│  │    "leaderboard": [                                 │         │
│  │      {                                              │         │
│  │        "rank": 1,                                   │         │
│  │        "user_id": "uuid",                           │         │
│  │        "display_name": "John Doe",                  │         │
│  │        "total_words": 1250,                         │         │
│  │        "session_count": 15,                         │         │
│  │        "top_words": [...]                           │         │
│  │      }                                              │         │
│  │    ]                                                │         │
│  │  }                                                  │         │
│  └────────────────────────────────────────────────────┘         │
│                                                                   │
│  ┌────────────────────────────────────────────────────┐         │
│  │  GET /auth/search  ✅ IMPLEMENTED                   │         │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │         │
│  │  Query: ?query=john&group_id=abc&limit=10          │         │
│  │  Returns: Users matching search query              │         │
│  │  Used for: Tagging speakers as other users         │         │
│  └────────────────────────────────────────────────────┘         │
│                                                                   │
│  ┌────────────────────────────────────────────────────┐         │
│  │  POST /sessions/{id}/claim  ✅ ENHANCED             │         │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │         │
│  │  Now supports 3 claim types:                       │         │
│  │  - "self": Claim as yourself                       │         │
│  │  - "user": Tag as another user                     │         │
│  │  - "guest": Tag as guest participant               │         │
│  └────────────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

### 3. ML Training Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                  ML TRAINING PIPELINE (NEW)                      │
│                                                                   │
│  ┌────────────────────────────────────────────────────┐         │
│  │  ml/scripts/prepare_team_recordings.py             │         │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │         │
│  │                                                     │         │
│  │  Step 1: Record Audio                              │         │
│  │  └─→ Team records 90 Singlish sentences            │         │
│  │      (20 min per person)                            │         │
│  │                                                     │         │
│  │  Step 2: Auto-Transcribe                           │         │
│  │  └─→ python prepare_team_recordings.py             │         │
│  │      --auto-transcribe                              │         │
│  │                                                     │         │
│  │  Step 3: Manual Correction                         │         │
│  │  └─→ Edit transcripts in text editor               │         │
│  │      Fix ASR errors, verify Singlish words         │         │
│  │                                                     │         │
│  │  Step 4: Generate Training Data                    │         │
│  │  └─→ python prepare_team_recordings.py             │         │
│  │      --process                                      │         │
│  │      Creates: train.json, val.json, test.json      │         │
│  │                                                     │         │
│  │  Output: Ready for LoRA fine-tuning!               │         │
│  └────────────────────────────────────────────────────┘         │
│                                                                   │
│  ┌────────────────────────────────────────────────────┐         │
│  │  ml/data/sentence_templates.txt                    │         │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │         │
│  │  90 pre-written Singlish sentences covering:       │         │
│  │  - Particles: lah, lor, leh, meh, sia, hor, ah...  │         │
│  │  - Exclamations: walao, wah, aiyo, alamak          │         │
│  │  - Common words: can, paiseh, shiok, sian...       │         │
│  │                                                     │         │
│  │  Examples:                                          │         │
│  │  01. Come on lah, we going to be late already.     │         │
│  │  29. Walao, why so expensive this one!             │         │
│  │  49. Wah this mala damn shiok sia!                 │         │
│  └────────────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔌 Integration Points

### Point 1: Transcription Service → Backend Processor

```
BEFORE (processor.py):
┌──────────────────────────────────────┐
│ 1. Concatenate audio chunks          │
│ 2. Run diarization                   │
│ 3. ❌ Transcription: NOT IMPLEMENTED │
│ 4. ❌ Word counting: NOT IMPLEMENTED │
└──────────────────────────────────────┘

AFTER (processor.py):
┌──────────────────────────────────────┐
│ 1. Concatenate audio chunks          │
│ 2. Run diarization                   │
│ 3. ✅ Transcription: READY TO USE    │
│    from services.transcription       │
│    import process_transcription      │
│                                      │
│ 4. ✅ Word counting: BUILT-IN        │
│    result = process_transcription()  │
│    word_counts = result['word_counts']│
└──────────────────────────────────────┘

CODE:
from services.transcription import process_transcription

for segment in speaker_segments:
    result = process_transcription(segment.audio_path)
    save_to_db(
        speaker_id=segment.speaker,
        transcript=result['corrected_text'],
        word_counts=result['word_counts']
    )
```

### Point 2: New Endpoints → Mobile App

```
BEFORE (StatsScreen.tsx):
┌──────────────────────────────────────┐
│ Tabs:                                │
│ - Personal Stats                     │
│ - Group Stats                        │
│                                      │
│ Shows:                               │
│ - Current period stats only          │
│ - Group leaderboard only             │
└──────────────────────────────────────┘

AFTER (StatsScreen.tsx):
┌──────────────────────────────────────┐
│ Tabs:                                │
│ - Personal Stats                     │
│ - Group Stats                        │
│ - ✨ Global Leaderboard (NEW)       │
│ - ✨ Session History (NEW)          │
│                                      │
│ Shows:                               │
│ - Period filter (day/week/month/all) │
│ - Global rankings                    │
│ - Past session list                  │
└──────────────────────────────────────┘

CODE:
// Add to mobile/src/api/client.ts
export const getSessionHistory = async (period, limit) => {
  return api.get('/sessions/history', { params: { period, limit } });
};

export const getGlobalLeaderboard = async (period, limit) => {
  return api.get('/stats/global/leaderboard', { params: { period, limit } });
};

// Use in StatsScreen.tsx
const [history, setHistory] = useState([]);
const [leaderboard, setLeaderboard] = useState([]);

useEffect(() => {
  loadData();
}, [period]);

const loadData = async () => {
  const [historyData, leaderboardData] = await Promise.all([
    getSessionHistory(period),
    getGlobalLeaderboard(period)
  ]);
  setHistory(historyData.sessions);
  setLeaderboard(leaderboardData.leaderboard);
};
```

### Point 3: Enhanced Claiming → Mobile UI

```
BEFORE (ClaimingScreen.tsx):
┌──────────────────────────────────────┐
│ Speaker List:                        │
│ - Speaker 1 [Claim as Me] button     │
│ - Speaker 2 [Claim as Me] button     │
│                                      │
│ Only option: Claim as yourself       │
└──────────────────────────────────────┘

AFTER (ClaimingScreen.tsx):
┌──────────────────────────────────────┐
│ Speaker List:                        │
│ - Speaker 1                          │
│   ┌────────────────────────────────┐ │
│   │ Mode: [Self] [User] [Guest]    │ │
│   │                                │ │
│   │ [Self]: Claim as Me button     │ │
│   │ [User]: Search user input      │ │
│   │         + Autocomplete list    │ │
│   │ [Guest]: Guest name input      │ │
│   └────────────────────────────────┘ │
│                                      │
│ Three options:                       │
│ 1. Claim as yourself                 │
│ 2. Tag as another user               │
│ 3. Tag as guest participant          │
└──────────────────────────────────────┘

CODE:
const [claimMode, setClaimMode] = useState('self');
const [selectedUser, setSelectedUser] = useState(null);
const [guestName, setGuestName] = useState('');

// Mode selector
<SegmentedControl
  values={['Claim as Me', 'Tag User', 'Tag Guest']}
  onChange={(index) => setClaimMode(['self', 'user', 'guest'][index])}
/>

// User search (for 'user' mode)
{claimMode === 'user' && (
  <UserSearchInput
    onSearch={searchUsers}
    onSelect={setSelectedUser}
  />
)}

// Guest input (for 'guest' mode)
{claimMode === 'guest' && (
  <TextInput
    placeholder="Guest name"
    value={guestName}
    onChangeText={setGuestName}
  />
)}

// Claim with appropriate data
const claim = async () => {
  await api.post(`/sessions/${sessionId}/claim`, {
    speaker_id: speaker.id,
    claim_type: claimMode,
    ...(claimMode === 'user' && { attributed_to_user_id: selectedUser.id }),
    ...(claimMode === 'guest' && { guest_name: guestName })
  });
};
```

---

## 📊 Data Flow

### Complete Recording → Results Flow (Updated)

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER RECORDS AUDIO                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│  MOBILE: Upload chunks to backend                               │
│  POST /sessions/{id}/upload-chunk                               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│  BACKEND: processor.py                                          │
│  ┌────────────────────────────────────────────────────┐         │
│  │ 1. Concatenate chunks → full_audio.wav             │         │
│  │ 2. Diarization → SPEAKER_00, SPEAKER_01, ...       │         │
│  │ 3. ✨ NEW: Transcription (MERaLiON)                │         │
│  │    - transcribe_audio(segment)                     │         │
│  │    - apply_corrections(text)                       │         │
│  │    - count_target_words(text)                      │         │
│  │ 4. Save to database                                │         │
│  └────────────────────────────────────────────────────┘         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│  MOBILE: Claiming Screen                                        │
│  ┌────────────────────────────────────────────────────┐         │
│  │ ✨ NEW: Three claiming modes                       │         │
│  │ - Self: Claim as yourself                          │         │
│  │ - User: Tag as another user (with search)          │         │
│  │ - Guest: Tag as guest participant                  │         │
│  └────────────────────────────────────────────────────┘         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│  MOBILE: Results Screen                                         │
│  - Shows all speakers (users + guests)                          │
│  - Word counts per speaker                                      │
│  - Leaderboard                                                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│  MOBILE: Stats Screen                                           │
│  ┌────────────────────────────────────────────────────┐         │
│  │ ✨ NEW: Four tabs                                  │         │
│  │ 1. Personal Stats (existing)                       │         │
│  │ 2. Group Stats (existing)                          │         │
│  │ 3. Global Leaderboard (NEW)                        │         │
│  │ 4. Session History (NEW)                           │         │
│  └────────────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Priority Integration Order

### 🔥 High Priority (Do First)
1. **Transcription Service** - Core ML functionality
   - File: `backend/processor.py`
   - Effort: 30 minutes
   - Impact: Enables end-to-end flow

2. **Session History** - Easy win, high value
   - Files: `mobile/src/api/client.ts`, `mobile/src/screens/StatsScreen.tsx`
   - Effort: 15 minutes
   - Impact: Better user engagement

3. **Global Leaderboard** - Easy win, high value
   - Files: `mobile/src/api/client.ts`, `mobile/src/screens/StatsScreen.tsx`
   - Effort: 15 minutes
   - Impact: Social competition

### 🟡 Medium Priority (Do Next)
4. **Enhanced Claiming** - Improves flexibility
   - File: `mobile/src/screens/ClaimingScreen.tsx`
   - Effort: 1 hour
   - Impact: Supports guests and tagging

5. **Team Recording Data** - Improves ML quality
   - Files: Team records audio, run scripts
   - Effort: 20 min/person + 30 min processing
   - Impact: Better ASR accuracy

### 🟢 Low Priority (Nice to Have)
6. **LoRA Training** - Long-term improvement
   - Files: `ml/scripts/train_lora.py` (needs implementation)
   - Effort: 1-2 days
   - Impact: Significantly better Singlish recognition

---

## 📁 File Reference

### Backend Files (Ready)
- ✅ `backend/services/transcription.py` - Transcription service
- ✅ `backend/routers/sessions.py` - Session history endpoints
- ✅ `backend/routers/stats.py` - Global leaderboard
- ✅ `backend/routers/auth.py` - User search
- ⏳ `backend/processor.py` - Needs transcription integration

### Mobile Files (Need Updates)
- ⏳ `mobile/src/api/client.ts` - Add new API methods
- ⏳ `mobile/src/screens/StatsScreen.tsx` - Add history & global tabs
- ⏳ `mobile/src/screens/ClaimingScreen.tsx` - Add 3-mode claiming
- ⏳ `mobile/src/screens/ResultsScreen.tsx` - Display guests

### ML Files (Ready)
- ✅ `ml/scripts/prepare_team_recordings.py` - Recording workflow
- ✅ `ml/data/sentence_templates.txt` - Sentences to record
- ⏳ `ml/scripts/train_lora.py` - Needs implementation

### Documentation
- 📖 `INTEGRATION_OPPORTUNITIES.md` - Full integration guide
- 📖 `QUICK_INTEGRATION_GUIDE.md` - Quick start guide
- 📖 `backend/SESSION_HISTORY_API.md` - API documentation
- 📖 `GLOBAL_LEADERBOARD_FEATURE.md` - Feature guide
- 📖 `CLAIMING_FEATURE_GUIDE.md` - Claiming guide

---

## 🚀 Next Steps

1. **Read the guides:**
   - `QUICK_INTEGRATION_GUIDE.md` for code examples
   - `INTEGRATION_OPPORTUNITIES.md` for full details

2. **Start integrating:**
   - Begin with session history (easiest)
   - Then add global leaderboard
   - Finally enhance claiming screen

3. **Test end-to-end:**
   - Record → Process → Claim → View Results
   - Verify all new features work

4. **Record training data:**
   - Have team record 90 sentences
   - Process into training data
   - Prepare for fine-tuning

---

**Questions?** Check the documentation files or review the commit history!

*Last updated: January 17, 2026*
