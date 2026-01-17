import React from 'react';
import { createStackNavigator } from '@react-navigation/stack';
import LoginScreen from '../screens/auth/LoginScreen';
import SignupScreen from '../screens/auth/SignupScreen';
import SignupSuccessScreen from '../screens/auth/SignupSuccessScreen';

export type AuthStackParamList = {
  Login: undefined;
  Signup: undefined;
  SignupSuccess: undefined;
};

const Stack = createStackNavigator<AuthStackParamList>();

export function AuthNavigator() {
  return (
    <Stack.Navigator
      screenOptions={{
        headerShown: false,
      }}
    >
      <Stack.Screen name="Login" component={LoginScreen} />
      <Stack.Screen name="Signup" component={SignupScreen} />
      <Stack.Screen name="SignupSuccess" component={SignupSuccessScreen} />
    </Stack.Navigator>
  );
}
