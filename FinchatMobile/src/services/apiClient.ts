import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform } from 'react-native';

// Configuración de URL según plataforma
const getBaseURL = () => {
  // IMPORTANTE: Si estás usando un dispositivo físico, necesitas la IP local de tu PC
  // Para encontrarla: ejecuta "ipconfig" en Windows o "ifconfig" en Mac/Linux
  const LOCAL_IP = '192.168.18.9'; // Tu IP local en la red

  // Para Web (compilación web de Expo)
  if (Platform.OS === 'web') {
    return 'http://localhost:8000/api/v1';
  }

  // Para iOS Simulator
  if (Platform.OS === 'ios') {
    return 'http://localhost:8000/api/v1';
  }

  // Para Android
  if (Platform.OS === 'android') {
    // Si estás en Expo Go (dispositivo físico), usa la IP local
    // Si estás en emulador, usa 10.0.2.2
    // Expo Go siempre es dispositivo físico, así que usamos la IP local
    return `http://${LOCAL_IP}:8000/api/v1`;
  }

  // Fallback
  return 'http://localhost:8000/api/v1';
};

const BASE_URL = getBaseURL();

console.log('🔧 API Base URL:', BASE_URL);

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to include JWT token
apiClient.interceptors.request.use(
  async (config) => {
    console.log('📤 API Request:', config.method?.toUpperCase(), config.url);
    const token = await AsyncStorage.getItem('@finchat_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    console.error('❌ Request Error:', error);
    return Promise.reject(error);
  }
);

// Add response interceptor to handle 401 errors
apiClient.interceptors.response.use(
  (response) => {
    console.log('✅ API Response:', response.status, response.config.url);
    return response;
  },
  async (error) => {
    if (error.response) {
      console.error('❌ API Error:', error.response.status, error.response.data);
    } else if (error.request) {
      console.error('❌ Network Error: No response received', error.message);
    } else {
      console.error('❌ Request Setup Error:', error.message);
    }

    if (error.response?.status === 401) {
      // Token expired or invalid, clear it
      await AsyncStorage.removeItem('@finchat_token');
      // The auth context will handle redirection to login
    }
    return Promise.reject(error);
  }
);
