/**
 * useRecording.test.ts - Recording Hook Tests
 *
 * PURPOSE:
 *     Test the useRecording hook behavior.
 *     Covers recording lifecycle and chunk uploads.
 *
 * REFERENCED BY:
 *     - Jest test runner
 *     - CI/CD pipeline
 *
 * REFERENCES:
 *     - hooks/useRecording.ts - Hook under test
 *     - api/client.ts - Mocked API
 *
 * TEST CASES:
 *
 *     initial_state:
 *         - isRecording is false
 *         - duration is 0
 *         - sessionId is null
 *         - error is null
 *
 *     requests_permission:
 *         - requestPermission called
 *         - Returns true if granted
 *         - Returns false if denied
 *
 *     starts_recording:
 *         - startRecording called
 *         - Creates session via API
 *         - isRecording becomes true
 *         - sessionId is set
 *
 *     tracks_duration:
 *         - While recording
 *         - duration increments every second
 *
 *     uploads_chunks:
 *         - After 30 seconds
 *         - API upload called
 *         - chunksUploaded increments
 *
 *     stops_recording:
 *         - stopRecording called
 *         - API end session called
 *         - isRecording becomes false
 *         - Returns sessionId
 *
 *     handles_permission_denied:
 *         - Permission denied
 *         - startRecording fails
 *         - error is set
 *
 *     handles_api_error:
 *         - API returns error
 *         - error is set
 *         - isRecording is false
 *
 *     cleans_up_on_unmount:
 *         - Component unmounts while recording
 *         - Recording stops
 *         - Resources cleaned up
 *
 * MOCKS:
 *     - expo-av Audio
 *     - API client
 *     - Permissions
 */
