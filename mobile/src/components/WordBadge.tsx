import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

interface Props {
  word: string;
  count: number;
  size?: 'small' | 'medium' | 'large';
}

export default function WordBadge({ word, count, size = 'medium' }: Props) {
  const sizeStyles = {
    small: { fontSize: 12, padding: 6 },
    medium: { fontSize: 14, padding: 8 },
    large: { fontSize: 16, padding: 10 },
  };

  return (
    <View style={[styles.container, { padding: sizeStyles[size].padding }]}>
      <Text style={[styles.word, { fontSize: sizeStyles[size].fontSize }]}>
        {word}
      </Text>
      <Text style={[styles.count, { fontSize: sizeStyles[size].fontSize - 2 }]}>
        {count}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#007AFF',
    borderRadius: 16,
    marginRight: 8,
    marginBottom: 8,
  },
  word: {
    color: '#fff',
    fontWeight: '600',
    marginRight: 4,
  },
  count: {
    color: '#fff',
    opacity: 0.8,
  },
});
