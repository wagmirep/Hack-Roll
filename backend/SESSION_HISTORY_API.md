# Session History & Comparison API

New endpoints for viewing session history, comparing sessions, and tracking trends over time.

---

## 📋 **GET /sessions** - List Session History

Get paginated list of past sessions with summary stats.

### Query Parameters:
- `group_id` (optional): Filter by specific group UUID
- `status` (optional): Filter by status (`recording`, `processing`, `ready_for_claiming`, `completed`, `failed`)
- `limit` (optional): Number of results (default: 20, max: 100)
- `offset` (optional): Pagination offset (default: 0)

### Response:
```json
[
  {
    "id": "uuid",
    "group_id": "uuid",
    "started_by": "uuid",
    "started_by_name": "Alice Tan",
    "status": "completed",
    "started_at": "2026-01-15T14:30:00Z",
    "ended_at": "2026-01-15T15:00:00Z",
    "duration_seconds": 1800,
    "total_speakers": 4,
    "my_total_words": 45,
    "group_total_words": 180
  }
]
```

### Example Usage (Mobile):
```typescript
// Get last 20 sessions
const sessions = await api.sessions.list();

// Get completed sessions for a specific group
const groupSessions = await api.sessions.list(
  groupId, 
  'completed', 
  20, 
  0
);

// Pagination
const nextPage = await api.sessions.list(groupId, null, 20, 20);
```

---

## 📊 **GET /sessions/{session_id}/my-stats** - Get My Session Stats

Get your personal word counts for a specific session.

### Response:
```json
{
  "session_id": "uuid",
  "user_id": "uuid",
  "username": "alice_tan",
  "display_name": "Alice Tan",
  "word_counts": [
    { "word": "lah", "count": 12, "emoji": "💬" },
    { "word": "walao", "count": 5, "emoji": "😱" }
  ],
  "total_words": 17,
  "session_started_at": "2026-01-15T14:30:00Z",
  "session_duration": 1800
}
```

### Example Usage (Mobile):
```typescript
const myStats = await api.sessions.getMyStats(sessionId);

console.log(`I said ${myStats.total_words} words in this session`);
console.log(`My favorite word was: ${myStats.word_counts[0].word}`);
```

---

## 🔄 **GET /sessions/compare** - Compare Multiple Sessions

Compare your performance across 2-10 sessions.

### Query Parameters:
- `session_ids` (required): Array of 2-10 session UUIDs

### Response:
```json
{
  "user_id": "uuid",
  "sessions": [
    {
      "session_id": "uuid",
      "started_at": "2026-01-10T14:00:00Z",
      "total_words": 45,
      "unique_words": 8,
      "word_counts": [
        { "word": "lah", "count": 12, "emoji": "💬" }
      ]
    },
    {
      "session_id": "uuid",
      "started_at": "2026-01-15T14:00:00Z",
      "total_words": 52,
      "unique_words": 9,
      "word_counts": [
        { "word": "lah", "count": 15, "emoji": "💬" }
      ]
    }
  ],
  "total_across_sessions": 97,
  "average_per_session": 48.5
}
```

### Example Usage (Mobile):
```typescript
const comparison = await api.sessions.compare([sessionId1, sessionId2]);

console.log(`Average: ${comparison.average_per_session} words/session`);
console.log(`Trend: ${comparison.sessions[1].total_words > comparison.sessions[0].total_words ? '📈 Up' : '📉 Down'}`);
```

---

## 📈 **GET /users/me/trends** - Get Usage Trends

Get time-series data of your Singlish usage over time.

### Query Parameters:
- `granularity` (optional): `day`, `week`, or `month` (default: `day`)
- `limit` (optional): Number of data points (default: 30, max: 365)
- `group_id` (optional): Filter by group

### Response:
```json
[
  {
    "period": "2026-01-01T00:00:00Z",
    "total_words": 45,
    "sessions": 2
  },
  {
    "period": "2026-01-02T00:00:00Z",
    "total_words": 32,
    "sessions": 1
  }
]
```

### Example Usage (Mobile):
```typescript
// Get daily trends for last 30 days
const dailyTrends = await api.stats.getTrends('day', 30);

// Get weekly trends for last 12 weeks
const weeklyTrends = await api.stats.getTrends('week', 12);

// Plot on chart
const chartData = dailyTrends.map(point => ({
  x: point.period,
  y: point.total_words
}));
```

---

## 🎯 **Use Cases**

### 1. Session History Screen
```typescript
// Show list of past sessions
const sessions = await api.sessions.list(groupId, 'completed');

sessions.forEach(session => {
  console.log(`
    ${session.started_by_name} started a session
    Duration: ${session.duration_seconds}s
    You said: ${session.my_total_words} words
    Group total: ${session.group_total_words} words
  `);
});
```

### 2. Session Detail View
```typescript
// Tap on a session to see details
const sessionStats = await api.sessions.getMyStats(sessionId);
const sessionResults = await api.sessions.getResults(sessionId);

// Show both personal stats and full session results
```

### 3. Progress Tracking
```typescript
// Compare last 5 sessions to see improvement
const recentSessions = await api.sessions.list(groupId, 'completed', 5);
const sessionIds = recentSessions.map(s => s.id);
const comparison = await api.sessions.compare(sessionIds);

if (comparison.sessions[0].total_words < comparison.sessions[4].total_words) {
  console.log('You\'re using more Singlish! 📈');
}
```

### 4. Trend Visualization
```typescript
// Show chart of usage over time
const trends = await api.stats.getTrends('week', 12, groupId);

// Use in a chart library (e.g., react-native-chart-kit)
<LineChart
  data={{
    labels: trends.map(t => formatDate(t.period)),
    datasets: [{
      data: trends.map(t => t.total_words)
    }]
  }}
/>
```

### 5. Personal vs Group Comparison
```typescript
// See how you stack up
const myStats = await api.stats.getMyStats('week', groupId);
const groupStats = await api.stats.getGroupStats(groupId, 'week');

const myRank = groupStats.leaderboard.findIndex(u => u.user_id === myUserId) + 1;
const myPercentage = (myStats.total_words / groupStats.total_words) * 100;

console.log(`You're #${myRank} in the group!`);
console.log(`You contribute ${myPercentage.toFixed(1)}% of the group's Singlish`);
```

---

## 🚀 **Quick Integration Checklist**

- [x] Backend endpoints implemented
- [x] Mobile API client updated
- [ ] Add Session History Screen to mobile app
- [ ] Add Session Detail Screen
- [ ] Add Trends Chart component
- [ ] Add Session Comparison view
- [ ] Update navigation to include history

---

## 📱 **Suggested Mobile Screens**

### 1. **History Tab**
- List of past sessions (using `GET /sessions`)
- Pull-to-refresh
- Infinite scroll pagination
- Tap to view session details

### 2. **Session Detail Screen**
- Session info (date, duration, participants)
- Your stats (using `GET /sessions/{id}/my-stats`)
- Full results (using `GET /sessions/{id}/results`)
- Button to compare with other sessions

### 3. **Trends Screen** 
- Chart of usage over time (using `GET /users/me/trends`)
- Toggle between day/week/month
- Filter by group
- Show key insights (average, peak, trend direction)

### 4. **Comparison View**
- Select multiple sessions to compare
- Side-by-side stats
- Highlight improvements or declines

---

## ✅ **All Data Is Preserved**

Every recording session and word count is permanently saved in the database:

- ✅ All session metadata (date, duration, participants)
- ✅ Per-session word counts (who said what)
- ✅ Individual user stats over time
- ✅ Group aggregates
- ✅ Guest participants (in session results only)

**Nothing is deleted** unless you explicitly call delete endpoints (which don't exist yet!).
