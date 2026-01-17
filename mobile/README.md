# LahStats Mobile App

React Native mobile app for tracking Singlish word usage in group conversations.

## Features

- 🎙️ Record group conversations
- 🗣️ AI-powered speaker diarization
- 📝 Automatic transcription
- 🏆 Group leaderboards
- 📊 Personal statistics
- 🎁 Wrapped-style yearly recaps

## Tech Stack

- **Framework**: React Native (Expo)
- **Language**: TypeScript
- **Navigation**: React Navigation
- **Auth**: Supabase Auth
- **State Management**: React Context
- **Audio**: Expo AV
- **HTTP Client**: Axios

## Setup

### Prerequisites

- Node.js 18+ 
- Expo CLI
- iOS Simulator (Mac) or Android Emulator

### Installation

1. Install dependencies:
```bash
npm install
# or
bun install
```

2. Create `.env` file:
```bash
cp .env.example .env
```

3. Update `.env` with your credentials:
```env
EXPO_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
EXPO_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
EXPO_PUBLIC_API_URL=http://localhost:8000
```

4. Start the app:
```bash
npm start
# or
bun start
```

### Running on Devices

**iOS Simulator:**
```bash
npm run ios
```

**Android Emulator:**
```bash
npm run android
```

**Physical Device:**
1. Install Expo Go app
2. Scan QR code from `npm start`
3. Update `EXPO_PUBLIC_API_URL` to your computer's IP address

## Project Structure

```
mobile/
├── src/
│   ├── api/              # API client & endpoints
│   ├── components/       # Reusable components
│   ├── contexts/         # React contexts
│   ├── hooks/            # Custom hooks
│   ├── lib/              # Third-party integrations
│   ├── navigation/       # Navigation setup
│   ├── screens/          # Screen components
│   ├── types/            # TypeScript types
│   └── utils/            # Utility functions
├── assets/               # Images, fonts
├── App.js               # Root component
└── package.json
```

## Key Components

### Authentication Flow
- `LoginScreen` - User sign in
- `SignupScreen` - User registration
- `AuthContext` - Auth state management

### Recording Flow
1. **RecordingScreen** - Start/stop recording
2. **ProcessingScreen** - AI processing progress
3. **ClaimingScreen** - Claim your voice
4. **ResultsScreen** - View session results

### Statistics
- **StatsScreen** - Group leaderboards
- **WrappedScreen** - Yearly recap (coming soon)

## API Integration

The app communicates with the FastAPI backend:

- **Auth**: JWT tokens via Supabase
- **Sessions**: Create, upload chunks, end
- **Claiming**: Claim speakers, get results
- **Stats**: Group and personal statistics

See `src/api/client.ts` for all endpoints.

## Development

### Adding a New Screen

1. Create screen in `src/screens/`
2. Add route in navigation
3. Import in navigator

### Adding a New API Endpoint

1. Add method in `src/api/client.ts`
2. Define types in `src/types/`
3. Use in components via hooks

## Troubleshooting

### Microphone Permission Denied
- iOS: Check Settings > Privacy > Microphone
- Android: Check App Permissions in Settings

### Network Errors
- Ensure backend is running
- Update `EXPO_PUBLIC_API_URL` with correct IP
- Check firewall settings

### Audio Recording Issues
- Test on physical device (simulators have limited audio)
- Ensure proper audio format (WAV, 16kHz, mono)

## Testing

Run tests:
```bash
npm test
```

## Building

### Development Build
```bash
eas build --profile development --platform ios
```

### Production Build
```bash
eas build --profile production --platform all
```

## Contributing

1. Create feature branch
2. Make changes
3. Test thoroughly
4. Submit pull request

## License

MIT
