# LahStats Mobile App

React Native + Expo app for tracking Singlish word usage.

## Setup

```bash
# Install dependencies
bun install  # or npm install

# Run on iOS simulator
bun run ios

# Run on Android emulator
bun run android

# Run with Expo Go (scan QR code)
bun run start
```

## Project Structure

```
mobile/
├── src/
│   ├── screens/
│   │   ├── RecordingScreen.js    - Group recording
│   │   ├── ProcessingScreen.js   - Processing status
│   │   ├── ClaimingScreen.js     - Speaker claiming UI
│   │   ├── ResultsScreen.js      - Session results
│   │   ├── StatsScreen.js        - Weekly/monthly stats
│   │   └── WrappedScreen.js      - Spotify Wrapped-style
│   ├── components/
│   ├── hooks/
│   ├── api/                       - API client
│   └── utils/
└── package.json
```

## Key Features

- **One-phone recording** - 16kHz mono WAV format
- **Chunk upload** - Every 30 seconds
- **Real-time polling** - Processing status updates
- **Audio playback** - For speaker claiming
- **Firebase sync** - Live group updates

## Environment Variables

Copy `.env.example` to `.env` and configure:
- `API_URL` - Backend API endpoint
- `FIREBASE_CONFIG` - Firebase configuration JSON
