export interface Profile {
  id: string;
  username: string;
  display_name: string;
  avatar_url?: string;
  created_at?: string;
  updated_at?: string;
}

export interface Group {
  id: string;
  name: string;
  invite_code: string;
  created_by: string;
  created_at: string;
  member_count?: number;
  role?: 'admin' | 'member';
}

export interface AuthContextType {
  session: any | null;
  user: any | null;
  profile: Profile | null;
  groups: Group[];
  loading: boolean;
  signUp: (email: string, password: string, username: string) => Promise<void>;
  signIn: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
  refreshProfile: () => Promise<void>;
}
