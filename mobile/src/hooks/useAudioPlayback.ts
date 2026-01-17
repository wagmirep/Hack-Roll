/**
 * useAudioPlayback.ts - Audio Playback Hook
 *
 * PURPOSE:
 *     Manage audio playback state for speaker samples.
 *     Provides play, pause, seek functionality.
 *
 * RESPONSIBILITIES:
 *     - Load audio from URL
 *     - Control playback (play/pause/stop)
 *     - Track playback position and duration
 *     - Handle loading and error states
 *     - Clean up on unmount
 *
 * REFERENCED BY:
 *     - components/AudioPlayer.tsx - Playback component
 *     - screens/ClaimingScreen.tsx - Direct playback control
 *
 * REFERENCES:
 *     - expo-av - Audio playback API
 *
 * PARAMS:
 *     audioUrl: string - URL of audio file to play
 *
 * RETURNS:
 *     {
 *         // State
 *         isPlaying: boolean
 *         isLoading: boolean
 *         isLoaded: boolean
 *         position: number (milliseconds)
 *         duration: number (milliseconds)
 *         error: string | null
 *
 *         // Derived
 *         progress: number (0-1)
 *         positionFormatted: string (MM:SS)
 *         durationFormatted: string (MM:SS)
 *
 *         // Actions
 *         play: () => Promise<void>
 *         pause: () => Promise<void>
 *         stop: () => Promise<void>
 *         seek: (position: number) => Promise<void>
 *         replay: () => Promise<void>
 *     }
 *
 * BEHAVIOR:
 *     - Auto-loads audio when URL provided
 *     - Auto-stops when reaching end
 *     - Cleans up sound object on unmount
 *     - Only one audio can play at a time (app-wide)
 */
