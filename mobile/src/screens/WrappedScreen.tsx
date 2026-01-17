import React, { useState, useRef, useCallback, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  TouchableOpacity,
  Image,
  ScrollView,
  Modal,
  Dimensions,
  FlatList,
  ViewToken,
  useWindowDimensions,
  ActivityIndicator,
} from 'react-native';
import { StackNavigationProp } from '@react-navigation/stack';
import { RouteProp } from '@react-navigation/native';
import { RecordStackParamList } from '../navigation/MainNavigator';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { api } from '../api/client';

type WrappedScreenNavigationProp = StackNavigationProp<RecordStackParamList, 'Wrapped'>;
type WrappedScreenRouteProp = RouteProp<RecordStackParamList, 'Wrapped'>;

interface Props {
  navigation: WrappedScreenNavigationProp;
  route: WrappedScreenRouteProp;
}

interface Speaker {
  id: string;
  name: string;
  handle: string;
  totalWords: number;
  topWord: string;
  wordBreakdown: Array<{ word: string; count: number }>;
}

interface WrappedData {
  singlishWordsCount: number;
  totalWords: number;
  sessionDuration: string;
  speakers: Speaker[];
}

export default function WrappedScreen({ navigation, route }: Props) {
  const { sessionId } = route.params;
  const { width: SCREEN_WIDTH } = useWindowDimensions();
  const [currentSlide, setCurrentSlide] = useState(0);
  const [showSpeakerModal, setShowSpeakerModal] = useState(false);
  const flatListRef = useRef<FlatList>(null);
  
  // State for fetching real data
  const [data, setData] = useState<WrappedData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch session results from backend
  useEffect(() => {
    const fetchSessionResults = async () => {
      try {
        console.log(`Fetching results for session: ${sessionId}`);
        setLoading(true);
        
        const results = await api.sessions.getResults(sessionId);
        console.log('Session results:', results);
        
        // Transform backend data to match WrappedData format
        const transformedData: WrappedData = {
          singlishWordsCount: results.total_singlish_words || 0,
          totalWords: results.total_words || 0,
          sessionDuration: formatDuration(results.duration_seconds || 0),
          speakers: results.speakers.map((speaker: any) => ({
            id: speaker.speaker_id,
            name: speaker.name || `Speaker ${speaker.speaker_id}`,
            handle: speaker.username ? `@${speaker.username}` : `@speaker${speaker.speaker_id}`,
            totalWords: speaker.total_words || 0,
            topWord: speaker.top_word?.word || 'N/A',
            wordBreakdown: (speaker.word_counts || []).map((wc: any) => ({
              word: wc.word,
              count: wc.count,
            })),
          })),
        };
        
        setData(transformedData);
        setError(null);
      } catch (err: any) {
        console.error('Error fetching session results:', err);
        setError(err.message || 'Failed to load session results');
      } finally {
        setLoading(false);
      }
    };

    fetchSessionResults();
  }, [sessionId]);

  // Helper function to format duration
  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Loading state
  if (loading) {
    return (
      <LinearGradient
        colors={['#FF6B5A', '#FF8A7A']}
        start={{ x: 0, y: 0 }}
        end={{ x: 0, y: 1 }}
        style={styles.container}
      >
        <SafeAreaView style={styles.safeArea}>
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color="#fff" />
            <Text style={styles.loadingText}>Loading your Wrapped...</Text>
          </View>
        </SafeAreaView>
      </LinearGradient>
    );
  }

  // Error state
  if (error || !data) {
    return (
      <LinearGradient
        colors={['#FF6B5A', '#FF8A7A']}
        start={{ x: 0, y: 0 }}
        end={{ x: 0, y: 1 }}
        style={styles.container}
      >
        <SafeAreaView style={styles.safeArea}>
          <View style={styles.errorContainer}>
            <Text style={styles.errorTitle}>Oops!</Text>
            <Text style={styles.errorMessage}>
              {error || 'Failed to load session results'}
            </Text>
            <TouchableOpacity
              style={styles.retryButton}
              onPress={() => navigation.goBack()}
            >
              <Text style={styles.retryButtonText}>Go Back</Text>
            </TouchableOpacity>
          </View>
        </SafeAreaView>
      </LinearGradient>
    );
  }

  // Data is already loaded, continue with rendering
  const totalSlides = 1 + data.speakers.length; // 1 summary + 1 per speaker
  
  // Create slides array: [summary, speaker1, speaker2, ...]
  const slides = [
    { type: 'summary', data },
    ...data.speakers.map((speaker, index) => ({ 
      type: 'speaker', 
      speaker, 
      index 
    })),
  ];

  const handleClose = () => {
    navigation.goBack();
  };

  const onViewableItemsChanged = useCallback(({ viewableItems }: { viewableItems: ViewToken[] }) => {
    if (viewableItems.length > 0 && viewableItems[0].index !== null) {
      setCurrentSlide(viewableItems[0].index);
    }
  }, []);

  const viewabilityConfig = useRef({
    itemVisiblePercentThreshold: 50,
  }).current;

  const selectSpeaker = (speakerId: string) => {
    const speakerIndex = data.speakers.findIndex((s) => s.id === speakerId);
    if (speakerIndex !== -1) {
      flatListRef.current?.scrollToIndex({ 
        index: speakerIndex + 1, // +1 because summary is at index 0
        animated: true 
      });
    }
    setShowSpeakerModal(false);
  };

  const getSpeakerRank = (speaker: Speaker) => {
    const sorted = [...data.speakers].sort((a, b) => b.totalWords - a.totalWords);
    return sorted.findIndex((s) => s.id === speaker.id) + 1;
  };

  const renderSlide = ({ item, index }: { item: any; index: number }) => {
    if (item.type === 'summary') {
      return (
        <View style={[styles.slideContainer, { width: SCREEN_WIDTH }]}>
          {/* Logo */}
          <View style={styles.logoContainer}>
            <View style={styles.logoCircle}>
              <Image
                source={require('../../assets/images/rabak-logo.jpg')}
                style={styles.logoImage}
                resizeMode="cover"
              />
            </View>
          </View>

          {/* Title */}
          <Text style={styles.title}>Your yap session wrapped</Text>

          {/* Main stat */}
          <View style={styles.mainStatContainer}>
            <Text style={styles.statLabel}>You said</Text>
            <Text style={styles.bigNumber}>{data.singlishWordsCount}</Text>
            <Text style={styles.statSubtitle}>Singlish words</Text>
          </View>

          {/* Additional stats */}
          <View style={styles.additionalStats}>
            <Text style={styles.additionalStatText}>
              That's {data.totalWords} words total
            </Text>
            <Text style={styles.additionalStatText}>
              Session lasted {data.sessionDuration}
            </Text>
          </View>
        </View>
      );
    } else {
      // Speaker slide
      const speaker = item.speaker;
      return (
        <View style={[styles.slideContainer, { width: SCREEN_WIDTH }]}>
          {/* Top controls */}
          <View style={styles.topControls}>
            <TouchableOpacity style={styles.controlButton}>
              <Ionicons name="volume-high" size={24} color="#000000" />
            </TouchableOpacity>

            <View style={styles.rankBadge}>
              <Text style={styles.rankNumber}>{getSpeakerRank(speaker)}</Text>
            </View>

            <TouchableOpacity
              style={styles.speakerButton}
              onPress={() => setShowSpeakerModal(true)}
            >
              <Text style={styles.speakerName}>{speaker.name}</Text>
              <Text style={styles.speakerHandle}>{speaker.handle}</Text>
            </TouchableOpacity>

            <TouchableOpacity style={styles.controlButton}>
              <MaterialCommunityIcons name="share-variant" size={24} color="#000000" />
            </TouchableOpacity>
          </View>

          {/* White card with speaker stats */}
          <View style={styles.statsCard}>
            {/* Top stats */}
            <View style={styles.cardTopStats}>
              <View style={styles.statBox}>
                <Text style={styles.statNumber}>{speaker.totalWords}</Text>
                <Text style={styles.statLabel2}>Total Words</Text>
              </View>
              <View style={styles.statBox}>
                <Text style={styles.statNumber}>{speaker.topWord}</Text>
                <Text style={styles.statLabel2}>Top Word</Text>
              </View>
            </View>

            {/* Word breakdown */}
            <View style={styles.wordBreakdownSection}>
              <Text style={styles.breakdownTitle}>Word Breakdown:</Text>
              <View style={styles.wordGrid}>
                {speaker.wordBreakdown.map((wordItem: any, wordIndex: number) => (
                  <View key={wordIndex} style={styles.wordPill}>
                    <Text style={styles.wordText}>{wordItem.word}</Text>
                    <Text style={styles.wordCount}>{wordItem.count}</Text>
                  </View>
                ))}
              </View>
            </View>
          </View>
        </View>
      );
    }
  };

  return (
    <LinearGradient
      colors={['#FF6B5A', '#FF8A7A']}
      start={{ x: 0, y: 0 }}
      end={{ x: 0, y: 1 }}
      style={styles.container}
    >
      <SafeAreaView style={styles.safeArea}>
        {/* Page indicators */}
        <View style={styles.pageIndicators}>
          {[...Array(totalSlides)].map((_, index) => (
            <View
              key={index}
              style={[
                styles.indicator,
                index === currentSlide && styles.indicatorActive,
              ]}
            />
          ))}
        </View>

        {/* Close button */}
        <TouchableOpacity style={styles.closeButton} onPress={handleClose}>
          <Text style={styles.closeIcon}>✕</Text>
        </TouchableOpacity>

        {/* Slides with horizontal scrolling */}
        <FlatList
          ref={flatListRef}
          data={slides}
          renderItem={renderSlide}
          keyExtractor={(item, index) => `slide-${index}`}
          horizontal
          pagingEnabled
          showsHorizontalScrollIndicator={false}
          onViewableItemsChanged={onViewableItemsChanged}
          viewabilityConfig={viewabilityConfig}
          decelerationRate="fast"
          snapToInterval={SCREEN_WIDTH}
          snapToAlignment="start"
          bounces={false}
          scrollEventThrottle={16}
          getItemLayout={(data, index) => ({
            length: SCREEN_WIDTH,
            offset: SCREEN_WIDTH * index,
            index,
          })}
          style={styles.flatList}
        />

        {/* Speaker selection modal */}
        <Modal
          visible={showSpeakerModal}
          transparent={true}
          animationType="fade"
          onRequestClose={() => setShowSpeakerModal(false)}
        >
          <TouchableOpacity
            style={styles.modalOverlay}
            activeOpacity={1}
            onPress={() => setShowSpeakerModal(false)}
          >
            <View style={styles.speakerModal}>
              <ScrollView showsVerticalScrollIndicator={false}>
                {data.speakers.map((speaker, index) => {
                  const isActive = currentSlide > 0 && currentSlide - 1 === index;
                  return (
                    <TouchableOpacity
                      key={speaker.id}
                      style={[
                        styles.speakerOption,
                        isActive && styles.speakerOptionActive,
                      ]}
                      onPress={() => selectSpeaker(speaker.id)}
                    >
                      <View>
                        <Text style={styles.speakerOptionName}>{speaker.name}</Text>
                        <Text style={styles.speakerOptionHandle}>{speaker.handle}</Text>
                      </View>
                      <Text style={styles.speakerRankBadge}>{getSpeakerRank(speaker)}</Text>
                    </TouchableOpacity>
                  );
                })}
              </ScrollView>
            </View>
          </TouchableOpacity>
        </Modal>
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
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 32,
  },
  loadingText: {
    fontSize: 18,
    color: '#fff',
    marginTop: 20,
    fontWeight: '600',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 32,
  },
  errorTitle: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 12,
  },
  errorMessage: {
    fontSize: 16,
    color: '#fff',
    textAlign: 'center',
    marginBottom: 24,
    opacity: 0.9,
  },
  retryButton: {
    backgroundColor: '#fff',
    paddingHorizontal: 32,
    paddingVertical: 16,
    borderRadius: 24,
  },
  retryButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FF6B5A',
  },
  pageIndicators: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingHorizontal: 32,
    paddingTop: 20,
  },
  indicator: {
    flex: 1,
    height: 4,
    backgroundColor: 'rgba(0, 0, 0, 0.2)',
    borderRadius: 2,
  },
  indicatorActive: {
    backgroundColor: '#000000',
  },
  closeButton: {
    position: 'absolute',
    top: 20,
    right: 32,
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 10,
  },
  closeIcon: {
    fontSize: 28,
    color: '#000000',
    fontWeight: '300',
  },
  flatList: {
    flex: 1,
  },
  slideContainer: {
    justifyContent: 'center',
    paddingHorizontal: 32,
    paddingTop: 40,
    paddingBottom: 40,
  },
  logoContainer: {
    alignItems: 'center',
    marginBottom: 30,
  },
  logoCircle: {
    width: 120,
    height: 120,
    borderRadius: 60,
    borderWidth: 4,
    borderColor: '#000000',
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
    fontSize: 32,
    fontWeight: '400',
    color: '#000000',
    textAlign: 'center',
    marginBottom: 60,
    letterSpacing: 0.3,
  },
  mainStatContainer: {
    alignItems: 'center',
    marginBottom: 50,
  },
  statLabel: {
    fontSize: 20,
    color: '#000000',
    marginBottom: 10,
    fontWeight: '400',
  },
  bigNumber: {
    fontSize: 140,
    fontWeight: '700',
    color: '#000000',
    lineHeight: 150,
    marginVertical: 10,
  },
  statSubtitle: {
    fontSize: 28,
    color: '#000000',
    fontWeight: '400',
    marginTop: 5,
  },
  additionalStats: {
    alignItems: 'center',
    gap: 8,
  },
  additionalStatText: {
    fontSize: 16,
    color: '#000000',
    fontWeight: '400',
  },
  topControls: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 16,
    paddingHorizontal: 20,
    marginBottom: 24,
  },
  statsCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 24,
    padding: 32,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 12,
    elevation: 5,
  },
  cardTopStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 40,
  },
  statBox: {
    alignItems: 'center',
  },
  statNumber: {
    fontSize: 56,
    fontWeight: '700',
    color: '#4A90E2',
    marginBottom: 8,
  },
  statLabel2: {
    fontSize: 16,
    color: '#666666',
    fontWeight: '500',
  },
  wordBreakdownSection: {
    marginTop: 20,
  },
  breakdownTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#333333',
    marginBottom: 20,
  },
  wordGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  wordPill: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#E8F0FE',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 20,
    gap: 12,
  },
  wordText: {
    fontSize: 16,
    color: '#333333',
    fontWeight: '500',
  },
  wordCount: {
    fontSize: 16,
    color: '#4A90E2',
    fontWeight: '700',
  },
  controlButton: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: 'rgba(255, 255, 255, 0.3)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  rankBadge: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#FFD700',
    justifyContent: 'center',
    alignItems: 'center',
  },
  rankNumber: {
    fontSize: 24,
    fontWeight: '700',
    color: '#000000',
  },
  speakerButton: {
    flex: 1,
    backgroundColor: 'rgba(255, 255, 255, 0.5)',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 28,
    alignItems: 'center',
  },
  speakerName: {
    fontSize: 18,
    fontWeight: '600',
    color: '#000000',
  },
  speakerHandle: {
    fontSize: 14,
    color: '#666666',
    marginTop: 2,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  speakerModal: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 20,
    width: '80%',
    maxHeight: '60%',
  },
  speakerOption: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 16,
    paddingHorizontal: 16,
    borderRadius: 12,
    marginBottom: 8,
  },
  speakerOptionActive: {
    backgroundColor: '#E8F0FE',
  },
  speakerOptionName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333333',
  },
  speakerOptionHandle: {
    fontSize: 14,
    color: '#666666',
    marginTop: 2,
  },
  speakerRankBadge: {
    fontSize: 18,
    fontWeight: '700',
    color: '#4A90E2',
  },
});
