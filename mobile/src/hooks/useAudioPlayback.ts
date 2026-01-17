import { useState, useEffect, useRef } from 'react';
import { Audio } from 'expo-av';

export interface UseAudioPlaybackResult {
  isPlaying: boolean;
  isLoading: boolean;
  error: string | null;
  play: (uri: string) => Promise<void>;
  stop: () => Promise<void>;
  pause: () => Promise<void>;
  resume: () => Promise<void>;
}

export function useAudioPlayback(): UseAudioPlaybackResult {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const soundRef = useRef<Audio.Sound | null>(null);
  const currentUri = useRef<string | null>(null);

  useEffect(() => {
    // Configure audio mode
    Audio.setAudioModeAsync({
      playsInSilentModeIOS: true,
      staysActiveInBackground: false,
    });

    return () => {
      // Cleanup on unmount
      if (soundRef.current) {
        soundRef.current.unloadAsync().catch(console.error);
      }
    };
  }, []);

  const play = async (uri: string): Promise<void> => {
    try {
      setError(null);
      setIsLoading(true);

      // If playing different URI, stop current sound
      if (currentUri.current !== uri && soundRef.current) {
        await soundRef.current.unloadAsync();
        soundRef.current = null;
      }

      // Load and play new sound
      if (!soundRef.current) {
        const { sound } = await Audio.Sound.createAsync(
          { uri },
          { shouldPlay: true },
          (status) => {
            if (status.isLoaded) {
              setIsPlaying(status.isPlaying);
              // Auto-cleanup when finished
              if (status.didJustFinish) {
                setIsPlaying(false);
                sound.unloadAsync().catch(console.error);
                soundRef.current = null;
                currentUri.current = null;
              }
            }
          }
        );

        soundRef.current = sound;
        currentUri.current = uri;
      } else {
        await soundRef.current.playAsync();
      }

      setIsPlaying(true);
    } catch (err: any) {
      console.error('Error playing audio:', err);
      setError(err.message || 'Failed to play audio');
    } finally {
      setIsLoading(false);
    }
  };

  const stop = async (): Promise<void> => {
    if (!soundRef.current) return;

    try {
      await soundRef.current.stopAsync();
      await soundRef.current.unloadAsync();
      soundRef.current = null;
      currentUri.current = null;
      setIsPlaying(false);
    } catch (err: any) {
      console.error('Error stopping audio:', err);
      setError(err.message || 'Failed to stop audio');
    }
  };

  const pause = async (): Promise<void> => {
    if (!soundRef.current) return;

    try {
      await soundRef.current.pauseAsync();
      setIsPlaying(false);
    } catch (err: any) {
      console.error('Error pausing audio:', err);
      setError(err.message || 'Failed to pause audio');
    }
  };

  const resume = async (): Promise<void> => {
    if (!soundRef.current) return;

    try {
      await soundRef.current.playAsync();
      setIsPlaying(true);
    } catch (err: any) {
      console.error('Error resuming audio:', err);
      setError(err.message || 'Failed to resume audio');
    }
  };

  return {
    isPlaying,
    isLoading,
    error,
    play,
    stop,
    pause,
    resume,
  };
}
