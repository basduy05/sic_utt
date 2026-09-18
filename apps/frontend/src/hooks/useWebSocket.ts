'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { TelemetryData } from '../types/chat';

interface UseWebSocketOptions {
  sessionId: string;
  onStreamStart?: (messageId: string) => void;
  onStreamChunk?: (chunk: string, accumulated: string) => void;
  onStreamEnd?: (
    messageId: string,
    fullText: string,
    latency_ms?: number,
    pipeline_breakdown?: any,
    alternative_answers?: Array<{ text: string; provider: string }>
  ) => void;
  onTelemetryUpdate?: (telemetry: TelemetryData) => void;
  onError?: (err: any) => void;
}

export function useWebSocket({
  sessionId,
  onStreamStart,
  onStreamChunk,
  onStreamEnd,
  onTelemetryUpdate,
  onError,
}: UseWebSocketOptions) {
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const pingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const isDestroyedRef = useRef<boolean>(false);

  // Keep references to handlers to prevent unnecessary socket re-creations
  const onStreamStartRef = useRef(onStreamStart);
  const onStreamChunkRef = useRef(onStreamChunk);
  const onStreamEndRef = useRef(onStreamEnd);
  const onTelemetryUpdateRef = useRef(onTelemetryUpdate);
  const onErrorRef = useRef(onError);
  const sessionIdRef = useRef(sessionId);

  useEffect(() => {
    onStreamStartRef.current = onStreamStart;
    onStreamChunkRef.current = onStreamChunk;
    onStreamEndRef.current = onStreamEnd;
    onTelemetryUpdateRef.current = onTelemetryUpdate;
    onErrorRef.current = onError;
    sessionIdRef.current = sessionId;
  });

  useEffect(() => {
    if (!sessionId) return;
    isDestroyedRef.current = false;

    const connectWebSocket = () => {
      if (isDestroyedRef.current) return;

      const baseWsUrl = (process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/api/v1/ws').replace(/\/+$/, '');
      const wsUrl = `${baseWsUrl}/${sessionId}`;
      
      try {
        const ws = new WebSocket(wsUrl);
        socketRef.current = ws;

        ws.onopen = () => {
          if (isDestroyedRef.current) return;
          setIsConnected(true);
          console.log('[WebSocket] Connected for session:', sessionId);

          // Clear existing ping
          if (pingIntervalRef.current) clearInterval(pingIntervalRef.current);
          // Ping heartbeat every 15s
          pingIntervalRef.current = setInterval(() => {
            if (ws.readyState === WebSocket.OPEN) {
              ws.send(JSON.stringify({ action: 'ping' }));
            }
          }, 15000);
        };

        ws.onmessage = (event) => {
          // Prevent events from superseded sockets
          if (socketRef.current !== ws) return;

          try {
            const data = JSON.parse(event.data);

            // Discard packet only if it explicitly belongs to a different session
            if (data.session_id && sessionIdRef.current && data.session_id !== sessionIdRef.current) {
              console.warn('[WebSocket] Discarding packet from past session:', data.session_id, 'current:', sessionIdRef.current);
              return;
            }

            switch (data.type) {
              case 'telemetry_update':
                onTelemetryUpdateRef.current?.(data.telemetry);
                break;
              case 'stream_start':
                onStreamStartRef.current?.(data.message_id);
                break;
              case 'stream_chunk':
                onStreamChunkRef.current?.(data.chunk, data.accumulated);
                break;
              case 'stream_end':
                onStreamEndRef.current?.(
                  data.message_id,
                  data.full_text,
                  data.latency_ms,
                  data.pipeline_breakdown,
                  data.alternative_answers || []
                );
                break;
              case 'pong':
                // Heartbeat acknowledged
                break;
              default:
                break;
            }
          } catch (err) {
            console.error('[WebSocket] Error parsing message:', err);
          }
        };

        ws.onclose = () => {
          if (socketRef.current === ws) {
            setIsConnected(false);
          }
          if (pingIntervalRef.current) clearInterval(pingIntervalRef.current);
          console.log('[WebSocket] Connection closed for:', sessionId);

          if (!isDestroyedRef.current) {
            if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
            reconnectTimeoutRef.current = setTimeout(() => {
              connectWebSocket();
            }, 2000);
          }
        };

        ws.onerror = (err) => {
          if (socketRef.current === ws) {
            console.error('[WebSocket] Error encountered:', err);
            onErrorRef.current?.(err);
          }
        };
      } catch (e) {
        console.error('[WebSocket] Failed to instantiate socket:', e);
        setIsConnected(false);
      }
    };

    connectWebSocket();

    return () => {
      isDestroyedRef.current = true;
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (pingIntervalRef.current) clearInterval(pingIntervalRef.current);
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, [sessionId]);

  const sendWsMessage = useCallback((message: string, chatHistory: any[] = []) => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      const geminiApiKey = typeof window !== 'undefined' ? localStorage.getItem('gemini_api_key') || undefined : undefined;
      const cohereApiKey = typeof window !== 'undefined' ? localStorage.getItem('cohere_api_key') || undefined : undefined;
      socketRef.current.send(JSON.stringify({
        action: 'chat',
        session_id: sessionIdRef.current,
        message,
        chat_history: chatHistory,
        gemini_api_key: geminiApiKey,
        cohere_api_key: cohereApiKey,
      }));
      return true;
    }
    return false;
  }, []);

  return { isConnected, sendWsMessage };
}
