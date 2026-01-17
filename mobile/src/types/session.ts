export type SessionStatus = 'recording' | 'processing' | 'ready_for_claiming' | 'completed' | 'error';

export interface Session {
  session_id: string;
  status: SessionStatus;
  progress: number;
  started_at: string;
  ended_at?: string;
  duration_seconds?: number;
  group_id: string;
  speaker_count?: number;
  total_words_detected?: number;
  error_message?: string;
}

export interface Speaker {
  speaker_id: string;
  speaker_label: string;
  segment_count: number;
  total_duration_seconds: number;
  sample_audio_url: string;
  sample_start_time: number;
  word_preview: Record<string, number>;
  claimed_by: string | null;
  claimed_by_username: string | null;
}

export interface SessionResult {
  user_id: string;
  username: string;
  display_name: string;
  total_words: number;
  words: Record<string, number>;
  top_word: string;
  ranking: number;
}

export interface ClaimResponse {
  success: boolean;
  speaker_label: string;
  claimed_by: string;
  word_counts: Record<string, number>;
  total_words: number;
}
