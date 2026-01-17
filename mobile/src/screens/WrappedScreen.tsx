import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableWithoutFeedback,
  TouchableOpacity,
  Dimensions,
  ActivityIndicator,
  Animated,
  Easing,
} from 'react-native';
import { StackNavigationProp } from '@react-navigation/stack';
import { RouteProp } from '@react-navigation/native';
import { RecordStackParamList } from '../navigation/MainNavigator';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { api } from '../api/client';

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');

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

interface WrappedData {
  speakerCount: number;
  duration: number;
  topWords: TopWord[];
  mostUsedWord: string;
  totalWords: number;
  singlishWordsCount: number;
}

const numberToWord = (num: number): string => {
  const words = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten'];
  return num <= 10 ? words[num] : num.toString();
};

// ============================================================================
// SLIDE 1: SPEAKERS
// ============================================================================
function SpeakersSlide({ count, isActive }: { count: number; isActive: boolean }) {
  const shape1Anim = useRef(new Animated.Value(0)).current;
  const shape2Anim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (isActive) {
      // Reset and play animations
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
      {
        translateX: shape1Anim.interpolate({
          inputRange: [0, 1],
          outputRange: [150, 0],
        }),
      },
      {
        translateY: shape1Anim.interpolate({
          inputRange: [0, 1],
          outputRange: [-150, 0],
        }),
      },
      {
        scale: shape1Anim.interpolate({
          inputRange: [0, 1],
          outputRange: [0.5, 1],
        }),
      },
    ],
    opacity: shape1Anim,
  };

  const shape2Style = {
    transform: [
      {
        translateX: shape2Anim.interpolate({
          inputRange: [0, 1],
          outputRange: [-150, 0],
        }),
      },
      {
        translateY: shape2Anim.interpolate({
          inputRange: [0, 1],
          outputRange: [150, 0],
        }),
      },
      {
        scale: shape2Anim.interpolate({
          inputRange: [0, 1],
          outputRange: [0.5, 1],
        }),
      },
    ],
    opacity: shape2Anim,
  };

  return (
    <View style={styles.slide}>
      <LinearGradient
        colors={['#22D3EE', '#F9A8D4', '#EC4899']}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={StyleSheet.absoluteFillObject}
      />
      
      {/* Top Right Stepped Shapes */}
      <Animated.View style={[styles.shapeContainer, styles.topRightShape, shape1Style]}>
        <View style={[styles.steppedShape, { backgroundColor: 'rgba(236, 72, 153, 0.5)', width: 300, height: 250 }]} />
        <View style={[styles.steppedShape, { backgroundColor: 'rgba(236, 72, 153, 0.7)', width: 260, height: 210, top: 30, right: 30 }]} />
        <View style={[styles.steppedShape, { backgroundColor: 'rgba(236, 72, 153, 0.9)', width: 220, height: 170, top: 60, right: 60 }]} />
      </Animated.View>
      
      {/* Bottom Left Stepped Shapes */}
      <Animated.View style={[styles.shapeContainer, styles.bottomLeftShape, shape2Style]}>
        <View style={[styles.steppedShape, { backgroundColor: 'rgba(239, 68, 68, 0.5)', width: 300, height: 250 }]} />
        <View style={[styles.steppedShape, { backgroundColor: 'rgba(239, 68, 68, 0.7)', width: 260, height: 210, bottom: 30, left: 30 }]} />
        <View style={[styles.steppedShape, { backgroundColor: 'rgba(239, 68, 68, 0.9)', width: 220, height: 170, bottom: 60, left: 60 }]} />
      </Animated.View>

      <View style={styles.centeredContent}>
        <Text style={styles.speakersText}>
          You had{' '}
          <Text style={styles.boldBlack}>{numberToWord(count)}</Text>
          {' '}speakers this yap session
        </Text>
      </View>
    </View>
  );
}

// ============================================================================
// SLIDE 2: DURATION
// ============================================================================
function DurationSlide({ seconds, isActive }: { seconds: number; isActive: boolean }) {
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
      {
        translateX: arcAnim.interpolate({
          inputRange: [0, 1],
          outputRange: [-100, 0],
        }),
      },
      {
        translateY: arcAnim.interpolate({
          inputRange: [0, 1],
          outputRange: [-100, 0],
        }),
      },
      {
        scale: arcAnim.interpolate({
          inputRange: [0, 1],
          outputRange: [0.3, 1],
        }),
      },
    ],
    opacity: arcAnim,
  };

  return (
    <View style={[styles.slide, { backgroundColor: '#FDE047' }]}>
      {/* Arc decoration */}
      <Animated.View style={[styles.arcContainer, arcStyle]}>
        <View style={[styles.arc, { backgroundColor: 'rgba(96, 165, 250, 0.6)', width: 400, height: 400 }]} />
        <View style={[styles.arc, { backgroundColor: 'rgba(167, 139, 250, 0.5)', width: 320, height: 320, top: 40, left: 40 }]} />
        <View style={[styles.arc, { backgroundColor: 'rgba(196, 181, 253, 0.4)', width: 240, height: 240, top: 80, left: 80 }]} />
      </Animated.View>

      <View style={styles.centeredContent}>
        <Text style={styles.durationTitle}>You guys yapped for a total of</Text>
        <Text style={styles.durationNumber}>{seconds}</Text>
        <Text style={styles.durationUnit}>seconds</Text>
        <Text style={styles.durationSubtitle}>Drop it like it's hot</Text>
      </View>
    </View>
  );
}

// ============================================================================
// SLIDE 3: TOP WORDS
// ============================================================================
function TopWordsSlide({ words, isActive }: { words: TopWord[]; isActive: boolean }) {
  const fadeAnims = useRef(words.slice(0, 5).map(() => new Animated.Value(0))).current;

  useEffect(() => {
    if (isActive) {
      // Reset all animations
      fadeAnims.forEach(anim => anim.setValue(0));
      
      const animations = fadeAnims.map((anim, index) =>
        Animated.timing(anim, {
          toValue: 1,
          duration: 600,
          delay: index * 150,
          easing: Easing.out(Easing.cubic),
          useNativeDriver: true,
        })
      );
      Animated.parallel(animations).start();
    }
  }, [isActive]);

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
      <View style={styles.diagonalShape} />

      <View style={[styles.centeredContent, { alignItems: 'flex-start', paddingHorizontal: 40 }]}>
        <Text style={styles.topWordsTitle}>Your group's favorite Singlish words</Text>
        <View style={styles.wordsList}>
          {words.slice(0, 5).map((item, index) => (
            <Animated.View
              key={index}
              style={[
                styles.wordRow,
                {
                  opacity: fadeAnims[index] || new Animated.Value(1),
                  transform: [
                    {
                      translateY: (fadeAnims[index] || new Animated.Value(1)).interpolate({
                        inputRange: [0, 1],
                        outputRange: [20, 0],
                      }),
                    },
                  ],
                },
              ]}
            >
              <Text style={styles.wordRank}>{index + 1}</Text>
              <Text style={styles.wordText}>{item.word}</Text>
            </Animated.View>
          ))}
        </View>
      </View>
    </View>
  );
}

// ============================================================================
// SLIDE 4: MOST USED WORD
// ============================================================================
function MostUsedWordSlide({ word, isActive }: { word: string; isActive: boolean }) {
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const triangleAnim = useRef(new Animated.Value(0)).current;
  const pulseLoop = useRef<Animated.CompositeAnimation | null>(null);

  useEffect(() => {
    if (isActive) {
      triangleAnim.setValue(0);
      pulseAnim.setValue(1);
      
      // Triangle animation
      Animated.timing(triangleAnim, {
        toValue: 1,
        duration: 1500,
        easing: Easing.out(Easing.cubic),
        useNativeDriver: true,
      }).start();

      // Pulse animation
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
    
    return () => {
      pulseLoop.current?.stop();
    };
  }, [isActive]);

  const triangleStyle = {
    transform: [
      {
        translateX: triangleAnim.interpolate({
          inputRange: [0, 1],
          outputRange: [-150, 0],
        }),
      },
      {
        translateY: triangleAnim.interpolate({
          inputRange: [0, 1],
          outputRange: [-150, 0],
        }),
      },
      {
        scale: triangleAnim.interpolate({
          inputRange: [0, 1],
          outputRange: [0.5, 1],
        }),
      },
    ],
    opacity: triangleAnim,
  };

  return (
    <View style={[styles.slide, { backgroundColor: '#000000' }]}>
      {/* Green triangle layers */}
      <Animated.View style={[styles.triangleContainer, triangleStyle]}>
        <View style={[styles.triangle, { borderLeftWidth: 300, borderBottomWidth: 300, borderLeftColor: 'rgba(34, 197, 94, 0.9)' }]} />
        <View style={[styles.triangle, { borderLeftWidth: 250, borderBottomWidth: 250, borderLeftColor: 'rgba(34, 197, 94, 0.7)', top: 25, left: 25 }]} />
        <View style={[styles.triangle, { borderLeftWidth: 200, borderBottomWidth: 200, borderLeftColor: 'rgba(34, 197, 94, 0.5)', top: 50, left: 50 }]} />
      </Animated.View>

      <View style={styles.centeredContent}>
        <Text style={styles.mostUsedTitle}>
          And there was one singlish word you guys used again, and again, and again...
        </Text>
        <Animated.Text style={[styles.mostUsedWord, { transform: [{ scale: pulseAnim }] }]}>
          {word}
        </Animated.Text>
      </View>
    </View>
  );
}

// ============================================================================
// SLIDE 5: FINAL
// ============================================================================
function FinalSlide({ isActive }: { isActive: boolean }) {
  const squareAnims = useRef([0, 1, 2, 3, 4, 5].map(() => new Animated.Value(0))).current;
  const textAnims = useRef([0, 1, 2].map(() => new Animated.Value(0))).current;

  useEffect(() => {
    if (isActive) {
      // Reset all
      squareAnims.forEach(a => a.setValue(0));
      textAnims.forEach(a => a.setValue(0));
      
      // Square animations
      squareAnims.forEach((anim, index) => {
        Animated.timing(anim, {
          toValue: 1,
          duration: 1200,
          delay: index * 100,
          easing: Easing.out(Easing.cubic),
          useNativeDriver: true,
        }).start();
      });

      // Text animations
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
    
    return {
      transform: [
        {
          translateX: anim.interpolate({
            inputRange: [0, 1],
            outputRange: [isTopLeft ? -100 : 100, 0],
          }),
        },
        {
          translateY: anim.interpolate({
            inputRange: [0, 1],
            outputRange: [isTopLeft ? -100 : 100, 0],
          }),
        },
        { rotate: `${rotation}deg` },
        {
          scale: anim.interpolate({
            inputRange: [0, 1],
            outputRange: [0.5, 1],
          }),
        },
      ],
      opacity: anim.interpolate({
        inputRange: [0, 1],
        outputRange: [0, 0.8 - index * 0.15],
      }),
    };
  };

  return (
    <View style={[styles.slide, { backgroundColor: '#000000' }]}>
      {/* Top-left cyan squares */}
      {[0, 1, 2].map((i) => (
        <Animated.View
          key={`tl-${i}`}
          style={[
            styles.finalSquare,
            {
              top: -60 + i * 25,
              left: -60 + i * 25,
              width: 280 - i * 40,
              height: 280 - i * 40,
              backgroundColor: `rgba(34, 211, 238, ${0.8 - i * 0.2})`,
            },
            getSquareStyle(i, true),
          ]}
        />
      ))}

      {/* Bottom-right pink squares */}
      {[0, 1, 2].map((i) => (
        <Animated.View
          key={`br-${i}`}
          style={[
            styles.finalSquare,
            {
              bottom: -60 + i * 25,
              right: -60 + i * 25,
              width: 280 - i * 40,
              height: 280 - i * 40,
              backgroundColor: `rgba(236, 72, 153, ${0.8 - i * 0.2})`,
            },
            getSquareStyle(i + 3, false),
          ]}
        />
      ))}

      <View style={styles.centeredContent}>
        <Animated.Text
          style={[
            styles.finalYour,
            {
              opacity: textAnims[0],
              transform: [
                {
                  translateY: textAnims[0].interpolate({
                    inputRange: [0, 1],
                    outputRange: [20, 0],
                  }),
                },
              ],
            },
          ]}
        >
          Your
        </Animated.Text>
        <Animated.Text
          style={[
            styles.finalYapSession,
            {
              opacity: textAnims[1],
              transform: [
                {
                  translateY: textAnims[1].interpolate({
                    inputRange: [0, 1],
                    outputRange: [20, 0],
                  }),
                },
              ],
            },
          ]}
        >
          Yap Session
        </Animated.Text>
        <Animated.Text
          style={[
            styles.finalWrapped,
            {
              opacity: textAnims[2],
              transform: [
                {
                  translateY: textAnims[2].interpolate({
                    inputRange: [0, 1],
                    outputRange: [20, 0],
                  }),
                },
              ],
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
// MAIN COMPONENT
// ============================================================================
export default function WrappedScreen({ navigation, route }: Props) {
  const { sessionId } = route.params;
  const [currentSlide, setCurrentSlide] = useState(0);
  const [data, setData] = useState<WrappedData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const totalSlides = 5;

  useEffect(() => {
    const fetchSessionData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Get session status for duration
        const session = await api.sessions.getStatus(sessionId);
        console.log('=== DEBUG: Session Status ===');
        console.log(JSON.stringify(session, null, 2));
        
        // Get speakers (this has word counts for ALL speakers, even unclaimed)
        const speakersResponse = await api.sessions.getSpeakers(sessionId);
        console.log('=== DEBUG: Speakers Response ===');
        console.log(JSON.stringify(speakersResponse, null, 2));
        
        const speakers = speakersResponse.speakers || [];
        const speakerCount = speakers.length;
        
        console.log(`=== DEBUG: Found ${speakerCount} speakers ===`);
        
        // Collect all words from all speakers
        const allWordCounts: { [key: string]: number } = {};
        let totalWords = 0;
        
        speakers.forEach((speaker: any, idx: number) => {
          console.log(`=== DEBUG: Speaker ${idx} (${speaker.speaker_label}) ===`);
          console.log(`  Segment count: ${speaker.segment_count}`);
          console.log(`  Word counts: ${JSON.stringify(speaker.word_counts)}`);
          
          speaker.word_counts?.forEach((wc: any) => {
            allWordCounts[wc.word] = (allWordCounts[wc.word] || 0) + wc.count;
            totalWords += wc.count;
          });
        });
        
        console.log('=== DEBUG: Aggregated Word Counts ===');
        console.log(JSON.stringify(allWordCounts, null, 2));
        console.log(`Total words: ${totalWords}`);
        
        const topWords = Object.entries(allWordCounts)
          .map(([word, count]) => ({ word, count }))
          .sort((a, b) => b.count - a.count)
          .slice(0, 5);
        
        console.log('=== DEBUG: Top 5 Words ===');
        console.log(JSON.stringify(topWords, null, 2));
        
        setData({
          speakerCount,
          duration: session.duration_seconds || 0,
          topWords,
          mostUsedWord: topWords.length > 0 ? topWords[0].word : 'N/A',
          totalWords,
          singlishWordsCount: totalWords, // All words in word_counts are singlish words
        });
      } catch (err: any) {
        console.error('=== DEBUG: Error fetching session data ===');
        console.error(err);
        setError(err.message || 'Failed to load session data');
      } finally {
        setLoading(false);
      }
    };
    fetchSessionData();
  }, [sessionId]);

  const handleTap = (event: any) => {
    const x = event.nativeEvent.locationX;
    
    if (x < SCREEN_WIDTH / 3) {
      // Tap left third - go back
      if (currentSlide > 0) {
        setCurrentSlide(currentSlide - 1);
      }
    } else {
      // Tap right two-thirds - go forward
      if (currentSlide < totalSlides - 1) {
        setCurrentSlide(currentSlide + 1);
      } else {
        // Last slide - close
        navigation.goBack();
      }
    }
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <LinearGradient
          colors={['#C45C5C', '#8B3A3A']}
          style={StyleSheet.absoluteFillObject}
        />
        <ActivityIndicator size="large" color="#fff" />
        <Text style={styles.loadingText}>Loading your Wrapped...</Text>
      </View>
    );
  }

  if (error || !data) {
    return (
      <View style={styles.loadingContainer}>
        <LinearGradient
          colors={['#1a1a1a', '#000']}
          style={StyleSheet.absoluteFillObject}
        />
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
      case 0:
        return <SpeakersSlide count={data.speakerCount} isActive={currentSlide === 0} />;
      case 1:
        return <DurationSlide seconds={data.duration} isActive={currentSlide === 1} />;
      case 2:
        return <TopWordsSlide words={data.topWords} isActive={currentSlide === 2} />;
      case 3:
        return <MostUsedWordSlide word={data.mostUsedWord} isActive={currentSlide === 3} />;
      case 4:
        return <FinalSlide isActive={currentSlide === 4} />;
      default:
        return null;
    }
  };

  return (
    <TouchableWithoutFeedback onPress={handleTap}>
      <View style={styles.container}>
        {/* Progress bars */}
        <View style={styles.progressContainer}>
          {Array.from({ length: totalSlides }).map((_, index) => (
            <View
              key={index}
              style={[
                styles.progressBar,
                index <= currentSlide && styles.progressBarActive,
              ]}
            />
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

        {/* Current Slide */}
        {renderCurrentSlide()}
      </View>
    </TouchableWithoutFeedback>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
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
    top: 60,
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
    top: 55,
    right: 16,
    zIndex: 100,
    width: 44,
    height: 44,
    justifyContent: 'center',
    alignItems: 'center',
  },
  slide: {
    flex: 1,
    width: SCREEN_WIDTH,
    height: SCREEN_HEIGHT,
    overflow: 'hidden',
  },
  centeredContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 32,
    zIndex: 10,
  },

  // Speakers Slide
  speakersText: {
    fontSize: 48,
    fontWeight: '900',
    color: '#000',
    textAlign: 'center',
    lineHeight: 58,
  },
  boldBlack: {
    fontWeight: '900',
    color: '#000',
  },
  shapeContainer: {
    position: 'absolute',
  },
  topRightShape: {
    top: -30,
    right: -30,
  },
  bottomLeftShape: {
    bottom: -30,
    left: -30,
  },
  steppedShape: {
    position: 'absolute',
  },

  // Duration Slide
  arcContainer: {
    position: 'absolute',
    top: -150,
    left: -150,
  },
  arc: {
    position: 'absolute',
    borderBottomRightRadius: 500,
  },
  durationTitle: {
    fontSize: 36,
    fontWeight: '900',
    color: '#000',
    textAlign: 'center',
    marginBottom: 20,
  },
  durationNumber: {
    fontSize: 140,
    fontWeight: '900',
    color: '#000',
    textAlign: 'center',
    lineHeight: 150,
  },
  durationUnit: {
    fontSize: 40,
    fontWeight: '900',
    color: '#000',
    textAlign: 'center',
  },
  durationSubtitle: {
    fontSize: 22,
    fontWeight: '700',
    color: 'rgba(0,0,0,0.7)',
    textAlign: 'center',
    marginTop: 30,
  },

  // Top Words Slide
  diagonalShape: {
    position: 'absolute',
    top: 0,
    right: 0,
    width: SCREEN_WIDTH,
    height: SCREEN_HEIGHT / 3,
    backgroundColor: 'rgba(96, 165, 250, 0.3)',
    transform: [{ skewY: '-10deg' }, { translateY: -100 }],
  },
  topWordsTitle: {
    fontSize: 36,
    fontWeight: '900',
    color: '#fff',
    marginBottom: 40,
  },
  wordsList: {
    width: '100%',
  },
  wordRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  wordRank: {
    fontSize: 60,
    fontWeight: '900',
    color: '#fff',
    width: 80,
  },
  wordText: {
    fontSize: 44,
    fontWeight: '700',
    color: '#fff',
  },

  // Most Used Word Slide
  triangleContainer: {
    position: 'absolute',
    top: 0,
    left: 0,
  },
  triangle: {
    position: 'absolute',
    width: 0,
    height: 0,
    borderBottomColor: 'transparent',
    borderRightWidth: 0,
    borderRightColor: 'transparent',
  },
  mostUsedTitle: {
    fontSize: 28,
    fontWeight: '900',
    color: '#fff',
    textAlign: 'center',
    marginBottom: 50,
    lineHeight: 38,
    maxWidth: 320,
  },
  mostUsedWord: {
    fontSize: 120,
    fontWeight: '900',
    color: '#fff',
    textAlign: 'center',
  },

  // Final Slide
  finalSquare: {
    position: 'absolute',
  },
  finalYour: {
    fontSize: 60,
    fontWeight: '900',
    color: '#fff',
    textAlign: 'center',
  },
  finalYapSession: {
    fontSize: 70,
    fontWeight: '900',
    color: '#fff',
    textAlign: 'center',
  },
  finalWrapped: {
    fontSize: 52,
    fontWeight: '300',
    color: '#fff',
    textAlign: 'center',
  },
});
