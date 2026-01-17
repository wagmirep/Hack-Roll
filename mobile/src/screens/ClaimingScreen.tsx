import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Alert,
  SafeAreaView,
  ActivityIndicator,
} from 'react-native';
import { StackNavigationProp } from '@react-navigation/stack';
import { RouteProp } from '@react-navigation/native';
import { RecordStackParamList } from '../navigation/MainNavigator';
import { api } from '../api/client';
import { Speaker } from '../types/session';
import SpeakerCard from '../components/SpeakerCard';

type ClaimingScreenNavigationProp = StackNavigationProp<RecordStackParamList, 'Claiming'>;
type ClaimingScreenRouteProp = RouteProp<RecordStackParamList, 'Claiming'>;

interface Props {
  navigation: ClaimingScreenNavigationProp;
  route: ClaimingScreenRouteProp;
}

export default function ClaimingScreen({ navigation, route }: Props) {
  const { sessionId } = route.params;
  const [speakers, setSpeakers] = useState<Speaker[]>([]);
  const [loading, setLoading] = useState(true);
  const [claiming, setClaiming] = useState(false);

  useEffect(() => {
    fetchSpeakers();
  }, [sessionId]);

  const fetchSpeakers = async () => {
    try {
      const data = await api.sessions.getSpeakers(sessionId);
      setSpeakers(data.speakers || []);
    } catch (error) {
      Alert.alert('Error', 'Failed to load speakers');
    } finally {
      setLoading(false);
    }
  };

  const handleClaimSpeaker = async (speakerId: string) => {
    if (claiming) return;

    Alert.alert(
      'Claim Speaker',
      'Are you sure this is your voice?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Yes, That\'s Me!',
          onPress: async () => {
            setClaiming(true);
            try {
              const result = await api.sessions.claimSpeaker(sessionId, speakerId);
              
              // Show success message with word counts
              const topWords = Object.entries(result.word_counts)
                .sort(([, a], [, b]) => (b as number) - (a as number))
                .slice(0, 3)
                .map(([word, count]) => `${word}: ${count}`)
                .join(', ');

              Alert.alert(
                'Voice Claimed! 🎉',
                `You said ${result.total_words} tracked words!\nTop words: ${topWords}`,
                [{ text: 'View Results', onPress: () => navigation.replace('Results', { sessionId }) }]
              );
            } catch (error: any) {
              Alert.alert('Error', error.message || 'Failed to claim speaker');
            } finally {
              setClaiming(false);
            }
          },
        },
      ]
    );
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#007AFF" />
          <Text style={styles.loadingText}>Loading speakers...</Text>
        </View>
      </SafeAreaView>
    );
  }

  const unclaimedSpeakers = speakers.filter(s => !s.claimed_by);
  const claimedSpeakers = speakers.filter(s => s.claimed_by);

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <View style={styles.header}>
          <Text style={styles.title}>Claim Your Voice</Text>
          <Text style={styles.subtitle}>
            Tap the play button to hear a sample, then claim your voice!
          </Text>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Unclaimed Speakers ({unclaimedSpeakers.length})</Text>
          {unclaimedSpeakers.length === 0 ? (
            <Text style={styles.emptyText}>All speakers have been claimed!</Text>
          ) : (
            unclaimedSpeakers.map((speaker) => (
              <SpeakerCard
                key={speaker.speaker_id}
                speaker={speaker}
                onClaim={() => handleClaimSpeaker(speaker.speaker_id)}
                disabled={claiming}
              />
            ))
          )}
        </View>

        {claimedSpeakers.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Already Claimed ({claimedSpeakers.length})</Text>
            {claimedSpeakers.map((speaker) => (
              <SpeakerCard
                key={speaker.speaker_id}
                speaker={speaker}
                disabled={true}
              />
            ))}
          </View>
        )}

        <TouchableOpacity
          style={styles.skipButton}
          onPress={() => navigation.replace('Results', { sessionId })}
        >
          <Text style={styles.skipText}>Skip to Results →</Text>
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
    lineHeight: 22,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginBottom: 12,
  },
  emptyText: {
    fontSize: 14,
    color: '#999',
    fontStyle: 'italic',
    padding: 16,
    textAlign: 'center',
  },
  skipButton: {
    marginTop: 16,
    marginBottom: 32,
    padding: 16,
    alignItems: 'center',
  },
  skipText: {
    fontSize: 16,
    color: '#007AFF',
    fontWeight: '600',
  },
});
