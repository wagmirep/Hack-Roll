import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { useAuth } from '../contexts/AuthContext';
import { AuthNavigator } from './AuthNavigator';
import { MainNavigator } from './MainNavigator';
import { ActivityIndicator, View, StyleSheet } from 'react-native';

export function AppNavigator() {
  const { session, loading } = useAuth();

  console.log('AppNavigator render - loading:', loading, 'session:', session?.user?.id || 'null');

  if (loading) {
    console.log('Showing loading spinner');
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
      </View>
    );
  }

  console.log('Loading complete - showing', session ? 'MainNavigator' : 'AuthNavigator');

  return (
    <NavigationContainer>
      {session ? <MainNavigator /> : <AuthNavigator />}
    </NavigationContainer>
  );
}

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#fff',
  },
});
