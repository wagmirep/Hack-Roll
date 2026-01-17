/**
 * audio.ts - Audio Processing Utilities
 *
 * PURPOSE:
 *     Utility functions for audio processing on mobile.
 *     Handles format conversion, validation, and manipulation.
 *
 * RESPONSIBILITIES:
 *     - Validate audio file format
 *     - Convert audio to required format (16kHz mono WAV)
 *     - Calculate audio duration
 *     - Generate audio file from recording
 *     - Handle temporary file management
 *
 * REFERENCED BY:
 *     - hooks/useRecording.ts - Audio processing during recording
 *     - api/client.ts - Prepare audio for upload
 *
 * REFERENCES:
 *     - expo-av - Audio API
 *     - expo-file-system - File operations
 *
 * FUNCTIONS:
 *
 *     validateAudioFormat(uri: string): boolean
 *         Check if audio file is valid format
 *
 *     getAudioDuration(uri: string): Promise<number>
 *         Get duration of audio file in seconds
 *
 *     createTempFile(prefix: string): Promise<string>
 *         Create temporary file path for audio
 *
 *     deleteTempFile(uri: string): Promise<void>
 *         Delete temporary audio file
 *
 *     prepareForUpload(uri: string): Promise<Blob>
 *         Convert audio file to Blob for upload
 *
 *     formatDuration(seconds: number): string
 *         Format seconds as MM:SS string
 *
 * CONSTANTS:
 *     SAMPLE_RATE: 16000 (Hz)
 *     CHANNELS: 1 (mono)
 *     FORMAT: 'wav'
 *     CHUNK_DURATION: 30 (seconds)
 *
 * TEMP FILE LOCATION:
 *     ${FileSystem.cacheDirectory}/audio/
 */
