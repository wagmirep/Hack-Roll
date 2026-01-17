import React, { useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  ActivityIndicator,
} from 'react-native';
import { StackNavigationProp } from '@react-navigation/stack';
import { RouteProp } from '@react-navigation/native';
import { RecordStackParamList } from '../navigation/MainNavigator';
import { useSessionStatus } from '../hooks/useSessionStatus';
import ProgressBar from '../components/ProgressBar';

type ProcessingScreenNavigationProp = StackNavigationProp<RecordStackParamList, 'Processing'>;
type ProcessingScreenRouteProp = RouteProp<RecordStackParamList, 'Processing'>;

interface Props {
  navigation: ProcessingScreenNavigationProp;
  route: ProcessingScreenRouteProp;
}

export default function ProcessingScreen({ navigation, route }: Props) {
  const { sessionId } = route.params;
  const { status, progress, error } = useSessionStatus(sessionId);

  useEffect(() => {
    if (status === 'ready_for_claiming') {
      navigation.replace('Claiming', { sessionId });
    } else if (status === 'error') {
      // Stay on screen to show error
    }
  }, [status, sessionId, navigation]);

  const getStatusMessage = (): string => {
    if (error) return 'Error processing audio';
    
    if (progress < 30) return 'Concatenating audio chunks...';
    if (progress < 60) return 'Detecting speakers...';
    if (progress < 80) return 'Transcribing conversation...';
    if (progress < 100) return 'Analyzing word usage...';
    return 'Almost ready!';
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.title}>Processing Your Recording</Text>
        
        <View style={styles.animationContainer}>
          {error ? (
            <Text style={styles.errorIcon}>❌</Text>
          ) : (
            <ActivityIndicator size="large" color="#007AFF" />
          )}
        </View>

        <View style={styles.progressContainer}>
          <ProgressBar progress={progress} />
          <Text style={styles.progressText}>{progress}%</Text>
        </View>

        <Text style={[styles.statusText, error && styles.errorText]}>
          {getStatusMessage()}
        </Text>

        {error && (
          <Text style={styles.errorDetails}>{error}</Text>
        )}

        <Text style={styles.helperText}>
          This usually takes 30-60 seconds
        </Text>
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
    fontSize: 28,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 48,
    textAlign: 'center',
  },
  animationContainer: {
    marginBottom: 48,
  },
  errorIcon: {
    fontSize: 64,
  },
  progressContainer: {
    width: '100%',
    marginBottom: 24,
  },
  progressText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#007AFF',
    textAlign: 'center',
    marginTop: 16,
  },
  statusText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginBottom: 8,
  },
  errorText: {
    color: '#FF3B30',
  },
  errorDetails: {
    fontSize: 14,
    color: '#999',
    textAlign: 'center',
    marginTop: 8,
  },
  helperText: {
    fontSize: 14,
    color: '#999',
    marginTop: 32,
    textAlign: 'center',
  },
});
