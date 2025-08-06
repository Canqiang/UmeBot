// ============== src/hooks/useWebSocket.ts ==============
import { useState, useEffect, useCallback, useRef } from 'react';
import { WebSocketService } from '../services/websocket';
import { WebSocketMessage } from '../types';

interface UseWebSocketOptions {
  url: string;
  autoConnect?: boolean;
}

interface UseWebSocketReturn {
  isConnected: boolean;
  isConnecting: boolean;
  send: (data: any) => void;
  connect: () => Promise<void>;
  disconnect: () => void;
  lastMessage: WebSocketMessage | null;
  error: Error | null;
}

export const useWebSocket = ({
  url,
  autoConnect = true,
}: UseWebSocketOptions): UseWebSocketReturn => {
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [error, setError] = useState<Error | null>(null);

  const wsRef = useRef<WebSocketService | null>(null);

  const connect = useCallback(async () => {
    if (wsRef.current?.isConnected()) {
      return;
    }

    setIsConnecting(true);
    setError(null);

    try {
      if (!wsRef.current) {
        wsRef.current = new WebSocketService();
      }

      await wsRef.current.connect(url);

      wsRef.current.on('connected', () => {
        setIsConnected(true);
        setIsConnecting(false);
      });

      wsRef.current.on('disconnected', () => {
        setIsConnected(false);
      });

      wsRef.current.on('message', (data: WebSocketMessage) => {
        setLastMessage(data);
      });

      wsRef.current.on('error', (err: any) => {
        setError(new Error(err.message || 'WebSocket error'));
      });

    } catch (err) {
      setError(err as Error);
      setIsConnecting(false);
    }
    }, [url]);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.disconnect();
      setIsConnected(false);
    }
  }, []);

  const send = useCallback((data: any) => {
    if (wsRef.current?.isConnected()) {
      wsRef.current.send(data);
    } else {
      console.error('WebSocket is not connected');
      setError(new Error('WebSocket is not connected'));
    }
  }, []);

  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

  return {
    isConnected,
    isConnecting,
    send,
    connect,
    disconnect,
    lastMessage,
    error,
  };
};
