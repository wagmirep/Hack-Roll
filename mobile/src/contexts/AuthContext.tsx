import React, { createContext, useContext, useState, useEffect } from 'react';
import { Session, User } from '@supabase/supabase-js';
import { supabase } from '../lib/supabase';
import { Profile, Group, AuthContextType } from '../types/auth';
import { api } from '../api/client';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [groups, setGroups] = useState<Group[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Safety timeout: ensure loading never stays true forever
    const safetyTimeout = setTimeout(() => {
      console.warn('Loading timeout reached - forcing loading state to false');
      setLoading(false);
    }, 15000); // 15 second max loading time

    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      console.log('Initial session check:', session?.user?.id ? 'Session found' : 'No session');
      setSession(session);
      setUser(session?.user ?? null);
      if (session) {
        fetchProfile();
      } else {
        setLoading(false);
      }
    }).catch((error) => {
      console.error('Error getting initial session:', error);
      setLoading(false);
    });

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (_event, session) => {
        console.log('Auth state changed:', _event, session?.user?.id);
        setSession(session);
        setUser(session?.user ?? null);
        if (session) {
          await fetchProfile();
        } else {
          setProfile(null);
          setGroups([]);
          setLoading(false);
        }
      }
    );

    return () => {
      clearTimeout(safetyTimeout);
      subscription.unsubscribe();
    };
  }, []);

  const fetchProfile = async () => {
    try {
      console.log('Fetching profile from API...');
      const data = await api.auth.getMe();
      console.log('Profile fetched successfully:', data.profile?.username);
      setProfile(data.profile);
      setGroups(data.groups || []);
    } catch (error) {
      console.error('Error fetching profile:', error);
      // If profile fetch fails, still allow user to use the app
      // They have a valid session, just can't reach the backend right now
      console.warn('Continuing without profile data - backend may be unreachable');
      setProfile(null);
      setGroups([]);
    } finally {
      setLoading(false);
    }
  };

  const signUp = async (email: string, password: string, username: string) => {
    const { error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: { username }  // Passed to database trigger
      }
    });
    if (error) throw error;
  };

  const signIn = async (email: string, password: string) => {
    const { error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });
    if (error) throw error;
  };

  const signOut = async () => {
    const { error } = await supabase.auth.signOut();
    if (error) throw error;
  };

  const refreshProfile = async () => {
    await fetchProfile();
  };

  return (
    <AuthContext.Provider value={{
      session,
      user,
      profile,
      groups,
      loading,
      signUp,
      signIn,
      signOut,
      refreshProfile
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
