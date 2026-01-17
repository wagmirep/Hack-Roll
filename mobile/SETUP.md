# Mobile App Setup Guide

## Quick Start

### 1. Install Dependencies

```bash
cd mobile
npm install
# or
bun install
```

### 2. Configure Environment Variables

Create a `.env` file in the mobile directory:

```env
# Supabase Configuration
EXPO_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
EXPO_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Backend API Configuration  
EXPO_PUBLIC_API_URL=http://localhost:8000
```

**Getting Supabase Credentials:**
1. Go to your Supabase project dashboard
2. Settings → API
3. Copy the `URL` and `anon/public` key

**For Physical Devices:**
- Replace `localhost` with your computer's IP address
- Example: `http://192.168.1.100:8000`

### 3. Start the App

```bash
npm start
```

Then press:
- `i` for iOS simulator
- `a` for Android emulator
- Scan QR with Expo Go app on physical device

## Testing the App

### 1. Sign Up / Login
- Create a new account
- Email verification may be required (check Supabase settings)

### 2. Create a Group
- Currently you need to create a group via API or directly in database
- Or implement group creation UI (TODO)

### 3. Record a Session
1. Go to Record tab
2. Grant microphone permission
3. Tap "Start Recording"
4. Have a conversation with Singlish words
5. Tap "Stop Recording"
6. Wait for processing (30-60 seconds)

### 4. Claim Your Voice
- Listen to audio samples
- Tap "That's Me!" on your voice
- View your word counts

### 5. View Stats
- Go to Stats tab
- See group leaderboards
- Switch between week/month/all-time

## Architecture Overview

```
App.js (Root)
  └── AuthProvider (Auth state)
      └── AppNavigator (Navigation)
          ├── AuthNavigator (Not logged in)
          │   ├── LoginScreen
          │   └── SignupScreen
          │
          └── MainNavigator (Logged in)
              ├── RecordTab
              │   ├── RecordingScreen
              │   ├── ProcessingScreen
              │   ├── ClaimingScreen
              │   └── ResultsScreen
              │
              └── StatsTab
                  └── StatsScreen
```

## Key Files

### Core Infrastructure
- `src/lib/supabase.ts` - Supabase client setup
- `src/contexts/AuthContext.tsx` - Authentication state
- `src/api/client.ts` - API client with JWT interceptors
- `src/navigation/` - Navigation structure

### Hooks
- `useRecording.ts` - Audio recording & chunk upload
- `useSessionStatus.ts` - Poll processing status
- `useAudioPlayback.ts` - Play audio samples

### Screens
- `RecordingScreen.tsx` - Start/stop recording
- `ProcessingScreen.tsx` - Show processing progress
- `ClaimingScreen.tsx` - Claim speaker identity
- `ResultsScreen.tsx` - View session results
- `StatsScreen.tsx` - Group leaderboards

### Components
- `SpeakerCard.tsx` - Display speaker with audio player
- `AudioPlayer.tsx` - Play/pause audio samples
- `ProgressBar.tsx` - Processing progress indicator
- `WordBadge.tsx` - Display word + count

## API Endpoints Used

```
Auth:
  POST /auth/signup (via Supabase)
  POST /auth/signin (via Supabase)
  GET  /auth/me

Sessions:
  POST /sessions
  POST /sessions/{id}/chunks
  POST /sessions/{id}/end
  GET  /sessions/{id}
  GET  /sessions/{id}/speakers
  POST /sessions/{id}/claim
  GET  /sessions/{id}/results

Stats:
  GET /groups/{id}/stats
  GET /users/me/stats
  GET /users/me/wrapped
```

## Troubleshooting

### "Network request failed"
- Check backend is running on port 8000
- Verify EXPO_PUBLIC_API_URL is correct
- For physical devices, use IP address instead of localhost

### "Microphone permission denied"
- iOS: Settings → Privacy → Microphone → LahStats
- Android: App Settings → Permissions → Microphone

### "Audio recording not working in simulator"
- iOS simulator doesn't support microphone input
- Test on a physical device instead

### "Supabase auth errors"
- Verify EXPO_PUBLIC_SUPABASE_URL and ANON_KEY
- Check Supabase project is active
- Ensure Auth is enabled in Supabase

### "Processing stuck at X%"
- Check backend logs for errors
- Verify ML models are loaded correctly
- Ensure audio chunks uploaded successfully

## Next Steps

### Immediate TODO
1. Add group creation UI
2. Add invite code joining flow
3. Implement pull-to-refresh on stats
4. Add error boundaries
5. Add loading skeletons

### Future Enhancements
1. Wrapped screen implementation
2. Push notifications
3. Profile editing
4. Group management (leave, delete)
5. Export data feature

## Development Tips

### Hot Reload
- Save files to auto-reload
- Shake device for dev menu
- Press `r` in terminal to reload manually

### Debugging
- Use React DevTools (open dev menu → Debug)
- Check Metro bundler logs
- Use `console.log()` liberally

### Testing on Physical Device
1. Same WiFi network as development machine
2. Use IP address in API_URL
3. Grant microphone permissions
4. Record in a quiet environment

## Production Checklist

- [ ] Update all environment variables
- [ ] Remove console.log statements
- [ ] Test on multiple devices
- [ ] Optimize images and assets
- [ ] Set up error monitoring (Sentry)
- [ ] Configure push notifications
- [ ] Set up analytics
- [ ] Create app icons and splash screen
- [ ] Build and test production builds
- [ ] Submit to App Store / Play Store

## Support

For issues:
1. Check this guide first
2. Review backend logs
3. Check Supabase dashboard
4. Ask in team chat
