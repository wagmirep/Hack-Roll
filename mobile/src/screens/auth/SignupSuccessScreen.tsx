import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Animated,
  SafeAreaView,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { StackNavigationProp } from '@react-navigation/stack';
import { AuthStackParamList } from '../../navigation/AuthNavigator';

type SignupSuccessScreenNavigationProp = StackNavigationProp<AuthStackParamList, 'SignupSuccess'>;

interface Props {
  navigation: SignupSuccessScreenNavigationProp;
}

export default function SignupSuccessScreen({ navigation }: Props) {
  const [fadeAnim] = useState(new Animated.Value(0));
  const [countdown, setCountdown] = useState(5);

  useEffect(() => {
    // Fade in animation
    Animated.timing(fadeAnim, {
      toValue: 1,
      duration: 600,
      useNativeDriver: true,
    }).start();

    // Countdown timer
    const interval = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          navigation.navigate('Login');
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [fadeAnim, navigation]);

  const handleGoToLogin = () => {
    navigation.navigate('Login');
  };

  return (
    <LinearGradient
      colors={['#6B1B1B', '#A64545']}
      start={{ x: 0, y: 0 }}
      end={{ x: 0, y: 1 }}
      style={styles.container}
    >
      <SafeAreaView style={styles.safeArea}>
        <View style={styles.wrapper}>
          <Animated.View style={[styles.content, { opacity: fadeAnim }]}>
            {/* Success Icon */}
            <View style={styles.iconContainer}>
              <Text style={styles.checkmark}>✓</Text>
            </View>

            {/* Success Message */}
            <Text style={styles.title}>Account Created!</Text>
            <Text style={styles.subtitle}>
              Welcome to LahStats!
            </Text>

            {/* Email Verification Message */}
            <View style={styles.messageBox}>
              <Text style={styles.messageTitle}>Check Your Email</Text>
              <Text style={styles.messageText}>
                We've sent you a verification email.{'\n'}
                Please check your inbox and click the{'\n'}
                verification link to activate your account.
              </Text>
            </View>

            {/* Info Text */}
            <Text style={styles.infoText}>
              Didn't receive the email? Check your spam folder.
            </Text>

            {/* Countdown */}
            <Text style={styles.countdown}>
              Redirecting to sign in in {countdown}s...
            </Text>

            {/* Manual Button */}
            <TouchableOpacity 
              style={styles.button}
              onPress={handleGoToLogin}
            >
              <Text style={styles.buttonText}>Go to Sign In</Text>
            </TouchableOpacity>
          </Animated.View>
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
  wrapper: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  content: {
    alignItems: 'center',
    width: '100%',
    maxWidth: 400,
  },
  iconContainer: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: '#FFFFFF',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 32,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 4,
    },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  checkmark: {
    fontSize: 60,
    color: '#6B1B1B',
    fontWeight: 'bold',
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#FFFFFF',
    textAlign: 'center',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 18,
    color: 'rgba(255, 255, 255, 0.8)',
    textAlign: 'center',
    marginBottom: 32,
  },
  messageBox: {
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.3)',
    borderRadius: 16,
    padding: 24,
    width: '100%',
    alignItems: 'center',
    marginBottom: 24,
  },
  messageTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#FFFFFF',
    marginBottom: 12,
    textAlign: 'center',
  },
  messageText: {
    fontSize: 15,
    color: 'rgba(255, 255, 255, 0.8)',
    textAlign: 'center',
    lineHeight: 22,
  },
  infoText: {
    fontSize: 13,
    color: 'rgba(255, 255, 255, 0.6)',
    textAlign: 'center',
    marginBottom: 24,
    fontStyle: 'italic',
  },
  countdown: {
    fontSize: 14,
    color: '#FFFFFF',
    textAlign: 'center',
    marginBottom: 16,
    fontWeight: '500',
  },
  button: {
    backgroundColor: '#FFFFFF',
    paddingVertical: 16,
    paddingHorizontal: 32,
    borderRadius: 12,
    width: '100%',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 4,
  },
  buttonText: {
    color: '#6B1B1B',
    fontSize: 16,
    fontWeight: '600',
  },
});
