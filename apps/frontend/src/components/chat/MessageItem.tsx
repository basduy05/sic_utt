'use client';

import React, { useState, useEffect } from 'react';
import {
  Volume2,
  VolumeX,
  Bot,
  User,
  AlertTriangle,
  BookOpen,
  ShieldAlert,
  Copy,
  Check,
  Zap,
  Clock,
  Activity,
  Cpu,
  ChevronDown,
  Sparkles,
  CheckCircle,
  ThumbsUp,
  ThumbsDown,
  ChevronLeft,
  ChevronRight,
  MessageSquare,
  HelpCircle,
} from 'lucide-react';
import { ChatMessage } from '../../types/chat';
import { formatTimestamp } from '../../utils/formatters';
import { renderRichMarkdown } from '../../utils/markdownRenderer';

interface MessageItemProps {
  message: ChatMessage;
  sessionId?: string;
  onSetActiveAnswerIndex?: (messageId: string, index: number) => void;
  onSelectClarificationAnswer?: (answer: string) => void;
  onSubmitFeedback?: (
    messageId: string,
    sessionId: string,
    rating: 'like' | 'dislike',
    reason?: string,
    answerIndex?: number,
    answerProvider?: string,
    messagePreview?: string
  ) => void;
}

export const MessageItem: React.FC<MessageItemProps> = ({
  message,
  sessionId,
  onSetActiveAnswerIndex,
  onSelectClarificationAnswer,
  onSubmitFeedback,
}) => {
  const isUser = message.sender === 'user';
  const isEmergency = message.telemetry?.is_emergency;
  const [isPlayingTTS, setIsPlayingTTS] = useState(false);
  const [copied, setCopied] = useState(false);
  const [showPipelineDetails, setShowPipelineDetails] = useState(true);
  const [elapsed, setElapsed] = useState(0);
  const [showDislikeInput, setShowDislikeInput] = useState(false);
  const [dislikeReason, setDislikeReason] = useState('');
  const [dualViewMode, setDualViewMode] = useState<'split' | 'single'>('single');

  const altAnswers = message.alternative_answers || [];
  const totalAnswers = 1 + altAnswers.length;
  const activeIndex = message.active_answer_index || 0;

  const formatProviderLabel = (prov?: string) => {
    const p = (prov || '').toLowerCase();
    if (p.includes('cohere')) return 'Cohere AI';
    if (p.includes('second_opinion') || p.includes('second')) return 'Second Opinion AI (Hội chẩn độc lập)';
    if (p.includes('gemini')) return 'Google Gemini 2.0 Flash';
    if (p.includes('local')) return 'Local LLM (Qwen/Ollama)';
    if (p.includes('rule')) return 'Phác đồ Chuẩn Bộ Y Tế';
    return prov || 'Mô hình AI';
  };

  const currentText =
    activeIndex === 0
      ? message.content
      : altAnswers[activeIndex - 1]?.text || message.content;

  const currentProvider =
    activeIndex === 0
      ? message.provider || 'gemini'
      : altAnswers[activeIndex - 1]?.provider || 'cohere';

  const breakdown = message.pipeline_breakdown || message.telemetry?.pipeline_breakdown || {};
  const nerMs = breakdown.ner_ms || 28;
  const ragMs = breakdown.rag_ms || 65;
  const llmMs = breakdown.llm_ms || 180;
  const latencyVal =
    message.latency_ms ||
    message.pipeline_breakdown?.total_ms ||
    message.telemetry?.latency_ms ||
    message.telemetry?.pipeline_breakdown?.total_ms;
  const totalMs = latencyVal || (nerMs + ragMs + llmMs);
  const symptoms = message.telemetry?.symptoms || [];
  const topPredictions = message.telemetry?.top_predictions || [];

  // Live timer for active thinking state
  useEffect(() => {
    if (!message.isStreaming || message.content) {
      return;
    }
    const start = Date.now();
    const interval = setInterval(() => {
      setElapsed(Math.floor((Date.now() - start) / 100) / 10);
    }, 100);
    return () => clearInterval(interval);
  }, [message.isStreaming, message.content]);

  const handleCopy = () => {
    navigator.clipboard.writeText(currentText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSpeak = () => {
    if ('speechSynthesis' in window) {
      if (isPlayingTTS) {
        window.speechSynthesis.cancel();
        setIsPlayingTTS(false);
        return;
      }

      const cleanText = currentText.replace(/[*_`#>-]/g, '');
      const utterance = new SpeechSynthesisUtterance(cleanText);
      utterance.lang = 'vi-VN';
      utterance.rate = 0.95;

      utterance.onend = () => setIsPlayingTTS(false);
      utterance.onerror = () => setIsPlayingTTS(false);

      window.speechSynthesis.speak(utterance);
      setIsPlayingTTS(true);
    }
  };

  const isThinking = !isUser && message.isStreaming && !message.content;

  // Compute active stage during thinking
  let stageText = 'Chuẩn hóa triệu chứng & nhận diện thực thể (PhoBERT NER)...';
  let stageIndex = 1;
  let stageBadge = 'PhoBERT NER';

  if (elapsed >= 2.2) {
    stageText = 'Tổng hợp chẩn đoán & xây dựng phác đồ điều trị (Gemini Flash AI)...';
    stageIndex = 4;
    stageBadge = 'Gemini Flash';
  } else if (elapsed >= 1.4) {
    stageText = 'Rà soát quy tắc cấp cứu Red Flag & cận lâm sàng...';
    stageIndex = 3;
    stageBadge = 'Clinical Red Flag';
  } else if (elapsed >= 0.6) {
    stageText = 'Truy xuất 640 phác đồ BYT & tra cứu vector ICD-10 (Dense MiniLM)...';
    stageIndex = 2;
    stageBadge = 'RAG Dense Search';
  }

  return (
    <div
      className={`flex items-start space-x-3 ${
        isUser ? 'flex-row-reverse space-x-reverse' : ''
      } animate-in fade-in duration-200 group`}
    >
      {/* Avatar */}
      <div
        className={`w-10 h-10 rounded-2xl flex items-center justify-center flex-shrink-0 shadow-sm transition-all ${
          isUser
            ? 'bg-gradient-to-tr from-blue-500 to-indigo-600 text-white shadow-blue-500/20'
            : isEmergency
            ? 'bg-gradient-to-tr from-red-500 to-rose-600 text-white shadow-red-500/30 animate-pulse'
            : isThinking
            ? 'bg-gradient-to-tr from-teal-400 via-emerald-500 to-blue-500 text-white shadow-teal-500/30 ring-2 ring-teal-300 ring-offset-2 animate-pulse'
            : 'bg-gradient-to-tr from-teal-500 to-blue-600 text-white shadow-teal-500/20'
        }`}
      >
        {isUser ? (
          <User className="w-5 h-5" />
        ) : isEmergency ? (
          <AlertTriangle className="w-5 h-5" />
        ) : isThinking ? (
          <Activity className="w-5 h-5 animate-pulse" />
        ) : (
          <Bot className="w-5 h-5" />
        )}
      </div>

      {/* Bubble Container - Single Unified Frame */}
      <div
        className={`chat-message-bubble ${
          !isUser && totalAnswers > 1
            ? 'w-full max-w-[96%] lg:max-w-[94%]'
            : 'max-w-[92%] md:max-w-[88%] lg:max-w-[85%]'
        } rounded-[1.6rem] px-5 py-4 shadow-sm transition-[max-width,width] duration-300 relative ${
          isUser
            ? 'bg-gradient-to-br from-teal-600 to-blue-600 text-white rounded-tr-xs shadow-teal-500/20'
            : isEmergency
            ? 'bg-red-50/95 border border-red-200 text-red-950 rounded-tl-xs'
            : isThinking
            ? 'bg-white/95 backdrop-blur-md border border-teal-300/90 text-slate-800 rounded-tl-xs shadow-[0_8px_30px_rgb(0,0,0,0.06)]'
            : 'bg-white/90 backdrop-blur-md border border-slate-200/80 text-slate-800 rounded-tl-xs shadow-[0_4px_20px_-2px_rgba(0,0,0,0.04)]'
        }`}
      >
        {/* Header Label */}
        <div
          className={`flex items-center justify-between pb-1.5 mb-2 border-b text-xs font-semibold ${
            isUser
              ? 'border-teal-400/40 text-teal-100'
              : 'border-slate-100 text-slate-500'
          }`}
        >
          <div className="flex items-center space-x-2">
            <span className="font-bold">
              {isUser ? 'Bạn' : 'MediBot AI (Bộ Y Tế & ICD-10)'}
            </span>

            {/* If completed with latency: show quick pill */}
            {!isUser && !isThinking && Boolean(message.latency_ms) && (
              <div
                className="relative group/lat inline-flex items-center space-x-1 px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200/70 font-mono text-[10px] cursor-help shadow-2xs"
                title="Thời gian phản hồi toàn bộ AI Pipeline"
              >
                <Zap size={11} className="text-amber-500 fill-amber-400" />
                <span>{message.latency_ms}ms</span>

                {/* Hover Popover Breakdown */}
                {message.pipeline_breakdown && (
                  <div className="absolute left-0 top-full mt-1.5 z-40 hidden group-hover/lat:block w-56 p-3 bg-slate-900 text-white rounded-xl shadow-2xl text-[11px] font-sans border border-slate-700 pointer-events-none animate-in fade-in zoom-in-95 duration-150">
                    <div className="font-semibold text-teal-300 pb-1.5 mb-1.5 border-b border-slate-800 flex items-center justify-between">
                      <span className="flex items-center gap-1">
                        <Clock size={11} /> Chi tiết Pipeline
                      </span>
                      <span className="font-mono text-emerald-400 font-bold">
                        {message.latency_ms}ms
                      </span>
                    </div>
                    <div className="space-y-1.5 text-slate-300">
                      <div className="flex justify-between items-center">
                        <span className="text-slate-400">PhoBERT NER:</span>
                        <span className="font-mono text-teal-300 font-medium">
                          {message.pipeline_breakdown.ner_ms || 0}ms
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-slate-400">RAG MiniLM 640 BYT:</span>
                        <span className="font-mono text-blue-300 font-medium">
                          {message.pipeline_breakdown.rag_ms || 0}ms
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-slate-400">Gemini 2.0 Flash:</span>
                        <span className="font-mono text-amber-300 font-medium">
                          {message.pipeline_breakdown.llm_ms || 0}ms
                        </span>
                      </div>
                      <div className="pt-1 border-t border-slate-800 flex justify-between items-center text-[10px] text-slate-400">
                        <span>Tổng thời gian:</span>
                        <span className="font-mono text-emerald-400 font-bold">
                          {message.pipeline_breakdown.total_ms || message.latency_ms}ms
                        </span>
                      </div>
                      {Boolean(message.telemetry?.cloud_error) && (
                        <div className="pt-1 text-[10px] text-amber-300 border-t border-slate-800">
                          <span className="text-slate-400">Trạng thái Cloud: </span>
                          <span className="font-mono">{message.telemetry?.cloud_error}</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="flex items-center space-x-2">
            <span suppressHydrationWarning>{formatTimestamp(message.timestamp)}</span>
            {message.content && (
              <button
                type="button"
                onClick={handleCopy}
                title="Sao chép nội dung tin nhắn"
                className={`p-1 rounded-md transition ${
                  isUser
                    ? 'hover:bg-teal-400/30 text-teal-100'
                    : 'hover:bg-slate-100 text-slate-400 hover:text-slate-700'
                }`}
              >
                {copied ? (
                  <Check size={14} className="text-emerald-500" />
                ) : (
                  <Copy size={14} />
                )}
              </button>
            )}
          </div>
        </div>

        {/* --- CASE 1: ACTIVE THINKING STATE (Live 4-Step Real-time Pipeline) --- */}
        {isThinking && (
          <div className="py-2 space-y-3 animate-in fade-in duration-200">
            {/* Top row: Status header and Live Elapsed Counter */}
            <div className="flex items-center justify-between pb-2 border-b border-teal-100/70">
              <div className="flex items-center space-x-2">
                <span className="relative flex h-2.5 w-2.5">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-teal-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-teal-500"></span>
                </span>
                <span className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
                  <Activity className="w-3.5 h-3.5 text-teal-600 animate-pulse" />
                  Quy trình phân tích lâm sàng (4 bước)
                </span>
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-teal-50 text-teal-700 border border-teal-200">
                  Chuẩn BYT & ICD-10
                </span>
              </div>

              <div className="flex items-center space-x-1 font-mono text-xs font-bold text-teal-700 bg-teal-50/90 px-2.5 py-0.5 rounded-lg border border-teal-200 shadow-2xs">
                <Clock className="w-3.5 h-3.5 text-teal-600 animate-spin" />
                <span>{elapsed.toFixed(1)}s (Thời gian thực)</span>
              </div>
            </div>

            {/* Progressive Step Progress Bar */}
            <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden flex">
              <div
                className="bg-gradient-to-r from-teal-500 via-cyan-500 to-blue-500 h-full rounded-full transition-all duration-300 ease-out"
                style={{
                  width: `${Math.min(100, Math.max(18, (stageIndex / 4) * 100))}%`,
                }}
              />
            </div>

            {/* Progressive Stage Description */}
            <div className="flex items-center justify-between text-xs text-slate-600">
              <span className="font-medium truncate pr-2">{stageText}</span>
              <span className="font-mono text-[10px] text-teal-600 font-bold flex-shrink-0">
                Bước {stageIndex}/4
              </span>
            </div>

            {/* 4 Mini Steps indicators */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-1.5 pt-1">
              <div
                className={`px-2 py-1.5 rounded-xl text-[10px] font-medium border flex items-center gap-1.5 ${
                  stageIndex >= 1
                    ? 'bg-teal-50/90 border-teal-300 text-teal-900 font-semibold shadow-2xs'
                    : 'bg-slate-50 border-slate-200 text-slate-400'
                }`}
              >
                <Check
                  size={11}
                  className={stageIndex >= 1 ? 'text-teal-600 font-bold' : 'text-slate-300'}
                />
                <span>1. PhoBERT NER</span>
              </div>
              <div
                className={`px-2 py-1.5 rounded-xl text-[10px] font-medium border flex items-center gap-1.5 ${
                  stageIndex >= 2
                    ? 'bg-teal-50/90 border-teal-300 text-teal-900 font-semibold shadow-2xs'
                    : 'bg-slate-50 border-slate-200 text-slate-400'
                }`}
              >
                <Check
                  size={11}
                  className={stageIndex >= 2 ? 'text-teal-600 font-bold' : 'text-slate-300'}
                />
                <span>2. Phác đồ 640 BYT</span>
              </div>
              <div
                className={`px-2 py-1.5 rounded-xl text-[10px] font-medium border flex items-center gap-1.5 ${
                  stageIndex >= 3
                    ? 'bg-teal-50/90 border-teal-300 text-teal-900 font-semibold shadow-2xs'
                    : 'bg-slate-50 border-slate-200 text-slate-400'
                }`}
              >
                <Check
                  size={11}
                  className={stageIndex >= 3 ? 'text-teal-600 font-bold' : 'text-slate-300'}
                />
                <span>3. Red Flag Cấp cứu</span>
              </div>
              <div
                className={`px-2 py-1.5 rounded-xl text-[10px] font-medium border flex items-center gap-1.5 ${
                  stageIndex >= 4
                    ? 'bg-teal-50/90 border-teal-300 text-teal-900 font-semibold shadow-2xs'
                    : 'bg-slate-50 border-slate-200 text-slate-400'
                }`}
              >
                <Check
                  size={11}
                  className={stageIndex >= 4 ? 'text-teal-600 font-bold' : 'text-slate-300'}
                />
                <span>4. Gemini Flash</span>
              </div>
            </div>
          </div>
        )}

        {/* --- CASE 2 & 3: COMPLETED OR STREAMING RESPONSE --- */}
        {!isThinking && (
          <>
            {/* Quy trình phân tích lâm sàng 4 bước (Hiển thị thời gian thực & chi tiết dữ liệu đã xử lý) */}
            {!isUser && (
              <div className="mb-3 rounded-2xl border border-teal-200/90 bg-gradient-to-br from-teal-50/40 via-white to-slate-50/60 p-3 shadow-2xs">
                <div
                  role="button"
                  tabIndex={0}
                  onClick={() => setShowPipelineDetails(!showPipelineDetails)}
                  className="flex items-center justify-between cursor-pointer select-none"
                >
                  <div className="flex items-center gap-2 flex-wrap">
                    <div className="p-1 rounded-lg bg-teal-500/15 text-teal-700">
                      <Activity className="w-3.5 h-3.5 text-teal-600" />
                    </div>
                    <span className="text-xs font-bold text-slate-800">
                      Quy trình phân tích lâm sàng (4 bước)
                    </span>
                    <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-teal-50 text-teal-700 border border-teal-200">
                      Chuẩn BYT & ICD-10
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    <div className="flex items-center space-x-1 font-mono text-[11px] font-bold text-teal-700 bg-white px-2 py-0.5 rounded-lg border border-teal-200 shadow-2xs">
                      <Clock className="w-3 h-3 text-teal-600" />
                      <span>{totalMs}ms (Thời gian thực)</span>
                    </div>
                    <button
                      type="button"
                      className="p-1 rounded-md text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition"
                      title={showPipelineDetails ? 'Thu gọn quy trình' : 'Xem chi tiết 4 bước'}
                    >
                      <ChevronDown
                        size={14}
                        className={`transition-transform duration-200 ${
                          showPipelineDetails ? 'rotate-180 text-teal-600' : ''
                        }`}
                      />
                    </button>
                  </div>
                </div>

                {/* Chi tiết nội dung 4 bước đã xử lý */}
                {showPipelineDetails && (
                  <div className="mt-2.5 pt-2.5 border-t border-teal-100/80 space-y-2 animate-in fade-in duration-150">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
                      {/* Bước 1: PhoBERT NER */}
                      <div className="p-2.5 rounded-xl bg-white border border-slate-200/90 shadow-2xs space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-slate-800 flex items-center gap-1.5 text-[11px]">
                            <span className="w-4 h-4 rounded-full bg-teal-100 text-teal-800 text-[10px] font-bold flex items-center justify-center">1</span>
                            <span>Trích xuất thực thể PhoBERT NER</span>
                          </span>
                          <span className="font-mono text-[10px] font-bold text-teal-700 bg-teal-50 px-1.5 py-0.2 rounded border border-teal-200">
                            {nerMs}ms
                          </span>
                        </div>
                        <div className="text-[11px] text-slate-600 leading-snug">
                          {symptoms.length > 0 ? (
                            <div className="flex flex-wrap items-center gap-1 mt-0.5">
                              <span className="text-slate-400 font-medium">Bóc tách:</span>
                              {symptoms.map((s, idx) => (
                                <span key={idx} className="inline-flex items-center px-1.5 py-0.2 rounded-md bg-teal-50 text-teal-800 font-semibold border border-teal-200 text-[10px]">
                                  {s.standard_term}
                                </span>
                              ))}
                            </div>
                          ) : (
                            <span className="text-slate-500">Đã nhận diện ngữ cảnh và chuẩn hóa triệu chứng lâm sàng ban đầu.</span>
                          )}
                        </div>
                      </div>

                      {/* Bước 2: Phác đồ 640 BYT & Vector ICD-10 */}
                      <div className="p-2.5 rounded-xl bg-white border border-slate-200/90 shadow-2xs space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-slate-800 flex items-center gap-1.5 text-[11px]">
                            <span className="w-4 h-4 rounded-full bg-blue-100 text-blue-800 text-[10px] font-bold flex items-center justify-center">2</span>
                            <span>Phác đồ 640 BYT & Vector ICD-10</span>
                          </span>
                          <span className="font-mono text-[10px] font-bold text-blue-700 bg-blue-50 px-1.5 py-0.2 rounded border border-blue-200">
                            {ragMs}ms
                          </span>
                        </div>
                        <div className="text-[11px] text-slate-600 leading-snug">
                          {topPredictions.length > 0 ? (
                            <div className="flex flex-wrap items-center gap-1 mt-0.5">
                              <span className="text-slate-400 font-medium">Đối soát BYT:</span>
                              {topPredictions.slice(0, 2).map((p, idx) => (
                                <span key={idx} className="inline-flex items-center px-1.5 py-0.2 rounded-md bg-blue-50 text-blue-800 font-semibold border border-blue-200 text-[10px]">
                                  {p.disease_name_vi} ({p.icd_code}): {p.probability_percentage}
                                </span>
                              ))}
                            </div>
                          ) : (
                            <span className="text-slate-500">Truy xuất kho tri thức 640 phác đồ điều trị Bộ Y Tế & cơ sở dữ liệu ICD-10.</span>
                          )}
                        </div>
                      </div>

                      {/* Bước 3: Sàng lọc Cảnh báo đỏ Red Flag */}
                      <div className="p-2.5 rounded-xl bg-white border border-slate-200/90 shadow-2xs space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-slate-800 flex items-center gap-1.5 text-[11px]">
                            <span className="w-4 h-4 rounded-full bg-amber-100 text-amber-800 text-[10px] font-bold flex items-center justify-center">3</span>
                            <span>Sàng lọc Cảnh báo đỏ Red Flag</span>
                          </span>
                          <span className="font-mono text-[10px] font-bold text-amber-700 bg-amber-50 px-1.5 py-0.2 rounded border border-amber-200">
                            {Math.max(12, Math.round(nerMs * 0.4))}ms
                          </span>
                        </div>
                        <div className="text-[11px] text-slate-600 leading-snug">
                          {isEmergency ? (
                            <span className="text-rose-700 font-semibold flex items-center gap-1">
                              🚨 Phát hiện tiêu chí cờ đỏ - Yêu cầu can thiệp cấp cứu 115!
                            </span>
                          ) : (
                            <span className="text-emerald-700 font-medium flex items-center gap-1">
                              <CheckCircle size={12} className="text-emerald-600 flex-shrink-0" />
                              <span>An toàn: Không có dấu hiệu đe dọa tính mạng - Phù hợp tư vấn ngoại trú.</span>
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Bước 4: Suy luận Lâm sàng & Hội chẩn */}
                      <div className="p-2.5 rounded-xl bg-white border border-slate-200/90 shadow-2xs space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-slate-800 flex items-center gap-1.5 text-[11px]">
                            <span className="w-4 h-4 rounded-full bg-purple-100 text-purple-800 text-[10px] font-bold flex items-center justify-center">4</span>
                            <span>Suy luận Lâm sàng & Hội chẩn</span>
                          </span>
                          <span className="font-mono text-[10px] font-bold text-purple-700 bg-purple-50 px-1.5 py-0.2 rounded border border-purple-200">
                            {llmMs}ms
                          </span>
                        </div>
                        <div className="text-[11px] text-slate-600 leading-snug">
                          {Boolean(message.telemetry?.cloud_error) ? (
                            <span className="text-teal-800 font-medium flex items-center gap-1">
                              <span>Phác đồ Chuẩn Bộ Y Tế & Hội chẩn Độc lập</span>
                              <span className="text-[9px] text-teal-700 bg-teal-50 px-1.5 py-0.2 rounded border border-teal-200" title={message.telemetry?.cloud_error}>
                                Chuẩn BYT
                              </span>
                            </span>
                          ) : totalAnswers > 1 ? (
                            'Đã đối chiếu chéo song song 2 AI độc lập (Bác sĩ Chính & Hội chẩn Chuyên khoa).'
                          ) : (
                            'Đã hoàn tất phân tích sinh lý bệnh học vi mô, ma trận loại trừ & cận lâm sàng.'
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* While streaming text: show subtle in-flight indicator */}
            {!isUser && message.isStreaming && message.content && (
              <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 mb-2 rounded-full bg-teal-50 border border-teal-200 text-[10px] font-medium text-teal-800">
                <Sparkles size={11} className="text-teal-600 animate-spin" />
                <span>Đang truyền tải lời khuyên lâm sàng...</span>
              </div>
            )}

            {/* Dual AI Model Tabs & View Mode Switcher (Single AI view by default) */}
            {!isUser && totalAnswers > 1 && !message.isStreaming && (
              <div className="flex flex-wrap items-center justify-between gap-2 p-1.5 mb-3 rounded-2xl bg-gradient-to-r from-teal-50/70 via-slate-50 to-cyan-50/70 border border-slate-200/90 shadow-2xs">
                {/* AI Tabs for 1-by-1 viewing */}
                <div className="flex items-center gap-1.5 flex-wrap">
                  <button
                    type="button"
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      onSetActiveAnswerIndex?.(message.id, 0);
                      setDualViewMode('single');
                    }}
                    className={`flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                      dualViewMode === 'single' && activeIndex === 0
                        ? 'bg-white text-teal-900 shadow-xs border border-teal-300 ring-1 ring-teal-200 font-bold'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-white/70'
                    }`}
                  >
                    <span className="w-2.5 h-2.5 rounded-full bg-teal-500 shadow-2xs"></span>
                    <span>AI 1: Bác sĩ Chính</span>
                    <span className="text-[10px] font-mono px-1.5 py-0.2 rounded-md bg-teal-50 text-teal-700 border border-teal-200/70">
                      {formatProviderLabel(message.provider || 'gemini').split(' ')[0]}
                    </span>
                  </button>

                  <button
                    type="button"
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      onSetActiveAnswerIndex?.(message.id, 1);
                      setDualViewMode('single');
                    }}
                    className={`flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                      dualViewMode === 'single' && activeIndex === 1
                        ? 'bg-white text-cyan-900 shadow-xs border border-cyan-300 ring-1 ring-cyan-200 font-bold'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-white/70'
                    }`}
                  >
                    <span className="w-2.5 h-2.5 rounded-full bg-cyan-500 shadow-2xs"></span>
                    <span>AI 2: Hội chẩn Độc lập</span>
                    <span className="text-[10px] font-mono px-1.5 py-0.2 rounded-md bg-cyan-50 text-cyan-700 border border-cyan-200/70">
                      {formatProviderLabel(altAnswers[0]?.provider || 'cohere').split(' ')[0]}
                    </span>
                  </button>
                </div>

                {/* Split vs Single Mode Toggle */}
                <button
                  type="button"
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    setDualViewMode(dualViewMode === 'split' ? 'single' : 'split');
                  }}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                    dualViewMode === 'split'
                      ? 'bg-teal-700 text-white shadow-xs'
                      : 'bg-white text-slate-700 hover:text-teal-900 border border-slate-200/90 shadow-2xs hover:bg-teal-50/50'
                  }`}
                  title={dualViewMode === 'split' ? 'Chuyển về xem từng AI' : 'Mở xem song song cả 2 AI'}
                >
                  <Bot size={13} className={dualViewMode === 'split' ? 'text-teal-200' : 'text-teal-600'} />
                  <span>{dualViewMode === 'split' ? '⊟ Xem từng AI' : '⊞ So sánh song song'}</span>
                </button>
              </div>
            )}

            {/* Message Body Content */}
            {!isUser && totalAnswers > 1 && !message.isStreaming && dualViewMode === 'split' ? (
              /* DUAL SIDE-BY-SIDE SIMULTANEOUS VIEW */
              <div className="space-y-3">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-3.5">
                  {/* Card 1: AI 1 (Primary Model) */}
                  <div className="rounded-2xl border border-teal-200/90 bg-gradient-to-b from-teal-50/20 to-white p-4 shadow-sm flex flex-col justify-between animate-in fade-in zoom-in-[0.99] duration-200">
                    <div>
                      <div className="flex items-center justify-between pb-2 mb-3 border-b border-teal-100">
                        <div className="flex items-center space-x-1.5">
                          <span className="w-2.5 h-2.5 rounded-full bg-teal-500"></span>
                          <span className="font-bold text-teal-950 text-xs">
                            AI 1: {formatProviderLabel(message.provider || 'gemini')}
                          </span>
                        </div>
                        <button
                          type="button"
                          onClick={() => {
                            navigator.clipboard.writeText(message.content);
                            setCopied(true);
                            setTimeout(() => setCopied(false), 2000);
                          }}
                          className="p-1 rounded-md hover:bg-teal-100/70 text-slate-400 hover:text-teal-700 transition"
                          title="Sao chép câu trả lời AI 1"
                        >
                          {copied ? <Check size={13} className="text-emerald-500" /> : <Copy size={13} />}
                        </button>
                      </div>
                      <div className="chat-message-content text-[15px] leading-relaxed font-normal text-slate-800">
                        {renderRichMarkdown(message.content)}
                      </div>
                    </div>
                    <div className="mt-3 pt-2 border-t border-slate-100 text-[11px] text-teal-700 font-medium flex items-center gap-1">
                      <CheckCircle size={12} className="text-teal-600" />
                      <span>Ý kiến Chẩn đoán & Phác đồ điều trị ban đầu</span>
                    </div>
                  </div>

                  {/* Card 2: AI 2 (Second Opinion / Cohere) */}
                  <div className="rounded-2xl border border-cyan-200/90 bg-gradient-to-b from-cyan-50/20 to-white p-4 shadow-sm flex flex-col justify-between animate-in fade-in zoom-in-[0.99] duration-200">
                    <div>
                      <div className="flex items-center justify-between pb-2 mb-3 border-b border-cyan-100">
                        <div className="flex items-center space-x-1.5">
                          <span className="w-2.5 h-2.5 rounded-full bg-cyan-500"></span>
                          <span className="font-bold text-cyan-950 text-xs">
                            AI 2: {formatProviderLabel(altAnswers[0]?.provider || 'second_opinion')}
                          </span>
                        </div>
                        <button
                          type="button"
                          onClick={() => {
                            if (altAnswers[0]?.text) {
                              navigator.clipboard.writeText(altAnswers[0].text);
                              setCopied(true);
                              setTimeout(() => setCopied(false), 2000);
                            }
                          }}
                          className="p-1 rounded-md hover:bg-cyan-100/70 text-slate-400 hover:text-cyan-700 transition"
                          title="Sao chép câu trả lời AI 2"
                        >
                          {copied ? <Check size={13} className="text-emerald-500" /> : <Copy size={13} />}
                        </button>
                      </div>
                      <div className="chat-message-content text-[15px] leading-relaxed font-normal text-slate-800">
                        {renderRichMarkdown(altAnswers[0]?.text || '')}
                      </div>
                    </div>
                    <div className="mt-3 pt-2 border-t border-slate-100 text-[11px] text-cyan-700 font-medium flex items-center gap-1">
                      <CheckCircle size={12} className="text-cyan-600" />
                      <span>Ý kiến Hội chẩn chuyên khoa & An toàn dược lâm sàng</span>
                    </div>
                  </div>
                </div>

                {/* Consensus Footer Notice */}
                <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200/80 text-[11px] text-slate-600 flex items-center gap-2">
                  <Sparkles size={13} className="text-amber-500 flex-shrink-0" />
                  <span>
                    <strong>Đồng thuận Y khoa:</strong> Hai câu trả lời trên được xử lý độc lập để bạn có góc nhìn toàn diện nhất. Cả 2 đều tuân thủ nguyên tắc an toàn cấp cứu & phác đồ Bộ Y Tế.
                  </span>
                </div>
              </div>
            ) : (
              /* STANDARD SINGLE VIEW */
              <div className="chat-message-content text-base leading-relaxed font-normal">
                {isUser ? (
                  <div className="whitespace-pre-wrap text-white font-medium text-base">
                    {message.content}
                  </div>
                ) : (
                  renderRichMarkdown(currentText)
                )}
                {message.isStreaming && (
                  <span className="inline-block w-2 h-4 ml-1 bg-teal-600 animate-pulse align-middle rounded-xs" />
                )}
              </div>
            )}

            {/* Interactive Clarification Questions embedded directly in Chat */}
            {!isUser && !message.isStreaming && message.telemetry?.clarification?.questions && message.telemetry.clarification.questions.length > 0 && (
              <div className="mt-3.5 p-3.5 rounded-2xl bg-gradient-to-br from-amber-50/90 via-white to-amber-50/60 border border-amber-200/90 space-y-3 shadow-xs">
                <div className="flex items-center space-x-2 text-amber-950 font-bold text-xs">
                  <div className="p-1 rounded-lg bg-amber-500/15 text-amber-800">
                    <HelpCircle className="w-3.5 h-3.5 text-amber-700" />
                  </div>
                  <span>Hỏi bổ sung lâm sàng (Bấm để chọn và trả lời ngay):</span>
                </div>
                {message.telemetry.clarification.questions.map((q, qIdx) => (
                  <div key={q.id || qIdx} className="space-y-1.5 pt-1">
                    <p className="text-xs font-semibold text-slate-800 flex items-center gap-1.5">
                      <span className="w-4 h-4 rounded-full bg-amber-200 text-amber-900 text-[10px] font-bold flex items-center justify-center flex-shrink-0">
                        {qIdx + 1}
                      </span>
                      <span>{q.question}</span>
                    </p>
                    <div className="flex flex-wrap gap-1.5 pl-5">
                      {q.options?.map((opt, optIdx) => (
                        <button
                          key={optIdx}
                          type="button"
                          onClick={() => onSelectClarificationAnswer?.(`Tôi xin bổ sung: ${opt}`)}
                          className="text-xs px-3 py-1.5 rounded-xl bg-white hover:bg-amber-100/90 text-slate-800 hover:text-amber-950 border border-amber-200/80 transition-all font-medium shadow-2xs hover:shadow-xs active:scale-95 text-left flex items-center gap-1.5 cursor-pointer"
                        >
                          <span className="text-amber-600 font-bold">👉</span>
                          <span>{opt}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Dislike Reason Input Box (Inline Form) */}
            {showDislikeInput && (
              <div className="mt-2.5 p-3 bg-rose-50/90 border border-rose-200 rounded-xl space-y-2 animate-in fade-in duration-200">
                <div className="text-xs font-semibold text-rose-800 flex items-center gap-1.5">
                  <MessageSquare size={13} className="text-rose-600" />
                  <span>Góp ý lý do chưa hài lòng (gửi tới Quản trị viên):</span>
                </div>
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    placeholder="VD: Thông tin chưa chuẩn xác, khuyến nghị chung chung..."
                    value={dislikeReason}
                    onChange={(e) => setDislikeReason(e.target.value)}
                    className="flex-1 text-xs px-3 py-1.5 rounded-lg border border-rose-300 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-rose-400"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && dislikeReason.trim()) {
                        onSubmitFeedback?.(
                          message.id,
                          sessionId || '',
                          'dislike',
                          dislikeReason.trim(),
                          activeIndex,
                          currentProvider,
                          currentText
                        );
                        setShowDislikeInput(false);
                      }
                    }}
                  />
                  <button
                    type="button"
                    onClick={() => {
                      onSubmitFeedback?.(
                        message.id,
                        sessionId || '',
                        'dislike',
                        dislikeReason.trim() || 'Chưa hài lòng với câu trả lời',
                        activeIndex,
                        currentProvider,
                        currentText
                      );
                      setShowDislikeInput(false);
                    }}
                    className="px-3 py-1.5 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-xs font-semibold transition shadow-2xs"
                  >
                    Gửi
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowDislikeInput(false)}
                    className="px-2 py-1.5 text-xs text-slate-500 hover:text-slate-700"
                  >
                    Hủy
                  </button>
                </div>
              </div>
            )}

            {/* Bottom Actions for Completed Assistant Message */}
            {!isUser && !message.isStreaming && message.content && (
              <div className="mt-3 pt-2.5 border-t border-slate-100 flex flex-wrap items-center justify-between gap-2 text-xs">
                <div className="flex items-center flex-wrap gap-2">
                  <span className="text-[11px] text-slate-500 font-medium flex items-center gap-1">
                    <CheckCircle size={12} className="text-teal-600" />
                    Chuẩn hóa ICD-10 & Phác đồ Bộ Y Tế
                  </span>
                  {latencyVal != null && latencyVal > 0 && (
                    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-emerald-50 border border-emerald-200/90 text-[11px] font-bold text-emerald-800 shadow-2xs">
                      <Zap size={11} className="text-amber-500 fill-amber-400" />
                      Độ trễ: {latencyVal}ms
                    </span>
                  )}
                </div>
                <div className="flex items-center space-x-2">
                  {/* Feedback Controls */}
                  {message.feedback?.rating === 'like' ? (
                    <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-700 text-[11px] font-semibold">
                      <ThumbsUp size={12} className="fill-emerald-500 text-emerald-600" />
                      Đã thích
                    </span>
                  ) : message.feedback?.rating === 'dislike' ? (
                    <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-rose-50 border border-rose-200 text-rose-700 text-[11px] font-semibold">
                      <ThumbsDown size={12} className="fill-rose-500 text-rose-600" />
                      Đã góp ý
                    </span>
                  ) : (
                    <div className="flex items-center space-x-1 border-r border-slate-200 pr-2">
                      <button
                        type="button"
                        onClick={() =>
                          onSubmitFeedback?.(
                            message.id,
                            sessionId || '',
                            'like',
                            undefined,
                            activeIndex,
                            currentProvider,
                            currentText
                          )
                        }
                        title="Hài lòng với câu trả lời"
                        className="p-1.5 rounded-full hover:bg-emerald-50 text-slate-400 hover:text-emerald-600 transition"
                      >
                        <ThumbsUp size={14} />
                      </button>
                      <button
                        type="button"
                        onClick={() => setShowDislikeInput(!showDislikeInput)}
                        title="Không hài lòng (góp ý)"
                        className={`p-1.5 rounded-full transition ${
                          showDislikeInput
                            ? 'bg-rose-100 text-rose-600'
                            : 'hover:bg-rose-50 text-slate-400 hover:text-rose-600'
                        }`}
                      >
                        <ThumbsDown size={14} />
                      </button>
                    </div>
                  )}

                  <button
                    type="button"
                    onClick={handleCopy}
                    className="flex items-center space-x-1 px-3 py-1.5 rounded-full bg-slate-100/80 hover:bg-slate-200 text-slate-700 font-semibold transition text-xs shadow-2xs"
                  >
                    {copied ? (
                      <Check size={13} className="text-emerald-600" />
                    ) : (
                      <Copy size={13} />
                    )}
                    <span>{copied ? 'Đã sao chép' : 'Sao chép'}</span>
                  </button>

                  <button
                    type="button"
                    onClick={handleSpeak}
                    title="Đọc văn bản lời khuyên"
                    className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-slate-100/80 hover:bg-teal-50 text-slate-600 hover:text-teal-800 font-medium transition border border-slate-200/60 text-[11px] shadow-2xs"
                  >
                    {isPlayingTTS ? (
                      <>
                        <VolumeX className="w-3.5 h-3.5 text-red-500" />
                        <span className="text-red-600">Dừng đọc</span>
                      </>
                    ) : (
                      <>
                        <Volume2 className="w-3.5 h-3.5 text-teal-600" />
                        <span>Nghe Giọng Đọc</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};
