import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Alert,
  SafeAreaView,
  Image,
  Animated,
  Easing,
} from 'react-native';
import { StackNavigationProp } from '@react-navigation/stack';
import { RouteProp } from '@react-navigation/native';
import { RecordStackParamList } from '../navigation/MainNavigator';
import { useRecording } from '../hooks/useRecording';
import { useAuth } from '../contexts/AuthContext';
import { LinearGradient } from 'expo-linear-gradient';

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
  const [isPaused, setIsPaused] = useState(false);

  const {
    isRecording,
    duration,
    error,
    chunksUploaded,
    startRecording,
    stopRecording,
    requestPermission,
  } = useRecording();

  // Pulsing animation for recording state
  const pulseAnim1 = useRef(new Animated.Value(1)).current;
  const pulseAnim2 = useRef(new Animated.Value(1)).current;
  const pulseAnim3 = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    requestPermission();
  }, []);

  useEffect(() => {
    if (error) {
      Alert.alert('Recording Error', error);
    }
  }, [error]);

  useEffect(() => {
    if (isRecording && !isPaused) {
      // Start pulsing animation
      const createPulse = (animValue: Animated.Value, delay: number) => {
        return Animated.loop(
          Animated.sequence([
            Animated.delay(delay),
            Animated.timing(animValue, {
              toValue: 1.5,
              duration: 2000,
              easing: Easing.inOut(Easing.ease),
              useNativeDriver: true,
            }),
            Animated.timing(animValue, {
              toValue: 1,
              duration: 0,
              useNativeDriver: true,
            }),
          ])
        );
      };

      const pulse1 = createPulse(pulseAnim1, 0);
      const pulse2 = createPulse(pulseAnim2, 400);
      const pulse3 = createPulse(pulseAnim3, 800);

      pulse1.start();
      pulse2.start();
      pulse3.start();

      return () => {
        pulse1.stop();
        pulse2.stop();
        pulse3.stop();
      };
    }
  }, [isRecording, isPaused]);

  const handleStartRecording = async () => {
    if (!selectedGroupId) {
      Alert.alert('No Group', 'Please create or join a group first');
      return;
    }

    try {
      await startRecording(selectedGroupId);
      setIsPaused(false);
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

  const handlePauseResume = () => {
    setIsPaused(!isPaused);
    // TODO: Implement actual pause/resume logic in useRecording hook
  };

  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const renderIdleState = () => (
    <>
      <Text style={styles.titleText}>Start your yap session</Text>
      <TouchableOpacity
        style={styles.logoButton}
        onPress={handleStartRecording}
        activeOpacity={0.8}
      >
        <View style={styles.logoCircle}>
          <Image
            source={require('../../assets/images/rabak-logo.jpg')}
            style={styles.logoImage}
            resizeMode="contain"
          />
        </View>
      </TouchableOpacity>
    </>
  );

  const renderRecordingState = () => (
    <>
      <Text style={styles.titleText}>Recording...</Text>
      <View style={styles.recordingContainer}>
        {/* Pulsing circles */}
        <Animated.View
          style={[
            styles.pulseCircle,
            styles.pulseCircle3,
            {
              transform: [{ scale: pulseAnim3 }],
              opacity: pulseAnim3.interpolate({
                inputRange: [1, 1.5],
                outputRange: [0.3, 0],
              }),
            },
          ]}
        />
        <Animated.View
          style={[
            styles.pulseCircle,
            styles.pulseCircle2,
            {
              transform: [{ scale: pulseAnim2 }],
              opacity: pulseAnim2.interpolate({
                inputRange: [1, 1.5],
                outputRange: [0.4, 0],
              }),
            },
          ]}
        />
        <Animated.View
          style={[
            styles.pulseCircle,
            styles.pulseCircle1,
            {
              transform: [{ scale: pulseAnim1 }],
              opacity: pulseAnim1.interpolate({
                inputRange: [1, 1.5],
                outputRange: [0.5, 0],
              }),
            },
          ]}
        />

        <TouchableOpacity
          style={styles.logoButton}
          onPress={handlePauseResume}
          activeOpacity={0.8}
        >
          <View style={styles.logoCircle}>
            <Image
              source={require('../../assets/images/rabak-logo.jpg')}
              style={styles.logoImage}
              resizeMode="contain"
            />
          </View>
        </TouchableOpacity>
      </View>
    </>
  );

  const renderPausedState = () => (
    <>
      <Text style={styles.titleText}>Paused</Text>
      <TouchableOpacity
        style={styles.logoButton}
        onPress={handlePauseResume}
        activeOpacity={0.8}
      >
        <View style={styles.logoCircle}>
          <Image
            source={require('../../assets/images/rabak-logo.jpg')}
            style={styles.logoImage}
            resizeMode="contain"
          />
        </View>
      </TouchableOpacity>

      <View style={styles.controlButtons}>
        <TouchableOpacity
          style={styles.controlButton}
          onPress={handlePauseResume}
        >
          <View style={styles.playIcon} />
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.controlButton}
          onPress={handleStopRecording}
        >
          <View style={styles.stopIcon} />
        </TouchableOpacity>
      </View>
    </>
  );

  return (
    <LinearGradient
      colors={['#E88080', '#ED6B6B']}
      style={styles.container}
    >
      <SafeAreaView style={styles.safeArea}>
        {/* Top Navigation */}
        <View style={styles.topNav}>
          <TouchableOpacity style={styles.navButton}>
            <Text style={styles.navIcon}>🕐</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.navButton}>
            <Text style={styles.navIcon}>⚙️</Text>
            <View style={styles.notificationDot} />
          </TouchableOpacity>
        </View>

        {/* Main Content */}
        <View style={styles.content}>
          {groups.length === 0 ? (
            <View style={styles.noGroupContainer}>
              <Text style={styles.noGroupText}>No groups yet!</Text>
              <Text style={styles.noGroupSubtext}>
                Create or join a group to start recording
              </Text>
            </View>
          ) : (
            <>
              {!isRecording && renderIdleState()}
              {isRecording && !isPaused && renderRecordingState()}
              {isRecording && isPaused && renderPausedState()}
            </>
          )}
        </View>
      </SafeAreaView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  safeArea: {
    flex: 1,
  },
  topNav: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingTop: 10,
  },
  navButton: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  navIcon: {
    fontSize: 24,
  },
  notificationDot: {
    position: 'absolute',
    top: 8,
    right: 8,
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: '#FF3B30',
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 24,
  },
  titleText: {
    fontSize: 36,
    fontWeight: '400',
    color: '#FFFFFF',
    textAlign: 'center',
    marginBottom: 80,
    letterSpacing: 0.5,
  },
  logoButton: {
    width: 240,
    height: 240,
    justifyContent: 'center',
    alignItems: 'center',
  },
  logoCircle: {
    width: 240,
    height: 240,
    borderRadius: 120,
    borderWidth: 6,
    borderColor: '#FFFFFF',
    backgroundColor: '#ED4545',
    justifyContent: 'center',
    alignItems: 'center',
    overflow: 'hidden',
  },
  logoImage: {
    width: '80%',
    height: '80%',
  },
  recordingContainer: {
    width: 300,
    height: 300,
    justifyContent: 'center',
    alignItems: 'center',
  },
  pulseCircle: {
    position: 'absolute',
    borderRadius: 150,
    borderWidth: 2,
    borderColor: '#FFFFFF',
  },
  pulseCircle1: {
    width: 240,
    height: 240,
  },
  pulseCircle2: {
    width: 280,
    height: 280,
  },
  pulseCircle3: {
    width: 320,
    height: 320,
  },
  controlButtons: {
    flexDirection: 'row',
    marginTop: 80,
    gap: 40,
  },
  controlButton: {
    width: 80,
    height: 80,
    borderRadius: 40,
    borderWidth: 3,
    borderColor: 'rgba(255, 255, 255, 0.6)',
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  playIcon: {
    width: 0,
    height: 0,
    backgroundColor: 'transparent',
    borderStyle: 'solid',
    borderLeftWidth: 20,
    borderRightWidth: 0,
    borderTopWidth: 12,
    borderBottomWidth: 12,
    borderLeftColor: '#FFFFFF',
    borderRightColor: 'transparent',
    borderTopColor: 'transparent',
    borderBottomColor: 'transparent',
    marginLeft: 4,
  },
  stopIcon: {
    width: 24,
    height: 24,
    backgroundColor: '#FFFFFF',
    borderRadius: 2,
  },
  noGroupContainer: {
    alignItems: 'center',
    padding: 32,
  },
  noGroupText: {
    fontSize: 24,
    fontWeight: '600',
    color: '#FFFFFF',
    marginBottom: 12,
  },
  noGroupSubtext: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.8)',
    textAlign: 'center',
  },
});
