/**
 * client.ts - Backend API Client
 *
 * PURPOSE:
 *     Centralized API client for all backend communication.
 *     Handles requests, authentication, and error handling.
 *
 * RESPONSIBILITIES:
 *     - Configure base URL from environment
 *     - Make HTTP requests to backend
 *     - Handle authentication headers
 *     - Parse responses and handle errors
 *     - Provide typed API methods
 *
 * REFERENCED BY:
 *     - hooks/useRecording.ts - Session and upload APIs
 *     - hooks/useSessionStatus.ts - Status polling
 *     - screens/ClaimingScreen.tsx - Speakers and claim APIs
 *     - screens/ResultsScreen.tsx - Results API
 *     - screens/StatsScreen.tsx - Stats API
 *
 * REFERENCES:
 *     - .env - API_URL configuration
 *
 * CONFIGURATION:
 *     API_URL: Base URL for backend (from environment)
 *     Timeout: 30 seconds default
 *     Headers: Content-Type, Authorization (if authenticated)
 *
 * API METHODS:
 *
 *     Sessions:
 *         createSession(groupId, startedBy) -> { id, status, started_at }
 *         uploadChunk(sessionId, chunkNumber, audioBlob) -> { uploaded: true }
 *         endSession(sessionId) -> { status: 'processing' }
 *         getSessionStatus(sessionId) -> { status, progress, message }
 *         getSpeakers(sessionId) -> { speakers: Speaker[] }
 *         claimSpeaker(sessionId, speakerId, userId) -> { success, message }
 *
 *     Groups:
 *         getGroupStats(groupId, period?) -> GroupStats
 *         getLeaderboard(groupId, word?, period?) -> LeaderboardEntry[]
 *         getWrapped(groupId, userId, year?) -> WrappedData
 *
 * ERROR HANDLING:
 *     - Network errors: Throw with message
 *     - 4xx errors: Parse error response, throw
 *     - 5xx errors: Generic server error message
 *     - Timeout: Throw timeout error
 *
 * TYPES:
 *     See schemas.py for corresponding backend types
 */
