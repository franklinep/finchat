import React from 'react';
import { createStackNavigator } from '@react-navigation/stack';
import { ActivityIndicator, View, StyleSheet } from 'react-native';
import { useAuth } from '../context/AuthContext';
import { ChatScreen } from '../screens/ChatScreen';
import { UploadReceiptScreen } from '../screens/UploadReceiptScreen';
import { ReceiptDetailScreen } from '../screens/ReceiptDetailScreen';
import { SettingsScreen } from '../screens/SettingsScreen';
import { LoginScreen } from '../screens/LoginScreen';
import { RegisterScreen } from '../screens/RegisterScreen';
import { colors } from '../theme/colors';

const Stack = createStackNavigator();

const AuthStack = () => (
  <Stack.Navigator screenOptions={{ headerShown: false }}>
    <Stack.Screen name="Login" component={LoginScreen} />
    <Stack.Screen name="Register" component={RegisterScreen} />
  </Stack.Navigator>
);

const MainStack = () => (
  <Stack.Navigator
    initialRouteName="Chat"
    screenOptions={{
      headerShown: false,
    }}
  >
    <Stack.Screen name="Chat" component={ChatScreen} />
    <Stack.Screen
      name="UploadReceipt"
      component={UploadReceiptScreen}
      options={{ headerShown: true, title: 'Subir Comprobante' }}
    />
    <Stack.Screen
      name="ReceiptDetail"
      component={ReceiptDetailScreen}
      options={{ headerShown: true, title: 'Detalle' }}
    />
    <Stack.Screen
      name="Settings"
      component={SettingsScreen}
      options={{ headerShown: true, title: 'Configuración' }}
    />
  </Stack.Navigator>
);

export const AppNavigator = () => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  return isAuthenticated ? <MainStack /> : <AuthStack />;
};

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: colors.background,
  },
});
