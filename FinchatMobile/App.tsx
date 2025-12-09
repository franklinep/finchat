import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { Provider as PaperProvider } from 'react-native-paper';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { AppNavigator } from './src/navigation/AppNavigator';
import { ChatProvider } from './src/context/ChatContext';
import { AuthProvider } from './src/context/AuthContext';

export default function App() {
  return (
    <SafeAreaProvider>
      <PaperProvider>
        <AuthProvider>
          <ChatProvider>
            <NavigationContainer>
              <AppNavigator />
            </NavigationContainer>
          </ChatProvider>
        </AuthProvider>
      </PaperProvider>
    </SafeAreaProvider>
  );
}
