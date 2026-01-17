/**
 * useRecording.ts - Audio Recording Hook
 *
 * PURPOSE:
 *     Manage audio recording state and logic.
 *     Handles start, stop, chunking, and upload.
 *
 * RESPONSIBILITIES:
 *     - Request microphone permissions
 *     - Start audio recording at 16kHz mono
 *     - Track recording duration
 *     - Split recording into 30-second chunks
 *     - Upload chunks to backend in background
 *     - Stop recording and finalize session
 *     - Handle recording errors
 *
 * REFERENCED BY:
 *     - screens/RecordingScreen.tsx - Main recording interface
 *
 * REFERENCES:
 *     - api/client.ts - Upload chunks, create/end session
 *     - expo-av - Audio recording API
 *     - utils/audio.ts - Audio processing utilities
 *
 * RETURNS:
 *     {
 *         // State
 *         isRecording: boolean
 *         duration: number (seconds)
 *         sessionId: string | null
 *         error: string | null
 *         permissionGranted: boolean
 *         chunksUploaded: number
 *
 *         // Actions
 *         startRecording: () => Promise<void>
 *         stopRecording: () => Promise<string> // returns sessionId
 *         requestPermission: () => Promise<boolean>
 *     }
 *
 * RECORDING CONFIG:
 *     - Sample rate: 16000 Hz
 *     - Channels: 1 (mono)
 *     - Format: WAV
 *     - Chunk interval: 30 seconds
 *
 * CHUNK UPLOAD FLOW:
 *     1. Every 30s, pause recording briefly
 *     2. Save current chunk to temp file
 *     3. Upload chunk via api/client.ts
 *     4. Resume recording
 *     5. Track chunk number for backend
 */
