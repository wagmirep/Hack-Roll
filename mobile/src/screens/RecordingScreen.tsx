import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Alert,
  SafeAreaView,
} from 'react-native';
import { StackNavigationProp } from '@react-navigation/stack';
import { RouteProp } from '@react-navigation/native';
import { RecordStackParamList } from '../navigation/MainNavigator';
import { useRecording } from '../hooks/useRecording';
import { useAuth } from '../contexts/AuthContext';

type RecordingScreenNavigationProp = StackNavigationProp<RecordStackParamList, 'Recording'>;
type RecordingScreenRouteProp = RouteProp<RecordStackParamList, 'Recording'>;

interface Props {
  navigation: RecordingScreenNavigationProp;
  route: RecordingScreenRouteProp;
}

export default function RecordingScreen({ navigation, route }: Props) {
  const { groups } = useAuth();
  const [selectedGroupId, setSelectedGroupId] = useState<string | null>(
    route.params?.groupId || groups[0]?.id || null
  );

  const {
    isRecording,
    duration,
    error,
    chunksUploaded,
    startRecording,
    stopRecording,
    requestPermission,
  } = useRecording();

  useEffect(() => {
    // Request microphone permission on mount
    requestPermission();
  }, []);

  useEffect(() => {
    if (error) {
      Alert.alert('Recording Error', error);
    }
  }, [error]);

  const handleStartRecording = async () => {
    if (!selectedGroupId) {
      Alert.alert('No Group', 'Please create or join a group first');
      return;
    }

    try {
      await startRecording(selectedGroupId);
    } catch (err) {
      // Error already handled by hook
    }
  };

  const handleStopRecording = async () => {
    try {
      const sessionId = await stopRecording();
      if (sessionId) {
        navigation.navigate('Processing', { sessionId });
      }
    } catch (err) {
      Alert.alert('Error', 'Failed to stop recording');
    }
  };

  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.title}>LahStats</Text>
        <Text style={styles.subtitle}>Record Your Conversation</Text>

        {groups.length === 0 ? (
          <View style={styles.noGroupContainer}>
            <Text style={styles.noGroupText}>No groups yet!</Text>
            <Text style={styles.noGroupSubtext}>Create or join a group to start recording</Text>
          </View>
        ) : (
          <>
            <View style={styles.timerContainer}>
              <Text style={styles.timerText}>{formatDuration(duration)}</Text>
              {isRecording && (
                <View style={styles.recordingIndicator}>
                  <View style={styles.recordingDot} />
                  <Text style={styles.recordingText}>Recording...</Text>
                </View>
              )}
              {chunksUploaded > 0 && (
                <Text style={styles.chunksText}>
                  {chunksUploaded} chunk{chunksUploaded > 1 ? 's' : ''} uploaded
                </Text>
              )}
            </View>

            <View style={styles.buttonContainer}>
              {!isRecording ? (
                <TouchableOpacity
                  style={[styles.recordButton, styles.startButton]}
                  onPress={handleStartRecording}
                >
                  <Text style={styles.buttonIcon}>🎙️</Text>
                  <Text style={styles.buttonText}>Start Recording</Text>
                </TouchableOpacity>
              ) : (
                <TouchableOpacity
                  style={[styles.recordButton, styles.stopButton]}
                  onPress={handleStopRecording}
                >
                  <Text style={styles.buttonIcon}>⏹️</Text>
                  <Text style={styles.buttonText}>Stop Recording</Text>
                </TouchableOpacity>
              )}
            </View>

            {selectedGroupId && (
              <View style={styles.groupInfo}>
                <Text style={styles.groupLabel}>Recording for:</Text>
                <Text style={styles.groupName}>
                  {groups.find(g => g.id === selectedGroupId)?.name || 'Unknown Group'}
                </Text>
              </View>
            )}
          </>
        )}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  content: {
    flex: 1,
    padding: 24,
    justifyContent: 'center',
    alignItems: 'center',
  },
  title: {
    fontSize: 36,
    fontWeight: 'bold',
    color: '#007AFF',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 18,
    color: '#666',
    marginBottom: 48,
  },
  noGroupContainer: {
    alignItems: 'center',
    padding: 32,
  },
  noGroupText: {
    fontSize: 20,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
  },
  noGroupSubtext: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
  },
  timerContainer: {
    alignItems: 'center',
    marginBottom: 48,
  },
  timerText: {
    fontSize: 64,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 16,
  },
  recordingIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  recordingDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: '#FF3B30',
    marginRight: 8,
  },
  recordingText: {
    fontSize: 16,
    color: '#FF3B30',
    fontWeight: '600',
  },
  chunksText: {
    fontSize: 14,
    color: '#666',
    marginTop: 8,
  },
  buttonContainer: {
    width: '100%',
    alignItems: 'center',
  },
  recordButton: {
    width: 200,
    height: 200,
    borderRadius: 100,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  startButton: {
    backgroundColor: '#007AFF',
  },
  stopButton: {
    backgroundColor: '#FF3B30',
  },
  buttonIcon: {
    fontSize: 48,
    marginBottom: 8,
  },
  buttonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
  groupInfo: {
    marginTop: 32,
    alignItems: 'center',
  },
  groupLabel: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
  groupName: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
  },
});
