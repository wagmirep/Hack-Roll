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
import BubbleLoadingOverlay from '../components/BubbleLoadingOverlay';

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
  const [pausedDuration, setPausedDuration] = useState(0);
  const pausedRotationValue = useRef<number>(0);
  const pauseStartTime = useRef<number>(0);
  const totalPausedTime = useRef<number>(0);
  const [showLoadingAnimation, setShowLoadingAnimation] = useState(true);

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
  const rotateAnim = useRef(new Animated.Value(0)).current;
  const indicatorPulse = useRef(new Animated.Value(1)).current;
  const buttonScale = useRef(new Animated.Value(1)).current;

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
              toValue: 1.6,
              duration: 1500,
              easing: Easing.out(Easing.ease),
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
      const pulse2 = createPulse(pulseAnim2, 500);
      const pulse3 = createPulse(pulseAnim3, 1000);

      // Rotation animation - reset to 0 before each loop
      const rotate = Animated.loop(
        Animated.sequence([
          Animated.timing(rotateAnim, {
            toValue: 1,
            duration: 3000,
            easing: Easing.linear,
            useNativeDriver: true,
          }),
          Animated.timing(rotateAnim, {
            toValue: 0,
            duration: 0,
            useNativeDriver: true,
          }),
        ])
      );

      // Recording indicator pulse
      const indicatorAnimation = Animated.loop(
        Animated.sequence([
          Animated.timing(indicatorPulse, {
            toValue: 1.3,
            duration: 800,
            easing: Easing.ease,
            useNativeDriver: true,
          }),
          Animated.timing(indicatorPulse, {
            toValue: 1,
            duration: 800,
            easing: Easing.ease,
            useNativeDriver: true,
          }),
        ])
      );

      pulse1.start();
      pulse2.start();
      pulse3.start();
      rotate.start();
      indicatorAnimation.start();

      return () => {
        pulse1.stop();
        pulse2.stop();
        pulse3.stop();
        rotate.stop();
        indicatorAnimation.stop();
        indicatorPulse.setValue(1);
      };
    }
  }, [isRecording, isPaused]);

  const animateButtonPress = () => {
    Animated.sequence([
      Animated.timing(buttonScale, {
        toValue: 0.95,
        duration: 100,
        useNativeDriver: true,
      }),
      Animated.timing(buttonScale, {
        toValue: 1,
        duration: 100,
        useNativeDriver: true,
      }),
    ]).start();
  };

  const handleStartRecording = async () => {
    animateButtonPress();
    
    // Reset pause tracking
    totalPausedTime.current = 0;
    pauseStartTime.current = 0;
    pausedRotationValue.current = 0;
    rotateAnim.setValue(0);
      
    // Use selected group ID or null for personal sessions
    const groupId = selectedGroupId || groups[0]?.id || null;

    try {
      console.log('Starting recording with groupId:', groupId);
      await startRecording(groupId);
      setIsPaused(false);
      console.log('Recording started successfully');
    } catch (err: any) {
      console.error('Failed to start recording:', err);
      Alert.alert('Recording Error', err?.message || 'Failed to start recording');
    }
  };

  const handleStopRecording = async () => {
    console.log('🛑 STOP BUTTON PRESSED - handleStopRecording called');
    try {
      console.log('🛑 Calling stopRecording...');
      const sessionId = await stopRecording();
      console.log('🛑 stopRecording returned sessionId:', sessionId);
      if (sessionId) {
        console.log('🛑 Navigating to Processing screen with sessionId:', sessionId);
        navigation.navigate('Processing', { sessionId });
      } else {
        console.log('🛑 No sessionId returned, not navigating');
      }
    } catch (err) {
      console.error('🛑 Error in handleStopRecording:', err);
      Alert.alert('Error', 'Failed to stop recording');
    }
  };

  const handlePauseResume = () => {
    if (!isPaused) {
      // Pausing - record when we paused and save the current display time
      pauseStartTime.current = duration;
      setPausedDuration(duration - totalPausedTime.current);
      pausedRotationValue.current = rotateAnim.__getValue();
    } else {
      // Resuming - add the paused duration to total and restore rotation
      const pauseDuration = duration - pauseStartTime.current;
      totalPausedTime.current += pauseDuration;
      
      // Set rotation to where we paused before starting animation again
      rotateAnim.setValue(pausedRotationValue.current);
    }
    setIsPaused(!isPaused);
  };

  // When paused, show frozen time. When active, subtract paused time from duration
  const displayDuration = isPaused ? pausedDuration : (duration - totalPausedTime.current);

  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const renderIdleState = () => (
    <>
      <Text style={styles.titleText}>Start your yap session</Text>
      <View style={styles.mainButtonContainer}>
        <TouchableOpacity
          onPress={handleStartRecording}
          activeOpacity={1}
        >
          <Animated.View 
            style={[
              styles.logoButton,
              {
                transform: [{ scale: buttonScale }],
              },
            ]}
          >
            <View style={styles.logoCircle}>
              <Image
                source={require('../../assets/images/rabak-logo.jpg')}
                style={styles.logoImage}
                resizeMode="cover"
              />
              <View style={styles.greyOverlay} />
            </View>
          </Animated.View>
        </TouchableOpacity>
      </View>
      <View style={styles.controlsPlaceholder} />
      <Text style={styles.subtitleText}>Tap to begin recording</Text>
    </>
  );

  const renderRecordingState = () => {
    const spin = rotateAnim.interpolate({
      inputRange: [0, 1],
      outputRange: ['0deg', '360deg'],
    });

    return (
      <>
        <Text style={styles.titleText}>Recording...</Text>
        <View style={styles.mainButtonContainer}>
          <View style={styles.recordingContainer}>
            {/* Pulsing circles */}
            <Animated.View
              style={[
                styles.pulseCircle,
                styles.pulseCircle3,
                {
                  transform: [{ scale: pulseAnim3 }],
                  opacity: pulseAnim3.interpolate({
                    inputRange: [1, 1.6],
                    outputRange: [0.4, 0],
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
                    inputRange: [1, 1.6],
                    outputRange: [0.5, 0],
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
                    inputRange: [1, 1.6],
                    outputRange: [0.6, 0],
                  }),
                },
              ]}
            />

            <View style={styles.logoButton}>
              <View style={styles.logoCircle}>
                <Animated.Image
                  source={require('../../assets/images/rabak-logo.jpg')}
                  style={[
                    styles.logoImage,
                    {
                      transform: [{ rotate: spin }],
                    },
                  ]}
                  resizeMode="cover"
                />
                <View style={styles.greyOverlay} />
              </View>
            </View>
          </View>
        </View>

        {/* Control buttons */}
        <View style={styles.recordingControls}>
          <TouchableOpacity
            style={styles.controlNavButton}
            onPress={handlePauseResume}
            activeOpacity={0.7}
          >
            <Text style={styles.controlIcon}>❚❚</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.controlNavButton}
            onPress={handleStopRecording}
            activeOpacity={0.7}
          >
            <Text style={styles.controlIcon}>■</Text>
          </TouchableOpacity>
        </View>
        <Text style={styles.subtitleText}>Recording in progress...</Text>
      </>
    );
  };

  const renderPausedState = () => {
    const pausedSpin = rotateAnim.interpolate({
      inputRange: [0, 1],
      outputRange: ['0deg', '360deg'],
    });

    return (
      <>
        <Text style={styles.titleText}>Paused</Text>
        <View style={styles.mainButtonContainer}>
          <View style={styles.logoButton}>
            <View style={styles.logoCircle}>
              <Animated.Image
                source={require('../../assets/images/rabak-logo.jpg')}
                style={[
                  styles.logoImage,
                  {
                    transform: [{ rotate: pausedSpin }],
                  },
                ]}
                resizeMode="cover"
              />
              <View style={styles.greyOverlay} />
            </View>
          </View>
        </View>

        <View style={styles.recordingControls}>
          <TouchableOpacity
            style={styles.controlNavButton}
            onPress={handlePauseResume}
            activeOpacity={0.7}
          >
            <Text style={styles.controlIcon}>▶</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.controlNavButton}
            onPress={handleStopRecording}
            activeOpacity={0.7}
          >
            <Text style={styles.controlIcon}>■</Text>
          </TouchableOpacity>
        </View>
        <Text style={styles.subtitleText}>Resume or stop recording</Text>
      </>
    );
  };

  return (
    <LinearGradient
      colors={['#0A0A0A', '#1A1A1A', '#0F0F0F']}
      locations={[0, 0.5, 1]}
      start={{ x: 0, y: 0 }}
      end={{ x: 0, y: 1 }}
      style={styles.container}
    >
      <SafeAreaView style={styles.safeArea}>
        {/* Recording Duration */}
        {isRecording && (
          <View style={styles.durationContainer}>
            <Animated.View 
              style={[
                styles.recordingIndicator,
                {
                  transform: [{ scale: isPaused ? 1 : indicatorPulse }],
                },
              ]} 
            />
            <Text style={styles.durationText}>{formatDuration(displayDuration)}</Text>
          </View>
        )}

        {/* Main Content */}
        <View style={styles.content}>
          {!isRecording && renderIdleState()}
          {isRecording && !isPaused && renderRecordingState()}
          {isRecording && isPaused && renderPausedState()}
        </View>

        {/* Upload Status */}
        {isRecording && chunksUploaded > 0 && (
          <View style={styles.statusContainer}>
            <Text style={styles.statusText}>
              {chunksUploaded} chunk{chunksUploaded !== 1 ? 's' : ''} uploaded
            </Text>
          </View>
        )}
      </SafeAreaView>
      
      {/* Bubble Loading Animation Overlay */}
      {showLoadingAnimation && (
        <BubbleLoadingOverlay 
          onComplete={() => setShowLoadingAnimation(false)}
        />
      )}
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
    paddingHorizontal: 24,
    paddingTop: 16,
  },
  navButton: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
    elevation: 4,
  },
  navIconText: {
    fontSize: 26,
    color: '#FFFFFF',
  },
  notificationDot: {
    position: 'absolute',
    top: 10,
    right: 10,
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#FF3B30',
    borderWidth: 1.5,
    borderColor: '#FFFFFF',
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 32,
  },
  titleText: {
    fontSize: 32,
    fontWeight: '600',
    color: '#FFFFFF',
    textAlign: 'center',
    marginBottom: 64,
    letterSpacing: 0.3,
    textShadowColor: 'rgba(0, 0, 0, 0.3)',
    textShadowOffset: { width: 0, height: 2 },
    textShadowRadius: 4,
  },
  subtitleText: {
    fontSize: 16,
    fontWeight: '400',
    color: 'rgba(255, 255, 255, 0.8)',
    textAlign: 'center',
    marginTop: 32,
    letterSpacing: 0.2,
  },
  mainButtonContainer: {
    width: 300,
    height: 300,
    justifyContent: 'center',
    alignItems: 'center',
  },
  logoButton: {
    width: 220,
    height: 220,
    justifyContent: 'center',
    alignItems: 'center',
  },
  logoCircle: {
    width: 220,
    height: 220,
    borderRadius: 110,
    borderWidth: 5,
    borderColor: '#FFFFFF',
    backgroundColor: '#4A4A4A',
    justifyContent: 'center',
    alignItems: 'center',
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.3,
    shadowRadius: 16,
    elevation: 8,
  },
  logoImage: {
    width: '100%',
    height: '100%',
  },
  greyOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(128, 128, 128, 0.7)',
    mixBlendMode: 'saturation',
  },
  recordingContainer: {
    width: 300,
    height: 300,
    justifyContent: 'center',
    alignItems: 'center',
  },
  pulseCircle: {
    position: 'absolute',
    borderRadius: 160,
    borderWidth: 2.5,
    borderColor: 'rgba(255, 255, 255, 0.8)',
  },
  pulseCircle1: {
    width: 220,
    height: 220,
  },
  pulseCircle2: {
    width: 260,
    height: 260,
  },
  pulseCircle3: {
    width: 300,
    height: 300,
  },
  recordingControls: {
    flexDirection: 'row',
    height: 64,
    gap: 32,
    alignItems: 'center',
    justifyContent: 'center',
  },
  controlsPlaceholder: {
    height: 64,
  },
  controlNavButton: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: 'rgba(255, 255, 255, 0.4)',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
    elevation: 4,
  },
  controlIcon: {
    fontSize: 24,
    color: '#FFFFFF',
    fontWeight: '700',
  },
  durationContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    paddingHorizontal: 24,
    backgroundColor: 'rgba(0, 0, 0, 0.3)',
    borderRadius: 24,
    alignSelf: 'center',
    marginTop: 16,
  },
  recordingIndicator: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: '#FF3B30',
    marginRight: 10,
  },
  durationText: {
    fontSize: 20,
    fontWeight: '600',
    color: '#FFFFFF',
    fontVariant: ['tabular-nums'],
  },
  statusContainer: {
    position: 'absolute',
    bottom: 40,
    alignSelf: 'center',
    paddingVertical: 8,
    paddingHorizontal: 16,
    backgroundColor: 'rgba(0, 0, 0, 0.3)',
    borderRadius: 16,
  },
  statusText: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.8)',
    fontWeight: '500',
  },
});
