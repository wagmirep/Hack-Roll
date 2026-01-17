/**
 * AudioPlayer.tsx - Audio Playback Component
 *
 * PURPOSE:
 *     Reusable audio player for playing speaker sample clips.
 *     Used in ClaimingScreen for speaker identification.
 *
 * RESPONSIBILITIES:
 *     - Load and play audio from URL
 *     - Display play/pause button
 *     - Show playback progress
 *     - Handle loading and error states
 *     - Auto-stop when unmounted
 *
 * REFERENCED BY:
 *     - screens/ClaimingScreen.tsx - Play speaker samples
 *     - components/SpeakerCard.tsx - Embedded player
 *
 * REFERENCES:
 *     - hooks/useAudioPlayback.ts - Playback logic
 *     - expo-av - Audio playback library
 *
 * PROPS:
 *     audioUrl: string - URL of audio file to play
 *     onPlay?: () => void - Callback when playback starts
 *     onStop?: () => void - Callback when playback stops
 *     onError?: (error: Error) => void - Error handler
 *     autoPlay?: boolean - Start playing immediately (default: false)
 *     style?: ViewStyle - Container style override
 *
 * STATE:
 *     isPlaying: boolean
 *     isLoading: boolean
 *     progress: number (0-1)
 *     duration: number (seconds)
 *     error: string | null
 *
 * UI ELEMENTS:
 *     - Play/Pause button (icon)
 *     - Progress bar
 *     - Duration text (0:00 / 0:05)
 *     - Loading spinner (while loading)
 */
