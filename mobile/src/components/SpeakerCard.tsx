import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Speaker } from '../types/session';
import AudioPlayer from './AudioPlayer';
import WordBadge from './WordBadge';

interface Props {
  speaker: Speaker;
  onClaim?: () => void;
  disabled?: boolean;
}

export default function SpeakerCard({ speaker, onClaim, disabled }: Props) {
  const topWords = Object.entries(speaker.word_preview)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 3);

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View style={styles.audioSection}>
          <AudioPlayer audioUrl={speaker.sample_audio_url} size="medium" />
          <View style={styles.speakerInfo}>
            <Text style={styles.speakerLabel}>{speaker.speaker_label}</Text>
            <Text style={styles.speakerMeta}>
              {speaker.segment_count} segments • {Math.round(speaker.total_duration_seconds)}s
            </Text>
          </View>
        </View>
      </View>

      <View style={styles.wordsSection}>
        <Text style={styles.wordsTitle}>Preview:</Text>
        <View style={styles.wordBadges}>
          {topWords.map(([word, count]) => (
            <WordBadge key={word} word={word} count={count} size="small" />
          ))}
        </View>
      </View>

      {speaker.claimed_by ? (
        <View style={styles.claimedBanner}>
          <Text style={styles.claimedText}>
            ✅ Claimed by {speaker.claimed_by_username || 'Unknown'}
          </Text>
        </View>
      ) : (
        onClaim && (
          <TouchableOpacity
            style={[styles.claimButton, disabled && styles.claimButtonDisabled]}
            onPress={onClaim}
            disabled={disabled}
          >
            <Text style={styles.claimButtonText}>
              {disabled ? 'Claiming...' : "That's Me! 🙋"}
            </Text>
          </TouchableOpacity>
        )
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  header: {
    marginBottom: 12,
  },
  audioSection: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  speakerInfo: {
    marginLeft: 12,
    flex: 1,
  },
  speakerLabel: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 4,
  },
  speakerMeta: {
    fontSize: 12,
    color: '#666',
  },
  wordsSection: {
    marginBottom: 12,
  },
  wordsTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: '#666',
    marginBottom: 8,
  },
  wordBadges: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  claimButton: {
    backgroundColor: '#007AFF',
    padding: 14,
    borderRadius: 12,
    alignItems: 'center',
  },
  claimButtonDisabled: {
    opacity: 0.6,
  },
  claimButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  claimedBanner: {
    backgroundColor: '#34C759',
    padding: 12,
    borderRadius: 12,
    alignItems: 'center',
  },
  claimedText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
});
