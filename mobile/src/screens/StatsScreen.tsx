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

export default function StatsScreen() {
  const { groups } = useAuth();
  const [selectedGroupId, setSelectedGroupId] = useState<string | null>(null);
  const [stats, setStats] = useState<GroupStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [period, setPeriod] = useState<'week' | 'month' | 'all_time'>('week');

  useEffect(() => {
    if (groups.length > 0 && !selectedGroupId) {
      setSelectedGroupId(groups[0].id);
    }
  }, [groups]);

  useEffect(() => {
    if (selectedGroupId) {
      fetchStats();
    }
  }, [selectedGroupId, period]);

  const fetchStats = async () => {
    if (!selectedGroupId) return;

    setLoading(true);
    try {
      const data = await api.stats.getGroupStats(selectedGroupId, period);
      setStats(data);
    } catch (error) {
      console.error('Error fetching stats:', error);
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

  if (groups.length === 0) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyTitle}>No Groups Yet</Text>
          <Text style={styles.emptyText}>Join or create a group to see stats!</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <View style={styles.header}>
          <Text style={styles.title}>Group Stats</Text>
          
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

        {/* Group Selector */}
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

        {loading ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color="#007AFF" />
          </View>
        ) : stats ? (
          <>
            {/* Summary */}
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

            {/* Leaderboard */}
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
                    {Object.entries(entry.top_words)
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
        ) : (
          <Text style={styles.emptyText}>No stats available</Text>
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
});
