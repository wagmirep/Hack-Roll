/**
 * RecordingScreen.tsx - Main Recording Interface
 *
 * PURPOSE:
 *     Primary screen for group audio recording.
 *     "One phone on the table" recording experience.
 *
 * RESPONSIBILITIES:
 *     - Display recording UI with start/stop button
 *     - Show live recording duration
 *     - Capture audio at 16kHz mono WAV format
 *     - Upload audio chunks every 30 seconds
 *     - Display recording status and indicators
 *     - Navigate to ProcessingScreen when stopped
 *
 * REFERENCED BY:
 *     - App.tsx / Navigation - Main tab or home screen
 *     - Navigation stack - Entry point for recording flow
 *
 * REFERENCES:
 *     - hooks/useRecording.ts - Recording logic and state
 *     - api/client.ts - Upload chunks to backend
 *     - components/ProgressBar.tsx - Recording duration display
 *
 * USER FLOW:
 *     1. User opens app -> lands on this screen
 *     2. User taps "Start Recording"
 *     3. Timer shows elapsed time
 *     4. Chunks upload every 30s in background
 *     5. User taps "Stop Recording"
 *     6. Navigate to ProcessingScreen
 *
 * PROPS:
 *     navigation: NavigationProp - React Navigation prop
 *
 * STATE:
 *     isRecording: boolean
 *     duration: number (seconds)
 *     sessionId: string | null
 *     uploadProgress: number
 */
