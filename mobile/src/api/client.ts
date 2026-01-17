import axios, { AxiosInstance } from 'axios';
import { supabase } from '../lib/supabase';

const API_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000';

// Cache for the current session to avoid multiple concurrent getSession calls
let sessionCache: { token: string | null, expiresAt: number } = { token: null, expiresAt: 0 };
let pendingSessionFetch: Promise<any> | null = null;

// Function to clear the session cache (call on sign out)
export const clearSessionCache = () => {
  sessionCache = { token: null, expiresAt: 0 };
  pendingSessionFetch = null;
};

// Update cache externally (called on login/auth state change)
export function updateSessionCache(token: string, expiresAt: number) {
  sessionCache = {
    token,
    expiresAt: expiresAt * 1000 - 5 * 60 * 1000 // 5 min buffer
  };
  console.log('Session cache updated externally');
}

export const axiosInstance: AxiosInstance = axios.create({
  baseURL: API_URL,
  timeout: 5000, // Reduced to 5 seconds for faster feedback
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: Add JWT token to all requests
axiosInstance.interceptors.request.use(
  async (config) => {
    try {
      // Check if we have a valid cached token
      const now = Date.now();
      if (sessionCache.token && sessionCache.expiresAt > now) {
        config.headers.Authorization = `Bearer ${sessionCache.token}`;
        return config;
      }

      // Fetch new session if cache is invalid
      console.log('Fetching new session token...');
      
      // Reuse pending fetch if one is already in progress
      if (!pendingSessionFetch) {
        pendingSessionFetch = Promise.race([
          supabase.auth.getSession(),
          new Promise((_, reject) => 
            setTimeout(() => reject(new Error('getSession timeout')), 10000) // 10 second timeout
          )
        ]).finally(() => {
          pendingSessionFetch = null;
        });
      }
      
      const { data: { session } } = await pendingSessionFetch as any;

      if (session?.access_token) {
        // Cache the token with a 5-minute expiry buffer
        sessionCache = {
          token: session.access_token,
          expiresAt: (session.expires_at || 0) * 1000 - 5 * 60 * 1000
        };
        config.headers.Authorization = `Bearer ${session.access_token}`;
        console.log('Token added to request');
      } else {
        console.warn('No session token available');
        // Proceed without token - let backend return 401 if needed
        return config;
      }
    } catch (error: any) {
      console.error('Error getting session in interceptor:', error);
      
      // Determine if this is a timeout error
      const isTimeout = error?.message?.includes('timeout');
      if (isTimeout) {
        console.warn('SESSION TIMEOUT - proceeding without token, request may fail with 401');
        // Don't sign out on timeout - just proceed without token
        // The backend will return 401 if auth is required, handled in response interceptor
        return config;
      }
      
      // For non-timeout errors, reject the request but DON'T sign out
      // Let the user stay logged in and try again
      console.error('Session error - rejecting request but keeping user logged in');
      clearSessionCache();
      throw error; // Reject the request but don't sign out
    }

    return config;
  },
  (error) => {
    console.error('Request interceptor error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor: Handle 401 errors and token refresh
axiosInstance.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      console.warn('Received 401 Unauthorized - attempting token refresh...');
      
      try {
        // Clear cached token on 401
        clearSessionCache();
        
        // Token expired, try to refresh ONCE
        const originalRequest = error.config;
        
        // Prevent infinite retry loop
        if (originalRequest._retry) {
          console.error('Token refresh already attempted - signing out');
          await supabase.auth.signOut();
          return Promise.reject(error);
        }
        
        originalRequest._retry = true;
        
        // Try to refresh the session
        const { data: { session }, error: refreshError } = await supabase.auth.refreshSession();

        if (session?.access_token) {
          console.log('Token refreshed successfully - retrying request');
          // Update cache with new token
          sessionCache = {
            token: session.access_token,
            expiresAt: (session.expires_at || 0) * 1000 - 5 * 60 * 1000
          };
          
          // Retry original request with new token
          originalRequest.headers.Authorization = `Bearer ${session.access_token}`;
          return axiosInstance.request(originalRequest);
        } else {
          // Refresh failed - session is truly invalid
          console.error('Session refresh failed:', refreshError?.message || 'No session returned');
          console.log('Signing out user - please log in again');
          await supabase.auth.signOut();
          return Promise.reject(new Error('Session expired - please log in again'));
        }
      } catch (refreshError) {
        console.error('Error refreshing session:', refreshError);
        // Refresh failed - sign out to prevent broken state
        await supabase.auth.signOut();
        return Promise.reject(error);
      }
    }

    return Promise.reject(error);
  }
);

// API modules
export const api = {
  auth: {
    getMe: async () => {
      const { data } = await axiosInstance.get('/auth/me');
      return data;
    },
    updateProfile: async (updates: any) => {
      const { data } = await axiosInstance.patch('/auth/profile', updates);
      return data;
    },
  },

  groups: {
    create: async (name: string) => {
      const { data } = await axiosInstance.post('/groups', { name });
      return data;
    },
    join: async (inviteCode: string) => {
      const { data } = await axiosInstance.post('/groups/join', { invite_code: inviteCode });
      return data;
    },
    getMembers: async (groupId: string) => {
      const { data } = await axiosInstance.get(`/groups/${groupId}/members`);
      return data;
    },
    getDetails: async (groupId: string) => {
      const { data } = await axiosInstance.get(`/groups/${groupId}`);
      return data;
    },
  },

  sessions: {
    list: async (groupId?: string, status?: string, limit?: number, offset?: number) => {
      const { data } = await axiosInstance.get('/sessions', {
        params: { group_id: groupId, status, limit, offset },
      });
      return data;
    },
    create: async (groupId: string | null = null) => {
      const { data } = await axiosInstance.post('/sessions', { group_id: groupId });
      return data;
    },
    uploadChunk: async (sessionId: string, formData: FormData) => {
      const { data } = await axiosInstance.post(
        `/sessions/${sessionId}/chunks`,
        formData,
        { 
          headers: { 'Content-Type': 'multipart/form-data' },
          timeout: 60000  // Longer timeout for file uploads
        }
      );
      return data;
    },
    end: async (sessionId: string, duration: number) => {
      const { data } = await axiosInstance.post(`/sessions/${sessionId}/end`, {
        final_duration_seconds: duration,
      });
      return data;
    },
    getStatus: async (sessionId: string) => {
      const { data } = await axiosInstance.get(`/sessions/${sessionId}`);
      return data;
    },
    getSpeakers: async (sessionId: string) => {
      const { data } = await axiosInstance.get(`/sessions/${sessionId}/speakers`);
      return data;
    },
    claimSpeaker: async (sessionId: string, speakerId: string) => {
      const { data } = await axiosInstance.post(`/sessions/${sessionId}/claim`, {
        speaker_id: speakerId,
      });
      return data;
    },
    getResults: async (sessionId: string) => {
      const { data } = await axiosInstance.get(`/sessions/${sessionId}/results`);
      return data;
    },
    getMyStats: async (sessionId: string) => {
      const { data } = await axiosInstance.get(`/sessions/${sessionId}/my-stats`);
      return data;
    },
    compare: async (sessionIds: string[]) => {
      const { data } = await axiosInstance.get('/sessions/compare', {
        params: { session_ids: sessionIds },
      });
      return data;
    },
  },

  stats: {
    getGroupStats: async (groupId: string, period: string = 'week') => {
      const { data } = await axiosInstance.get(`/groups/${groupId}/stats`, {
        params: { period },
      });
      return data;
    },
    getMyStats: async (period: string = 'all_time', groupId?: string) => {
      const { data } = await axiosInstance.get('/users/me/stats', {
        params: { period, group_id: groupId },
      });
      return data;
    },
    getWrapped: async () => {
      const { data } = await axiosInstance.get('/users/me/wrapped');
      return data;
    },
    getTrends: async (granularity: string = 'day', limit: number = 30, groupId?: string) => {
      const { data } = await axiosInstance.get('/users/me/trends', {
        params: { granularity, limit, group_id: groupId },
      });
      return data;
    },
    getGlobalLeaderboard: async (period: string = 'all_time') => {
      const { data } = await axiosInstance.get('/users/global/leaderboard', {
        params: { period },
      });
      return data;
    },
  },
};
