import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  SafeAreaView,
  ActivityIndicator,
  TouchableOpacity,
  Modal,
} from 'react-native';
import { StackNavigationProp } from '@react-navigation/stack';
import { RouteProp } from '@react-navigation/native';
import { RecordStackParamList } from '../navigation/MainNavigator';
import { api } from '../api/client';
import { SessionResult } from '../types/session';
import { LinearGradient } from 'expo-linear-gradient';

type ResultsScreenNavigationProp = StackNavigationProp<RecordStackParamList, 'Results'>;
type ResultsScreenRouteProp = RouteProp<RecordStackParamList, 'Results'>;

interface Props {
  navigation: ResultsScreenNavigationProp;
  route: ResultsScreenRouteProp;
}

interface Speaker {
  id: string;
  name: string;
  username: string;
  rank: number;
}

export default function ResultsScreen({ navigation, route }: Props) {
  const { sessionId } = route.params;
  const [results, setResults] = useState<SessionResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedSpeaker, setSelectedSpeaker] = useState<SessionResult | null>(null);
  const [showSpeakerDropdown, setShowSpeakerDropdown] = useState(false);

  useEffect(() => {
    fetchResults();
  }, [sessionId]);

  useEffect(() => {
    if (results.length > 0 && !selectedSpeaker) {
      setSelectedSpeaker(results[0]);
    }
  }, [results]);

  const fetchResults = async () => {
    try {
      const data = await api.sessions.getResults(sessionId);
      setResults(data.results || []);
    } catch (error) {
      console.error('Error fetching results:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    navigation.goBack();
  };

  const handleSpeakerSelect = (speaker: SessionResult) => {
    setSelectedSpeaker(speaker);
    setShowSpeakerDropdown(false);
  };

  if (loading) {
    return (
      <LinearGradient
        colors={['#F5A8A8', '#F5A8A8']}
        style={styles.container}
      >
        <SafeAreaView style={styles.safeArea}>
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color="#FFFFFF" />
            <Text style={styles.loadingText}>Loading results...</Text>
          </View>
        </SafeAreaView>
      </LinearGradient>
    );
  }

  const getTopWord = () => {
    if (!selectedSpeaker || !selectedSpeaker.words) return 'N/A';
    const entries = Object.entries(selectedSpeaker.words);
    if (entries.length === 0) return 'N/A';
    const sorted = entries.sort(([, a], [, b]) => (b as number) - (a as number));
    return sorted[0][0];
  };

  const getSortedWords = () => {
    if (!selectedSpeaker || !selectedSpeaker.words) return [];
    return Object.entries(selectedSpeaker.words)
      .sort(([, a], [, b]) => (b as number) - (a as number))
      .slice(0, 6); // Show top 6 words
  };

  return (
    <LinearGradient
      colors={['#F5A8A8', '#F5A8A8']}
      style={styles.container}
    >
      <SafeAreaView style={styles.safeArea}>
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
        >
          {/* Page indicators */}
          <View style={styles.pageIndicators}>
            <View style={styles.indicator} />
            <View style={[styles.indicator, styles.indicatorActive]} />
            <View style={styles.indicator} />
          </View>

          {/* Close button */}
          <TouchableOpacity
            style={styles.closeButton}
            onPress={handleClose}
          >
            <Text style={styles.closeIcon}>✕</Text>
          </TouchableOpacity>

          {/* Main Stats Card */}
          {selectedSpeaker && (
            <View style={styles.statsCard}>
              {/* Top Stats */}
              <View style={styles.topStats}>
                <View style={styles.statBox}>
                  <Text style={styles.statNumber}>
                    {selectedSpeaker.total_words || 0}
                  </Text>
                  <Text style={styles.statLabel}>Total Words</Text>
                </View>
                <View style={styles.statBox}>
                  <Text style={styles.statNumber}>{getTopWord()}</Text>
                  <Text style={styles.statLabel}>Top Word</Text>
                </View>
              </View>

              {/* Word Breakdown */}
              <View style={styles.wordBreakdownSection}>
                <Text style={styles.wordBreakdownTitle}>Word Breakdown:</Text>
                <View style={styles.wordPills}>
                  {getSortedWords().map(([word, count], index) => (
                    <View key={index} style={styles.wordPill}>
                      <Text style={styles.wordPillText}>{word}</Text>
                      <Text style={styles.wordPillCount}>{count}</Text>
                    </View>
                  ))}
                </View>
              </View>
            </View>
          )}
        </ScrollView>

        {/* Bottom Navigation Bar */}
        <View style={styles.bottomNav}>
          <TouchableOpacity style={styles.navIconButton}>
            <Text style={styles.navIcon}>🔊</Text>
          </TouchableOpacity>

          <View style={styles.trophyBadge}>
            <Text style={styles.trophyIcon}>🏆</Text>
            <Text style={styles.trophyNumber}>
              {selectedSpeaker?.ranking || 1}
            </Text>
          </View>

          <TouchableOpacity
            style={styles.speakerButton}
            onPress={() => setShowSpeakerDropdown(!showSpeakerDropdown)}
          >
            <Text style={styles.speakerButtonText}>
              {selectedSpeaker?.display_name || 'Speaker 1'}
            </Text>
            <Text style={styles.speakerUsername}>
              @{selectedSpeaker?.username || 'speaker1'}
            </Text>
            <Text style={styles.dropdownArrow}>
              {showSpeakerDropdown ? '▲' : '▼'}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.navIconButton}>
            <Text style={styles.navIcon}>🔗</Text>
          </TouchableOpacity>
        </View>

        {/* Speaker Dropdown Modal */}
        <Modal
          visible={showSpeakerDropdown}
          transparent
          animationType="fade"
          onRequestClose={() => setShowSpeakerDropdown(false)}
        >
          <TouchableOpacity
            style={styles.modalOverlay}
            activeOpacity={1}
            onPress={() => setShowSpeakerDropdown(false)}
          >
            <View style={styles.dropdownContainer}>
              {results.map((speaker, index) => (
                <TouchableOpacity
                  key={speaker.user_id}
                  style={styles.dropdownItem}
                  onPress={() => handleSpeakerSelect(speaker)}
                >
                  <View>
                    <Text style={styles.dropdownItemName}>
                      {speaker.display_name}
                    </Text>
                    <Text style={styles.dropdownItemUsername}>
                      @{speaker.username}
                    </Text>
                  </View>
                  <Text style={styles.dropdownItemRank}>{index + 1}</Text>
                </TouchableOpacity>
              ))}
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
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#FFFFFF',
  },
  scrollContent: {
    flexGrow: 1,
    paddingHorizontal: 24,
    paddingTop: 20,
    paddingBottom: 120,
  },
  pageIndicators: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 20,
  },
  indicator: {
    width: 100,
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
    right: 24,
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
  statsCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 24,
    padding: 32,
    marginTop: 40,
  },
  topStats: {
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
  statLabel: {
    fontSize: 14,
    color: '#666666',
    fontWeight: '400',
  },
  wordBreakdownSection: {
    marginTop: 20,
  },
  wordBreakdownTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#000000',
    marginBottom: 20,
  },
  wordPills: {
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
    borderRadius: 24,
    gap: 12,
  },
  wordPillText: {
    fontSize: 16,
    color: '#000000',
    fontWeight: '500',
  },
  wordPillCount: {
    fontSize: 16,
    color: '#4A90E2',
    fontWeight: '700',
  },
  bottomNav: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    backgroundColor: '#F5A8A8',
    borderTopWidth: 1,
    borderTopColor: 'rgba(0, 0, 0, 0.1)',
  },
  navIconButton: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: 'rgba(255, 255, 255, 0.3)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  navIcon: {
    fontSize: 24,
  },
  trophyBadge: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: '#F5A623',
    justifyContent: 'center',
    alignItems: 'center',
    position: 'relative',
  },
  trophyIcon: {
    fontSize: 28,
  },
  trophyNumber: {
    position: 'absolute',
    bottom: 8,
    fontSize: 14,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  speakerButton: {
    flex: 1,
    marginHorizontal: 12,
    backgroundColor: 'rgba(255, 255, 255, 0.5)',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 24,
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 8,
  },
  speakerButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000000',
  },
  speakerUsername: {
    fontSize: 12,
    color: 'rgba(0, 0, 0, 0.6)',
  },
  dropdownArrow: {
    fontSize: 12,
    color: '#000000',
    marginLeft: 4,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  dropdownContainer: {
    backgroundColor: '#FFFFFF',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    paddingVertical: 20,
    paddingHorizontal: 24,
    maxHeight: 400,
  },
  dropdownItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#F0F0F0',
  },
  dropdownItemName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000000',
    marginBottom: 4,
  },
  dropdownItemUsername: {
    fontSize: 14,
    color: '#666666',
  },
  dropdownItemRank: {
    fontSize: 18,
    fontWeight: '700',
    color: '#4A90E2',
  },
});
