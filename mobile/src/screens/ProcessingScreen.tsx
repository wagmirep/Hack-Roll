/**
 * ProcessingScreen.tsx - AI Processing Status Display
 *
 * PURPOSE:
 *     Show progress while backend processes the recorded audio.
 *     Displays status updates from speaker diarization and transcription.
 *
 * RESPONSIBILITIES:
 *     - Poll backend for processing status
 *     - Display progress bar with percentage
 *     - Show current processing step (diarization, transcription, etc.)
 *     - Auto-navigate to ClaimingScreen when complete
 *     - Handle processing errors gracefully
 *
 * REFERENCED BY:
 *     - RecordingScreen.tsx - Navigates here after stopping
 *     - Navigation stack - Processing step in flow
 *
 * REFERENCES:
 *     - hooks/useSessionStatus.ts - Status polling logic
 *     - api/client.ts - Backend status endpoint
 *     - components/ProgressBar.tsx - Visual progress display
 *
 * USER FLOW:
 *     1. Arrives from RecordingScreen with sessionId
 *     2. Shows "Processing your conversation..."
 *     3. Progress bar updates (0% -> 100%)
 *     4. Status text: "Analyzing speakers..." -> "Transcribing..." -> "Counting words..."
 *     5. On complete: Auto-navigate to ClaimingScreen
 *
 * PROPS:
 *     route.params.sessionId: string - Session being processed
 *     navigation: NavigationProp
 *
 * STATE:
 *     status: 'processing' | 'ready_for_claiming' | 'error'
 *     progress: number (0-100)
 *     message: string
 */
