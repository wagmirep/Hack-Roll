import { useState, useEffect, useRef } from 'react';
import { api } from '../api/client';
import { Session, SessionStatus } from '../types/session';

export interface UseSessionStatusResult {
  status: SessionStatus;
  progress: number;
  session: Session | null;
  error: string | null;
  isPolling: boolean;
}

export function useSessionStatus(
  sessionId: string | null,
  options: {
    pollInterval?: number;
    stopOnStatus?: SessionStatus[];
  } = {}
): UseSessionStatusResult {
  const {
    pollInterval = 2000,
    stopOnStatus = ['ready_for_claiming', 'completed', 'error'],
  } = options;

  const [status, setStatus] = useState<SessionStatus>('recording');
  const [progress, setProgress] = useState(0);
  const [session, setSession] = useState<Session | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPolling, setIsPolling] = useState(false);

  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const isMountedRef = useRef(true);

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  useEffect(() => {
    if (!sessionId) {
      setIsPolling(false);
      return;
    }

    const fetchStatus = async () => {
      try {
        const sessionData = await api.sessions.getStatus(sessionId);
        
        if (!isMountedRef.current) return;

        setSession(sessionData);
        setStatus(sessionData.status);
        setProgress(sessionData.progress || 0);
        setError(sessionData.error_message || null);

        // Stop polling if we've reached a terminal status
        if (stopOnStatus.includes(sessionData.status)) {
          if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
          }
          setIsPolling(false);
        }
      } catch (err: any) {
        console.error('Error fetching session status:', err);
        if (isMountedRef.current) {
          setError(err.message || 'Failed to fetch status');
        }
      }
    };

    // Initial fetch
    fetchStatus();
    setIsPolling(true);

    // Set up polling
    intervalRef.current = setInterval(fetchStatus, pollInterval);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [sessionId, pollInterval, stopOnStatus]);

  return {
    status,
    progress,
    session,
    error,
    isPolling,
  };
}
