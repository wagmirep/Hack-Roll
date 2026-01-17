# 🎯 Three-Way Speaker Claiming System

**Implementation Date:** January 17, 2026  
**Status:** ✅ Backend Complete | 📱 Mobile Integration Needed

---

## TL;DR

Users can now identify speakers in three ways:
1. **Claim as yourself** → Your stats
2. **Tag another registered user** → Their stats  
3. **Tag as guest** → Session only (no profile stats)

---

## Why This Feature?

**Problem:** Not everyone in a recording session has an account, but we want them included in the session results.

**Solution:** Flexible claiming that supports guests while still allowing proper stat attribution for registered users.

---

## How It Works

### Recording Phase ✅ (Unchanged)
```
Start Session → Record Audio → Process → Identify Speakers → Count Words
                                          ↓
                        SPEAKER_00, SPEAKER_01, SPEAKER_02...
```

### Claiming Phase ✨ (NEW)

When you see the unclaimed speakers, you have **3 options**:

#### Option 1: "This Is Me" (Claim as Self)
```
Speaker 1 → [This is me] → Your profile gets the stats
```
- Use when: You're identifying yourself
- Stats go to: Your user profile
- Appears in: Your stats, group leaderboard

#### Option 2: "This Is @username" (Tag Registered User)
```
Speaker 2 → [Search: "john"] → @john_doe → Their profile gets the stats
```
- Use when: You know who the speaker is and they have an account
- Stats go to: Their user profile (not yours!)
- Appears in: Their stats, group leaderboard
- Requirement: User must be in the same group

#### Option 3: "This Is Guest Name" (Tag Guest)
```
Speaker 3 → [Enter name: "Sarah"] → Session results only
```
- Use when: Speaker doesn't have an account
- Stats go to: Nowhere (stays in session only)
- Appears in: Session results only (not leaderboards)
- No profile impact

---

## API Usage

### Claim Speaker Endpoint

**Endpoint:** `POST /sessions/{session_id}/claim`

#### Claim as Yourself
```json
{
  "speaker_id": "a1b2c3d4-...",
  "claim_type": "self"
}
```

#### Tag Another User
```json
{
  "speaker_id": "a1b2c3d4-...",
  "claim_type": "user",
  "attributed_to_user_id": "e5f6g7h8-..."
}
```

#### Tag as Guest
```json
{
  "speaker_id": "a1b2c3d4-...",
  "claim_type": "guest",
  "guest_name": "Sarah (visitor)"
}
```

### Search Users Endpoint (NEW)

**Endpoint:** `GET /auth/search`

```
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
  "total": 1
}
```

---

## Database Changes

### Migration File
`backend/migrations/002_add_claim_types.sql`

### New Columns in `session_speakers`

| Column | Type | Description |
|--------|------|-------------|
| `claim_type` | VARCHAR(20) | 'self', 'user', or 'guest' |
| `attributed_to_user_id` | UUID | User who gets the stats (for self/user) |
| `guest_name` | VARCHAR(100) | Display name (for guest) |

### Existing Columns

| Column | Type | Description |
|--------|------|-------------|
| `claimed_by` | UUID | User who performed the claiming action |
| `claimed_at` | TIMESTAMP | When the claim happened |

---

## Data Flow Examples

### Example 1: Self Claim
```
Speaker Detection → SessionSpeaker(speaker_label="SPEAKER_00")
                           ↓
User Claims Self → SessionSpeaker.claim_type = "self"
                   SessionSpeaker.claimed_by = user_a_id
                   SessionSpeaker.attributed_to_user_id = user_a_id
                           ↓
Copy Stats → WordCount(user_id=user_a_id, word="lah", count=5)
                           ↓
Results → User A: 5x lah, 3x sia...
```

### Example 2: Tag Other User
```
Speaker Detection → SessionSpeaker(speaker_label="SPEAKER_01")
                           ↓
User A Tags User B → SessionSpeaker.claim_type = "user"
                     SessionSpeaker.claimed_by = user_a_id (who clicked)
                     SessionSpeaker.attributed_to_user_id = user_b_id (who gets stats)
                           ↓
Copy Stats → WordCount(user_id=user_b_id, word="walao", count=8)
                           ↓
Results → User B: 8x walao, 2x cheebai...
```

### Example 3: Tag Guest
```
Speaker Detection → SessionSpeaker(speaker_label="SPEAKER_02")
                           ↓
User Tags Guest → SessionSpeaker.claim_type = "guest"
                  SessionSpeaker.claimed_by = user_a_id
                  SessionSpeaker.guest_name = "Sarah"
                  SessionSpeaker.attributed_to_user_id = NULL
                           ↓
NO WordCount Created → Stats remain in SpeakerWordCount only
                           ↓
Results → Sarah (Guest): 4x lah, 1x lor...
```

---

## Mobile App Integration TODO

### Files to Update

1. **Types** (`mobile/src/types/session.ts`)
```typescript
export interface Speaker {
  id: string;
  speaker_label: string;
  segment_count: number;
  claimed_by?: string;
  claim_type?: 'self' | 'user' | 'guest';  // NEW
  attributed_to_user_id?: string;          // NEW
  guest_name?: string;                     // NEW
  // ... other fields
}
```

2. **Claiming Screen** (`mobile/src/screens/ClaimingScreen.tsx`)
```typescript
// Add claim mode selector
<SegmentedControl>
  <Segment value="self">This is me</Segment>
  <Segment value="user">Tag user</Segment>
  <Segment value="guest">Tag guest</Segment>
</SegmentedControl>

// For 'user' mode: Add user search
{claimMode === 'user' && (
  <UserSearchInput
    onSearch={(query) => api.searchUsers(query, groupId)}
    onSelect={(user) => setSelectedUser(user)}
  />
)}

// For 'guest' mode: Add name input
{claimMode === 'guest' && (
  <TextInput
    placeholder="Enter guest name"
    value={guestName}
    onChangeText={setGuestName}
  />
)}
```

3. **Results Screen** (`mobile/src/screens/ResultsScreen.tsx`)
```typescript
// Display guest users
<UserCard>
  <Avatar source={user.is_guest ? null : user.avatar_url} />
  <Name>{user.display_name}</Name>
  {user.is_guest && <Badge>Guest</Badge>}  {/* NEW */}
  <WordCounts>{/* ... */}</WordCounts>
</UserCard>
```

4. **API Client** (`mobile/src/api/client.ts`)
```typescript
// Add user search method
export const searchUsers = async (
  query: string,
  groupId?: string
): Promise<UserSearchResponse> => {
  const response = await api.get('/auth/search', {
    params: { query, group_id: groupId, limit: 10 }
  });
  return response.data;
};
```

---

## Testing Scenarios

### ✅ Test Case 1: All Registered Users
**Setup:** 4 friends with accounts  
**Action:** All claim themselves  
**Expected:** All 4 get individual profile stats

### ✅ Test Case 2: Mixed Group
**Setup:** 2 registered + 2 guests  
**Action:** Registered users claim self, one tags guests  
**Expected:** 
- 2 users get profile stats
- 2 guests appear in results only
- Leaderboard shows only 2 users

### ✅ Test Case 3: Late Arrival
**Setup:** User arrives late, sees unclaimed speakers  
**Action:** Late user tags other speakers as correct users  
**Expected:** Everyone gets correct stats

### ✅ Test Case 4: Cross-Tagging
**Setup:** User A and User B in same session  
**Action:** User A tags a speaker as User B  
**Expected:** User B's profile gets those stats (not User A's)

---

## Implementation Checklist

### Backend ✅ COMPLETE
- [x] Database migration created
- [x] SQLAlchemy models updated
- [x] Pydantic schemas updated
- [x] Claim endpoint updated
- [x] Results endpoint updated
- [x] User search endpoint added
- [x] No linter errors

### Mobile 📱 TODO
- [ ] Update TypeScript types
- [ ] Add claim mode selector UI
- [ ] Add user search with autocomplete
- [ ] Add guest name input
- [ ] Update results screen for guests
- [ ] Add "Guest" badge visual
- [ ] Test all three claim modes
- [ ] Handle edge cases

### Database 🔄 TODO
- [ ] Run migration: `002_add_claim_types.sql`
- [ ] Verify new columns exist
- [ ] Test RLS policies still work
- [ ] Backfill existing claims (auto-set to 'self')

---

## Common Questions

**Q: Can guests claim speakers?**  
A: No, only registered users can perform claims. But registered users can tag speakers as guests.

**Q: Can I tag someone outside my group?**  
A: No, for privacy and data integrity, you can only tag users who are members of the same group.

**Q: What if someone tags the wrong person?**  
A: Currently claims are permanent. A future feature could add "unclaim" functionality.

**Q: Do guest stats count toward leaderboards?**  
A: No, guest stats stay in the session only and don't affect any leaderboards or personal stats.

**Q: Can I search for any user in the system?**  
A: The search endpoint can show all users OR filter to just your group members (recommended).

---

## Files Modified

### Backend
- ✅ `backend/migrations/002_add_claim_types.sql` (NEW)
- ✅ `backend/models.py`
- ✅ `backend/schemas.py`
- ✅ `backend/routers/sessions.py`
- ✅ `backend/routers/auth.py`

### Documentation
- ✅ `TASKS.md` (comprehensive feature section added)
- ✅ `CLAIMING_FEATURE_GUIDE.md` (this file)

### Mobile (Needs Update)
- ⏳ `mobile/src/types/session.ts`
- ⏳ `mobile/src/screens/ClaimingScreen.tsx`
- ⏳ `mobile/src/screens/ResultsScreen.tsx`
- ⏳ `mobile/src/api/client.ts`

---

## Next Steps

1. **Deploy Migration:** Run `002_add_claim_types.sql` on Supabase
2. **Update Mobile:** Implement three-mode claiming UI
3. **Test:** Verify all three claim modes work end-to-end
4. **Polish:** Add loading states, error handling
5. **Document:** Update mobile IMPLEMENTATION_SUMMARY.md

---

**Questions?** Check `TASKS.md` for the comprehensive feature documentation.

**Need help?** This feature is fully implemented on the backend. Mobile just needs UI updates!

---

*Last updated: January 17, 2026*
