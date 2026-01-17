import React, { useEffect, useRef, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  Image,
  Animated,
  Easing,
} from 'react-native';
import { StackNavigationProp } from '@react-navigation/stack';
import { RouteProp } from '@react-navigation/native';
import { RecordStackParamList } from '../navigation/MainNavigator';
import { useSessionStatus } from '../hooks/useSessionStatus';
import { LinearGradient } from 'expo-linear-gradient';

type ProcessingScreenNavigationProp = StackNavigationProp<RecordStackParamList, 'Processing'>;
type ProcessingScreenRouteProp = RouteProp<RecordStackParamList, 'Processing'>;

interface Props {
  navigation: ProcessingScreenNavigationProp;
  route: ProcessingScreenRouteProp;
}

const SINGLISH_MESSAGES = [
  'Wait ah, collecting audio chunks leh...',
  'Aiyo, processing your recording...',
  'Walao, need some time to process ah...',
  'Steady lah, almost done loading...',
  'Sibei long sia, but wait ah...',
  'Chop chop, processing now...',
];

export default function ProcessingScreen({ navigation, route }: Props) {
  const { sessionId } = route.params;
  // const { status, progress, error } = useSessionStatus(sessionId);

  // TEMPORARY: Fake loading progress
  const [fakeProgress, setFakeProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const progress = fakeProgress;

  const spinValue = useRef(new Animated.Value(0)).current;
  const progressAnim = useRef(new Animated.Value(0)).current;
  const [messageIndex, setMessageIndex] = useState(0);

  // TEMPORARY: Fake progress increment
  useEffect(() => {
    const interval = setInterval(() => {
      setFakeProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          // Navigate to Wrapped screen after a short delay
          setTimeout(() => {
            navigation.replace('Wrapped', { sessionId });
          }, 500);
          return 100;
        }
        // Increment by 1% every 100ms (complete in ~10 seconds)
        return prev + 1;
      });
    }, 100);

    return () => clearInterval(interval);
  }, [navigation, sessionId]);

  // useEffect(() => {
  //   if (status === 'ready_for_claiming' || status === 'completed') {
  //     // Navigate to Wrapped screen with session data
  //     navigation.replace('Wrapped', { sessionId });
  //   } else if (status === 'error') {
  //     // Stay on screen to show error
  //   }
  // }, [status, sessionId, navigation]);

  useEffect(() => {
    // Spinning animation - use sequence with reset to ensure continuous loop
    const spinAnimation = Animated.loop(
      Animated.sequence([
        Animated.timing(spinValue, {
          toValue: 1,
          duration: 2000,
          easing: Easing.linear,
          useNativeDriver: true,
        }),
        Animated.timing(spinValue, {
          toValue: 0,
          duration: 0,
          useNativeDriver: true,
        }),
      ])
    );
    
    spinAnimation.start();
    
    // Cleanup: stop animation when component unmounts
    return () => {
      spinAnimation.stop();
    };
  }, [spinValue]);

  useEffect(() => {
    // Progress bar animation
    Animated.timing(progressAnim, {
      toValue: progress,
      duration: 500,
      useNativeDriver: false,
    }).start();
  }, [progress]);

  // Cycle through Singlish messages
  useEffect(() => {
    if (progress < 30 && !error) {
      const interval = setInterval(() => {
        setMessageIndex((prev) => (prev + 1) % SINGLISH_MESSAGES.length);
      }, 2000); // Change message every 2 seconds

      return () => clearInterval(interval);
    }
  }, [progress, error]);

  const spin = spinValue.interpolate({
    inputRange: [0, 1],
    outputRange: ['0deg', '360deg'],
  });

  const getStatusMessage = (): string => {
    if (error) return 'Error processing audio';

    if (progress < 30) return SINGLISH_MESSAGES[messageIndex];
    if (progress < 50) return 'Detecting speakers...';
    if (progress < 70) return 'Transcribing conversation...';
    if (progress < 90) return 'Alamak need to analyse word usage...';
    return 'Almost ready!';
  };

  return (
    <LinearGradient
      colors={['#6B1B1B', '#A64545']}
      start={{ x: 0, y: 0 }}
      end={{ x: 0, y: 1 }}
      style={styles.container}
    >
      <SafeAreaView style={styles.safeArea}>
        <View style={styles.content}>
          {/* Logo at top */}
          <View style={styles.logoContainer}>
            <View style={styles.logoCircle}>
              <Image
                source={require('../../assets/images/rabak-logo.jpg')}
                style={styles.logoImage}
                resizeMode="cover"
              />
            </View>
          </View>

          <Text style={styles.title}>Processing Your Recording</Text>

          {/* Spinning loader */}
          <View style={styles.spinnerContainer}>
            {!error && (
              <Animated.View
                style={[
                  styles.spinner,
                  {
                    transform: [{ rotate: spin }],
                  },
                ]}
              />
            )}
          </View>

          {/* Progress bar */}
          <View style={styles.progressBarContainer}>
            <View style={styles.progressBarBg}>
              <Animated.View
                style={[
                  styles.progressBarFill,
                  {
                    width: progressAnim.interpolate({
                      inputRange: [0, 100],
                      outputRange: ['0%', '100%'],
                    }),
                  },
                ]}
              />
            </View>
          </View>

          {/* Percentage */}
          <Text style={styles.progressText}>{progress}%</Text>

          {/* Status message */}
          <Text style={[styles.statusText, error && styles.errorText]}>
            {getStatusMessage()}
          </Text>

          {error && (
            <Text style={styles.errorDetails}>{error}</Text>
          )}

          {/* Time estimate */}
          {!error && (
            <Text style={styles.helperText}>
              This usually takes 30-60 seconds
            </Text>
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
  content: {
    flex: 1,
    paddingHorizontal: 32,
    justifyContent: 'center',
    alignItems: 'center',
  },
  logoContainer: {
    marginBottom: 40,
  },
  logoCircle: {
    width: 160,
    height: 160,
    borderRadius: 80,
    borderWidth: 5,
    borderColor: '#FFFFFF',
    backgroundColor: '#ED4545',
    justifyContent: 'center',
    alignItems: 'center',
    overflow: 'hidden',
  },
  logoImage: {
    width: '100%',
    height: '100%',
  },
  title: {
    fontSize: 28,
    fontWeight: '400',
    color: '#FFFFFF',
    textAlign: 'center',
    marginBottom: 60,
    letterSpacing: 0.5,
  },
  spinnerContainer: {
    height: 80,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 40,
  },
  spinner: {
    width: 60,
    height: 60,
    borderRadius: 30,
    borderWidth: 4,
    borderColor: 'rgba(255, 255, 255, 0.3)',
    borderTopColor: '#FFFFFF',
  },
  progressBarContainer: {
    width: '100%',
    marginBottom: 20,
  },
  progressBarBg: {
    width: '100%',
    height: 8,
    backgroundColor: 'rgba(255, 255, 255, 0.3)',
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressBarFill: {
    height: '100%',
    backgroundColor: '#FFFFFF',
    borderRadius: 4,
  },
  progressText: {
    fontSize: 48,
    fontWeight: '600',
    color: '#FFFFFF',
    marginBottom: 30,
  },
  statusText: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.9)',
    textAlign: 'center',
    marginBottom: 12,
  },
  errorText: {
    color: '#FFFFFF',
    fontWeight: '600',
  },
  errorDetails: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.7)',
    textAlign: 'center',
    marginTop: 8,
    paddingHorizontal: 20,
  },
  helperText: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.7)',
    marginTop: 20,
    textAlign: 'center',
  },
});
