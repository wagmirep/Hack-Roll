# 🚨 URGENT TODO: Three-Way Claiming System

**Priority:** HIGH  
**Status:** 🔴 Backend Complete - Frontend Implementation Required  
**Date:** January 17, 2026

---

## What Is This?

The backend now supports **three different ways** to claim speakers:

1. **"This is me"** → Claim as yourself
2. **"This is @username"** → Tag another registered user
3. **"This is Guest Name"** → Tag a non-registered guest

**Why?** So friends without accounts can participate in sessions!

---

## 📝 Step-by-Step Implementation Guide

### Step 1: Update Types (5 minutes)

**File:** `src/types/session.ts`

Add these fields to your `Speaker` interface:

```typescript
export interface Speaker {
  // ... existing fields
  claim_type?: 'self' | 'user' | 'guest';  // NEW
  attributed_to_user_id?: string;          // NEW
  guest_name?: string;                     // NEW
}
```

Add to your user/result interface:

```typescript
export interface SessionResult {
  // ... existing fields
  is_guest: boolean;  // NEW - indicates if this is a guest user
}
```

---

### Step 2: Add User Search API (10 minutes)

**File:** `src/api/client.ts`

Add this new function:

```typescript
export const searchUsers = async (
  query: string,
  groupId?: string
): Promise<{
  users: Array<{
    id: string;
    username: string;
    display_name?: string;
    avatar_url?: string;
  }>;
  total: number;
}> => {
  const response = await api.get('/auth/search', {
    params: { 
      query, 
      group_id: groupId, 
      limit: 10 
    },
  });
  return response.data;
};
```

---

### Step 3: Update ClaimingScreen (30-45 minutes)

**File:** `src/screens/ClaimingScreen.tsx`

#### 3a. Add State Variables

```typescript
const [claimMode, setClaimMode] = useState<'self' | 'user' | 'guest'>('self');
const [selectedUser, setSelectedUser] = useState<any>(null);
const [guestName, setGuestName] = useState('');
const [userSearchQuery, setUserSearchQuery] = useState('');
const [searchResults, setSearchResults] = useState([]);
```

#### 3b. Add Mode Selector UI

```typescript
<View style={styles.modeSelector}>
  <TouchableOpacity 
    style={[styles.modeButton, claimMode === 'self' && styles.modeButtonActive]}
    onPress={() => setClaimMode('self')}
  >
    <Text>This is me</Text>
  </TouchableOpacity>
  
  <TouchableOpacity 
    style={[styles.modeButton, claimMode === 'user' && styles.modeButtonActive]}
    onPress={() => setClaimMode('user')}
  >
    <Text>Tag user</Text>
  </TouchableOpacity>
  
  <TouchableOpacity 
    style={[styles.modeButton, claimMode === 'guest' && styles.modeButtonActive]}
    onPress={() => setClaimMode('guest')}
  >
    <Text>Tag guest</Text>
  </TouchableOpacity>
</View>
```

#### 3c. Add Conditional Input Fields

```typescript
{/* For 'user' mode: User search */}
{claimMode === 'user' && (
  <View style={styles.searchContainer}>
    <TextInput
      placeholder="Search for user..."
      value={userSearchQuery}
      onChangeText={async (text) => {
        setUserSearchQuery(text);
        if (text.length > 2) {
          const results = await searchUsers(text, currentGroupId);
          setSearchResults(results.users);
        }
      }}
      style={styles.searchInput}
    />
    
    <ScrollView style={styles.searchResults}>
      {searchResults.map(user => (
        <TouchableOpacity
          key={user.id}
          onPress={() => {
            setSelectedUser(user);
            setUserSearchQuery(user.display_name || user.username);
            setSearchResults([]);
          }}
          style={styles.searchResultItem}
        >
          <Image source={{ uri: user.avatar_url }} style={styles.avatar} />
          <Text>{user.display_name || user.username}</Text>
        </TouchableOpacity>
      ))}
    </ScrollView>
  </View>
)}

{/* For 'guest' mode: Name input */}
{claimMode === 'guest' && (
  <TextInput
    placeholder="Enter guest name (e.g., John's friend)"
    value={guestName}
    onChangeText={setGuestName}
    style={styles.guestInput}
  />
)}
```

#### 3d. Update Claim Handler

```typescript
const handleClaimSpeaker = async (speaker: Speaker) => {
  try {
    // Build claim data based on mode
    const claimData: any = {
      speaker_id: speaker.id,
      claim_type: claimMode,
    };
    
    // Add mode-specific data
    if (claimMode === 'user') {
      if (!selectedUser) {
        Alert.alert('Error', 'Please select a user');
        return;
      }
      claimData.attributed_to_user_id = selectedUser.id;
    } else if (claimMode === 'guest') {
      if (!guestName.trim()) {
        Alert.alert('Error', 'Please enter a guest name');
        return;
      }
      claimData.guest_name = guestName.trim();
    }
    
    // Make the claim
    await api.claimSpeaker(sessionId, claimData);
    
    // Success feedback
    Alert.alert('Success', `Speaker claimed as ${
      claimMode === 'self' ? 'yourself' :
      claimMode === 'user' ? selectedUser.display_name :
      guestName
    }`);
    
    // Refresh speakers
    loadSpeakers();
    
    // Reset form
    setClaimMode('self');
    setSelectedUser(null);
    setGuestName('');
    setUserSearchQuery('');
    
  } catch (error) {
    Alert.alert('Error', 'Failed to claim speaker');
    console.error(error);
  }
};
```

---

### Step 4: Update ResultsScreen (15 minutes)

**File:** `src/screens/ResultsScreen.tsx`

Update the user card rendering to handle guests:

```typescript
{results.users.map((user, index) => (
  <View key={index} style={styles.userCard}>
    {/* Avatar or Guest Badge */}
    {user.is_guest ? (
      <View style={styles.guestAvatar}>
        <Text style={styles.guestAvatarText}>Guest</Text>
      </View>
    ) : (
      <Image 
        source={{ uri: user.avatar_url || 'default_avatar_url' }} 
        style={styles.avatar} 
      />
    )}
    
    {/* Name with Guest Badge */}
    <View style={styles.userInfo}>
      <Text style={styles.userName}>
        {user.display_name || user.username || 'Unknown'}
      </Text>
      {user.is_guest && (
        <View style={styles.guestBadge}>
          <Text style={styles.guestBadgeText}>GUEST</Text>
        </View>
      )}
    </View>
    
    {/* Word counts - same as before */}
    <View style={styles.wordCounts}>
      {user.word_counts.map((wc, idx) => (
        <WordBadge key={idx} word={wc.word} count={wc.count} emoji={wc.emoji} />
      ))}
    </View>
  </View>
))}
```

Add these styles:

```typescript
const styles = StyleSheet.create({
  // ... existing styles
  
  guestAvatar: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: '#E0E0E0',
    justifyContent: 'center',
    alignItems: 'center',
  },
  guestAvatarText: {
    fontSize: 12,
    color: '#666',
    fontWeight: 'bold',
  },
  guestBadge: {
    backgroundColor: '#FFA500',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
    marginLeft: 8,
  },
  guestBadgeText: {
    color: 'white',
    fontSize: 10,
    fontWeight: 'bold',
  },
});
```

---

## ✅ Testing Checklist

Test each mode thoroughly:

### Self Claim (existing flow - should still work)
- [ ] Select "This is me"
- [ ] Claim a speaker
- [ ] Verify it appears in your stats

### User Tagging (NEW)
- [ ] Select "Tag user"
- [ ] Search for another user in your group
- [ ] Select user from search results
- [ ] Claim speaker
- [ ] Verify stats go to THAT user (not you)
- [ ] Check that user's profile shows the stats

### Guest Tagging (NEW)
- [ ] Select "Tag guest"
- [ ] Enter a guest name (e.g., "Sarah")
- [ ] Claim speaker
- [ ] Verify guest appears in session results
- [ ] Verify guest has "GUEST" badge
- [ ] Verify guest stats DON'T appear in leaderboard
- [ ] Verify guest stats DON'T affect user profiles

### Edge Cases
- [ ] Try to claim without selecting user (should error)
- [ ] Try to claim without entering guest name (should error)
- [ ] Search with no results (handle gracefully)
- [ ] Guest name with special characters (should work)
- [ ] All speakers claimed → session completes

---

## 📚 Resources

- **Quick Guide:** `../CLAIMING_FEATURE_GUIDE.md`
- **Full Spec:** `../TASKS.md` (search "THREE-WAY CLAIMING")
- **Backend Code:** `../backend/routers/sessions.py` (see claim endpoint)
- **Database Schema:** `../backend/migrations/002_add_claim_types.sql`

---

## 🎯 Why This Is Important

**Before:** Only registered users could participate  
**After:** Anyone can join sessions, stats are accurately attributed

**Use Cases:**
1. Group of 4 friends → 2 with accounts, 2 without → All can be in results
2. Late arrival → Friend tags speakers for others → Everyone gets correct stats
3. Guest speakers → Don't pollute user profiles → Clean data

---

## 💡 Pro Tips

1. **Start with types** - Get the data structures right first
2. **Test user search** - Make sure it filters by group correctly  
3. **UI can be simple** - Buttons + basic inputs are fine for MVP
4. **Guest badge** - Make it visually distinct so it's clear
5. **Error handling** - Show helpful messages if required fields missing

---

## 🚀 When You're Done

1. Test all three modes end-to-end
2. Check that stats go to the right profiles
3. Verify guests appear in results only (not leaderboards)
4. Update this file to mark as complete
5. Delete this file or mark as DONE

---

**Estimated Time:** 1-1.5 hours for a working implementation

**Questions?** Check `CLAIMING_FEATURE_GUIDE.md` or ask the team!

Good luck! 🎉
