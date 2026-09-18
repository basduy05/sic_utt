import { fetchApi } from './api';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export const chatService = {
  async sendMessage(sessionId: string, message: string, chatHistory: any[] = []): Promise<any> {
    return fetchApi('/chat/message', {
      method: 'POST',
      body: JSON.stringify({
        session_id: sessionId,
        message,
        message_type: 'text',
        chat_history: chatHistory,
      }),
    });
  },

  async streamMessage(
    sessionId: string,
    message: string,
    chatHistory: any[] = [],
    onChunk: (chunk: string) => void,
    onDone: (data: any) => void
  ): Promise<void> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    if (typeof window !== 'undefined') {
      const key = localStorage.getItem('gemini_api_key');
      if (key) headers['x-gemini-api-key'] = key;
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000);

    let response: Response;
    try {
      response = await fetch(`${API_BASE_URL}/chat/stream`, {
        method: 'POST',
        headers,
        signal: controller.signal,
        body: JSON.stringify({
          session_id: sessionId,
          message,
          message_type: 'text',
          chat_history: chatHistory,
        }),
      });
      clearTimeout(timeoutId);
    } catch (fetchErr: any) {
      clearTimeout(timeoutId);
      if (fetchErr.name === 'AbortError') {
        throw new Error('Kết nối tới luồng AI quá thời gian (Timeout 15s). Vui lòng kiểm tra backend.');
      }
      throw fetchErr;
    }

    if (!response.ok || !response.body) {
      throw new Error(`HTTP Error ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            if (data.type === 'chunk') {
              onChunk(data.content);
            } else if (data.type === 'done') {
              onDone(data);
            }
          } catch (e) {
            console.error('Error parsing SSE event', e);
          }
        }
      }
    }
  },

  async generateMedicalRecord(sessionId: string, chatHistory: any[], telemetry?: any): Promise<string> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    if (typeof window !== 'undefined') {
      const key = localStorage.getItem('gemini_api_key');
      if (key) headers['x-gemini-api-key'] = key;
    }

    const res = await fetch(`${API_BASE_URL}/chat/medical-record`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        session_id: sessionId,
        chat_history: chatHistory,
        telemetry: telemetry || {},
      }),
    });

    if (!res.ok) {
      throw new Error(`Failed to generate medical record (HTTP ${res.status})`);
    }

    const data = await res.json();
    return data.medical_record_markdown || '';
  },

  async getHistory(sessionId: string): Promise<{ session_id: string; messages: any[] }> {
    return fetchApi(`/chat/history/${sessionId}`);
  },

  async exportSessionAudit(sessionId: string): Promise<any> {
    return fetchApi(`/chat/export-audit/${sessionId}`);
  },
};
