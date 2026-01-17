import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  SafeAreaView,
  ActivityIndicator,
  TouchableOpacity,
} from 'react-native';
import { StackNavigationProp } from '@react-navigation/stack';
import { RouteProp } from '@react-navigation/native';
import { RecordStackParamList } from '../navigation/MainNavigator';
import { api } from '../api/client';
import { SessionResult } from '../types/session';
import WordBadge from '../components/WordBadge';

type ResultsScreenNavigationProp = StackNavigationProp<RecordStackParamList, 'Results'>;
type ResultsScreenRouteProp = RouteProp<RecordStackParamList, 'Results'>;

interface Props {
  navigation: ResultsScreenNavigationProp;
  route: ResultsScreenRouteProp;
}

export default function ResultsScreen({ navigation, route }: Props) {
  const { sessionId } = route.params;
  const [results, setResults] = useState<SessionResult[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchResults();
  }, [sessionId]);

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

  const getRankEmoji = (rank: number): string => {
    if (rank === 1) return '🥇';
    if (rank === 2) return '🥈';
    if (rank === 3) return '🥉';
    return '🏅';
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#007AFF" />
          <Text style={styles.loadingText}>Loading results...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <View style={styles.header}>
          <Text style={styles.title}>Session Results</Text>
          <Text style={styles.subtitle}>Who said what? 🎭</Text>
        </View>

        <View style={styles.resultsContainer}>
          {results.length === 0 ? (
            <Text style={styles.emptyText}>
              No results yet. Speakers need to claim their voices!
            </Text>
          ) : (
            results.map((result, index) => (
              <View key={result.user_id} style={styles.resultCard}>
                <View style={styles.resultHeader}>
                  <Text style={styles.rankText}>
                    {getRankEmoji(result.ranking)} #{result.ranking}
                  </Text>
                  <View style={styles.userInfo}>
                    <Text style={styles.displayName}>{result.display_name}</Text>
                    <Text style={styles.username}>@{result.username}</Text>
                  </View>
                </View>

                <View style={styles.statsRow}>
                  <View style={styles.statBox}>
                    <Text style={styles.statValue}>{result.total_words}</Text>
                    <Text style={styles.statLabel}>Total Words</Text>
                  </View>
                  <View style={styles.statBox}>
                    <Text style={styles.statValue}>{result.top_word}</Text>
                    <Text style={styles.statLabel}>Top Word</Text>
                  </View>
                </View>

                <View style={styles.wordsSection}>
                  <Text style={styles.wordsTitle}>Word Breakdown:</Text>
                  <View style={styles.wordBadges}>
                    {Object.entries(result.words)
                      .sort(([, a], [, b]) => (b as number) - (a as number))
                      .map(([word, count]) => (
                        <WordBadge key={word} word={word} count={count as number} />
                      ))}
                  </View>
                </View>
              </View>
            ))
          )}
        </View>

        <TouchableOpacity
          style={styles.doneButton}
          onPress={() => navigation.navigate('Recording', {})}
        >
          <Text style={styles.doneButtonText}>Back to Home</Text>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#666',
  },
  scrollContent: {
    padding: 16,
  },
  header: {
    marginBottom: 24,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
  },
  resultsContainer: {
    marginBottom: 24,
  },
  emptyText: {
    fontSize: 16,
    color: '#999',
    textAlign: 'center',
    padding: 32,
    fontStyle: 'italic',
  },
  resultCard: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  resultHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  rankText: {
    fontSize: 32,
    marginRight: 12,
  },
  userInfo: {
    flex: 1,
  },
  displayName: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
  },
  username: {
    fontSize: 14,
    color: '#666',
    marginTop: 2,
  },
  statsRow: {
    flexDirection: 'row',
    marginBottom: 16,
  },
  statBox: {
    flex: 1,
    alignItems: 'center',
    padding: 12,
    backgroundColor: '#f5f5f5',
    borderRadius: 12,
    marginHorizontal: 4,
  },
  statValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#007AFF',
    marginBottom: 4,
  },
  statLabel: {
    fontSize: 12,
    color: '#666',
  },
  wordsSection: {
    marginTop: 8,
  },
  wordsTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#666',
    marginBottom: 8,
  },
  wordBadges: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  doneButton: {
    backgroundColor: '#007AFF',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginBottom: 32,
  },
  doneButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});
