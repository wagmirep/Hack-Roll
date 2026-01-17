# 🚀 Quick Start Guide

## Get Running in 5 Minutes

### 1. Install Dependencies (1 min)
```bash
cd mobile
npm install
```

### 2. Set Up Environment (2 min)

Edit `mobile/.env`:
```env
EXPO_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
EXPO_PUBLIC_SUPABASE_ANON_KEY=eyJhbGci...
EXPO_PUBLIC_API_URL=http://localhost:8000
```

**Get Supabase Credentials:**
- Dashboard → Settings → API
- Copy URL and anon key

### 3. Start Backend (1 min)
```bash
# In backend directory
cd ../backend
python -m uvicorn main:app --reload
```

### 4. Start Mobile App (1 min)
```bash
# In mobile directory
npm start
```

Press:
- `i` for iOS
- `a` for Android
- Scan QR for physical device

## First Time Flow

1. **Sign Up**
   - Email + password + username
   - Check email for verification (optional)

2. **Create/Join Group**
   - (Manual for now - add via API/database)
   - OR implement group creation screen

3. **Record Session**
   - Tap "Start Recording"
   - Talk with Singlish words
   - Tap "Stop Recording"

4. **Wait for Processing**
   - 30-60 seconds
   - Shows progress bar

5. **Claim Your Voice**
   - Play audio samples
   - Tap "That's Me!"

6. **View Results**
   - See your word counts
   - Check leaderboard

## Testing Checklist

✅ **Basic Flow:**
- [ ] Sign up/login works
- [ ] Microphone permission granted
- [ ] Recording starts/stops
- [ ] Chunks upload (check network tab)
- [ ] Processing completes
- [ ] Audio samples play
- [ ] Claiming works
- [ ] Results display

✅ **Edge Cases:**
- [ ] Network error handling
- [ ] Permission denied
- [ ] Stop before first chunk
- [ ] Multiple claims

## Common Issues

**"Network request failed"**
```bash
# Use your IP instead of localhost
EXPO_PUBLIC_API_URL=http://192.168.1.100:8000
```

**"Microphone not working"**
- Use physical device (simulator doesn't support mic)
- Grant permissions in Settings

**"Supabase auth error"**
- Double-check URL and anon key
- Ensure no trailing slashes

## Development Commands

```bash
# Start app
npm start

# Clear cache
npm start -- --clear

# iOS simulator
npm run ios

# Android emulator
npm run android

# Format code
npm run format
```

## Directory Structure

```
mobile/
├── src/
│   ├── screens/       👈 UI screens
│   ├── components/    👈 Reusable components
│   ├── hooks/         👈 Custom hooks
│   ├── api/           👈 Backend API
│   └── navigation/    👈 Navigation setup
├── App.js            👈 Root component
└── .env              👈 Configuration
```

## Key Files to Know

- `App.js` - App entry point
- `src/contexts/AuthContext.tsx` - Auth state
- `src/api/client.ts` - API calls
- `src/hooks/useRecording.ts` - Recording logic
- `src/screens/RecordingScreen.tsx` - Main screen

## Next Steps

1. Test the complete flow
2. Add group creation UI
3. Implement invite codes
4. Polish UI/UX
5. Deploy backend
6. Build production app

## Help

- Read `README.md` for full docs
- Check `SETUP.md` for detailed setup
- See `IMPLEMENTATION_SUMMARY.md` for architecture

**Happy coding! 🎉**
