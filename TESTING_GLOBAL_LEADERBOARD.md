# Testing the Global Leaderboard Feature

## ✅ Status: Implementation Complete

The global leaderboard feature has been successfully implemented and the backend endpoint is registered and running.

## Backend Verification

### Endpoint Details
- **URL**: `GET /users/global/leaderboard`
- **Query Parameter**: `period` (day, week, month, all_time)
- **Authentication**: Required (Bearer token)

### Verified Routes
```
✅ GET /users/me/stats
✅ GET /users/me/wrapped
✅ GET /users/global/leaderboard  ← NEW
✅ GET /users/me/trends
```

## Mobile App Testing

### Prerequisites
1. Backend server must be running on port 8000
2. Mobile app must be running (npm start)
3. You must be logged in with a valid user account

### Testing Steps

1. **Navigate to Stats Tab**
   - Open the mobile app
   - Tap on the "Stats" tab in the bottom navigation

2. **Switch to Global View**
   - At the top of the screen, you'll see two buttons: "Group" and "Global"
   - Tap on "Global" to switch to the global leaderboard view

3. **Verify Display Elements**
   - ✅ Summary Card showing:
     - Total Users
     - Total Sessions
     - Total Words
   
   - ✅ Top Singlish Words section showing:
     - Top 5 most used words with emojis
     - Word counts for each
   
   - ✅ Global Leaderboard showing:
     - User ranks (with colored badges)
     - User display names and usernames
     - Total word counts per user
     - Top 3 words per user with emojis

4. **Test Period Filters**
   - Try switching between "Week", "Month", and "All Time"
   - Verify that the data updates correctly for each period

5. **Switch Back to Group View**
   - Tap "Group" to verify you can switch back
   - Verify group stats still work correctly

## Expected Behavior

### Global View Shows:
- **All users** across all groups (not just your groups)
- Aggregate statistics across the entire system
- Most popular Singlish words globally
- Global rankings by total word count

### Group View Shows:
- Only users within the selected group
- Group-specific statistics
- Group leaderboard

## Testing with Sample Data

If you want to verify stats are updating correctly:

1. **Create multiple users** (or use existing ones)
2. **Record sessions** in different groups
3. **Claim speakers** and attribute words to users
4. **Check the global leaderboard** to see:
   - Are all users showing up?
   - Are word counts correct?
   - Is the ranking order correct?
   - Are the top words accurate?

## Troubleshooting

### Backend Not Responding
```bash
# Check if backend is running
curl http://localhost:8000/docs

# Expected: HTML response for Swagger docs
```

### Mobile App Not Showing Global Stats
1. Check console logs for errors
2. Verify backend URL in mobile/.env: `EXPO_PUBLIC_API_URL=http://localhost:8000`
3. Restart the mobile app if needed

### No Data Showing
- Ensure you have at least one completed session with claimed speakers
- Verify word counts exist in the database
- Check that the period filter matches when data was created

## API Testing (Optional)

You can test the endpoint directly using curl:

```bash
# First, get your auth token from the mobile app or login endpoint
TOKEN="your_jwt_token_here"

# Test the global leaderboard endpoint
curl -H "Authorization: Bearer $TOKEN" \
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
      "word_counts": [...]
    }
  ],
  "top_words": [
    {"word": "lah", "count": 234, "emoji": "🗣️"},
    ...
  ]
}
```

## Success Criteria

- ✅ Backend endpoint registered and responding
- ✅ Mobile UI shows toggle between Group and Global views
- ✅ Global view displays summary statistics
- ✅ Global view shows top words section
- ✅ Global view shows leaderboard with all users
- ✅ Period filters work correctly
- ✅ Data updates when switching periods
- ✅ Can switch back to group view without issues

## Files Modified

### Backend
1. `backend/schemas.py` - Added `GlobalLeaderboardResponse`
2. `backend/routers/stats.py` - Added `/users/global/leaderboard` endpoint

### Mobile
1. `mobile/src/api/client.ts` - Added `getGlobalLeaderboard` method
2. `mobile/src/screens/StatsScreen.tsx` - Added global view UI and logic

## Next Steps

Once testing is complete and working:
1. Test with multiple users and sessions
2. Verify performance with larger datasets
3. Consider adding pagination if leaderboard grows large
4. Optionally add user's rank highlight in global view
5. Consider adding animated transitions between views
