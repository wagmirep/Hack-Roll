import React, { useEffect, useRef } from 'react';
import {
  View,
  StyleSheet,
  Animated,
  Dimensions,
  Image,
  Easing,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';

interface BubbleLoadingOverlayProps {
  onComplete: () => void;
}

export default function BubbleLoadingOverlay({ onComplete }: BubbleLoadingOverlayProps) {
  const [screenDimensions] = React.useState(Dimensions.get('window'));
  const overlayOpacity = useRef(new Animated.Value(1)).current;
  const logoScale = useRef(new Animated.Value(0)).current;
  const logoOpacity = useRef(new Animated.Value(0)).current;
  const logoGlow = useRef(new Animated.Value(0)).current;

  // Geometric shape animations - Top Right
  const shapeTopRight1 = useRef(new Animated.Value(0)).current;
  const shapeTopRight2 = useRef(new Animated.Value(0)).current;
  const shapeTopRight3 = useRef(new Animated.Value(0)).current;

  // Geometric shape animations - Bottom Left
  const shapeBottomLeft1 = useRef(new Animated.Value(0)).current;
  const shapeBottomLeft2 = useRef(new Animated.Value(0)).current;
  const shapeBottomLeft3 = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    // Phase 1: Geometric shapes spread out (0-1.5s)
    const shapesAnimation = Animated.parallel([
      // Top Right shapes
      Animated.timing(shapeTopRight1, {
        toValue: 1,
        duration: 1500,
        easing: Easing.out(Easing.cubic),
        useNativeDriver: true,
      }),
      Animated.timing(shapeTopRight2, {
        toValue: 1,
        duration: 1500,
        delay: 100,
        easing: Easing.out(Easing.cubic),
        useNativeDriver: true,
      }),
      Animated.timing(shapeTopRight3, {
        toValue: 1,
        duration: 1500,
        delay: 200,
        easing: Easing.out(Easing.cubic),
        useNativeDriver: true,
      }),
      // Bottom Left shapes
      Animated.timing(shapeBottomLeft1, {
        toValue: 1,
        duration: 1500,
        delay: 300,
        easing: Easing.out(Easing.cubic),
        useNativeDriver: true,
      }),
      Animated.timing(shapeBottomLeft2, {
        toValue: 1,
        duration: 1500,
        delay: 400,
        easing: Easing.out(Easing.cubic),
        useNativeDriver: true,
      }),
      Animated.timing(shapeBottomLeft3, {
        toValue: 1,
        duration: 1500,
        delay: 500,
        easing: Easing.out(Easing.cubic),
        useNativeDriver: true,
      }),
    ]);

    shapesAnimation.start(() => {
      // Phase 2: Logo reveal with glow (1.5-2.5s)
      Animated.parallel([
        Animated.timing(logoScale, {
          toValue: 1,
          duration: 800,
          easing: Easing.out(Easing.back(1.2)),
          useNativeDriver: true,
        }),
        Animated.timing(logoOpacity, {
          toValue: 1,
          duration: 600,
          useNativeDriver: true,
        }),
        Animated.sequence([
          Animated.timing(logoGlow, {
            toValue: 1,
            duration: 600,
            easing: Easing.out(Easing.ease),
            useNativeDriver: false,
          }),
          Animated.timing(logoGlow, {
            toValue: 0.3,
            duration: 400,
            easing: Easing.inOut(Easing.ease),
            useNativeDriver: false,
          }),
        ]),
      ]).start(() => {
        // Phase 3: Auto-transition (after 600ms hold)
        setTimeout(() => {
          Animated.timing(overlayOpacity, {
            toValue: 0,
            duration: 500,
            easing: Easing.in(Easing.ease),
            useNativeDriver: true,
          }).start(() => {
            onComplete();
          });
        }, 600);
      });
    });
  }, []);

  const centerX = screenDimensions.width / 2;
  const centerY = screenDimensions.height / 2;

  // Interpolate shape positions for spread animation
  const topRightTransform1 = shapeTopRight1.interpolate({
    inputRange: [0, 1],
    outputRange: [150, 0],
  });
  const topRightTransform2 = shapeTopRight2.interpolate({
    inputRange: [0, 1],
    outputRange: [150, 0],
  });
  const topRightTransform3 = shapeTopRight3.interpolate({
    inputRange: [0, 1],
    outputRange: [150, 0],
  });

  const bottomLeftTransform1 = shapeBottomLeft1.interpolate({
    inputRange: [0, 1],
    outputRange: [-150, 0],
  });
  const bottomLeftTransform2 = shapeBottomLeft2.interpolate({
    inputRange: [0, 1],
    outputRange: [-150, 0],
  });
  const bottomLeftTransform3 = shapeBottomLeft3.interpolate({
    inputRange: [0, 1],
    outputRange: [-150, 0],
  });

  return (
    <Animated.View
      style={[
        styles.overlay,
        {
          opacity: overlayOpacity,
        },
      ]}
      pointerEvents="none"
    >
      <LinearGradient
        colors={['#0A0A0A', '#1A1A1A', '#0F0F0F']}
        locations={[0, 0.5, 1]}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={styles.gradient}
      >
        {/* Top Right Stepped Shapes */}
        <Animated.View
          style={[
            styles.shapeTopRight1,
            {
              opacity: shapeTopRight1,
              transform: [
                { translateX: topRightTransform1 },
                { translateY: topRightTransform1.interpolate({
                  inputRange: [-150, 0],
                  outputRange: [150, 0],
                }) },
                { scale: shapeTopRight1 },
              ],
            },
          ]}
        />
        <Animated.View
          style={[
            styles.shapeTopRight2,
            {
              opacity: shapeTopRight2,
              transform: [
                { translateX: topRightTransform2 },
                { translateY: topRightTransform2.interpolate({
                  inputRange: [-150, 0],
                  outputRange: [150, 0],
                }) },
                { scale: shapeTopRight2 },
              ],
            },
          ]}
        />
        <Animated.View
          style={[
            styles.shapeTopRight3,
            {
              opacity: shapeTopRight3,
              transform: [
                { translateX: topRightTransform3 },
                { translateY: topRightTransform3.interpolate({
                  inputRange: [-150, 0],
                  outputRange: [150, 0],
                }) },
                { scale: shapeTopRight3 },
              ],
            },
          ]}
        />

        {/* Bottom Left Stepped Shapes */}
        <Animated.View
          style={[
            styles.shapeBottomLeft1,
            {
              opacity: shapeBottomLeft1,
              transform: [
                { translateX: bottomLeftTransform1 },
                { translateY: bottomLeftTransform1.interpolate({
                  inputRange: [-150, 0],
                  outputRange: [-150, 0],
                }) },
                { scale: shapeBottomLeft1 },
              ],
            },
          ]}
        />
        <Animated.View
          style={[
            styles.shapeBottomLeft2,
            {
              opacity: shapeBottomLeft2,
              transform: [
                { translateX: bottomLeftTransform2 },
                { translateY: bottomLeftTransform2.interpolate({
                  inputRange: [-150, 0],
                  outputRange: [-150, 0],
                }) },
                { scale: shapeBottomLeft2 },
              ],
            },
          ]}
        />
        <Animated.View
          style={[
            styles.shapeBottomLeft3,
            {
              opacity: shapeBottomLeft3,
              transform: [
                { translateX: bottomLeftTransform3 },
                { translateY: bottomLeftTransform3.interpolate({
                  inputRange: [-150, 0],
                  outputRange: [-150, 0],
                }) },
                { scale: shapeBottomLeft3 },
              ],
            },
          ]}
        />

        {/* Logo - Center with glow */}
        <Animated.View
          style={[
            styles.logoContainer,
            {
              left: centerX - 100,
              top: centerY - 100,
              transform: [{ scale: logoScale }],
              opacity: logoOpacity,
            },
          ]}
        >
          <Animated.View
            style={[
              styles.logoGlow,
              {
                opacity: logoGlow,
              },
            ]}
          />
          <View style={styles.logoCircle}>
            <Image
              source={require('../../assets/images/rabak-logo.jpg')}
              style={styles.logoImage}
              resizeMode="cover"
            />
            <View style={styles.greyOverlay} />
          </View>
        </Animated.View>
      </LinearGradient>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  overlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    zIndex: 999,
  },
  gradient: {
    flex: 1,
  },
  // Top Right Stepped Shapes (Pink/Red gradient)
  shapeTopRight1: {
    position: 'absolute',
    top: -40,
    right: -40,
    width: 500,
    height: 400,
    backgroundColor: 'rgba(255, 105, 180, 0.7)',
    borderBottomLeftRadius: 200,
  },
  shapeTopRight2: {
    position: 'absolute',
    top: 8,
    right: 8,
    width: 450,
    height: 350,
    backgroundColor: 'rgba(255, 105, 180, 0.85)',
    borderBottomLeftRadius: 180,
  },
  shapeTopRight3: {
    position: 'absolute',
    top: 56,
    right: 56,
    width: 400,
    height: 300,
    backgroundColor: 'rgba(255, 20, 147, 1)',
    borderBottomLeftRadius: 160,
  },
  // Bottom Left Stepped Shapes (Red/Pink gradient)
  shapeBottomLeft1: {
    position: 'absolute',
    bottom: -40,
    left: -40,
    width: 500,
    height: 400,
    backgroundColor: 'rgba(220, 38, 38, 0.7)',
    borderTopRightRadius: 200,
  },
  shapeBottomLeft2: {
    position: 'absolute',
    bottom: 8,
    left: 8,
    width: 450,
    height: 350,
    backgroundColor: 'rgba(220, 38, 38, 0.85)',
    borderTopRightRadius: 180,
  },
  shapeBottomLeft3: {
    position: 'absolute',
    bottom: 56,
    left: 56,
    width: 400,
    height: 300,
    backgroundColor: 'rgba(185, 28, 28, 1)',
    borderTopRightRadius: 160,
  },
  // Logo styles
  logoContainer: {
    position: 'absolute',
    width: 200,
    height: 200,
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 100,
  },
  logoGlow: {
    position: 'absolute',
    width: 240,
    height: 240,
    borderRadius: 120,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    shadowColor: '#FFFFFF',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.6,
    shadowRadius: 30,
  },
  logoCircle: {
    width: 200,
    height: 200,
    borderRadius: 100,
    borderWidth: 6,
    borderColor: '#FFFFFF',
    backgroundColor: '#4A4A4A',
    justifyContent: 'center',
    alignItems: 'center',
    overflow: 'hidden',
    shadowColor: '#FFFFFF',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.3,
    shadowRadius: 20,
    elevation: 10,
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
  },
});
