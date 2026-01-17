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
import { useAuth } from '../contexts/AuthContext';
import { api } from '../api/client';

interface GroupStats {
  group_id: string;
  group_name: string;
  leaderboard: Array<{
    rank: number;
    username: string;
    display_name: string;
    total_words: number;
    top_words: Record<string, number>;
  }>;
  total_sessions: number;
  total_words: number;
}

interface GlobalStats {
  period: string;
  total_users: number;
  total_sessions: number;
  total_words: number;
  leaderboard: Array<{
    rank: number;
    username: string;
    display_name: string;
    total_words: number;
    word_counts: Array<{
      word: string;
      count: number;
      emoji?: string;
    }>;
  }>;
  top_words: Array<{
    word: string;
    count: number;
    emoji?: string;
  }>;
}

export default function StatsScreen() {
  const { groups } = useAuth();
  const [viewMode, setViewMode] = useState<'group' | 'global'>('group');
  const [selectedGroupId, setSelectedGroupId] = useState<string | null>(null);
  const [stats, setStats] = useState<GroupStats | null>(null);
  const [globalStats, setGlobalStats] = useState<GlobalStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [period, setPeriod] = useState<'week' | 'month' | 'all_time'>('week');

  useEffect(() => {
    if (groups.length > 0 && !selectedGroupId) {
      setSelectedGroupId(groups[0].id);
    } else if (groups.length === 0 && viewMode === 'group') {
      // No groups available, switch to global view
      setViewMode('global');
    }
  }, [groups]);

  useEffect(() => {
    if (viewMode === 'group' && selectedGroupId) {
      fetchGroupStats();
    } else if (viewMode === 'global') {
      fetchGlobalStats();
    }
  }, [selectedGroupId, period, viewMode]);

  const fetchGroupStats = async () => {
    if (!selectedGroupId) return;

    setLoading(true);
    try {
      const data = await api.stats.getGroupStats(selectedGroupId, period);
      setStats(data);
    } catch (error) {
      console.error('Error fetching group stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchGlobalStats = async () => {
    setLoading(true);
    try {
      const data = await api.stats.getGlobalLeaderboard(period);
      setGlobalStats(data);
    } catch (error) {
      console.error('Error fetching global stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const getRankColor = (rank: number): string => {
    if (rank === 1) return '#FFD700';
    if (rank === 2) return '#C0C0C0';
    if (rank === 3) return '#CD7F32';
    return '#007AFF';
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <View style={styles.header}>
          <Text style={styles.title}>Stats</Text>
          
          {/* View Mode Selector */}
          <View style={styles.viewModeSelector}>
            <TouchableOpacity
              style={[styles.viewModeButton, viewMode === 'group' && styles.viewModeButtonActive]}
              onPress={() => setViewMode('group')}
              disabled={groups.length === 0}
            >
              <Text style={[styles.viewModeText, viewMode === 'group' && styles.viewModeTextActive, groups.length === 0 && { opacity: 0.5 }]}>
                Group
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.viewModeButton, viewMode === 'global' && styles.viewModeButtonActive]}
              onPress={() => setViewMode('global')}
            >
              <Text style={[styles.viewModeText, viewMode === 'global' && styles.viewModeTextActive]}>
                Global
              </Text>
            </TouchableOpacity>
          </View>
          
          {/* Period Selector */}
          <View style={styles.periodSelector}>
            {(['week', 'month', 'all_time'] as const).map((p) => (
              <TouchableOpacity
                key={p}
                style={[styles.periodButton, period === p && styles.periodButtonActive]}
                onPress={() => setPeriod(p)}
              >
                <Text style={[styles.periodText, period === p && styles.periodTextActive]}>
                  {p === 'all_time' ? 'All Time' : p.charAt(0).toUpperCase() + p.slice(1)}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Group Selector - Only show in group mode */}
        {viewMode === 'group' && (
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.groupSelector}>
            {groups.map((group) => (
              <TouchableOpacity
                key={group.id}
                style={[
                  styles.groupChip,
                  selectedGroupId === group.id && styles.groupChipActive,
                ]}
                onPress={() => setSelectedGroupId(group.id)}
              >
                <Text
                  style={[
                    styles.groupChipText,
                    selectedGroupId === group.id && styles.groupChipTextActive,
                  ]}
                >
                  {group.name}
                </Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        )}

        {loading ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color="#007AFF" />
          </View>
        ) : viewMode === 'group' && stats ? (
          <>
            {/* Group Summary */}
            <View style={styles.summaryCard}>
              <View style={styles.summaryRow}>
                <View style={styles.summaryItem}>
                  <Text style={styles.summaryValue}>{stats.total_sessions}</Text>
                  <Text style={styles.summaryLabel}>Sessions</Text>
                </View>
                <View style={styles.summaryItem}>
                  <Text style={styles.summaryValue}>{stats.total_words}</Text>
                  <Text style={styles.summaryLabel}>Total Words</Text>
                </View>
              </View>
            </View>

            {/* Group Leaderboard */}
            <Text style={styles.sectionTitle}>Leaderboard 🏆</Text>
            {stats.leaderboard.length === 0 ? (
              <Text style={styles.emptyText}>No data for this period</Text>
            ) : (
              stats.leaderboard.map((entry) => (
                <View key={entry.username} style={styles.leaderboardCard}>
                  <View style={styles.leaderboardHeader}>
                    <View
                      style={[
                        styles.rankBadge,
                        { backgroundColor: getRankColor(entry.rank) },
                      ]}
                    >
                      <Text style={styles.rankText}>#{entry.rank}</Text>
                    </View>
                    <View style={styles.playerInfo}>
                      <Text style={styles.playerName}>{entry.display_name}</Text>
                      <Text style={styles.playerUsername}>@{entry.username}</Text>
                    </View>
                    <Text style={styles.totalWords}>{entry.total_words}</Text>
                  </View>
                  <View style={styles.topWords}>
                    {Object.entries(entry.top_words || {})
                      .sort(([, a], [, b]) => (b as number) - (a as number))
                      .slice(0, 3)
                      .map(([word, count]) => (
                        <View key={word} style={styles.wordChip}>
                          <Text style={styles.wordChipText}>
                            {word}: {count}
                          </Text>
                        </View>
                      ))}
                  </View>
                </View>
              ))
            )}
          </>
        ) : viewMode === 'global' && globalStats ? (
          <>
            {/* Global Summary */}
            <View style={styles.summaryCard}>
              <View style={styles.summaryRow}>
                <View style={styles.summaryItem}>
                  <Text style={styles.summaryValue}>{globalStats.total_users}</Text>
                  <Text style={styles.summaryLabel}>Users</Text>
                </View>
                <View style={styles.summaryItem}>
                  <Text style={styles.summaryValue}>{globalStats.total_sessions}</Text>
                  <Text style={styles.summaryLabel}>Sessions</Text>
                </View>
                <View style={styles.summaryItem}>
                  <Text style={styles.summaryValue}>{globalStats.total_words}</Text>
                  <Text style={styles.summaryLabel}>Total Words</Text>
                </View>
              </View>
            </View>

            {/* Top Words Section */}
            {globalStats.top_words.length > 0 && (
              <>
                <Text style={styles.sectionTitle}>Top Singlish Words 🔥</Text>
                <View style={styles.topWordsCard}>
                  {globalStats.top_words.slice(0, 5).map((wordStat, index) => (
                    <View key={wordStat.word} style={styles.topWordRow}>
                      <Text style={styles.topWordRank}>#{index + 1}</Text>
                      <Text style={styles.topWordWord}>
                        {wordStat.emoji} {wordStat.word}
                      </Text>
                      <Text style={styles.topWordCount}>{wordStat.count}</Text>
                    </View>
                  ))}
                </View>
              </>
            )}

            {/* Global Leaderboard */}
            <Text style={styles.sectionTitle}>Global Leaderboard 🌍</Text>
            {globalStats.leaderboard.length === 0 ? (
              <Text style={styles.emptyText}>No data for this period</Text>
            ) : (
              globalStats.leaderboard.map((entry) => (
                <View key={entry.username} style={styles.leaderboardCard}>
                  <View style={styles.leaderboardHeader}>
                    <View
                      style={[
                        styles.rankBadge,
                        { backgroundColor: getRankColor(entry.rank) },
                      ]}
                    >
                      <Text style={styles.rankText}>#{entry.rank}</Text>
                    </View>
                    <View style={styles.playerInfo}>
                      <Text style={styles.playerName}>
                        {entry.display_name || entry.username}
                      </Text>
                      <Text style={styles.playerUsername}>@{entry.username}</Text>
                    </View>
                    <Text style={styles.totalWords}>{entry.total_words}</Text>
                  </View>
                  <View style={styles.topWords}>
                    {entry.word_counts
                      .sort((a, b) => b.count - a.count)
                      .slice(0, 3)
                      .map((wordCount) => (
                        <View key={wordCount.word} style={styles.wordChip}>
                          <Text style={styles.wordChipText}>
                            {wordCount.emoji} {wordCount.word}: {wordCount.count}
                          </Text>
                        </View>
                      ))}
                  </View>
                </View>
              ))
            )}
          </>
        ) : (
          <View style={styles.emptyContainer}>
            {viewMode === 'group' && groups.length === 0 ? (
              <>
                <Text style={styles.emptyTitle}>No Groups Yet</Text>
                <Text style={styles.emptyText}>Join or create a group to see group stats!</Text>
              </>
            ) : (
              <Text style={styles.emptyText}>
                {viewMode === 'group' ? 'No stats available for this group' : 'No global stats available'}
              </Text>
            )}
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  scrollContent: {
    padding: 16,
  },
  header: {
    marginBottom: 16,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 16,
  },
  viewModeSelector: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 12,
  },
  viewModeButton: {
    flex: 1,
    padding: 12,
    borderRadius: 8,
    backgroundColor: '#fff',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  viewModeButtonActive: {
    backgroundColor: '#007AFF',
    borderColor: '#007AFF',
  },
  viewModeText: {
    fontSize: 16,
    color: '#666',
    fontWeight: '600',
  },
  viewModeTextActive: {
    color: '#fff',
  },
  periodSelector: {
    flexDirection: 'row',
    gap: 8,
  },
  periodButton: {
    flex: 1,
    padding: 12,
    borderRadius: 8,
    backgroundColor: '#fff',
    alignItems: 'center',
  },
  periodButtonActive: {
    backgroundColor: '#007AFF',
  },
  periodText: {
    fontSize: 14,
    color: '#666',
  },
  periodTextActive: {
    color: '#fff',
    fontWeight: '600',
  },
  groupSelector: {
    marginBottom: 16,
  },
  groupChip: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#fff',
    marginRight: 8,
  },
  groupChipActive: {
    backgroundColor: '#007AFF',
  },
  groupChipText: {
    fontSize: 14,
    color: '#666',
  },
  groupChipTextActive: {
    color: '#fff',
    fontWeight: '600',
  },
  loadingContainer: {
    padding: 48,
    alignItems: 'center',
  },
  summaryCard: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 20,
    marginBottom: 24,
  },
  summaryRow: {
    flexDirection: 'row',
  },
  summaryItem: {
    flex: 1,
    alignItems: 'center',
  },
  summaryValue: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#007AFF',
  },
  summaryLabel: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 12,
  },
  leaderboardCard: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
  },
  leaderboardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  rankBadge: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  rankText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
  },
  playerInfo: {
    flex: 1,
  },
  playerName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  playerUsername: {
    fontSize: 12,
    color: '#666',
  },
  totalWords: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#007AFF',
  },
  topWords: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  wordChip: {
    backgroundColor: '#f5f5f5',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  wordChipText: {
    fontSize: 12,
    color: '#666',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  emptyTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
  },
  emptyText: {
    fontSize: 16,
    color: '#999',
    textAlign: 'center',
  },
  topWordsCard: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 16,
    marginBottom: 24,
  },
  topWordRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f5f5f5',
  },
  topWordRank: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#999',
    width: 40,
  },
  topWordWord: {
    flex: 1,
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  topWordCount: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#007AFF',
  },
});
