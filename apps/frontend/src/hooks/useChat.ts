'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import { ChatMessage, TelemetryData } from '../types/chat';
import { useWebSocket } from './useWebSocket';
import { chatService } from '../services/chatService';

export interface ChatSession {
  id: string;
  title: string;
  timestamp: number;
  messages: ChatMessage[];
  telemetry: TelemetryData | null;
}

const DEFAULT_WELCOME_MESSAGE: ChatMessage = {
  id: 'welcome_1',
  sessionId: 'session_default',
  sender: 'assistant',
  content: 'Xin chào! Tôi là Trợ Lý Y Tế AI (MediBot) chuẩn hóa Bộ Y Tế & ICD-10. Tôi sẽ hỏi thăm kỹ càng và ghi nhớ toàn bộ thông tin của bạn. Bạn đang gặp phải những triệu chứng hay vấn đề sức khỏe nào?',
  timestamp: '2026-09-01T08:00:00.000Z',
};

export function useChat() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [sessionId, setSessionId] = useState<string>('session_default');
  const [messages, setMessages] = useState<ChatMessage[]>([DEFAULT_WELCOME_MESSAGE]);
  const [telemetry, setTelemetry] = useState<TelemetryData | null>(null);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [isEmergencyModalOpen, setIsEmergencyModalOpen] = useState<boolean>(false);
  const isInitializedRef = useRef<boolean>(false);
  const activeSessionIdRef = useRef<string>('session_default');
  const abortControllerRef = useRef<AbortController | null>(null);
  const processingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const cancelQuery = useCallback(() => {
    if (abortControllerRef.current) {
      try {
        abortControllerRef.current.abort();
      } catch {}
      abortControllerRef.current = null;
    }
    if (processingTimeoutRef.current) {
      clearTimeout(processingTimeoutRef.current);
      processingTimeoutRef.current = null;
    }
    setIsProcessing(false);
    setMessages((prev) =>
      prev.map((msg) =>
        msg.isStreaming && msg.sender === 'assistant'
          ? {
              ...msg,
              isStreaming: false,
              content: msg.content.trim()
                ? msg.content + '\n\n*(Truy vấn đã được người dùng dừng lại)*'
                : '*(Bạn đã dừng yêu cầu phân tích)*',
            }
          : msg
      )
    );
  }, []);

  // Load all sessions from localStorage on mount & sanitize
  useEffect(() => {
    try {
      const saved = localStorage.getItem('medibot_chat_sessions');
      if (saved) {
        let parsed: ChatSession[] = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) {
          // BẢO VỆ CHỐNG NHIỄM DỮ LIỆU CŨ:
          // Bất kỳ phiên nào chưa có tin nhắn của người dùng thì telemetry BẮT BUỘC là null
          // Loại bỏ tin nhắn lỗi timeout cũ [ERR_TIMEOUT_WS_45S]
          parsed = parsed.map((s) => {
            const hasUserMsg = s.messages && s.messages.some((m) => m.sender === 'user');
            const cleanMsgs = (s.messages || [])
              .map((m) => ({ ...m, isStreaming: false }))
              .filter((m) => !m.content?.includes('[ERR_TIMEOUT_WS_45S]'));
            return {
              ...s,
              messages: cleanMsgs.length > 0 ? cleanMsgs : [{ ...DEFAULT_WELCOME_MESSAGE, id: `welcome_${Date.now()}`, sessionId: s.id }],
              telemetry: hasUserMsg ? s.telemetry || null : null,
            };
          });

          setSessions(parsed);
          const savedActiveId = localStorage.getItem('medibot_active_session_id');
          const active = parsed.find((s) => s.id === savedActiveId) || parsed[0];
          activeSessionIdRef.current = active.id;
          setSessionId(active.id);

          const activeMsgs =
            active.messages && active.messages.length > 0
              ? active.messages
              : [{ ...DEFAULT_WELCOME_MESSAGE, id: `welcome_${Date.now()}`, sessionId: active.id }];
          setMessages(activeMsgs);

          const hasUser = activeMsgs.some((m) => m.sender === 'user');
          setTelemetry(hasUser ? active.telemetry || null : null);
          isInitializedRef.current = true;
          return;
        }
      }
    } catch (e) {
      console.error('Error loading sessions from localStorage', e);
    }

    // Khởi tạo phiên đầu tiên sạch hoàn toàn
    const initialId = `session_${Date.now()}`;
    activeSessionIdRef.current = initialId;
    const initialWelcome: ChatMessage = {
      ...DEFAULT_WELCOME_MESSAGE,
      id: `welcome_${Date.now()}`,
      sessionId: initialId,
    };
    const initialSession: ChatSession = {
      id: initialId,
      title: 'Khám bệnh mới',
      timestamp: Date.now(),
      messages: [initialWelcome],
      telemetry: null,
    };

    setSessions([initialSession]);
    setSessionId(initialId);
    setMessages([initialWelcome]);
    setTelemetry(null);

    try {
      localStorage.setItem('medibot_chat_sessions', JSON.stringify([initialSession]));
      localStorage.setItem('medibot_active_session_id', initialId);
    } catch (e) {}
    isInitializedRef.current = true;
  }, []);

  // Save active session to localStorage whenever messages or telemetry changes
  useEffect(() => {
    if (!isInitializedRef.current || !sessionId) return;
    if (sessionId !== activeSessionIdRef.current) return;

    // BẢO VỆ CHỐNG NHIỄM DỮ LIỆU: Chỉ lưu khi messages thực sự thuộc về sessionId hiện hành!
    if (messages.length > 0 && messages[0].sessionId && messages[0].sessionId !== sessionId) {
      return;
    }

    const hasUser = messages.some((m) => m.sender === 'user');
    // Nếu phiên chưa có tin nhắn người dùng hỏi, telemetry TUYỆT ĐỐI là null
    const safeTelemetry = hasUser ? telemetry : null;

    try {
      localStorage.setItem('medibot_active_session_id', sessionId);
    } catch (e) {}

    setSessions((prev) => {
      let found = false;
      const updated = prev.map((s) => {
        if (s.id === sessionId) {
          found = true;
          let title = s.title;
          const firstUserMsg = messages.find((m) => m.sender === 'user');
          if (firstUserMsg && (s.title === 'Khám bệnh mới' || !s.title)) {
            title = firstUserMsg.content.slice(0, 35) + (firstUserMsg.content.length > 35 ? '...' : '');
          }
          return {
            ...s,
            title,
            messages,
            telemetry: safeTelemetry,
            timestamp: Date.now(),
          };
        }
        return s;
      });

      if (!found) {
        let title = 'Khám bệnh mới';
        const firstUserMsg = messages.find((m) => m.sender === 'user');
        if (firstUserMsg) {
          title = firstUserMsg.content.slice(0, 35) + (firstUserMsg.content.length > 35 ? '...' : '');
        }
        updated.unshift({
          id: sessionId,
          title,
          timestamp: Date.now(),
          messages,
          telemetry: safeTelemetry,
        });
      }

      try {
        localStorage.setItem('medibot_chat_sessions', JSON.stringify(updated));
      } catch (e) {
        console.error('Error saving sessions', e);
      }
      return updated;
    });
  }, [sessionId, messages, telemetry]);

  // Create a brand new clean session (Khám Mới)
  const createNewSession = useCallback(() => {
    const newId = `session_${Date.now()}`;
    activeSessionIdRef.current = newId;

    const newMsg: ChatMessage = {
      ...DEFAULT_WELCOME_MESSAGE,
      id: `welcome_${Date.now()}`,
      sessionId: newId,
    };
    const newSession: ChatSession = {
      id: newId,
      title: 'Khám bệnh mới',
      timestamp: Date.now(),
      messages: [newMsg],
      telemetry: null,
    };

    // 1. Reset ngay lập tức toàn bộ trạng thái đang hiển thị trên giao diện
    setSessionId(newId);
    setMessages([newMsg]);
    setTelemetry(null);
    setIsProcessing(false);

    try {
      localStorage.setItem('medibot_active_session_id', newId);
    } catch (e) {}

    // 2. Thêm phiên mới vào danh sách và lưu trữ
    setSessions((prev) => {
      // Dọn dẹp: bất kỳ phiên nào chưa có tin nhắn user thì telemetry phải là null
      const cleaned = prev.map((s) => {
        const hasUser = s.messages && s.messages.some((m) => m.sender === 'user');
        return hasUser ? s : { ...s, telemetry: null };
      });
      const updated = [newSession, ...cleaned.filter((s) => s.id !== newId)];
      try {
        localStorage.setItem('medibot_chat_sessions', JSON.stringify(updated));
      } catch (e) {}
      return updated;
    });
  }, []);

  // Load an existing session
  const loadSession = useCallback((targetId: string) => {
    activeSessionIdRef.current = targetId;

    setSessions((prev) => {
      const found = prev.find((s) => s.id === targetId);
      if (found) {
        const targetMsgs =
          found.messages && found.messages.length > 0
            ? found.messages
            : [
                {
                  ...DEFAULT_WELCOME_MESSAGE,
                  id: `welcome_${Date.now()}`,
                  sessionId: found.id,
                },
              ];

        const hasUser = targetMsgs.some((m) => m.sender === 'user');
        const targetTelemetry = hasUser ? found.telemetry || null : null;

        setSessionId(found.id);
        setMessages(targetMsgs);
        setTelemetry(targetTelemetry);
        setIsProcessing(false);

        try {
          localStorage.setItem('medibot_active_session_id', found.id);
        } catch (e) {}
      }
      return prev;
    });
  }, []);

  // Delete a session
  const deleteSession = useCallback((targetId: string) => {
    setSessions((prev) => {
      const remaining = prev.filter((s) => s.id !== targetId);
      try {
        localStorage.setItem('medibot_chat_sessions', JSON.stringify(remaining));
      } catch (e) {}

      if (targetId === activeSessionIdRef.current) {
        if (remaining.length > 0) {
          const next = remaining[0];
          activeSessionIdRef.current = next.id;
          setSessionId(next.id);
          const nextMsgs =
            next.messages && next.messages.length > 0
              ? next.messages
              : [{ ...DEFAULT_WELCOME_MESSAGE, id: `welcome_${Date.now()}`, sessionId: next.id }];
          setMessages(nextMsgs);
          const hasUser = nextMsgs.some((m) => m.sender === 'user');
          setTelemetry(hasUser ? next.telemetry || null : null);
          setIsProcessing(false);
          try {
            localStorage.setItem('medibot_active_session_id', next.id);
          } catch (e) {}
        } else {
          const newId = `session_${Date.now()}`;
          activeSessionIdRef.current = newId;
          const newMsg: ChatMessage = {
            ...DEFAULT_WELCOME_MESSAGE,
            id: `welcome_${Date.now()}`,
            sessionId: newId,
          };
          const freshSession: ChatSession = {
            id: newId,
            title: 'Khám bệnh mới',
            timestamp: Date.now(),
            messages: [newMsg],
            telemetry: null,
          };
          setSessionId(newId);
          setMessages([newMsg]);
          setTelemetry(null);
          setIsProcessing(false);
          try {
            localStorage.setItem('medibot_chat_sessions', JSON.stringify([freshSession]));
            localStorage.setItem('medibot_active_session_id', newId);
          } catch (e) {}
          return [freshSession];
        }
      }
      return remaining;
    });
  }, []);

  const handleStreamStart = useCallback((messageId: string) => {
    setIsProcessing(true);
    setMessages((prev) => {
      const existingIdx = prev.findIndex((m) => m.isStreaming && m.sender === 'assistant');
      if (existingIdx !== -1) {
        return prev.map((msg, idx) =>
          idx === existingIdx ? { ...msg, id: messageId } : msg
        );
      }
      return [
        ...prev,
        {
          id: messageId,
          sessionId,
          sender: 'assistant',
          content: '',
          timestamp: new Date().toISOString(),
          isStreaming: true,
        },
      ];
    });
  }, [sessionId]);

  const handleStreamChunk = useCallback((chunk: string, accumulated: string) => {
    setMessages((prev) =>
      prev.map((msg) =>
        msg.isStreaming && msg.sender === 'assistant'
          ? { ...msg, content: accumulated }
          : msg
      )
    );
  }, []);

  const handleStreamEnd = useCallback((
    messageId: string,
    fullText: string,
    latency_ms?: number,
    pipeline_breakdown?: any,
    alternative_answers?: Array<{ text: string; provider: string }>,
    telemetry?: any
  ) => {
    if (processingTimeoutRef.current) {
      clearTimeout(processingTimeoutRef.current);
      processingTimeoutRef.current = null;
    }
    setIsProcessing(false);
    setMessages((prev) =>
      prev.map((msg) =>
        msg.id === messageId || (msg.isStreaming && msg.sender === 'assistant')
          ? {
              ...msg,
              id: messageId || msg.id,
              content: fullText || msg.content,
              isStreaming: false,
              latency_ms: latency_ms ?? msg.latency_ms,
              pipeline_breakdown: pipeline_breakdown ?? msg.pipeline_breakdown,
              alternative_answers: alternative_answers && alternative_answers.length > 0
                ? alternative_answers
                : msg.alternative_answers,
              telemetry: telemetry ?? msg.telemetry,
              active_answer_index: 0,
            }
          : msg
      )
    );
    if (telemetry) {
      setTelemetry((prev) => ({
        ...(prev || {}),
        ...telemetry,
        latency_ms: latency_ms ?? prev?.latency_ms,
        pipeline_breakdown: pipeline_breakdown ?? prev?.pipeline_breakdown,
      }));
    } else if (latency_ms) {
      setTelemetry((prev) => (prev ? { ...prev, latency_ms, pipeline_breakdown } : prev));
    }
  }, []);

  const handleTelemetryUpdate = useCallback((newTelemetry: TelemetryData) => {
    setTelemetry(newTelemetry);
    setMessages((prev) =>
      prev.map((msg) =>
        msg.isStreaming && msg.sender === 'assistant'
          ? { ...msg, telemetry: newTelemetry }
          : msg
      )
    );
    if (newTelemetry.is_emergency) {
      setIsEmergencyModalOpen(true);
    }
  }, []);

  const handleWsError = useCallback((err: any) => {
    console.warn('WebSocket encountered issue, resetting isProcessing:', err);
    if (processingTimeoutRef.current) {
      clearTimeout(processingTimeoutRef.current);
      processingTimeoutRef.current = null;
    }
    setIsProcessing(false);
  }, []);

  const { isConnected, sendWsMessage } = useWebSocket({
    sessionId,
    onStreamStart: handleStreamStart,
    onStreamChunk: handleStreamChunk,
    onStreamEnd: handleStreamEnd,
    onTelemetryUpdate: handleTelemetryUpdate,
    onError: handleWsError,
  });

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim() || isProcessing) return;

      const userMsg: ChatMessage = {
        id: `user_${Date.now()}`,
        sessionId,
        sender: 'user',
        content: text,
        timestamp: new Date().toISOString(),
      };
      
      const tempAssistantId = `assistant_${Date.now()}`;
      const assistantPlaceholder: ChatMessage = {
        id: tempAssistantId,
        sessionId,
        sender: 'assistant',
        content: '',
        timestamp: new Date().toISOString(),
        isStreaming: true,
      };

      // Thêm ngay tin nhắn người dùng và khung trợ lý đang suy nghĩ (isThinking = true)
      const updatedMessages = [...messages, userMsg, assistantPlaceholder];
      setMessages(updatedMessages);
      setIsProcessing(true);

      // Multi-turn history to send to LLM (chỉ lấy tin nhắn đã có nội dung)
      const historyPayload = [...messages, userMsg].map((m) => ({
        sender: m.sender,
        content: m.content,
      }));

      // Fallback function tự động chuyển sang REST HTTP khi WebSocket bị chậm hoặc mất gói tin
      const executeRestFallback = async (reason?: string) => {
        console.warn('[useChat] Triggering automatic REST fallback:', reason);
        try {
          const res = await chatService.sendMessage(sessionId, text, historyPayload);
          if (processingTimeoutRef.current) {
            clearTimeout(processingTimeoutRef.current);
            processingTimeoutRef.current = null;
          }
          setIsProcessing(false);
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === tempAssistantId
                ? {
                    ...msg,
                    id: res.message_id || tempAssistantId,
                    content: res.text_content,
                    isStreaming: false,
                    telemetry: res.telemetry,
                    latency_ms: res.latency_ms,
                    pipeline_breakdown: res.pipeline_breakdown,
                    alternative_answers: res.alternative_answers || [],
                    active_answer_index: 0,
                  }
                : msg
            )
          );
          if (res.telemetry) {
            handleTelemetryUpdate({
              ...res.telemetry,
              latency_ms: res.latency_ms,
              pipeline_breakdown: res.pipeline_breakdown,
            });
          }
        } catch (restErr: any) {
          if (processingTimeoutRef.current) {
            clearTimeout(processingTimeoutRef.current);
            processingTimeoutRef.current = null;
          }
          setIsProcessing(false);
          const errCode = restErr?.response?.status ? `HTTP_${restErr.response.status}` : (restErr?.code || 'ERR_NETWORK');
          const errDetail = restErr?.message || 'Không thể kết nối đến máy chủ';
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === tempAssistantId && msg.isStreaming
                ? {
                    ...msg,
                    content:
                      `Hiện hệ thống đang có vấn đề và chúng tôi sẽ nỗ lực để sửa chữa, câu trả lời của bạn đã được ghi lại.\n\n🚨 **Mã lỗi:** \`[${errCode}]\`: ${errDetail}`,
                    isStreaming: false,
                  }
                : msg
            )
          );
        }
      };

      // Thiết lập timeout tự động: Nếu WS không hoàn thành trong 12s, tự động lấy kết quả qua REST
      if (processingTimeoutRef.current) {
        clearTimeout(processingTimeoutRef.current);
      }
      processingTimeoutRef.current = setTimeout(() => {
        executeRestFallback('WS_TIMEOUT_12S');
      }, 12000);

      // If WebSocket is active, use WS streaming
      if (isConnected) {
        const sent = sendWsMessage(text, historyPayload);
        if (sent) return;
      }

      // SSE Chunking Stream with Multi-turn Memory (Fallback)
      let accumulatedContent = '';

        try {
          await chatService.streamMessage(
            sessionId,
            text,
            historyPayload,
            (chunk) => {
              accumulatedContent += chunk;
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === tempAssistantId
                    ? { ...msg, content: accumulatedContent }
                    : msg
                )
              );
            },
            (doneData) => {
              if (processingTimeoutRef.current) {
                clearTimeout(processingTimeoutRef.current);
                processingTimeoutRef.current = null;
              }
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === tempAssistantId
                    ? {
                        ...msg,
                        id: doneData.message_id || tempAssistantId,
                        content: doneData.full_text || accumulatedContent,
                        isStreaming: false,
                        telemetry: doneData.telemetry,
                        latency_ms: doneData.latency_ms,
                        pipeline_breakdown: doneData.pipeline_breakdown,
                        alternative_answers: doneData.alternative_answers || [],
                        active_answer_index: 0,
                      }
                    : msg
                )
              );
              if (doneData.telemetry) {
                handleTelemetryUpdate({
                  ...doneData.telemetry,
                  latency_ms: doneData.latency_ms,
                  pipeline_breakdown: doneData.pipeline_breakdown,
                });
              }
            }
          );
        } catch (err) {
          console.error('Streaming error, falling back to REST:', err);
          try {
            const res = await chatService.sendMessage(sessionId, text, historyPayload);
            if (processingTimeoutRef.current) {
              clearTimeout(processingTimeoutRef.current);
              processingTimeoutRef.current = null;
            }
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === tempAssistantId
                  ? {
                      ...msg,
                      id: res.message_id,
                      content: res.text_content,
                      isStreaming: false,
                      telemetry: res.telemetry,
                      latency_ms: res.latency_ms,
                      pipeline_breakdown: res.pipeline_breakdown,
                      alternative_answers: res.alternative_answers || [],
                      active_answer_index: 0,
                    }
                  : msg
              )
            );
            if (res.telemetry) {
              handleTelemetryUpdate({
                ...res.telemetry,
                latency_ms: res.latency_ms,
                pipeline_breakdown: res.pipeline_breakdown,
              });
            }
          } catch (restErr: any) {
            console.error('REST call also failed:', restErr);
            if (processingTimeoutRef.current) {
              clearTimeout(processingTimeoutRef.current);
              processingTimeoutRef.current = null;
            }
            const errCode = restErr?.response?.status ? `HTTP_${restErr.response.status}` : (restErr?.code || 'ERR_NETWORK');
            const errDetail = restErr?.message || 'Không thể kết nối đến máy chủ';
            const failureMsg =
              `Hiện hệ thống đang có vấn đề và chúng tôi sẽ nỗ lực để sửa chữa, câu trả lời của bạn đã được ghi lại, chúng tôi sẽ liên hệ với bạn để trả lời.\n\n🚨 **Mã lỗi:** \`[${errCode}]\`: ${errDetail}`;
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === tempAssistantId
                  ? {
                      ...msg,
                      content: failureMsg,
                      isStreaming: false,
                    }
                  : msg
              )
            );
          }
        } finally {
          setIsProcessing(false);
        }
    },
    [sessionId, messages, isConnected, isProcessing, sendWsMessage, handleTelemetryUpdate]
  );

  const generateMedicalRecord = useCallback(async (): Promise<string> => {
    return chatService.generateMedicalRecord(sessionId, messages, telemetry);
  }, [sessionId, messages, telemetry]);

  const exportSessionAuditJson = useCallback(
    async (targetSessionId?: string) => {
      const sid = targetSessionId || sessionId;
      try {
        let auditData: any = null;
        try {
          auditData = await chatService.exportSessionAudit(sid);
        } catch {}

        const targetSession = sessions.find((s) => s.id === sid);
        const currentMsgs = targetSession ? targetSession.messages : messages;

        // Ensure auditData has complete dialogue history with user messages
        if (
          !auditData ||
          !auditData.dialogue_history ||
          auditData.dialogue_history.length === 0 ||
          !auditData.dialogue_history.some((m: any) => m.sender === 'user')
        ) {
          const latencies = currentMsgs
            .map((m) => m.latency_ms || 0)
            .filter((lat) => lat > 0);
          const avgLat =
            latencies.length > 0
              ? Math.round(latencies.reduce((a, b) => a + b, 0) / latencies.length)
              : 0;

          auditData = {
            metadata: {
              session_id: sid,
              exported_at: new Date().toISOString(),
              exporter_role: 'admin',
              system_version: 'MediBot AI v2.2 - Multi-Modal Healthcare Agent',
              rag_engine: 'Dense Embedding MiniLM-L6-v2 (640 Q&A BYT Medical Protocol)',
              ner_model: 'PhoBERT-Medical-NER v1.0',
              llm_engine: 'Google Gemini 2.0 Flash',
              total_turns: currentMsgs.length,
              performance_metrics: {
                total_recorded_responses: latencies.length,
                avg_latency_ms: avgLat,
                min_latency_ms: latencies.length > 0 ? Math.min(...latencies) : 0,
                max_latency_ms: latencies.length > 0 ? Math.max(...latencies) : 0,
              },
            },
            dialogue_history: currentMsgs,
          };
        }

        const blob = new Blob([JSON.stringify(auditData, null, 2)], {
          type: 'application/json;charset=utf-8;',
        });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute(
          'download',
          `medibot_audit_${sid}_${new Date().toISOString().replace(/[:.]/g, '-')}.json`
        );
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
      } catch (err) {
        console.error('Lỗi khi xuất JSON hội thoại:', err);
      }
    },
    [sessionId, sessions, messages]
  );

  /** Chuyển đổi giữa câu trả lời chính và câu trả lời thay thế */
  const setActiveAnswerIndex = useCallback((messageId: string, index: number) => {
    setMessages((prev) =>
      prev.map((msg) =>
        msg.id === messageId
          ? { ...msg, active_answer_index: index }
          : msg
      )
    );
  }, []);

  /** Gửi feedback (like/dislike) về backend */
  const submitFeedback = useCallback(
    async (
      messageId: string,
      sessionId: string,
      rating: 'like' | 'dislike',
      reason?: string,
      answerIndex: number = 0,
      answerProvider?: string,
      messagePreview?: string
    ) => {
      const userId =
        typeof window !== 'undefined'
          ? JSON.parse(localStorage.getItem('medibot_auth_user') || '{}')?.id || 'anonymous'
          : 'anonymous';

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === messageId
            ? { ...msg, feedback: { rating, reason, answer_index: answerIndex } }
            : msg
        )
      );

      try {
        const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
        await fetch(`${API_BASE}/admin/feedback`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message_id: messageId,
            session_id: sessionId,
            user_id: userId,
            rating,
            reason: reason || null,
            answer_index: answerIndex,
            answer_provider: answerProvider || 'unknown',
            message_preview: messagePreview?.slice(0, 200) || '',
          }),
        });
      } catch (e) {
        console.warn('Failed to submit feedback:', e);
      }
    },
    []
  );

  return {
    sessions,
    sessionId,
    setSessionId,
    createNewSession,
    loadSession,
    deleteSession,
    messages,
    telemetry,
    isProcessing,
    isConnected,
    isEmergencyModalOpen,
    setIsEmergencyModalOpen,
    sendMessage,
    cancelQuery,
    setTelemetry,
    generateMedicalRecord,
    exportSessionAuditJson,
    setActiveAnswerIndex,
    submitFeedback,
  };

}

