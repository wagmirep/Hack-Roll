import { useState, useRef, useEffect } from 'react';
import { Audio } from 'expo-av';
import { api } from '../api/client';

export interface UseRecordingResult {
  isRecording: boolean;
  duration: number;
  sessionId: string | null;
  error: string | null;
  permissionGranted: boolean;
  chunksUploaded: number;
  startRecording: (groupId: string) => Promise<void>;
  stopRecording: () => Promise<string | null>;
  requestPermission: () => Promise<boolean>;
}

export function useRecording(): UseRecordingResult {
  const [isRecording, setIsRecording] = useState(false);
  const [duration, setDuration] = useState(0);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [permissionGranted, setPermissionGranted] = useState(false);
  const [chunksUploaded, setChunksUploaded] = useState(0);

  const recordingRef = useRef<Audio.Recording | null>(null);
  const chunkIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const durationIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const chunkNumber = useRef(0);
  const currentGroupId = useRef<string>('');

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (chunkIntervalRef.current) {
        clearInterval(chunkIntervalRef.current);
      }
      if (durationIntervalRef.current) {
        clearInterval(durationIntervalRef.current);
      }
      if (recordingRef.current) {
        recordingRef.current.stopAndUnloadAsync().catch(console.error);
      }
    };
  }, []);

  const requestPermission = async (): Promise<boolean> => {
    try {
      const { status } = await Audio.requestPermissionsAsync();
      const granted = status === 'granted';
      setPermissionGranted(granted);
      return granted;
    } catch (err) {
      console.error('Error requesting permission:', err);
      setError('Failed to request microphone permission');
      return false;
    }
  };

  const startRecording = async (groupId: string): Promise<void> => {
    try {
      setError(null);
      currentGroupId.current = groupId;

      // Request permissions
      const hasPermission = await requestPermission();
      if (!hasPermission) {
        throw new Error('Microphone permission not granted');
      }

      // Set audio mode
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
      });

      // Create session in backend
      const session = await api.sessions.create(groupId);
      setSessionId(session.session_id);

      // Prepare recording
      const recording = new Audio.Recording();
      await recording.prepareToRecordAsync({
        android: {
          extension: '.wav',
          outputFormat: Audio.AndroidOutputFormat.DEFAULT,
          audioEncoder: Audio.AndroidAudioEncoder.DEFAULT,
          sampleRate: 16000,
          numberOfChannels: 1,
          bitRate: 128000,
        },
        ios: {
          extension: '.wav',
          audioQuality: Audio.IOSAudioQuality.HIGH,
          sampleRate: 16000,
          numberOfChannels: 1,
          linearPCMBitDepth: 16,
          linearPCMIsBigEndian: false,
          linearPCMIsFloat: false,
        },
        web: {
          mimeType: 'audio/webm',
          bitsPerSecond: 128000,
        },
      });

      await recording.startAsync();
      recordingRef.current = recording;
      setIsRecording(true);
      chunkNumber.current = 0;

      // Update duration every second
      durationIntervalRef.current = setInterval(() => {
        setDuration(d => d + 1);
      }, 1000);

      // Upload chunks every 30 seconds
      chunkIntervalRef.current = setInterval(() => {
        uploadCurrentChunk(session.session_id);
      }, 30000);

    } catch (err: any) {
      console.error('Error starting recording:', err);
      setError(err.message || 'Failed to start recording');
      throw err;
    }
  };

  const uploadCurrentChunk = async (sessId: string): Promise<void> => {
    if (!recordingRef.current) return;

    try {
      // Stop current recording
      await recordingRef.current.stopAndUnloadAsync();
      const uri = recordingRef.current.getURI();

      if (uri) {
        // Create form data
        const formData = new FormData();
        formData.append('chunk_number', chunkNumber.current.toString());
        formData.append('duration_seconds', '30');
        
        // @ts-ignore - FormData file handling in React Native
        formData.append('audio_file', {
          uri,
          name: `chunk_${chunkNumber.current}.wav`,
          type: 'audio/wav',
        });

        // Upload to backend
        await api.sessions.uploadChunk(sessId, formData);
        setChunksUploaded(prev => prev + 1);
        chunkNumber.current++;
      }

      // Start new recording for next chunk
      const newRecording = new Audio.Recording();
      await newRecording.prepareToRecordAsync({
        android: {
          extension: '.wav',
          outputFormat: Audio.AndroidOutputFormat.DEFAULT,
          audioEncoder: Audio.AndroidAudioEncoder.DEFAULT,
          sampleRate: 16000,
          numberOfChannels: 1,
          bitRate: 128000,
        },
        ios: {
          extension: '.wav',
          audioQuality: Audio.IOSAudioQuality.HIGH,
          sampleRate: 16000,
          numberOfChannels: 1,
          linearPCMBitDepth: 16,
          linearPCMIsBigEndian: false,
          linearPCMIsFloat: false,
        },
        web: {
          mimeType: 'audio/webm',
          bitsPerSecond: 128000,
        },
      });
      await newRecording.startAsync();
      recordingRef.current = newRecording;

    } catch (err) {
      console.error('Error uploading chunk:', err);
      // Don't throw - continue recording even if upload fails
    }
  };

  const stopRecording = async (): Promise<string | null> => {
    if (!recordingRef.current || !sessionId) {
      return null;
    }

    try {
      // Clear intervals
      if (chunkIntervalRef.current) {
        clearInterval(chunkIntervalRef.current);
        chunkIntervalRef.current = null;
      }
      if (durationIntervalRef.current) {
        clearInterval(durationIntervalRef.current);
        durationIntervalRef.current = null;
      }

      // Upload final chunk
      await uploadCurrentChunk(sessionId);

      // End session
      await api.sessions.end(sessionId, duration);

      setIsRecording(false);
      return sessionId;

    } catch (err: any) {
      console.error('Error stopping recording:', err);
      setError(err.message || 'Failed to stop recording');
      throw err;
    } finally {
      // Reset state
      setDuration(0);
      chunkNumber.current = 0;
      setChunksUploaded(0);
    }
  };

  return {
    isRecording,
    duration,
    sessionId,
    error,
    permissionGranted,
    chunksUploaded,
    startRecording,
    stopRecording,
    requestPermission,
  };
}
