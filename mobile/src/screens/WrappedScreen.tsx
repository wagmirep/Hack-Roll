import React, { useState, useRef, useEffect, createContext, useContext } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableWithoutFeedback,
  TouchableOpacity,
  useWindowDimensions,
  ActivityIndicator,
  Animated,
  Easing,
  Share,
  Alert,
} from 'react-native';
import { StackNavigationProp } from '@react-navigation/stack';
import { RouteProp } from '@react-navigation/native';
import { RecordStackParamList } from '../navigation/MainNavigator';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { Audio } from 'expo-av';
import { api } from '../api/client';

// Context for responsive dimensions
const DimensionsContext = createContext({ width: 400, height: 800 });
const useDimensions = () => useContext(DimensionsContext);

type WrappedScreenNavigationProp = StackNavigationProp<RecordStackParamList, 'Wrapped'>;
type WrappedScreenRouteProp = RouteProp<RecordStackParamList, 'Wrapped'>;

interface Props {
  navigation: WrappedScreenNavigationProp;
  route: WrappedScreenRouteProp;
}

interface TopWord {
  word: string;
  count: number;
}

interface SpeakerData {
  id: string;
  name: string;
  topWords: TopWord[];
  mostUsedWord: string;
  audioClipUrl?: string;
}

interface WrappedData {
  speakerCount: number;
  duration: number;
  topWords: TopWord[];
  mostUsedWord: string;
  totalWords: number;
  singlishWordsCount: number;
  speakers: SpeakerData[];
}

const numberToWord = (num: number): string => {
  const words = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten'];
  return num <= 10 ? words[num] : num.toString();
};

// Capitalize first letter
const capitalize = (str: string): string => {
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
};

// ============================================================================
// SLIDE 1: SPEAKERS - Cyan-Pink gradient with stepped angular shapes
// ============================================================================
function SpeakersSlide({ count, isActive }: { count: number; isActive: boolean }) {
  const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = useDimensions();
  const shape1Anim = useRef(new Animated.Value(0)).current;
  const shape2Anim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (isActive) {
      shape1Anim.setValue(0);
      shape2Anim.setValue(0);
      
      Animated.parallel([
        Animated.timing(shape1Anim, {
          toValue: 1,
          duration: 1500,
          easing: Easing.out(Easing.cubic),
          useNativeDriver: true,
        }),
        Animated.timing(shape2Anim, {
          toValue: 1,
          duration: 1500,
          delay: 300,
          easing: Easing.out(Easing.cubic),
          useNativeDriver: true,
        }),
      ]).start();
    }
  }, [isActive]);

  const shape1Style = {
    transform: [
      { translateX: shape1Anim.interpolate({ inputRange: [0, 1], outputRange: [150, 0] }) },
      { translateY: shape1Anim.interpolate({ inputRange: [0, 1], outputRange: [-150, 0] }) },
      { scale: shape1Anim.interpolate({ inputRange: [0, 1], outputRange: [0.5, 1] }) },
    ],
    opacity: shape1Anim,
  };

  const shape2Style = {
    transform: [
      { translateX: shape2Anim.interpolate({ inputRange: [0, 1], outputRange: [-150, 0] }) },
      { translateY: shape2Anim.interpolate({ inputRange: [0, 1], outputRange: [150, 0] }) },
      { scale: shape2Anim.interpolate({ inputRange: [0, 1], outputRange: [0.5, 1] }) },
    ],
    opacity: shape2Anim,
  };

  const shapeSize = SCREEN_WIDTH * 0.9;

  return (
    <View style={styles.slide}>
      <LinearGradient
        colors={['#22D3EE', '#F9A8D4', '#EC4899']}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={StyleSheet.absoluteFillObject}
      />
      
      {/* Top Right Stepped Shapes */}
      <Animated.View style={[{ position: 'absolute', top: -40, right: -40 }, shape1Style]}>
        <View style={[styles.angularShape, { width: shapeSize, height: shapeSize * 0.8, backgroundColor: 'rgba(236, 72, 153, 0.5)' }]} />
        <View style={[styles.angularShape, { width: shapeSize * 0.9, height: shapeSize * 0.7, top: 24, right: 24, backgroundColor: 'rgba(236, 72, 153, 0.7)' }]} />
        <View style={[styles.angularShape, { width: shapeSize * 0.8, height: shapeSize * 0.6, top: 48, right: 48, backgroundColor: 'rgba(236, 72, 153, 0.9)' }]} />
      </Animated.View>
      
      {/* Bottom Left Stepped Shapes */}
      <Animated.View style={[{ position: 'absolute', bottom: -40, left: -40 }, shape2Style]}>
        <View style={[styles.angularShape, { width: shapeSize, height: shapeSize * 0.8, backgroundColor: 'rgba(239, 68, 68, 0.5)' }]} />
        <View style={[styles.angularShape, { width: shapeSize * 0.9, height: shapeSize * 0.7, bottom: 24, left: 24, backgroundColor: 'rgba(239, 68, 68, 0.7)' }]} />
        <View style={[styles.angularShape, { width: shapeSize * 0.8, height: shapeSize * 0.6, bottom: 48, left: 48, backgroundColor: 'rgba(239, 68, 68, 0.9)' }]} />
      </Animated.View>

      <View style={styles.centeredContent}>
        <Text style={[styles.speakersText, { fontSize: SCREEN_WIDTH * 0.115, lineHeight: SCREEN_WIDTH * 0.14 }]}>
          You had{'\n'}
          <Text style={styles.boldBlack}>{numberToWord(count)}</Text>
          {'\n'}speakers this{'\n'}yap session
        </Text>
      </View>
    </View>
  );
}

// ============================================================================
// SLIDE 2: DURATION - Yellow with purple arc
// ============================================================================
function DurationSlide({ seconds, isActive }: { seconds: number; isActive: boolean }) {
  const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = useDimensions();
  const arcAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (isActive) {
      arcAnim.setValue(0);
      Animated.timing(arcAnim, {
        toValue: 1,
        duration: 1500,
        easing: Easing.out(Easing.cubic),
        useNativeDriver: true,
      }).start();
    }
  }, [isActive]);

  const arcStyle = {
    transform: [
      { translateX: arcAnim.interpolate({ inputRange: [0, 1], outputRange: [-100, 0] }) },
      { translateY: arcAnim.interpolate({ inputRange: [0, 1], outputRange: [-100, 0] }) },
      { scale: arcAnim.interpolate({ inputRange: [0, 1], outputRange: [0.3, 1] }) },
    ],
    opacity: arcAnim,
  };

  const arcSize = SCREEN_WIDTH * 1.2;

  return (
    <View style={[styles.slide, { backgroundColor: '#FDE047' }]}>
      {/* Arc decoration */}
      <Animated.View style={[{ position: 'absolute', top: -arcSize * 0.4, left: -arcSize * 0.4 }, arcStyle]}>
        <View style={[styles.arc, { width: arcSize, height: arcSize, backgroundColor: 'rgba(96, 165, 250, 0.6)', borderBottomRightRadius: arcSize }]} />
        <View style={[styles.arc, { width: arcSize * 0.8, height: arcSize * 0.8, top: arcSize * 0.1, left: arcSize * 0.1, backgroundColor: 'rgba(167, 139, 250, 0.5)', borderBottomRightRadius: arcSize * 0.8 }]} />
        <View style={[styles.arc, { width: arcSize * 0.6, height: arcSize * 0.6, top: arcSize * 0.2, left: arcSize * 0.2, backgroundColor: 'rgba(196, 181, 253, 0.4)', borderBottomRightRadius: arcSize * 0.6 }]} />
      </Animated.View>

      <View style={styles.centeredContent}>
        <Text style={[styles.durationTitle, { fontSize: SCREEN_WIDTH * 0.09 }]}>You guys yapped{'\n'}for a total of</Text>
        <Text style={[styles.durationNumber, { fontSize: SCREEN_WIDTH * 0.32, lineHeight: SCREEN_WIDTH * 0.35 }]}>{seconds}</Text>
        <Text style={[styles.durationUnit, { fontSize: SCREEN_WIDTH * 0.1 }]}>seconds</Text>
        <Text style={[styles.durationSubtitle, { fontSize: SCREEN_WIDTH * 0.055 }]}>Drop it like it's hot</Text>
      </View>
    </View>
  );
}

// ============================================================================
// SLIDE 3: TOP WORDS - Blue gradient with diagonal
// ============================================================================
function TopWordsSlide({ words, isActive }: { words: TopWord[]; isActive: boolean }) {
  const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = useDimensions();
  const fadeAnims = useRef(words.slice(0, 5).map(() => new Animated.Value(0))).current;
  const diagonalAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (isActive) {
      diagonalAnim.setValue(0);
      fadeAnims.forEach(anim => anim.setValue(0));
      
      // Diagonal animation
      Animated.timing(diagonalAnim, {
        toValue: 1,
        duration: 1200,
        easing: Easing.out(Easing.cubic),
        useNativeDriver: true,
      }).start();

      // Word fade-in animations
      const animations = fadeAnims.map((anim, index) =>
        Animated.timing(anim, {
          toValue: 1,
          duration: 600,
          delay: 200 + index * 100,
          easing: Easing.out(Easing.cubic),
          useNativeDriver: true,
        })
      );
      Animated.parallel(animations).start();
    }
  }, [isActive]);

  const diagonalStyle = {
    transform: [
      { translateX: diagonalAnim.interpolate({ inputRange: [0, 1], outputRange: [SCREEN_WIDTH, 0] }) },
      { translateY: diagonalAnim.interpolate({ inputRange: [0, 1], outputRange: [-SCREEN_HEIGHT * 0.3, 0] }) },
    ],
    opacity: diagonalAnim,
  };

  return (
    <View style={styles.slide}>
      <LinearGradient
        colors={['#3B82F6', '#60A5FA', '#1E3A5F', '#000000']}
        locations={[0, 0.3, 0.7, 1]}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={StyleSheet.absoluteFillObject}
      />
      
      {/* Diagonal shape */}
      <Animated.View style={[styles.diagonalContainer, diagonalStyle]}>
        <View style={styles.diagonalShape} />
      </Animated.View>

      <View style={styles.topWordsContent}>
        <Text style={[styles.topWordsTitle, { fontSize: SCREEN_WIDTH * 0.095 }]}>Your group's{'\n'}favorite Singlish{'\n'}word</Text>
        <View style={styles.wordsList}>
          {words.slice(0, 5).map((item, index) => (
            <Animated.View
              key={index}
              style={[
                styles.wordRow,
                {
                  opacity: fadeAnims[index] || new Animated.Value(1),
                  transform: [{
                    translateY: (fadeAnims[index] || new Animated.Value(1)).interpolate({
                      inputRange: [0, 1],
                      outputRange: [20, 0],
                    }),
                  }],
                },
              ]}
            >
              <Text style={[styles.wordRank, { fontSize: SCREEN_WIDTH * 0.15, width: SCREEN_WIDTH * 0.22 }]}>{index + 1}</Text>
              <Text style={[styles.wordText, { fontSize: SCREEN_WIDTH * 0.11 }]}>{capitalize(item.word)}</Text>
            </Animated.View>
          ))}
        </View>
      </View>
    </View>
  );
}

// ============================================================================
// SLIDE 4: MOST USED WORD - Black with green triangles
// ============================================================================
function MostUsedWordSlide({ word, isActive }: { word: string; isActive: boolean }) {
  const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = useDimensions();
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const triangleAnim = useRef(new Animated.Value(0)).current;
  const pulseLoop = useRef<Animated.CompositeAnimation | null>(null);

  useEffect(() => {
    if (isActive) {
      triangleAnim.setValue(0);
      pulseAnim.setValue(1);
      
      Animated.timing(triangleAnim, {
        toValue: 1,
        duration: 1500,
        easing: Easing.out(Easing.cubic),
        useNativeDriver: true,
      }).start();

      pulseLoop.current = Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, {
            toValue: 1.05,
            duration: 1000,
            easing: Easing.inOut(Easing.ease),
            useNativeDriver: true,
          }),
          Animated.timing(pulseAnim, {
            toValue: 1,
            duration: 1000,
            easing: Easing.inOut(Easing.ease),
            useNativeDriver: true,
          }),
        ])
      );
      pulseLoop.current.start();
    } else {
      pulseLoop.current?.stop();
    }
    
    return () => { pulseLoop.current?.stop(); };
  }, [isActive]);

  const triangleStyle = {
    transform: [
      { translateX: triangleAnim.interpolate({ inputRange: [0, 1], outputRange: [-150, 0] }) },
      { translateY: triangleAnim.interpolate({ inputRange: [0, 1], outputRange: [-150, 0] }) },
      { scale: triangleAnim.interpolate({ inputRange: [0, 1], outputRange: [0.5, 1] }) },
    ],
    opacity: triangleAnim,
  };

  const triangleSize = SCREEN_WIDTH * 0.85;

  return (
    <View style={[styles.slide, { backgroundColor: '#000000' }]}>
      {/* Green triangle layers */}
      <Animated.View style={[{ position: 'absolute', top: 0, left: 0 }, triangleStyle]}>
        <View style={[styles.triangle, { 
          borderLeftWidth: triangleSize, 
          borderBottomWidth: triangleSize, 
          borderLeftColor: 'rgba(74, 222, 128, 0.9)',
        }]} />
        <View style={[styles.triangle, { 
          borderLeftWidth: triangleSize * 0.85, 
          borderBottomWidth: triangleSize * 0.85, 
          borderLeftColor: 'rgba(74, 222, 128, 0.7)',
          top: triangleSize * 0.08,
          left: triangleSize * 0.08,
        }]} />
        <View style={[styles.triangle, { 
          borderLeftWidth: triangleSize * 0.7, 
          borderBottomWidth: triangleSize * 0.7, 
          borderLeftColor: 'rgba(74, 222, 128, 0.5)',
          top: triangleSize * 0.16,
          left: triangleSize * 0.16,
        }]} />
      </Animated.View>

      <View style={styles.centeredContent}>
        <Text style={[styles.mostUsedTitle, { fontSize: SCREEN_WIDTH * 0.065, lineHeight: SCREEN_WIDTH * 0.09 }]}>
          And there was one{'\n'}singlish word you guys{'\n'}used again, and again,{'\n'}and again...
        </Text>
        <Animated.Text style={[styles.mostUsedWord, { fontSize: SCREEN_WIDTH * 0.28, transform: [{ scale: pulseAnim }] }]}>
          {capitalize(word)}
        </Animated.Text>
      </View>
    </View>
  );
}

// ============================================================================
// SLIDE 5: FINAL - Black with cyan/pink spiraling squares
// ============================================================================
function FinalSlide({ isActive }: { isActive: boolean }) {
  const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = useDimensions();
  const squareAnims = useRef([0, 1, 2, 3].map(() => new Animated.Value(0))).current;
  const textAnims = useRef([0, 1, 2].map(() => new Animated.Value(0))).current;

  useEffect(() => {
    if (isActive) {
      squareAnims.forEach(a => a.setValue(0));
      textAnims.forEach(a => a.setValue(0));
      
      squareAnims.forEach((anim, index) => {
        Animated.timing(anim, {
          toValue: 1,
          duration: 1200,
          delay: index * 100,
          easing: Easing.out(Easing.cubic),
          useNativeDriver: true,
        }).start();
      });

      textAnims.forEach((anim, index) => {
        Animated.timing(anim, {
          toValue: 1,
          duration: 800,
          delay: 300 + index * 300,
          easing: Easing.out(Easing.cubic),
          useNativeDriver: true,
        }).start();
      });
    }
  }, [isActive]);

  const getSquareStyle = (index: number, isTopLeft: boolean) => {
    const anim = squareAnims[index] || new Animated.Value(1);
    const rotation = isTopLeft ? index * 5 : -index * 5;
    const opacityValues = [0.8, 0.7, 0.6, 0.5];
    
    return {
      transform: [
        { translateX: anim.interpolate({ inputRange: [0, 1], outputRange: [isTopLeft ? -100 : 100, 0] }) },
        { translateY: anim.interpolate({ inputRange: [0, 1], outputRange: [isTopLeft ? -100 : 100, 0] }) },
        { rotate: `${rotation}deg` },
        { scale: anim.interpolate({ inputRange: [0, 1], outputRange: [0.5, 1] }) },
      ],
      opacity: anim.interpolate({ inputRange: [0, 1], outputRange: [0, opacityValues[index] || 0.5] }),
    };
  };

  const squareBaseSize = SCREEN_WIDTH * 0.85;

  return (
    <View style={[styles.slide, { backgroundColor: '#000000' }]}>
      {/* Top-left cyan squares */}
      {[0, 1, 2, 3].map((i) => (
        <Animated.View
          key={`tl-${i}`}
          style={[
            styles.finalSquare,
            {
              top: -squareBaseSize * 0.15 + i * (squareBaseSize * 0.06),
              left: -squareBaseSize * 0.15 + i * (squareBaseSize * 0.06),
              width: squareBaseSize - i * (squareBaseSize * 0.12),
              height: squareBaseSize - i * (squareBaseSize * 0.12),
            },
            getSquareStyle(i, true),
          ]}
        >
          <LinearGradient
            colors={['#22D3EE', '#3B82F6']}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
            style={StyleSheet.absoluteFillObject}
          />
        </Animated.View>
      ))}

      {/* Bottom-right pink squares */}
      {[0, 1, 2, 3].map((i) => (
        <Animated.View
          key={`br-${i}`}
          style={[
            styles.finalSquare,
            {
              bottom: -squareBaseSize * 0.15 + i * (squareBaseSize * 0.06),
              right: -squareBaseSize * 0.15 + i * (squareBaseSize * 0.06),
              width: squareBaseSize - i * (squareBaseSize * 0.12),
              height: squareBaseSize - i * (squareBaseSize * 0.12),
            },
            getSquareStyle(i, false),
          ]}
        >
          <LinearGradient
            colors={['#EC4899', '#F472B6']}
            start={{ x: 1, y: 1 }}
            end={{ x: 0, y: 0 }}
            style={StyleSheet.absoluteFillObject}
          />
        </Animated.View>
      ))}

      <View style={styles.centeredContent}>
        <Animated.Text
          style={[
            styles.finalYour,
            {
              fontSize: SCREEN_WIDTH * 0.15,
              opacity: textAnims[0],
              transform: [{ translateY: textAnims[0].interpolate({ inputRange: [0, 1], outputRange: [20, 0] }) }],
            },
          ]}
        >
          Your
        </Animated.Text>
        <Animated.Text
          style={[
            styles.finalYapSession,
            {
              fontSize: SCREEN_WIDTH * 0.16,
              opacity: textAnims[1],
              transform: [{ translateY: textAnims[1].interpolate({ inputRange: [0, 1], outputRange: [20, 0] }) }],
            },
          ]}
        >
          Yap Session
        </Animated.Text>
        <Animated.Text
          style={[
            styles.finalWrapped,
            {
              fontSize: SCREEN_WIDTH * 0.13,
              opacity: textAnims[2],
              transform: [{ translateY: textAnims[2].interpolate({ inputRange: [0, 1], outputRange: [20, 0] }) }],
            },
          ]}
        >
          Wrapped
        </Animated.Text>
      </View>
    </View>
  );
}

// ============================================================================
// SLIDE 6+: SPEAKER WRAPPED - Individual speaker statistics
// ============================================================================
interface SpeakerWrappedSlideProps {
  speaker: SpeakerData;
  allSpeakers: SpeakerData[];
  currentSpeakerIndex: number;
  onSpeakerChange: (index: number) => void;
  isActive: boolean;
}

function SpeakerWrappedSlide({ speaker, allSpeakers, currentSpeakerIndex, onSpeakerChange, isActive }: SpeakerWrappedSlideProps) {
  const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = useDimensions();
  const [isMuted, setIsMuted] = useState(false);
  const [showSpeakerMenu, setShowSpeakerMenu] = useState(false);
  const soundRef = useRef<Audio.Sound | null>(null);
  
  // Animations
  const cornerTLAnim = useRef(new Animated.Value(0)).current;
  const cornerTRAnim = useRef(new Animated.Value(0)).current;
  const cornerBLAnim = useRef(new Animated.Value(0)).current;
  const cornerBRAnim = useRef(new Animated.Value(0)).current;
  const titleAnim = useRef(new Animated.Value(0)).current;
  const wordAnim = useRef(new Animated.Value(0)).current;
  const listAnims = useRef(speaker.topWords.slice(0, 5).map(() => new Animated.Value(0))).current;

  // Auto-play audio on LOOP when slide becomes active
  useEffect(() => {
    const playAudio = async () => {
      console.log('=== Speaker Audio Debug ===');
      console.log('isActive:', isActive);
      console.log('audioClipUrl:', speaker.audioClipUrl);
      console.log('isMuted:', isMuted);
      
      if (isActive) {
        try {
          // Set up audio mode for playback
          await Audio.setAudioModeAsync({
            playsInSilentModeIOS: true,
            staysActiveInBackground: false,
            shouldDuckAndroid: true,
          });
          
          // Unload previous sound if any
          if (soundRef.current) {
            await soundRef.current.unloadAsync();
            soundRef.current = null;
          }
          
          if (speaker.audioClipUrl) {
            console.log('Attempting to play audio from:', speaker.audioClipUrl);
            
            const { sound } = await Audio.Sound.createAsync(
              { uri: speaker.audioClipUrl },
              { 
                shouldPlay: true, 
                volume: isMuted ? 0 : 1.0,
                isLooping: true,  // 🔁 LOOP THAT MF
              }
            );
            soundRef.current = sound;
            
            // Listen for playback status
            sound.setOnPlaybackStatusUpdate((status) => {
              if (status.isLoaded) {
                console.log('Audio playing:', status.isPlaying, 'looping:', status.isLooping);
              }
            });
          } else {
            console.log('No audio URL available for this speaker');
          }
        } catch (error) {
          console.log('Audio playback error:', error);
        }
      }
    };
    
    playAudio();
    
    // Cleanup on unmount or when slide becomes inactive
    return () => {
      if (soundRef.current) {
        soundRef.current.unloadAsync();
        soundRef.current = null;
      }
    };
  }, [isActive, speaker.audioClipUrl]);

  // Handle mute toggle - update volume on existing looping audio
  useEffect(() => {
    const updateVolume = async () => {
      if (soundRef.current) {
        try {
          await soundRef.current.setVolumeAsync(isMuted ? 0 : 1);
          console.log('Volume updated:', isMuted ? 'MUTED' : 'UNMUTED');
        } catch (error) {
          console.log('Error updating volume:', error);
        }
      }
    };
    updateVolume();
  }, [isMuted]);

  useEffect(() => {
    if (isActive) {
      // Reset animations
      cornerTLAnim.setValue(0);
      cornerTRAnim.setValue(0);
      cornerBLAnim.setValue(0);
      cornerBRAnim.setValue(0);
      titleAnim.setValue(0);
      wordAnim.setValue(0);
      listAnims.forEach(a => a.setValue(0));

      // Corner animations
      Animated.stagger(100, [
        Animated.timing(cornerTLAnim, {
          toValue: 1,
          duration: 800,
          easing: Easing.out(Easing.cubic),
          useNativeDriver: true,
        }),
        Animated.timing(cornerTRAnim, {
          toValue: 1,
          duration: 800,
          easing: Easing.out(Easing.cubic),
          useNativeDriver: true,
        }),
        Animated.timing(cornerBLAnim, {
          toValue: 1,
          duration: 800,
          easing: Easing.out(Easing.cubic),
          useNativeDriver: true,
        }),
        Animated.timing(cornerBRAnim, {
          toValue: 1,
          duration: 800,
          easing: Easing.out(Easing.cubic),
          useNativeDriver: true,
        }),
      ]).start();

      // Title animation
      Animated.timing(titleAnim, {
        toValue: 1,
        duration: 600,
        delay: 200,
        easing: Easing.out(Easing.cubic),
        useNativeDriver: true,
      }).start();

      // Word pop animation
      Animated.spring(wordAnim, {
        toValue: 1,
        delay: 300,
        friction: 4,
        tension: 50,
        useNativeDriver: true,
      }).start();

      // List items animation
      listAnims.forEach((anim, index) => {
        Animated.timing(anim, {
          toValue: 1,
          duration: 500,
          delay: 400 + index * 100,
          easing: Easing.out(Easing.cubic),
          useNativeDriver: true,
        }).start();
      });
    }
  }, [isActive]);

  const cornerTLStyle = {
    transform: [
      { translateX: cornerTLAnim.interpolate({ inputRange: [0, 1], outputRange: [-50, 0] }) },
      { translateY: cornerTLAnim.interpolate({ inputRange: [0, 1], outputRange: [-50, 0] }) },
    ],
    opacity: cornerTLAnim,
  };

  const cornerTRStyle = {
    transform: [
      { translateX: cornerTRAnim.interpolate({ inputRange: [0, 1], outputRange: [50, 0] }) },
      { translateY: cornerTRAnim.interpolate({ inputRange: [0, 1], outputRange: [-50, 0] }) },
    ],
    opacity: cornerTRAnim,
  };

  const cornerBLStyle = {
    transform: [
      { translateX: cornerBLAnim.interpolate({ inputRange: [0, 1], outputRange: [-50, 0] }) },
      { translateY: cornerBLAnim.interpolate({ inputRange: [0, 1], outputRange: [50, 0] }) },
    ],
    opacity: cornerBLAnim,
  };

  const cornerBRStyle = {
    transform: [
      { translateX: cornerBRAnim.interpolate({ inputRange: [0, 1], outputRange: [50, 0] }) },
      { translateY: cornerBRAnim.interpolate({ inputRange: [0, 1], outputRange: [50, 0] }) },
    ],
    opacity: cornerBRAnim,
  };

  const titleStyle = {
    opacity: titleAnim,
    transform: [
      { translateY: titleAnim.interpolate({ inputRange: [0, 1], outputRange: [-20, 0] }) },
    ],
  };

  const wordStyle = {
    opacity: wordAnim,
    transform: [
      { scale: wordAnim.interpolate({ inputRange: [0, 1], outputRange: [0.5, 1] }) },
    ],
  };

  const handleMuteToggle = () => {
    setIsMuted(!isMuted);
  };

  const handleShare = async () => {
    try {
      const result = await Share.share({
        message: `🎤 ${speaker.name}'s Singlish Wrapped!\n\nTop word: ${speaker.mostUsedWord}\n\nTop 5 words:\n${speaker.topWords.slice(0, 5).map((w, i) => `${i + 1}. ${w.word} (${w.count}x)`).join('\n')}\n\n#SinglishWrapped #YapSession`,
        title: `${speaker.name}'s Singlish Wrapped`,
      });
      
      if (result.action === Share.sharedAction) {
        console.log('Shared successfully');
      }
    } catch (error: any) {
      Alert.alert('Share Error', error.message);
    }
  };

  const zigzagSize = SCREEN_WIDTH * 0.35;

  return (
    <View style={[styles.slide, { backgroundColor: '#FFE500' }]}>
      {/* Zigzag Corner Decorations */}
      <Animated.View style={[styles.cornerDecoration, { top: 0, left: 0 }, cornerTLStyle]}>
        <View style={[styles.zigzagCorner, { width: zigzagSize, height: zigzagSize * 1.3 }]}>
          {[0, 1, 2, 3, 4, 5].map((i) => (
            <View key={i} style={[styles.zigzagStep, {
              top: i * (zigzagSize * 0.2),
              left: 0,
              width: zigzagSize * (0.4 - i * 0.05),
              height: zigzagSize * 0.22,
              backgroundColor: i % 2 === 0 ? '#FF1493' : '#FF69B4',
            }]} />
          ))}
        </View>
      </Animated.View>

      <Animated.View style={[styles.cornerDecoration, { top: 0, right: 0 }, cornerTRStyle]}>
        <View style={[styles.zigzagCorner, { width: zigzagSize, height: zigzagSize * 1.3, alignItems: 'flex-end' }]}>
          {[0, 1, 2, 3, 4, 5].map((i) => (
            <View key={i} style={[styles.zigzagStep, {
              top: i * (zigzagSize * 0.2),
              right: 0,
              width: zigzagSize * (0.4 - i * 0.05),
              height: zigzagSize * 0.22,
              backgroundColor: i % 2 === 0 ? '#FF1493' : '#FF69B4',
            }]} />
          ))}
        </View>
      </Animated.View>

      <Animated.View style={[styles.cornerDecoration, { bottom: 0, left: 0 }, cornerBLStyle]}>
        <View style={[styles.zigzagCorner, { width: zigzagSize, height: zigzagSize * 1.3, justifyContent: 'flex-end' }]}>
          {[0, 1, 2, 3, 4, 5].map((i) => (
            <View key={i} style={[styles.zigzagStep, {
              bottom: i * (zigzagSize * 0.2),
              left: 0,
              width: zigzagSize * (0.4 - i * 0.05),
              height: zigzagSize * 0.22,
              backgroundColor: i % 2 === 0 ? '#FF1493' : '#FF69B4',
            }]} />
          ))}
        </View>
      </Animated.View>

      <Animated.View style={[styles.cornerDecoration, { bottom: 0, right: 0 }, cornerBRStyle]}>
        <View style={[styles.zigzagCorner, { width: zigzagSize, height: zigzagSize * 1.3, alignItems: 'flex-end', justifyContent: 'flex-end' }]}>
          {[0, 1, 2, 3, 4, 5].map((i) => (
            <View key={i} style={[styles.zigzagStep, {
              bottom: i * (zigzagSize * 0.2),
              right: 0,
              width: zigzagSize * (0.4 - i * 0.05),
              height: zigzagSize * 0.22,
              backgroundColor: i % 2 === 0 ? '#FF1493' : '#FF69B4',
            }]} />
          ))}
        </View>
      </Animated.View>

      {/* Main Content */}
      <View style={styles.speakerContent}>
        {/* Speaker Title */}
        <Animated.Text style={[styles.speakerTitle, { fontSize: SCREEN_WIDTH * 0.065 }, titleStyle]}>
          {speaker.name}'s Wrapped
        </Animated.Text>

        {/* Most Used Word - Large 3D Style */}
        <Animated.View style={[styles.mostUsedWordContainer, wordStyle]}>
          <Text style={[styles.speakerMostUsedWord, { fontSize: SCREEN_WIDTH * 0.2 }]}>{speaker.mostUsedWord}</Text>
        </Animated.View>

        {/* Word List */}
        <View style={styles.speakerWordList}>
          {speaker.topWords.slice(0, 5).map((item, index) => (
            <Animated.View
              key={index}
              style={[
                styles.speakerWordRow,
                {
                  opacity: listAnims[index] || new Animated.Value(1),
                  transform: [{
                    translateX: (listAnims[index] || new Animated.Value(1)).interpolate({
                      inputRange: [0, 1],
                      outputRange: [-30, 0],
                    }),
                  }],
                },
              ]}
            >
              <View style={styles.speakerWordLeft}>
                <View style={styles.numberCircle}>
                  <Text style={styles.numberText}>{index + 1}</Text>
                </View>
                <Text style={[styles.speakerWordText, { fontSize: SCREEN_WIDTH * 0.065 }]}>{capitalize(item.word)}</Text>
              </View>
              <Text style={[styles.speakerWordCount, { fontSize: SCREEN_WIDTH * 0.065 }]}>{item.count}</Text>
            </Animated.View>
          ))}
        </View>
      </View>

      {/* Bottom Bar */}
      <View style={styles.bottomBar}>
        {/* Mute/Unmute Button */}
        <TouchableOpacity onPress={handleMuteToggle} style={styles.iconButton}>
          <View style={styles.muteButtonContainer}>
            <Ionicons 
              name="volume-high" 
              size={28} 
              color="#000" 
            />
            {isMuted && (
              <View style={styles.muteSlash} />
            )}
          </View>
        </TouchableOpacity>

        {/* Choose Speaker Button */}
        <View>
          <TouchableOpacity
            onPress={() => setShowSpeakerMenu(!showSpeakerMenu)}
            style={styles.chooseSpeakerButton}
          >
            <Text style={styles.chooseSpeakerText}>Choose Your Speaker</Text>
          </TouchableOpacity>

          {/* Speaker Dropdown Menu */}
          {showSpeakerMenu && (
            <View style={styles.speakerMenu}>
              {allSpeakers.map((s, index) => (
                <TouchableOpacity
                  key={s.id}
                  onPress={() => {
                    onSpeakerChange(index);
                    setShowSpeakerMenu(false);
                  }}
                  style={[
                    styles.speakerMenuItem,
                    index === currentSpeakerIndex && styles.speakerMenuItemActive,
                  ]}
                >
                  <Text style={styles.speakerMenuItemText}>{s.name}</Text>
                </TouchableOpacity>
              ))}
            </View>
          )}
        </View>

        {/* Share Icon */}
        <TouchableOpacity onPress={handleShare} style={styles.iconButton}>
          <Ionicons name="share-social" size={28} color="#000" />
        </TouchableOpacity>
      </View>
    </View>
  );
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================
export default function WrappedScreen({ navigation, route }: Props) {
  const { sessionId } = route.params;
  const [currentSlide, setCurrentSlide] = useState(0);
  const [data, setData] = useState<WrappedData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Responsive dimensions - updates automatically on resize!
  const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = useWindowDimensions();

  // Total slides = 5 base slides + number of speakers
  const totalSlides = data ? 5 + data.speakers.length : 5;

  useEffect(() => {
    const fetchSessionData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const session = await api.sessions.getStatus(sessionId);
        console.log('=== DEBUG: Session Status ===');
        console.log(JSON.stringify(session, null, 2));
        
        const speakersResponse = await api.sessions.getSpeakers(sessionId);
        console.log('=== DEBUG: Speakers Response ===');
        console.log(JSON.stringify(speakersResponse, null, 2));
        
        const speakers = speakersResponse.speakers || [];
        const speakerCount = speakers.length;
        
        const allWordCounts: { [key: string]: number } = {};
        let totalWords = 0;
        
        // Process individual speaker data
        console.log('=== Processing Speakers ===');
        const speakerDataList: SpeakerData[] = speakers.map((speaker: any, index: number) => {
          console.log(`Speaker ${index + 1} raw data:`, JSON.stringify(speaker, null, 2));
          
          const speakerWordCounts: { [key: string]: number } = {};
          
          speaker.word_counts?.forEach((wc: any) => {
            speakerWordCounts[wc.word] = (speakerWordCounts[wc.word] || 0) + wc.count;
            allWordCounts[wc.word] = (allWordCounts[wc.word] || 0) + wc.count;
            totalWords += wc.count;
          });
          
          const speakerTopWords = Object.entries(speakerWordCounts)
            .map(([word, count]) => ({ word, count }))
            .sort((a, b) => b.count - a.count)
            .slice(0, 5);
          
          const speakerData = {
            id: speaker.id || `speaker-${index + 1}`,
            name: speaker.name || speaker.speaker_label || `Speaker ${index + 1}`,
            topWords: speakerTopWords,
            mostUsedWord: speakerTopWords.length > 0 ? speakerTopWords[0].word.toUpperCase() : 'N/A',
            audioClipUrl: speaker.sample_audio_url,
          };
          
          console.log(`Speaker ${index + 1} processed:`, speakerData);
          return speakerData;
        });
        
        const topWords = Object.entries(allWordCounts)
          .map(([word, count]) => ({ word, count }))
          .sort((a, b) => b.count - a.count)
          .slice(0, 5);
        
        setData({
          speakerCount,
          duration: session.duration_seconds || 0,
          topWords,
          mostUsedWord: topWords.length > 0 ? topWords[0].word : 'N/A',
          totalWords,
          singlishWordsCount: totalWords,
          speakers: speakerDataList,
        });
      } catch (err: any) {
        console.error('Error fetching session data:', err);
        setError(err.message || 'Failed to load session data');
      } finally {
        setLoading(false);
      }
    };
    fetchSessionData();
  }, [sessionId]);

  const handleTap = (event: any) => {
    const x = event.nativeEvent.locationX;
    
    if (x < SCREEN_WIDTH / 2) {
      // Left side - go back
      if (currentSlide > 0) {
        setCurrentSlide(currentSlide - 1);
      } else {
        // Loop to last slide
        setCurrentSlide(totalSlides - 1);
      }
    } else {
      // Right side - go forward
      if (currentSlide < totalSlides - 1) {
        setCurrentSlide(currentSlide + 1);
      } else {
        // Loop back to start
        setCurrentSlide(0);
      }
    }
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <LinearGradient colors={['#C45C5C', '#8B3A3A']} style={StyleSheet.absoluteFillObject} />
        <ActivityIndicator size="large" color="#fff" />
        <Text style={styles.loadingText}>Loading your Wrapped...</Text>
      </View>
    );
  }

  if (error || !data) {
    return (
      <View style={styles.loadingContainer}>
        <LinearGradient colors={['#1a1a1a', '#000']} style={StyleSheet.absoluteFillObject} />
        <Ionicons name="alert-circle-outline" size={64} color="#ff6b6b" />
        <Text style={styles.errorTitle}>Oops!</Text>
        <Text style={styles.errorText}>{error || 'No session data available'}</Text>
        <TouchableOpacity style={styles.errorButton} onPress={() => navigation.goBack()}>
          <Text style={styles.errorButtonText}>Go Back</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const renderCurrentSlide = () => {
    switch (currentSlide) {
      case 0: return <SpeakersSlide count={data.speakerCount} isActive={currentSlide === 0} />;
      case 1: return <DurationSlide seconds={data.duration} isActive={currentSlide === 1} />;
      case 2: return <TopWordsSlide words={data.topWords} isActive={currentSlide === 2} />;
      case 3: return <MostUsedWordSlide word={data.mostUsedWord} isActive={currentSlide === 3} />;
      case 4: return <FinalSlide isActive={currentSlide === 4} />;
      default: {
        // Speaker slides (index 5 onwards)
        const speakerIndex = currentSlide - 5;
        if (speakerIndex >= 0 && speakerIndex < data.speakers.length) {
          return (
            <SpeakerWrappedSlide
              speaker={data.speakers[speakerIndex]}
              allSpeakers={data.speakers}
              currentSpeakerIndex={speakerIndex}
              onSpeakerChange={(newIndex) => setCurrentSlide(5 + newIndex)}
              isActive={true}
            />
          );
        }
        return null;
      }
    }
  };

  // Constrain dimensions for phone-like aspect ratio on wide screens
  const MAX_WIDTH = 500;
  const constrainedWidth = Math.min(SCREEN_WIDTH, MAX_WIDTH);
  const constrainedHeight = SCREEN_WIDTH > MAX_WIDTH ? Math.min(SCREEN_HEIGHT, MAX_WIDTH * 1.8) : SCREEN_HEIGHT;

  return (
    <View style={[styles.outerContainer, { width: SCREEN_WIDTH, height: SCREEN_HEIGHT }]}>
      <DimensionsContext.Provider value={{ width: constrainedWidth, height: constrainedHeight }}>
        <TouchableWithoutFeedback onPress={handleTap}>
          <View style={[styles.container, { 
            width: constrainedWidth, 
            height: constrainedHeight, 
            maxWidth: MAX_WIDTH,
            borderRadius: SCREEN_WIDTH > MAX_WIDTH ? 16 : 0,
          }]}>
            {/* Progress bars */}
            <View style={styles.progressContainer}>
              {Array.from({ length: totalSlides }).map((_, index) => (
                <View key={index} style={[styles.progressBar, index <= currentSlide && styles.progressBarActive]} />
              ))}
            </View>

            {/* Close button */}
            <TouchableOpacity 
              style={styles.closeButton} 
              onPress={() => navigation.goBack()}
              hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
            >
              <Ionicons name="close" size={28} color="#fff" />
            </TouchableOpacity>

            {renderCurrentSlide()}
          </View>
        </TouchableWithoutFeedback>
      </DimensionsContext.Provider>
    </View>
  );
}

const styles = StyleSheet.create({
  outerContainer: {
    flex: 1,
    backgroundColor: '#000',
    justifyContent: 'center',
    alignItems: 'center',
  },
  container: {
    flex: 1,
    backgroundColor: '#000',
    overflow: 'hidden',
    borderRadius: 0,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    fontSize: 18,
    color: '#fff',
    marginTop: 20,
    fontWeight: '600',
  },
  errorTitle: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#fff',
    marginTop: 20,
  },
  errorText: {
    fontSize: 16,
    color: '#aaa',
    marginTop: 10,
    textAlign: 'center',
    paddingHorizontal: 40,
  },
  errorButton: {
    marginTop: 30,
    backgroundColor: '#fff',
    paddingHorizontal: 32,
    paddingVertical: 14,
    borderRadius: 25,
  },
  errorButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000',
  },
  progressContainer: {
    position: 'absolute',
    top: 50,
    left: 16,
    right: 16,
    flexDirection: 'row',
    gap: 4,
    zIndex: 100,
  },
  progressBar: {
    flex: 1,
    height: 3,
    backgroundColor: 'rgba(255,255,255,0.3)',
    borderRadius: 2,
  },
  progressBarActive: {
    backgroundColor: '#fff',
  },
  closeButton: {
    position: 'absolute',
    top: 44,
    right: 16,
    zIndex: 100,
    width: 44,
    height: 44,
    justifyContent: 'center',
    alignItems: 'center',
  },
  slide: {
    flex: 1,
    width: '100%',
    height: '100%',
    overflow: 'hidden',
  },
  centeredContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 32,
    zIndex: 10,
    maxWidth: 500,
    alignSelf: 'center',
    width: '100%',
  },

  // Angular shapes for slide 1
  angularShape: {
    position: 'absolute',
  },

  // Speakers Slide
  speakersText: {
    fontSize: 46, // Overridden by inline style
    fontWeight: '900',
    color: '#000',
    textAlign: 'center',
    lineHeight: 56, // Overridden by inline style
  },
  boldBlack: {
    fontWeight: '900',
    color: '#000',
  },

  // Duration Slide
  arc: {
    position: 'absolute',
  },
  durationTitle: {
    fontSize: 36, // Overridden by inline style
    fontWeight: '900',
    color: '#000',
    textAlign: 'center',
    marginBottom: 16,
  },
  durationNumber: {
    fontSize: 128, // Overridden by inline style
    fontWeight: '900',
    color: '#000',
    textAlign: 'center',
    lineHeight: 140, // Overridden by inline style
  },
  durationUnit: {
    fontSize: 40, // Overridden by inline style
    fontWeight: '900',
    color: '#000',
    textAlign: 'center',
  },
  durationSubtitle: {
    fontSize: 22, // Overridden by inline style
    fontWeight: '700',
    color: 'rgba(0,0,0,0.7)',
    textAlign: 'center',
    marginTop: 24,
  },

  // Top Words Slide
  diagonalContainer: {
    position: 'absolute',
    top: 0,
    right: 0,
    width: '100%',
    height: '35%',
    overflow: 'hidden',
  },
  diagonalShape: {
    width: '150%',
    height: '100%',
    backgroundColor: 'rgba(96, 165, 250, 0.3)',
    transform: [{ rotate: '-15deg' }, { translateX: -50 }, { translateY: -100 }],
  },
  topWordsContent: {
    flex: 1,
    justifyContent: 'center',
    paddingHorizontal: 40,
    paddingTop: 60,
    zIndex: 10,
  },
  topWordsTitle: {
    fontSize: 38, // Overridden by inline style
    fontWeight: '900',
    fontStyle: 'italic',
    color: '#fff',
    marginBottom: 32,
  },
  wordsList: {
    width: '100%',
  },
  wordRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  wordRank: {
    fontSize: 60, // Overridden by inline style
    fontWeight: '900',
    color: '#fff',
    width: 88, // Overridden by inline style
  },
  wordText: {
    fontSize: 44, // Overridden by inline style
    fontWeight: '700',
    color: '#fff',
  },

  // Most Used Word Slide
  triangle: {
    position: 'absolute',
    width: 0,
    height: 0,
    borderBottomColor: 'transparent',
    borderRightWidth: 0,
    borderRightColor: 'transparent',
  },
  mostUsedTitle: {
    fontSize: 26, // Overridden by inline style
    fontWeight: '900',
    fontStyle: 'italic',
    color: '#fff',
    textAlign: 'center',
    marginBottom: 40,
    lineHeight: 36, // Overridden by inline style
  },
  mostUsedWord: {
    fontSize: 112, // Overridden by inline style
    fontWeight: '900',
    color: '#fff',
    textAlign: 'center',
  },

  // Final Slide
  finalSquare: {
    position: 'absolute',
    overflow: 'hidden',
  },
  finalYour: {
    fontSize: 60, // Overridden by inline style
    fontWeight: '900',
    color: '#fff',
    textAlign: 'center',
  },
  finalYapSession: {
    fontSize: 64, // Overridden by inline style
    fontWeight: '900',
    color: '#fff',
    textAlign: 'center',
  },
  finalWrapped: {
    fontSize: 52, // Overridden by inline style
    fontWeight: '300',
    color: '#fff',
    textAlign: 'center',
  },

  // Speaker Wrapped Slide
  cornerDecoration: {
    position: 'absolute',
    zIndex: 1,
  },
  zigzagCorner: {
    position: 'relative',
  },
  zigzagStep: {
    position: 'absolute',
  },
  speakerContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 32,
    paddingTop: 80,
    maxWidth: 500,
    alignSelf: 'center',
    width: '100%',
    zIndex: 10,
  },
  speakerTitle: {
    fontSize: 26, // Overridden by inline style
    fontWeight: '700',
    color: '#000',
    marginBottom: 16,
    textAlign: 'center',
  },
  mostUsedWordContainer: {
    marginBottom: 32,
  },
  speakerMostUsedWord: {
    fontSize: 80, // Overridden by inline style
    fontWeight: '900',
    color: '#FF5A5F',
    textAlign: 'center',
    textShadowColor: '#D44548',
    textShadowOffset: { width: 4, height: 4 },
    textShadowRadius: 0,
  },
  speakerWordList: {
    width: '100%',
    maxWidth: 320,
  },
  speakerWordRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  speakerWordLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  numberCircle: {
    width: 36,
    height: 36,
    borderRadius: 18,
    borderWidth: 3,
    borderColor: '#FF5A5F',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  numberText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#FF5A5F',
  },
  speakerWordText: {
    fontSize: 26, // Overridden by inline style
    fontWeight: '700',
    color: '#000',
  },
  speakerWordCount: {
    fontSize: 26, // Overridden by inline style
    fontWeight: '700',
    color: '#000',
  },
  bottomBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 24,
    paddingBottom: 40,
    paddingTop: 16,
    zIndex: 20,
  },
  iconButton: {
    padding: 12,
    borderRadius: 24,
  },
  muteButtonContainer: {
    position: 'relative',
    width: 28,
    height: 28,
    justifyContent: 'center',
    alignItems: 'center',
  },
  muteSlash: {
    position: 'absolute',
    width: 36,
    height: 4,
    backgroundColor: '#FF0000',
    borderRadius: 2,
    transform: [{ rotate: '-45deg' }],
  },
  chooseSpeakerButton: {
    backgroundColor: '#fff',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 24,
    borderWidth: 2,
    borderColor: '#000',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 4,
    elevation: 3,
  },
  chooseSpeakerText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#000',
    fontStyle: 'italic',
  },
  speakerMenu: {
    position: 'absolute',
    bottom: '100%',
    left: '50%',
    transform: [{ translateX: -75 }],
    marginBottom: 8,
    backgroundColor: '#fff',
    borderRadius: 12,
    borderWidth: 2,
    borderColor: '#000',
    overflow: 'hidden',
    minWidth: 150,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
    elevation: 5,
  },
  speakerMenuItem: {
    paddingHorizontal: 20,
    paddingVertical: 14,
  },
  speakerMenuItemActive: {
    backgroundColor: '#FFE500',
  },
  speakerMenuItemText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#000',
  },
});
