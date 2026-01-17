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
  startRecording: (groupId?: string | null) => Promise<void>;
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
  const lastChunkUploadTime = useRef<number>(0); // Track when last chunk was uploaded

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

  const startRecording = async (groupId?: string | null): Promise<void> => {
    try {
      console.log('🟢 startRecording() called with groupId:', groupId);
      setError(null);
      currentGroupId.current = groupId || '';

      // Request permissions
      console.log('🟢 Requesting permissions...');
      const hasPermission = await requestPermission();
      console.log('🟢 Permission granted:', hasPermission);
      if (!hasPermission) {
        throw new Error('Microphone permission not granted');
      }

      // Set audio mode
      console.log('🟢 Setting audio mode...');
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
      });

      // Create session in backend (groupId can be null for personal sessions)
      console.log('🟢 Creating session in backend with groupId:', groupId || null);
      const session = await api.sessions.create(groupId || null);
      console.log('🟢 Session created:', session);
      // Backend returns 'id' not 'session_id'
      const sessId = session.id || session.session_id;
      console.log('🟢 Session ID:', sessId);
      setSessionId(sessId);
      console.log('🟢 sessionId state updated to:', sessId);

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
      lastChunkUploadTime.current = 0; // Reset timestamp

      // Update duration every second
      durationIntervalRef.current = setInterval(() => {
        setDuration(d => d + 1);
      }, 1000);

      // Upload chunks every 5 seconds (reuse sessId declared above)
      chunkIntervalRef.current = setInterval(() => {
        uploadCurrentChunk(sessId);
      }, 5000);

    } catch (err: any) {
      console.error('Error starting recording:', err);
      setError(err.message || 'Failed to start recording');
      throw err;
    }
  };

  const uploadCurrentChunk = async (sessId: string): Promise<void> => {
    if (!recordingRef.current) return;

    try {
      // Get status first to check if recording is still active
      const status = await recordingRef.current.getStatusAsync();
      if (!status.canRecord && !status.isRecording) {
        console.log('⚠️  Recording already stopped, skipping chunk upload');
        return;
      }

      // Stop current recording
      await recordingRef.current.stopAndUnloadAsync();
      const uri = recordingRef.current.getURI();

      if (uri) {
        // Determine file format based on platform
        const isWeb = typeof navigator !== 'undefined' && navigator.product === 'ReactNative' ? false : true;
        const fileExtension = isWeb ? 'webm' : 'wav';
        const mimeType = isWeb ? 'audio/webm' : 'audio/wav';
        
        // Create form data with duration (5 seconds for periodic chunks)
        const formData = new FormData();
        formData.append('duration_seconds', '5');
        
        if (isWeb) {
          // On web, fetch the blob and create a proper File object
          const response = await fetch(uri);
          const blob = await response.blob();
          const file = new File([blob], `chunk_${chunkNumber.current}.${fileExtension}`, { type: mimeType });
          formData.append('file', file);
        } else {
          // @ts-ignore - FormData file handling in React Native
          formData.append('file', {
            uri,
            name: `chunk_${chunkNumber.current}.${fileExtension}`,
            type: mimeType,
          });
        }

        // Upload to backend
        await api.sessions.uploadChunk(sessId, formData);
        setChunksUploaded(prev => prev + 1);
        chunkNumber.current++;
        lastChunkUploadTime.current = Date.now(); // Track upload time
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
    console.log('🔴 stopRecording() called');
    console.log('🔴 recordingRef.current:', !!recordingRef.current);
    console.log('🔴 sessionId:', sessionId);
    
    if (!recordingRef.current || !sessionId) {
      console.log('🔴 EARLY RETURN: No recording or sessionId');
      console.log('🔴 recordingRef.current:', recordingRef.current);
      console.log('🔴 sessionId:', sessionId);
      return null;
    }

    try {
      console.log('🔴 Clearing intervals...');
      // Clear intervals first to prevent any more chunks
      if (chunkIntervalRef.current) {
        clearInterval(chunkIntervalRef.current);
        chunkIntervalRef.current = null;
        console.log('🔴 Chunk interval cleared');
      }
      if (durationIntervalRef.current) {
        clearInterval(durationIntervalRef.current);
        durationIntervalRef.current = null;
        console.log('🔴 Duration interval cleared');
      }

      // Wait a moment to ensure intervals are cleared and won't trigger
      await new Promise(resolve => setTimeout(resolve, 100));

      console.log('🔴 Stopping recording...');
      // Check if recording is still active before stopping
      const status = await recordingRef.current.getStatusAsync();
      console.log('🔴 Recording status:', status);
      
      let uri: string | null = null;
      
      // Only call stopAndUnloadAsync if actively recording
      // isDoneRecording: true means it's already stopped/unloaded (likely by chunk upload)
      if (status.isRecording) {
        console.log('🔴 Recording is active, stopping now...');
        await recordingRef.current.stopAndUnloadAsync();
        uri = recordingRef.current.getURI();
        console.log('🔴 Recording stopped, URI:', uri);
      } else {
        console.log('🔴 Recording already stopped/done, getting URI...');
        uri = recordingRef.current.getURI();
      }

      if (uri) {
        console.log('🔴 Uploading final chunk...');
        try {
          // Determine file format based on platform
          const isWeb = typeof navigator !== 'undefined' && navigator.product === 'ReactNative' ? false : true;
          const fileExtension = isWeb ? 'webm' : 'wav';
          const mimeType = isWeb ? 'audio/webm' : 'audio/wav';
          
          // Calculate actual duration of final chunk
          let finalChunkDuration: number;
          if (chunkNumber.current === 0) {
            // No chunks uploaded yet - use total duration
            finalChunkDuration = duration;
          } else if (lastChunkUploadTime.current > 0) {
            // Calculate time since last chunk upload (in seconds)
            const timeSinceLastUpload = (Date.now() - lastChunkUploadTime.current) / 1000;
            finalChunkDuration = Math.round(timeSinceLastUpload);
          } else {
            // Fallback to modulo calculation
            finalChunkDuration = (duration % 5) || 5;
          }
          
          // Ensure duration is at least 1 second and reasonable (5 seconds max for 5s chunks)
          finalChunkDuration = Math.max(1, Math.min(finalChunkDuration, 5));
          
          console.log('🔴 Platform:', isWeb ? 'web' : 'mobile', '| Format:', mimeType, '| Duration:', finalChunkDuration, 'seconds');
          
          // Create form data for final chunk
          const formData = new FormData();
          formData.append('duration_seconds', finalChunkDuration.toString());
          
          if (isWeb) {
            // On web, fetch the blob and create a proper File object
            console.log('🔴 Fetching blob for web upload...');
            const response = await fetch(uri);
            const blob = await response.blob();
            const file = new File([blob], `chunk_${chunkNumber.current}.${fileExtension}`, { type: mimeType });
            formData.append('file', file);
          } else {
            // @ts-ignore - FormData file handling in React Native
            formData.append('file', {
              uri,
              name: `chunk_${chunkNumber.current}.${fileExtension}`,
              type: mimeType,
            });
          }

          // Upload final chunk to backend
          await api.sessions.uploadChunk(sessionId, formData);
          console.log('🔴 Final chunk uploaded successfully');
          setChunksUploaded(prev => prev + 1);
        } catch (uploadErr: any) {
          console.error('🔴 Final chunk upload failed:', uploadErr.message);
          throw uploadErr; // Re-throw to handle properly
        }
      }

      console.log('🔴 Ending session...');
      // End session
      await api.sessions.end(sessionId, duration);
      console.log('🔴 Session ended successfully');

      // Clear recording reference
      recordingRef.current = null;
      setIsRecording(false);
      console.log('🔴 Recording state cleared, returning sessionId:', sessionId);
      return sessionId;

    } catch (err: any) {
      console.error('🔴 Error stopping recording:', err);
      setError(err.message || 'Failed to stop recording');
      throw err;
    } finally {
      console.log('🔴 Resetting state in finally block');
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
