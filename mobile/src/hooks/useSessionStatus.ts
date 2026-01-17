/**
 * useSessionStatus.ts - Session Status Polling Hook
 *
 * PURPOSE:
 *     Poll backend for session processing status.
 *     Auto-updates while session is processing.
 *
 * RESPONSIBILITIES:
 *     - Poll session status endpoint
 *     - Track progress percentage
 *     - Detect status transitions
 *     - Stop polling when complete or error
 *     - Provide status message for display
 *
 * REFERENCED BY:
 *     - screens/ProcessingScreen.tsx - Status display
 *
 * REFERENCES:
 *     - api/client.ts - Status endpoint
 *
 * PARAMS:
 *     sessionId: string - Session to track
 *     options?: {
 *         pollInterval?: number (default: 2000ms)
 *         enabled?: boolean (default: true)
 *     }
 *
 * RETURNS:
 *     {
 *         // State
 *         status: 'recording' | 'processing' | 'ready_for_claiming' | 'completed' | 'error'
 *         progress: number (0-100)
 *         message: string
 *         error: string | null
 *
 *         // Derived
 *         isProcessing: boolean
 *         isComplete: boolean
 *         isError: boolean
 *
 *         // Actions
 *         refetch: () => Promise<void>
 *         startPolling: () => void
 *         stopPolling: () => void
 *     }
 *
 * POLLING BEHAVIOR:
 *     - Starts automatically when enabled
 *     - Polls every pollInterval milliseconds
 *     - Stops when status is 'ready_for_claiming', 'completed', or 'error'
 *     - Cleans up interval on unmount
 *
 * STATUS MESSAGES:
 *     processing (0-30%): "Analyzing speakers..."
 *     processing (30-70%): "Transcribing audio..."
 *     processing (70-100%): "Counting words..."
 *     ready_for_claiming: "Ready for claiming!"
 *     error: Error message from backend
 */
