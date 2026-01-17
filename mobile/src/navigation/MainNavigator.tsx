import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createStackNavigator } from '@react-navigation/stack';
import RecordingScreen from '../screens/RecordingScreen';
import ProcessingScreen from '../screens/ProcessingScreen';
import ClaimingScreen from '../screens/ClaimingScreen';
import ResultsScreen from '../screens/ResultsScreen';
import WrappedScreen from '../screens/WrappedScreen';
import StatsScreen from '../screens/StatsScreen';
import { Text } from 'react-native';

export type MainTabParamList = {
  RecordTab: undefined;
  StatsTab: undefined;
};

export type RecordStackParamList = {
  Recording: { groupId?: string };
  Processing: { sessionId: string };
  Claiming: { sessionId: string };
  Results: { sessionId: string };
  Wrapped: { data?: any };
};

const Tab = createBottomTabNavigator<MainTabParamList>();
const RecordStack = createStackNavigator<RecordStackParamList>();

function RecordStackNavigator() {
  return (
    <RecordStack.Navigator screenOptions={{ headerShown: false }}>
      <RecordStack.Screen
        name="Recording"
        component={RecordingScreen}
      />
      <RecordStack.Screen
        name="Processing"
        component={ProcessingScreen}
      />
      <RecordStack.Screen
        name="Claiming"
        component={ClaimingScreen}
        options={{ headerShown: true, title: 'Claim Your Voice' }}
      />
      <RecordStack.Screen
        name="Results"
        component={ResultsScreen}
      />
      <RecordStack.Screen
        name="Wrapped"
        component={WrappedScreen}
      />
    </RecordStack.Navigator>
  );
}

export function MainNavigator() {
  return (
    <Tab.Navigator
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: '#007AFF',
        tabBarInactiveTintColor: '#8E8E93',
      }}
    >
      <Tab.Screen 
        name="RecordTab" 
        component={RecordStackNavigator}
        options={{
          title: 'Record',
          tabBarIcon: ({ color }) => <Text style={{ color, fontSize: 24, fontWeight: '600' }}>●</Text>,
        }}
      />
      <Tab.Screen 
        name="StatsTab" 
        component={StatsScreen}
        options={{
          title: 'Stats',
          tabBarIcon: ({ color }) => <Text style={{ color, fontSize: 24, fontWeight: '600' }}>≣</Text>,
        }}
      />
    </Tab.Navigator>
  );
}
