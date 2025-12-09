import React, { createContext, useState, useContext, ReactNode } from 'react';
import { Message } from '../types/chat';
import { chatService } from '../services/chatService';

interface ChatContextType {
  messages: Message[];
  sendMessage: (text: string) => Promise<void>;
  addMessage: (message: Message) => void;
  isLoading: boolean;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export const ChatProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      text: '¡Hola! Soy Finchat, tu asistente tributario. ¿En qué puedo ayudarte hoy?',
      sender: 'system',
      timestamp: new Date(),
    },
  ]);
  const [isLoading, setIsLoading] = useState(false);

  const addMessage = (message: Message) => {
    setMessages((prev) => [...prev, message]);
  };

  const sendMessage = async (text: string) => {
    const userMsg: Message = {
      id: Date.now().toString(),
      text,
      sender: 'user',
      timestamp: new Date(),
    };
    addMessage(userMsg);
    setIsLoading(true);

    try {
      const response = await chatService.sendMessage(text);
      addMessage(response);
    } catch (error) {
      console.error(error);
      addMessage({
        id: Date.now().toString(),
        text: 'Lo siento, hubo un error al procesar tu mensaje.',
        sender: 'system',
        timestamp: new Date(),
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <ChatContext.Provider value={{ messages, sendMessage, addMessage, isLoading }}>
      {children}
    </ChatContext.Provider>
  );
};

export const useChat = () => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
};
