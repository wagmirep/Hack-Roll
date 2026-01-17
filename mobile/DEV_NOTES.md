# Mobile App Development Notes

## 🚨 URGENT: NEW FEATURE TO IMPLEMENT

### Three-Way Speaker Claiming System

**Priority:** HIGH  
**Status:** 🔴 Backend Complete - Frontend Implementation Required  
**Added:** January 17, 2026

The backend now supports **three claiming modes** instead of just self-claiming:
1. **Claim as yourself**
2. **Tag another registered user** 
3. **Tag as guest participant**

**📝 Implementation Guide:** See `TODO_THREE_WAY_CLAIMING.md` in this directory

**Files to update:**
- `src/types/session.ts` - Add new fields
- `src/api/client.ts` - Add user search endpoint
- `src/screens/ClaimingScreen.tsx` - Add 3-mode UI
- `src/screens/ResultsScreen.tsx` - Display guests

**Estimated Time:** 1-1.5 hours

---

## ✅ Setup Complete!

The Expo development server is now running on your machine.

### Current Status

- **Expo Server**: Running on `http://localhost:8081`
- **Metro Bundler**: Active and responding
- **Environment Variables**: Configured (`.env`)

### How to Test the App

#### Option 1: iOS Simulator (Mac only)
In a new terminal:
```bash
cd /Users/winstonyang/Desktop/Coding/Hackathons/hacknroll/Hack-Roll/mobile
npm run ios
```

#### Option 2: Android Emulator
Make sure Android Studio is installed and an emulator is running, then:
```bash
cd /Users/winstonyang/Desktop/Coding/Hackathons/hacknroll/Hack-Roll/mobile
npm run android
```

#### Option 3: Physical Device (Expo Go App)
1. Install "Expo Go" app on your phone (iOS/Android)
2. Make sure your phone and computer are on the same WiFi
3. Open Expo Go and scan the QR code from the terminal
4. Or visit: `http://localhost:8081` in your browser to see the QR code

#### Option 4: Web Browser (for quick testing)
```bash
cd /Users/winstonyang/Desktop/Coding/Hackathons/hacknroll/Hack-Roll/mobile
npm run web
```

### Important Notes

⚠️ **Supabase Configuration Needed**

The app is configured to use Supabase URL: `https://tamrgxhjyabdvtubseyu.supabase.co`

However, you still need to set the **SUPABASE_ANON_KEY** in `.env`:
1. Go to [Supabase Dashboard](https://app.supabase.com)
2. Select your project
3. Go to Settings → API
4. Copy the `anon/public` key
5. Update in `/Users/winstonyang/Desktop/Coding/Hackathons/hacknroll/Hack-Roll/mobile/.env`:
   ```env
   EXPO_PUBLIC_SUPABASE_ANON_KEY=your-actual-anon-key-here
   ```

### Package Version Warnings

The following packages have version mismatches (non-critical but recommended to fix):
- `react-native@0.73.0` → should be `0.73.6`
- `react-native-screens@3.37.0` → should be `~3.29.0`
- `react-native-safe-area-context@4.14.1` → should be `4.8.2`
- `@react-native-async-storage/async-storage@1.24.0` → should be `1.21.0`

To fix (optional):
```bash
cd /Users/winstonyang/Desktop/Coding/Hackathons/hacknroll/Hack-Roll/mobile
npx expo install --fix
```

### Stopping the Server

To stop the Expo server:
1. Find the terminal where it's running (terminal #7)
2. Press `Ctrl+C`

### Useful Expo Commands

While the server is running, press:
- `i` - Open iOS simulator
- `a` - Open Android emulator
- `w` - Open in web browser
- `r` - Reload app
- `m` - Toggle menu
- `c` - Clear cache and reload

### Next Steps

1. Get the Supabase anon key and update `.env`
2. Make sure the backend API is running on `http://localhost:8000`
3. Test the authentication flow (login/signup)
4. Test audio recording features

### Troubleshooting

**"Network request failed"**
- Ensure backend is running: `cd ../backend && uvicorn main:app --reload`
- Check `EXPO_PUBLIC_API_URL` in `.env`

**"Supabase auth error"**
- Verify you've set the correct `EXPO_PUBLIC_SUPABASE_ANON_KEY`
- Check Supabase project is active

**Metro Bundler issues**
```bash
# Clear cache and restart
npx expo start -c
```

---

**Created:** 2026-01-17
**Last Updated:** 2026-01-17
