import React, { createContext, useContext, useState, useEffect } from 'react';
import { Session, User } from '@supabase/supabase-js';
import { supabase } from '../lib/supabase';
import { Profile, Group, AuthContextType } from '../types/auth';
import { api, clearSessionCache } from '../api/client';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [groups, setGroups] = useState<Group[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    // Get initial session with error handling
    const initSession = async () => {
      try {
        console.log('Attempting to restore session from storage...');
        
        // Add timeout to getSession to prevent hanging on page refresh
        const sessionPromise = supabase.auth.getSession();
        const timeoutPromise = new Promise((_, reject) => 
          setTimeout(() => reject(new Error('getSession timeout during init')), 3000)
        );
        
        const { data: { session }, error } = await Promise.race([
          sessionPromise, 
          timeoutPromise
        ]) as any;
        
        if (!isMounted) return;
        
        if (error) {
          console.error('Error getting initial session:', error);
          setLoading(false);
          return;
        }
        
        console.log('Initial session check:', session?.user?.id ? 'Session found' : 'No session');
        setSession(session);
        setUser(session?.user ?? null);
        
        if (session) {
          await fetchProfile();
        } else {
          // No session - show login screen immediately
          setLoading(false);
        }
      } catch (error: any) {
        console.error('Error getting initial session:', error);
        
        // If getSession timed out, clear storage and show login
        if (error?.message?.includes('timeout')) {
          console.error('getSession timed out during init - clearing ALL state and showing login');
          clearSessionCache();
          // Clear session state immediately so AppNavigator shows login
          setSession(null);
          setUser(null);
          setProfile(null);
          setGroups([]);
          // Don't await signOut - it might hang too. Fire and forget.
          supabase.auth.signOut({ scope: 'local' }).catch(e => 
            console.error('signOut also failed:', e)
          );
        }
        
        // ALWAYS set loading to false so login screen shows
        if (isMounted) {
          console.log('Setting loading=false after init error');
          setLoading(false);
          console.log('setLoading(false) called - should show login screen now');
        } else {
          console.warn('Component unmounted - not setting loading state');
        }
      }
    };

    initSession();

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (_event, session) => {
        if (!isMounted) return;
        
        console.log('Auth state changed:', _event, session?.user?.id);
        setSession(session);
        setUser(session?.user ?? null);
        
        if (session) {
          await fetchProfile();
        } else {
          console.log('No session - clearing state and setting loading=false');
          setProfile(null);
          setGroups([]);
          setLoading(false);
          console.log('Loading set to false, should show login screen now');
        }
      }
    );

    return () => {
      isMounted = false;
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
      setLoading(false);
    } catch (error: any) {
      console.error('Error fetching profile:', error);
      
      // Check if error is related to session/authentication
      const errorMessage = error?.message || '';
      const isSessionError = errorMessage.includes('session') || 
                            errorMessage.includes('timeout') || 
                            errorMessage.includes('getSession') ||
                            error?.response?.status === 401;
      
      if (isSessionError) {
        console.error('Session error detected during profile fetch - forcing loading=false');
        // Clear everything and set loading=false to ensure login screen shows
        clearSessionCache();
        setProfile(null);
        setGroups([]);
        setSession(null);
        setUser(null);
        setLoading(false);
        console.log('Cleared all auth state and set loading=false');
        return;
      }
      
      // Other errors (network issues, etc) - allow user to continue
      console.warn('Continuing without profile data - backend may be unreachable');
      setProfile(null);
      setGroups([]);
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
    clearSessionCache();
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
