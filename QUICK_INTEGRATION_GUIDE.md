# Quick Integration Guide - What's Ready Now

**TL;DR:** The latest pull added production-ready ML services and backend features. Here's what you can connect to your app **today**.

---

## 🟢 1. Transcription Service (READY NOW)

### What It Does
- Transcribes Singlish audio using MERaLiON-2-10B-ASR
- Auto-corrects common ASR errors (e.g., "while up" → "walao")
- Counts 20 target Singlish words
- Works on T4 GPUs (16GB) with automatic CPU offloading

### How to Use

```python
# backend/processor.py
from services.transcription import process_transcription

# Process audio file
result = process_transcription("path/to/audio.wav")

print(result)
# {
#   'original_text': 'while up this one damn good sia',
#   'corrected_text': 'walao this one damn good sia',
#   'word_counts': {'walao': 1, 'sia': 1, 'damn': 1}
# }
```

### Integration Steps
1. Import the service in your `processor.py`
2. Call `process_transcription()` after diarization
3. Save results to database
4. Done! ✅

**File:** `backend/services/transcription.py`

---

## 🟢 2. Session History API (READY NOW)

### What It Does
- Lists user's past recording sessions
- Filters by period (day/week/month/all-time)
- Shows session details, participants, word counts
- Pagination support

### API Endpoint

```bash
GET /sessions/history?period=week&limit=20
```

**Response:**
```json
{
  "sessions": [
    {
      "session_id": "uuid",
      "created_at": "2026-01-17T10:30:00Z",
      "duration": 180,
      "group_name": "My Squad",
      "total_words": 45,
      "your_words": 23,
      "speakers": [
        {"display_name": "You", "word_count": 23},
        {"display_name": "John", "word_count": 22}
      ]
    }
  ],
  "total": 15
}
```

### Mobile Integration

**Step 1:** Add to `mobile/src/api/client.ts`
```typescript
export const getSessionHistory = async (
  period: 'day' | 'week' | 'month' | 'all_time' = 'week',
  limit: number = 20
) => {
  const response = await api.get('/sessions/history', {
    params: { period, limit }
  });
  return response.data;
};
```

**Step 2:** Add to `mobile/src/screens/StatsScreen.tsx`
```typescript
const [history, setHistory] = useState([]);

useEffect(() => {
  const loadHistory = async () => {
    const data = await getSessionHistory('week');
    setHistory(data.sessions);
  };
  loadHistory();
}, []);

// Render history list
{history.map(session => (
  <SessionCard key={session.session_id} session={session} />
))}
```

**File:** `backend/routers/sessions.py` (lines 400+)

---

## 🟢 3. Global Leaderboard API (READY NOW)

### What It Does
- Shows top users across all groups
- Filters by period (day/week/month/all-time)
- Ranks by total word count
- Includes user details and stats

### API Endpoint

```bash
GET /stats/global/leaderboard?period=month&limit=50
```

**Response:**
```json
{
  "leaderboard": [
    {
      "rank": 1,
      "user_id": "uuid",
      "display_name": "John Doe",
      "total_words": 1250,
      "session_count": 15,
      "top_words": [
        {"word": "lah", "count": 234},
        {"word": "sia", "count": 189}
      ]
    }
  ],
  "period": "month",
  "total_users": 42
}
```

### Mobile Integration

**Step 1:** Add to `mobile/src/api/client.ts`
```typescript
export const getGlobalLeaderboard = async (
  period: 'day' | 'week' | 'month' | 'all_time' = 'month',
  limit: number = 50
) => {
  const response = await api.get('/stats/global/leaderboard', {
    params: { period, limit }
  });
  return response.data;
};
```

**Step 2:** Add to `mobile/src/screens/StatsScreen.tsx`
```typescript
const [leaderboard, setLeaderboard] = useState([]);

useEffect(() => {
  const loadLeaderboard = async () => {
    const data = await getGlobalLeaderboard('month');
    setLeaderboard(data.leaderboard);
  };
  loadLeaderboard();
}, []);

// Render leaderboard
{leaderboard.map(user => (
  <LeaderboardRow 
    key={user.user_id} 
    rank={user.rank}
    name={user.display_name}
    words={user.total_words}
  />
))}
```

**File:** `backend/routers/stats.py` (lines 200+)

---

## 🟢 4. User Search API (READY NOW)

### What It Does
- Search users by username or display name
- Filter by group membership
- Used for tagging speakers as other users
- Autocomplete-friendly

### API Endpoint

```bash
GET /auth/search?query=john&group_id=abc123&limit=10
```

**Response:**
```json
{
  "users": [
    {
      "id": "uuid",
      "username": "john_doe",
      "display_name": "John Doe",
      "avatar_url": "https://..."
    }
  ],
  "total": 5
}
```

### Mobile Integration

**Step 1:** Add to `mobile/src/api/client.ts`
```typescript
export const searchUsers = async (
  query: string,
  groupId?: string,
  limit: number = 10
) => {
  const response = await api.get('/auth/search', {
    params: { query, group_id: groupId, limit }
  });
  return response.data;
};
```

**Step 2:** Use in `mobile/src/screens/ClaimingScreen.tsx`
```typescript
const [searchQuery, setSearchQuery] = useState('');
const [searchResults, setSearchResults] = useState([]);

const handleSearch = async (query: string) => {
  setSearchQuery(query);
  if (query.length >= 2) {
    const data = await searchUsers(query, groupId);
    setSearchResults(data.users);
  }
};

// Render autocomplete dropdown
<TextInput
  value={searchQuery}
  onChangeText={handleSearch}
  placeholder="Search for user..."
/>
{searchResults.map(user => (
  <TouchableOpacity onPress={() => selectUser(user)}>
    <Text>{user.display_name} (@{user.username})</Text>
  </TouchableOpacity>
))}
```

**File:** `backend/routers/auth.py` (lines 150+)

---

## 🟡 5. Team Recording Pipeline (READY TO START)

### What It Does
- Creates training data from team voice recordings
- 90 pre-written Singlish sentences
- Auto-transcription + manual correction workflow
- Generates train/val/test splits for LoRA fine-tuning

### Workflow

**Step 1: Record Audio**
```bash
# Each team member records all 90 sentences
# Save as: speakername_template_001.wav, speakername_template_002.wav, etc.
# Place in: ml/data/team_recordings/audio/
```

**Step 2: Auto-Transcribe**
```bash
cd ml
python scripts/prepare_team_recordings.py --auto-transcribe
# Generates initial transcripts in ml/data/team_recordings/transcripts/
```

**Step 3: Manually Correct**
```bash
# Edit files in ml/data/team_recordings/transcripts/
# Fix any transcription errors
# Ensure Singlish words are spelled correctly
```

**Step 4: Generate Training Data**
```bash
python scripts/prepare_team_recordings.py --process
# Creates: ml/data/splits/train.json, val.json, test.json
```

### Why Do This?
- ✅ Improves ASR accuracy on your team's accents
- ✅ Better recognition of Singlish words
- ✅ Only takes ~20 minutes per person
- ✅ Creates 360+ training samples (4 people × 90 sentences)

**Files:**
- `ml/scripts/prepare_team_recordings.py` - Main script
- `ml/data/sentence_templates.txt` - Sentences to record
- `ml/data/team_recordings/README.md` - Instructions

---

## 🟡 6. Three-Way Claiming (BACKEND READY)

### What It Does
- Claim speaker as yourself (existing)
- Tag speaker as another registered user (new)
- Tag speaker as guest participant (new)

### API Changes

**Updated Endpoint:** `POST /sessions/{session_id}/claim`

**Request Body:**
```json
// Claim as yourself
{
  "speaker_id": "uuid",
  "claim_type": "self"
}

// Tag as another user
{
  "speaker_id": "uuid",
  "claim_type": "user",
  "attributed_to_user_id": "uuid-of-other-user"
}

// Tag as guest
{
  "speaker_id": "uuid",
  "claim_type": "guest",
  "guest_name": "John's Friend"
}
```

### Mobile UI Needed

**Update `mobile/src/screens/ClaimingScreen.tsx`:**

```typescript
// Add claim mode selector
const [claimMode, setClaimMode] = useState<'self' | 'user' | 'guest'>('self');

// Render mode selector
<SegmentedControl
  values={['Claim as Me', 'Tag User', 'Tag Guest']}
  selectedIndex={['self', 'user', 'guest'].indexOf(claimMode)}
  onChange={(e) => {
    const modes = ['self', 'user', 'guest'];
    setClaimMode(modes[e.nativeEvent.selectedSegmentIndex]);
  }}
/>

// Show appropriate input based on mode
{claimMode === 'user' && (
  <UserSearchInput onSelect={setSelectedUser} />
)}

{claimMode === 'guest' && (
  <TextInput
    placeholder="Guest name"
    value={guestName}
    onChangeText={setGuestName}
  />
)}

// Update claim function
const claimSpeaker = async () => {
  const payload = {
    speaker_id: selectedSpeaker.id,
    claim_type: claimMode,
    ...(claimMode === 'user' && { attributed_to_user_id: selectedUser.id }),
    ...(claimMode === 'guest' && { guest_name: guestName })
  };
  await api.post(`/sessions/${sessionId}/claim`, payload);
};
```

**File:** `backend/routers/sessions.py` (claim endpoint)

---

## 📋 Quick Start Checklist

### Today (30 minutes)
- [ ] Read `INTEGRATION_OPPORTUNITIES.md` for full details
- [ ] Add session history to mobile app (15 min)
- [ ] Add global leaderboard to mobile app (15 min)
- [ ] Test new endpoints with Postman/curl

### This Week (2-3 hours)
- [ ] Connect transcription service to backend processor (1 hour)
- [ ] Enhance claiming screen with 3 modes (1 hour)
- [ ] Record team training data (20 min per person)
- [ ] Test end-to-end flow

### Next Sprint (1-2 days)
- [ ] Deploy backend with GPU support
- [ ] Process team recordings into training data
- [ ] Implement LoRA training script
- [ ] Fine-tune and deploy improved model

---

## 🔗 Key Files to Check

**Backend Services:**
- `backend/services/transcription.py` - Transcription service
- `backend/routers/sessions.py` - Session history endpoints
- `backend/routers/stats.py` - Global leaderboard
- `backend/routers/auth.py` - User search

**ML Pipeline:**
- `ml/scripts/prepare_team_recordings.py` - Recording workflow
- `ml/data/sentence_templates.txt` - Sentences to record

**Documentation:**
- `INTEGRATION_OPPORTUNITIES.md` - Full integration guide (this file's parent)
- `backend/SESSION_HISTORY_API.md` - Session history API docs
- `GLOBAL_LEADERBOARD_FEATURE.md` - Leaderboard feature guide
- `CLAIMING_FEATURE_GUIDE.md` - Three-way claiming guide

---

## 💡 Pro Tips

1. **Start with Session History** - It's the easiest to integrate and adds immediate value
2. **Test Transcription Locally** - Run `scripts/test_meralion.py` to verify GPU setup
3. **Record Training Data in Parallel** - While building features, have team record sentences
4. **Use the Test Scripts** - `backend/test_history_endpoints.py` shows how to use the APIs

---

## ❓ Questions?

- **API not working?** Check `backend/.env` for correct Supabase credentials
- **GPU issues?** See `ml/README.md` for GPU setup instructions
- **Mobile errors?** Check `mobile/.env` for correct API URL
- **Need examples?** Look at the test files in `backend/test_*.py`

---

**Ready to integrate?** Start with the session history - it's just 10 lines of code! 🚀

*Last updated: January 17, 2026*
