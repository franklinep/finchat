import { apiClient } from './apiClient';
import AsyncStorage from '@react-native-async-storage/async-storage';

const TOKEN_KEY = '@finchat_token';
const USER_KEY = '@finchat_user';

export interface RegisterData {
  nombre_mostrar: string;
  correo_electronico: string;
  password: string;
}

export interface LoginData {
  correo_electronico: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export const authService = {
  async register(data: RegisterData): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/auth/register', data);
    if (response.data.access_token) {
      await this.saveToken(response.data.access_token);
    }
    return response.data;
  },

  async login(data: LoginData): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/auth/login', data);
    if (response.data.access_token) {
      await this.saveToken(response.data.access_token);
    }
    return response.data;
  },

  async saveToken(token: string): Promise<void> {
    await AsyncStorage.setItem(TOKEN_KEY, token);
  },

  async getToken(): Promise<string | null> {
    return await AsyncStorage.getItem(TOKEN_KEY);
  },

  async logout(): Promise<void> {
    await AsyncStorage.multiRemove([TOKEN_KEY, USER_KEY]);
  },

  async isAuthenticated(): Promise<boolean> {
    const token = await this.getToken();
    return !!token;
  },
};
