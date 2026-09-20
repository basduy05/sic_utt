'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Send, Mic, Paperclip, Loader2, Sparkles, Info, X, Square } from 'lucide-react';
import { ChatMessage } from '../../types/chat';
import { MessageItem } from './MessageItem';
import { VoiceRecorder } from './VoiceRecorder';
import { FileUploader } from './FileUploader';
import { OCRResult } from '../../types/medical';

interface ChatBoxProps {
  messages: ChatMessage[];
  isProcessing: boolean;
  onSendMessage: (text: string) => void;
  onCancelQuery?: () => void;
  onOCRComplete: (ocrResult: OCRResult, fileName: string) => void;
  sessionId?: string;
  onSetActiveAnswerIndex?: (messageId: string, index: number) => void;
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

const QUICK_PROMPTS = [
  { label: '🔥 Sốt cao & Chảy máu răng', prompt: 'Tôi bị sốt cao 39 độ 2 ngày nay, đau nhức hốc mắt và bị chảy máu chân răng', color: 'text-amber-800 bg-amber-50 hover:bg-amber-100 border-amber-200' },
  { label: '🌸 Da mặt bị rát và đỏ ửng', prompt: 'Da mặt tôi bị rát và đỏ ửng, cảm giác châm chích ngứa ngáy khó chịu', color: 'text-pink-800 bg-pink-50 hover:bg-pink-100 border-pink-200' },
  { label: '💔 Đau thắt ngực & Khó thở', prompt: 'Tôi bị đau thắt ngực trái dữ dội lan ra sau lưng và cánh tay, kèm vã mồ hôi và khó thở', color: 'text-rose-800 bg-rose-50 hover:bg-rose-100 border-rose-200' },
  { label: '⚡ Méo miệng FAST Đột quỵ', prompt: 'Người nhà tôi đột nhiên bị méo một bên miệng, nói ngọng và yếu liệt tay chân một bên', color: 'text-purple-800 bg-purple-50 hover:bg-purple-100 border-purple-200' },
  { label: '🤢 Đau quặn bụng thượng vị', prompt: 'Tôi bị đau quặn bụng cồn cào trên rốn sau khi ăn kèm buồn nôn và ợ chua', color: 'text-teal-800 bg-teal-50 hover:bg-teal-100 border-teal-200' },
];

const AUTOCOMPLETE_SYMPTOMS = [
  'Sốt cao 39 độ', 'Sốt rét run', 'Đau đầu dữ dội', 'Đau nửa đầu',
  'Đau thắt ngực', 'Khó thở thở dốc', 'Đau quặn bụng thượng vị',
  'Buồn nôn và nôn ói', 'Tiêu chảy đi ngoài phân lỏng', 'Chảy máu chân răng',
  'Méo miệng yếu liệt nửa người', 'Chóng mặt hoa mắt', 'Da mặt bị rát và đỏ ửng'
];

export const ChatBox: React.FC<ChatBoxProps> = ({
  messages,
  isProcessing,
  onSendMessage,
  onCancelQuery,
  onOCRComplete,
  sessionId,
  onSetActiveAnswerIndex,
  onSubmitFeedback,
}) => {
  const [inputText, setInputText] = useState<string>('');
  const [showVoiceRecorder, setShowVoiceRecorder] = useState<boolean>(false);
  const [showFileUploader, setShowFileUploader] = useState<boolean>(false);
  const [matchingSuggestions, setMatchingSuggestions] = useState<string[]>([]);

  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const prevMsgCountRef = useRef<number>(messages.length);
  const isUserScrolledUpRef = useRef<boolean>(false);

  // Monitor user manual scroll to avoid hijacking scroll when reading previous content
  const handleScroll = () => {
    if (!scrollContainerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = scrollContainerRef.current;
    // If distance from bottom is greater than 100px, user intentionally scrolled up
    isUserScrolledUpRef.current = scrollHeight - scrollTop - clientHeight > 100;
  };

  // Smart Auto-scroll: Only scroll if new message arrived or actively streaming, NOT on tab/answer switches!
  useEffect(() => {
    if (!scrollContainerRef.current) return;

    const hasNewMessage = messages.length > prevMsgCountRef.current;
    prevMsgCountRef.current = messages.length;

    const isStreaming = messages.some((m) => m.isStreaming);

    // If user clicked tab to switch answer or toggled view without adding new messages, DO NOT auto-scroll!
    if (!hasNewMessage && !isStreaming) {
      return;
    }

    // If streaming and user intentionally scrolled up to read previous messages, don't jerk screen
    if (isStreaming && isUserScrolledUpRef.current) {
      return;
    }

    scrollContainerRef.current.scrollTo({
      top: scrollContainerRef.current.scrollHeight,
      behavior: isStreaming ? 'auto' : 'smooth',
    });
  }, [messages]);

  // Autocomplete suggestions based on input length
  useEffect(() => {
    if (inputText.trim().length >= 2) {
      const lower = inputText.toLowerCase();
      const matched = AUTOCOMPLETE_SYMPTOMS.filter(
        (s) => s.toLowerCase().includes(lower) && s.toLowerCase() !== lower
      );
      setMatchingSuggestions(matched.slice(0, 4));
    } else {
      setMatchingSuggestions([]);
    }
  }, [inputText]);

  const handleSend = () => {
    if (!inputText.trim() || isProcessing) return;
    onSendMessage(inputText.trim());
    setInputText('');
    setMatchingSuggestions([]);
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInputTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputText(e.target.value);
    // Auto-resize textarea height up to 120px
    e.target.style.height = 'auto';
    e.target.style.height = `${Math.min(e.target.scrollHeight, 120)}px`;
  };

  const handleVoiceTranscribed = (text: string) => {
    onSendMessage(text);
    setShowVoiceRecorder(false);
  };

  return (
    <div className="flex flex-col h-full max-h-full bg-white/35 backdrop-blur-xl border border-white/60 rounded-[2.2rem] shadow-[0_8px_32px_0_rgba(31,38,135,0.08)] overflow-hidden relative">
      {/* Medical Disclaimer Banner */}
      <div className="bg-amber-100/60 backdrop-blur-sm border-b border-amber-200/60 py-2 px-4 flex items-center gap-2 text-xs text-amber-900 flex-shrink-0">
        <Info size={14} className="flex-shrink-0 text-amber-700" />
        <p className="text-[11px] leading-tight">
          Lưu ý: Thông tin mang tính tham khảo chuyên môn. Với dấu hiệu đe dọa tính mạng, vui lòng gọi cấp cứu 115 ngay lập tức.
        </p>
      </div>

      {/* Messages Scroll Area */}
      <div
        ref={scrollContainerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto custom-scrollbar p-4 md:p-6 space-y-4 min-h-0"
      >
        {messages.map((msg) => (
          <MessageItem
            key={msg.id}
            message={msg}
            sessionId={sessionId}
            onSetActiveAnswerIndex={onSetActiveAnswerIndex}
            onSubmitFeedback={onSubmitFeedback}
            onSelectClarificationAnswer={onSendMessage}
          />
        ))}
      </div>


      {/* Autocomplete Suggestions Popup Floating cleanly above input */}
      {matchingSuggestions.length > 0 && (
        <div className="px-4 py-2 bg-white/90 backdrop-blur-md border-t border-teal-100 flex items-center gap-2 overflow-x-auto no-scrollbar shadow-md">
          <span className="text-[11px] font-semibold text-teal-800 flex items-center gap-1 flex-shrink-0">
            <Sparkles size={12} className="text-teal-600" />
            <span>Gợi ý:</span>
          </span>
          {matchingSuggestions.map((sug, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => {
                setInputText(sug);
                setMatchingSuggestions([]);
              }}
              className="text-xs bg-teal-50 hover:bg-teal-100 text-teal-900 border border-teal-200 px-3 py-1 rounded-full transition flex-shrink-0 shadow-xs font-medium"
            >
              + {sug}
            </button>
          ))}
          <button
            type="button"
            onClick={() => setMatchingSuggestions([])}
            className="p-1 text-slate-400 hover:text-slate-600 rounded-full ml-auto"
            title="Đóng gợi ý"
          >
            <X size={14} />
          </button>
        </div>
      )}

      {/* Quick Prompt Chips */}
      <div className="flex-shrink-0 px-4 py-2 bg-white/40 backdrop-blur-md border-t border-white/50 flex items-center space-x-2 overflow-x-auto no-scrollbar">
        <span className="text-[11px] font-semibold text-slate-500 flex items-center space-x-1 flex-shrink-0">
          <Sparkles className="w-3.5 h-3.5 text-teal-600" />
          <span>Mẫu:</span>
        </span>
        {QUICK_PROMPTS.map((item, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => onSendMessage(item.prompt)}
            className={`text-[11px] font-semibold px-3.5 py-1.5 rounded-full border transition-all flex-shrink-0 hover:scale-105 shadow-xs ${item.color}`}
          >
            <span>{item.label}</span>
          </button>
        ))}
      </div>

      {/* Voice Recorder Overlay */}
      {showVoiceRecorder && (
        <div className="p-4 bg-white/95 backdrop-blur-md border-t border-white/60 animate-in slide-in-from-bottom-3 duration-150">
          <VoiceRecorder
            onTranscribed={handleVoiceTranscribed}
            onCancel={() => setShowVoiceRecorder(false)}
          />
        </div>
      )}

      {/* File Uploader Modal */}
      {showFileUploader && (
        <FileUploader
          onOCRComplete={(res, fn) => {
            onOCRComplete(res, fn);
            setShowFileUploader(false);
          }}
          onClose={() => setShowFileUploader(false)}
        />
      )}

      {/* Input Action Bar */}
      <div className="flex-shrink-0 p-3.5 bg-white/50 backdrop-blur-lg border-t border-white/60">
        <div className="flex items-end gap-2 bg-white/85 backdrop-blur-md border border-white/90 rounded-[1.8rem] p-2 shadow-xs focus-within:ring-2 focus-within:ring-teal-400/50 focus-within:bg-white transition-all">
          {/* Action Buttons Left */}
          <div className="flex items-center gap-1 pb-1">
            <button
              type="button"
              onClick={() => setShowFileUploader(true)}
              title="Tải lên ảnh hoặc PDF phiếu xét nghiệm máu"
              className="w-9 h-9 rounded-full flex items-center justify-center text-slate-500 hover:text-teal-700 hover:bg-teal-50 transition"
            >
              <Paperclip size={18} />
            </button>

            <button
              type="button"
              onClick={() => setShowVoiceRecorder(!showVoiceRecorder)}
              title="Ghi âm giọng nói triệu chứng"
              className={`w-9 h-9 rounded-full flex items-center justify-center transition ${
                showVoiceRecorder ? 'text-red-600 bg-red-100' : 'text-slate-500 hover:text-teal-700 hover:bg-teal-50'
              }`}
            >
              <Mic size={18} />
            </button>
          </div>

          {/* Auto-expanding Multiline Textarea */}
          <textarea
            ref={inputRef}
            rows={1}
            value={inputText}
            onChange={handleInputTextChange}
            onKeyDown={handleKeyDown}
            placeholder="Mô tả triệu chứng của bạn (Enter để gửi, Shift+Enter để xuống dòng)..."
            disabled={isProcessing}
            className="flex-1 bg-transparent border-none text-slate-800 placeholder-slate-400 px-2 py-2 outline-none text-[15.5px] font-medium resize-none max-h-32 min-h-[42px] leading-relaxed custom-scrollbar"
          />

          {/* Single Unified Action Button: Send or Stop/Cancel */}
          <div className="pb-1">
            {isProcessing ? (
              <button
                type="button"
                onClick={onCancelQuery}
                title="Hủy truy vấn / Dừng phản hồi"
                className="w-10 h-10 rounded-full flex items-center justify-center bg-rose-600 hover:bg-rose-700 text-white shadow-md shadow-rose-500/30 transition-all hover:scale-105 active:scale-95 animate-pulse cursor-pointer ring-2 ring-rose-300 ring-offset-1"
              >
                <Square size={15} className="fill-current" />
              </button>
            ) : (
              <button
                type="button"
                onClick={handleSend}
                disabled={!inputText.trim()}
                className={`w-10 h-10 rounded-full flex items-center justify-center transition-all ${
                  inputText.trim()
                    ? 'bg-gradient-to-tr from-teal-500 to-blue-600 text-white shadow-md shadow-teal-500/30 hover:scale-105 active:scale-95 cursor-pointer'
                    : 'bg-slate-200/80 text-slate-400 cursor-not-allowed'
                }`}
                title="Gửi tin nhắn"
              >
                <Send size={18} className={inputText.trim() ? 'ml-0.5' : ''} />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
