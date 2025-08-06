// ============== src/hooks/useChat.ts ==============
import { useState, useCallback, useEffect } from 'react';
import { Message } from '../types';
import { useWebSocket } from './useWebSocket';

interface UseChatOptions {
  sessionId: string;
  initialMessages?: Message[];
}

interface UseChatReturn {
  messages: Message[];
  sendMessage: (content: string) => void;
  isLoading: boolean;
  isConnected: boolean;
  error: Error | null;
  clearMessages: () => void;
  loadHistory: () => Promise<void>;
}

export const useChat = ({ sessionId, initialMessages = [] }: UseChatOptions): UseChatReturn => {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [isLoading, setIsLoading] = useState(false);

  const wsUrl = `ws://localhost:8000/ws/chat/${sessionId}`;

  const { isConnected, send, lastMessage, error } = useWebSocket({
    url: wsUrl,
    autoConnect: true,
  });

  // Handle incoming messages
  useEffect(() => {
    if (lastMessage && lastMessage.type === 'bot_message') {
      const newMessage: Message = {
        id: `msg_${Date.now()}`,
        type: 'bot',
        content: lastMessage.message || '',
        timestamp: lastMessage.timestamp || new Date().toISOString(),
        data: lastMessage.data,
      };

      setMessages(prev => [...prev, newMessage]);
      setIsLoading(false);
    }
  }, [lastMessage]);

  const sendMessage = useCallback((content: string) => {
    if (!content.trim() || !isConnected) return;

    // Add user message
    const userMessage: Message = {
      id: `msg_${Date.now()}`,
      type: 'user',
      content,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    // Send via WebSocket
    send({
      type: 'chat',
      message: content,
    });
  }, [isConnected, send]);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  const loadHistory = useCallback(async () => {
    // TODO: Implement loading chat history from server
    try {
      // const history = await api.getChatHistory(sessionId);
      // setMessages(history);
    } catch (err) {
      console.error('Failed to load chat history:', err);
    }
  }, [sessionId]);

  return {
    messages,
    sendMessage,
    isLoading,
    isConnected,
    error,
    clearMessages,
    loadHistory,
  };
};
