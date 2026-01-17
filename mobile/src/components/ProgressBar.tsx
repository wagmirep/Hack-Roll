import React from 'react';
import { View, StyleSheet } from 'react-native';

interface Props {
  progress: number; // 0-100
  color?: string;
  backgroundColor?: string;
  height?: number;
}

export default function ProgressBar({
  progress,
  color = '#007AFF',
  backgroundColor = '#E5E5EA',
  height = 8,
}: Props) {
  const clampedProgress = Math.min(Math.max(progress, 0), 100);

  return (
    <View style={[styles.container, { backgroundColor, height, borderRadius: height / 2 }]}>
      <View
        style={[
          styles.fill,
          {
            width: `${clampedProgress}%`,
            backgroundColor: color,
            height,
            borderRadius: height / 2,
          },
        ]}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    width: '100%',
    overflow: 'hidden',
  },
  fill: {
    transition: 'width 0.3s ease',
  },
});
