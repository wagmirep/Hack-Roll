import axios, { AxiosInstance } from 'axios';
import { supabase } from '../lib/supabase';

const API_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000';

export const axiosInstance: AxiosInstance = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: Add JWT token to all requests
axiosInstance.interceptors.request.use(
  async (config) => {
    const { data: { session } } = await supabase.auth.getSession();

    if (session?.access_token) {
      config.headers.Authorization = `Bearer ${session.access_token}`;
    }

    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: Handle 401 errors and token refresh
axiosInstance.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Token expired, try to refresh
      const { data: { session } } = await supabase.auth.refreshSession();

      if (session) {
        // Retry original request with new token
        error.config.headers.Authorization = `Bearer ${session.access_token}`;
        return axiosInstance.request(error.config);
      } else {
        // Refresh failed, sign out
        await supabase.auth.signOut();
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
    create: async (groupId: string) => {
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
  },
};
