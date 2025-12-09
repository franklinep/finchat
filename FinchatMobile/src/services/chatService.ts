import { apiClient } from './apiClient';
import { Message } from '../types/chat';

export const chatService = {
  sendMessage: async (text: string): Promise<Message> => {
    try {
      // Consulta de comprobantes vía backend
      const response = await apiClient.post('/comprobantes/consultar', { mensaje: text });

      // Transform backend response to Message format
      return {
        id: Date.now().toString(),
        text: response.data.respuesta || response.data.mensaje || 'Sin respuesta',
        sender: 'system',
        timestamp: new Date(),
      };
    } catch (error: any) {
      console.error('Error sending message:', error);
      throw error;
    }
  },
};
