import React from 'react';
import { View, TouchableOpacity, Text, StyleSheet, ActivityIndicator } from 'react-native';
import { useAudioPlayback } from '../hooks/useAudioPlayback';

interface Props {
  audioUrl: string;
  size?: 'small' | 'medium' | 'large';
  onPlayingChange?: (isPlaying: boolean) => void;
}

export default function AudioPlayer({ audioUrl, size = 'medium', onPlayingChange }: Props) {
  const { isPlaying, isLoading, play, stop } = useAudioPlayback();

  React.useEffect(() => {
    onPlayingChange?.(isPlaying);
  }, [isPlaying, onPlayingChange]);

  const handlePress = async () => {
    if (isPlaying) {
      await stop();
    } else {
      await play(audioUrl);
    }
  };

  const sizeConfig = {
    small: { buttonSize: 40, iconSize: 20 },
    medium: { buttonSize: 56, iconSize: 28 },
    large: { buttonSize: 72, iconSize: 36 },
  };

  const config = sizeConfig[size];

  return (
    <TouchableOpacity
      style={[
        styles.button,
        {
          width: config.buttonSize,
          height: config.buttonSize,
          borderRadius: config.buttonSize / 2,
        },
        isPlaying && styles.buttonPlaying,
      ]}
      onPress={handlePress}
      disabled={isLoading}
    >
      {isLoading ? (
        <ActivityIndicator color="#fff" />
      ) : (
        <Text style={[styles.icon, { fontSize: config.iconSize }]}>
          {isPlaying ? '⏸️' : '▶️'}
        </Text>
      )}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  button: {
    backgroundColor: '#007AFF',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 4,
  },
  buttonPlaying: {
    backgroundColor: '#FF3B30',
  },
  icon: {
    color: '#fff',
  },
});
