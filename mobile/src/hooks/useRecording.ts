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

// Recording configuration - reusable across buffers
const RECORDING_OPTIONS = {
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
};

export function useRecording(): UseRecordingResult {
  const [isRecording, setIsRecording] = useState(false);
  const [duration, setDuration] = useState(0);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [permissionGranted, setPermissionGranted] = useState(false);
  const [chunksUploaded, setChunksUploaded] = useState(0);

  // Double buffering: two recording instances that alternate
  const bufferA = useRef<Audio.Recording | null>(null);
  const bufferB = useRef<Audio.Recording | null>(null);
  const activeBuffer = useRef<'A' | 'B'>('A'); // Track which buffer is currently recording
  
  const chunkIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const durationIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const chunkNumber = useRef(0);
  const currentGroupId = useRef<string>('');
  const lastChunkUploadTime = useRef<number>(0);
  const isSwapping = useRef(false); // Prevent concurrent swaps

  // Helper to get active recording ref
  const getActiveRecording = () => {
    return activeBuffer.current === 'A' ? bufferA.current : bufferB.current;
  };

  // Helper to get inactive buffer ref
  const getInactiveBufferRef = () => {
    return activeBuffer.current === 'A' ? bufferB : bufferA;
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (chunkIntervalRef.current) {
        clearInterval(chunkIntervalRef.current);
      }
      if (durationIntervalRef.current) {
        clearInterval(durationIntervalRef.current);
      }
      // Clean up both buffers
      if (bufferA.current) {
        bufferA.current.stopAndUnloadAsync().catch(console.error);
      }
      if (bufferB.current) {
        bufferB.current.stopAndUnloadAsync().catch(console.error);
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

  // Create and prepare a new recording instance
  const createRecording = async (): Promise<Audio.Recording> => {
    const recording = new Audio.Recording();
    await recording.prepareToRecordAsync(RECORDING_OPTIONS);
    return recording;
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
      const sessId = session.id || session.session_id;
      console.log('🟢 Session ID:', sessId);
      setSessionId(sessId);

      // Prepare buffer A as the active recording
      console.log('🟢 Preparing buffer A...');
      const recording = await createRecording();
      await recording.startAsync();
      bufferA.current = recording;
      activeBuffer.current = 'A';
      
      // Pre-prepare buffer B so it's ready for fast swap
      console.log('🟢 Pre-preparing buffer B for double buffering...');
      try {
        const bufferBRecording = await createRecording();
        bufferB.current = bufferBRecording;
        console.log('🟢 Buffer B pre-prepared and ready');
      } catch (err) {
        console.log('⚠️ Could not pre-prepare buffer B, will prepare on demand');
        bufferB.current = null;
      }

      setIsRecording(true);
      chunkNumber.current = 0;
      lastChunkUploadTime.current = Date.now();
      isSwapping.current = false;

      // Update duration every second
      durationIntervalRef.current = setInterval(() => {
        setDuration(d => d + 1);
      }, 1000);

      // Upload chunks every 5 seconds using double buffering
      chunkIntervalRef.current = setInterval(() => {
        swapAndUploadChunk(sessId);
      }, 5000);

      console.log('🟢 Recording started with double buffering');

    } catch (err: any) {
      console.error('Error starting recording:', err);
      setError(err.message || 'Failed to start recording');
      throw err;
    }
  };

  // Double-buffer swap: start new recording FIRST, then stop and upload old one
  const swapAndUploadChunk = async (sessId: string): Promise<void> => {
    // Prevent concurrent swaps
    if (isSwapping.current) {
      console.log('⚠️ Swap already in progress, skipping');
      return;
    }
    isSwapping.current = true;

    const currentActive = getActiveRecording();
    if (!currentActive) {
      isSwapping.current = false;
      return;
    }

    try {
      // Check if current recording is still active
      const status = await currentActive.getStatusAsync();
      if (!status.canRecord && !status.isRecording) {
        console.log('⚠️ Active recording already stopped, skipping chunk upload');
        isSwapping.current = false;
        return;
      }

      console.log(`🔄 SWAP: Currently active buffer ${activeBuffer.current}, starting swap...`);

      // STEP 1: Get the inactive buffer and start it recording FIRST
      // This ensures continuous audio capture
      const inactiveRef = getInactiveBufferRef();
      let newRecording = inactiveRef.current;
      
      if (!newRecording) {
        // If no pre-prepared buffer, create one now
        console.log('🔄 Creating new recording for inactive buffer...');
        newRecording = await createRecording();
      }
      
      // Start the new recording BEFORE stopping the old one
      console.log('🔄 Starting new buffer recording...');
      await newRecording.startAsync();
      inactiveRef.current = newRecording;
      
      // Swap active buffer pointer
      const oldBuffer = activeBuffer.current;
      activeBuffer.current = oldBuffer === 'A' ? 'B' : 'A';
      console.log(`🔄 Active buffer swapped: ${oldBuffer} → ${activeBuffer.current}`);

      // STEP 2: Now stop and upload the old recording (no longer active)
      console.log('🔄 Stopping old buffer and uploading...');
      await currentActive.stopAndUnloadAsync();
      const uri = currentActive.getURI();

      if (uri) {
        const isWeb = typeof navigator !== 'undefined' && navigator.product === 'ReactNative' ? false : true;
        const fileExtension = isWeb ? 'webm' : 'wav';
        const mimeType = isWeb ? 'audio/webm' : 'audio/wav';
        
        const formData = new FormData();
        formData.append('duration_seconds', '5');
        
        if (isWeb) {
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

        // Upload to backend (now happens while new buffer is already recording)
        await api.sessions.uploadChunk(sessId, formData);
        setChunksUploaded(prev => prev + 1);
        chunkNumber.current++;
        lastChunkUploadTime.current = Date.now();
        console.log(`🔄 Chunk ${chunkNumber.current - 1} uploaded successfully`);
      }

      // STEP 3: Pre-prepare the old buffer for the next swap
      // This makes the next swap faster
      const oldBufferRef = oldBuffer === 'A' ? bufferA : bufferB;
      try {
        console.log(`🔄 Pre-preparing buffer ${oldBuffer} for next swap...`);
        const preparedRecording = await createRecording();
        oldBufferRef.current = preparedRecording;
        console.log(`🔄 Buffer ${oldBuffer} pre-prepared and ready`);
      } catch (err) {
        console.log(`⚠️ Could not pre-prepare buffer ${oldBuffer}, will prepare on demand`);
        oldBufferRef.current = null;
      }

    } catch (err) {
      console.error('Error in swap and upload:', err);
      // Don't throw - continue recording even if upload fails
    } finally {
      isSwapping.current = false;
    }
  };

  const stopRecording = async (): Promise<string | null> => {
    console.log('🔴 stopRecording() called');
    
    const currentActive = getActiveRecording();
    if (!currentActive || !sessionId) {
      console.log('🔴 EARLY RETURN: No active recording or sessionId');
      return null;
    }

    // Capture state before clearing
    const currentSessionId = sessionId;
    const currentDuration = duration;
    const currentChunkNumber = chunkNumber.current;

    try {
      console.log('🔴 Clearing intervals...');
      if (chunkIntervalRef.current) {
        clearInterval(chunkIntervalRef.current);
        chunkIntervalRef.current = null;
      }
      if (durationIntervalRef.current) {
        clearInterval(durationIntervalRef.current);
        durationIntervalRef.current = null;
      }

      // Wait for any in-progress swap to complete
      while (isSwapping.current) {
        console.log('🔴 Waiting for swap to complete...');
        await new Promise(resolve => setTimeout(resolve, 50));
      }

      console.log('🔴 Stopping active recording...');
      const status = await currentActive.getStatusAsync();
      
      let uri: string | null = null;
      if (status.isRecording) {
        await currentActive.stopAndUnloadAsync();
        uri = currentActive.getURI();
        console.log('🔴 Recording stopped, URI:', uri);
      } else {
        uri = currentActive.getURI();
      }

      // Also clean up the inactive buffer if it exists
      const inactiveRef = getInactiveBufferRef();
      if (inactiveRef.current) {
        try {
          const inactiveStatus = await inactiveRef.current.getStatusAsync();
          if (inactiveStatus.canRecord || inactiveStatus.isRecording) {
            await inactiveRef.current.stopAndUnloadAsync();
          }
        } catch (e) {
          // Ignore cleanup errors
        }
        inactiveRef.current = null;
      }

      // *** IMMEDIATELY update UI state after recording stops ***
      bufferA.current = null;
      bufferB.current = null;
      setIsRecording(false);
      setDuration(0);
      chunkNumber.current = 0;
      setChunksUploaded(0);
      console.log('🔴 Recording state cleared immediately after stop');

      // Now perform network operations in the background
      if (uri) {
        console.log('🔴 Uploading final chunk...');
        try {
          const isWeb = typeof navigator !== 'undefined' && navigator.product === 'ReactNative' ? false : true;
          const fileExtension = isWeb ? 'webm' : 'wav';
          const mimeType = isWeb ? 'audio/webm' : 'audio/wav';
          
          // Calculate actual duration of final chunk
          let finalChunkDuration: number;
          if (currentChunkNumber === 0) {
            finalChunkDuration = currentDuration;
          } else if (lastChunkUploadTime.current > 0) {
            const timeSinceLastUpload = (Date.now() - lastChunkUploadTime.current) / 1000;
            finalChunkDuration = Math.round(timeSinceLastUpload);
          } else {
            finalChunkDuration = (currentDuration % 5) || 5;
          }
          
          finalChunkDuration = Math.max(1, Math.min(finalChunkDuration, 5));
          console.log('🔴 Final chunk duration:', finalChunkDuration, 'seconds');
          
          const formData = new FormData();
          formData.append('duration_seconds', finalChunkDuration.toString());
          
          if (isWeb) {
            const response = await fetch(uri);
            const blob = await response.blob();
            const file = new File([blob], `chunk_${currentChunkNumber}.${fileExtension}`, { type: mimeType });
            formData.append('file', file);
          } else {
            // @ts-ignore - FormData file handling in React Native
            formData.append('file', {
              uri,
              name: `chunk_${currentChunkNumber}.${fileExtension}`,
              type: mimeType,
            });
          }

          await api.sessions.uploadChunk(currentSessionId, formData);
          console.log('🔴 Final chunk uploaded successfully');
        } catch (uploadErr: any) {
          console.error('🔴 Final chunk upload failed:', uploadErr.message);
          throw uploadErr;
        }
      }

      console.log('🔴 Ending session...');
      await api.sessions.end(currentSessionId, currentDuration);
      console.log('🔴 Session ended successfully');

      return currentSessionId;

    } catch (err: any) {
      console.error('🔴 Error stopping recording:', err);
      setError(err.message || 'Failed to stop recording');
      throw err;
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
