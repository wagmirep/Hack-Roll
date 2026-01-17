# Global Leaderboard Feature

## Overview
Added a global leaderboard feature to the Stats tab that shows stats across ALL users in the system (not just within a specific group). This allows you to verify that stats are being updated correctly system-wide.

## Changes Made

### 1. Backend Changes

#### A. Added New Schema (`backend/schemas.py`)
- **GlobalLeaderboardResponse**: New response model for global leaderboard data
  - `period`: Time period filter
  - `total_users`: Total number of users with activity
  - `total_sessions`: Total sessions across all groups
  - `total_words`: Total words detected globally
  - `leaderboard`: List of user stats ranked by total words
  - `top_words`: Most frequently used Singlish words globally

#### B. New API Endpoint (`backend/routers/stats.py`)
- **GET `/users/global/leaderboard`**
  - Query parameter: `period` (day, week, month, all_time)
  - Returns global statistics across all users
  - Includes:
    - Total users, sessions, and words
    - Global leaderboard ranked by word count
    - Top 10 most used Singlish words globally
  - Requires authentication (must be logged in)

### 2. Mobile App Changes

#### A. API Client (`mobile/src/api/client.ts`)
- Added `getGlobalLeaderboard(period)` method to stats API module

#### B. Stats Screen UI (`mobile/src/screens/StatsScreen.tsx`)
Enhanced the Stats screen with:

1. **View Mode Toggle**
   - Switch between "Group" and "Global" views
   - Prominently displayed at the top of the screen

2. **Global View Features**
   - **Summary Cards**: Shows total users, sessions, and words
   - **Top Singlish Words Section**: Displays the 5 most used words globally with emoji indicators
   - **Global Leaderboard**: Shows all users ranked by total word count
     - Rank badges with color coding (gold/silver/bronze for top 3)
     - User display names and usernames
     - Total word counts
     - Top 3 words per user with emoji indicators

3. **Group View** (Existing Functionality)
   - Kept all existing group stats functionality
   - Group selector for switching between your groups
   - Group-specific leaderboards and statistics

## UI Layout

```
Stats Screen
├── View Mode Toggle [Group | Global]
├── Period Selector [Week | Month | All Time]
├── Group Selector (only in Group mode)
└── Content Area
    ├── Global Mode:
    │   ├── Summary Card (Users | Sessions | Total Words)
    │   ├── Top Singlish Words 🔥
    │   │   └── Top 5 words with counts
    │   └── Global Leaderboard 🌍
    │       └── All users ranked by word count
    │
    └── Group Mode:
        ├── Summary Card (Sessions | Total Words)
        └── Group Leaderboard 🏆
            └── Group members ranked by word count
```

## How to Use

1. **Navigate to Stats Tab** in the mobile app
2. **Toggle to "Global"** view using the view mode selector
3. **Select a time period** (Week, Month, or All Time)
4. **View the global leaderboard** to see:
   - How many users are active
   - Total sessions and words across the system
   - Most popular Singlish words
   - User rankings by word count

## Testing the Feature

### Backend Testing
```bash
# Test the endpoint (requires authentication token)
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/users/global/leaderboard?period=all_time"
```

Expected response:
```json
{
  "period": "all_time",
  "total_users": 5,
  "total_sessions": 12,
  "total_words": 347,
  "leaderboard": [
    {
      "rank": 1,
      "user_id": "...",
      "username": "john_tan",
      "display_name": "John Tan",
      "total_words": 125,
      "word_counts": [
        {"word": "lah", "count": 45, "emoji": "🗣️"},
        ...
      ]
    },
    ...
  ],
  "top_words": [
    {"word": "lah", "count": 234, "emoji": "🗣️"},
    {"word": "walao", "count": 189, "emoji": "😱"},
    ...
  ]
}
```

### Mobile App Testing
1. Open the app and navigate to the Stats tab
2. Click on "Global" to switch to global view
3. Verify that:
   - Summary statistics show correct totals
   - Top words are displayed with emojis
   - Leaderboard shows all users ranked correctly
   - Rank badges are colored appropriately (gold/silver/bronze)

## Benefits

1. **System-wide Verification**: Easily check if stats are being recorded correctly across all users
2. **Motivation**: Users can see where they rank globally
3. **Engagement**: Top words section shows what's trending in the community
4. **Debugging**: Developers can quickly verify the stats system is working
5. **Competitive Element**: Global leaderboard encourages usage

## Technical Notes

- The global leaderboard endpoint uses the same date filtering logic as group stats
- The endpoint is protected and requires authentication
- Word counts are aggregated across all groups for each user
- Emojis are fetched from the `target_words` table
- The leaderboard is sorted by total word count in descending order
- Rank badges use color coding: Gold (#FFD700), Silver (#C0C0C0), Bronze (#CD7F32), Blue (#007AFF)

## Auto-Reload

Since both the backend (uvicorn with --reload) and mobile app (npm start) are running with hot reload enabled:
- Backend changes are automatically applied when you save files
- Mobile changes may require refreshing the app or may auto-reload depending on the change

## Future Enhancements

Possible improvements:
1. Add pagination for large leaderboards
2. Show user's global rank even if they're not in top positions
3. Add filters for specific time periods (daily, weekly trends)
4. Show percentage change compared to previous period
5. Add sharing capabilities for leaderboard positions
6. Show badges/achievements for top performers
