'use client';

import React, { useState, useEffect } from 'react';
import { useTheme, FontSizeScale } from '@/context/ThemeContext';
import { X, Type, Check, Sparkles, Volume2, Bell, Sliders, ShieldCheck, KeyRound } from 'lucide-react';
import { ModalPortal } from '../common/ModalPortal';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function SettingsModal({ isOpen, onClose }: SettingsModalProps) {
  const { fontSizeScale, setFontSizeScale, voiceEnabled, setVoiceEnabled, soundAlerts, setSoundAlerts } = useTheme();

  const [geminiKey, setGeminiKey] = useState<string>('');
  const [cohereKey, setCohereKey] = useState<string>('');
  const [savedAlert, setSavedAlert] = useState<boolean>(false);

  useEffect(() => {
    if (isOpen && typeof window !== 'undefined') {
      setGeminiKey(localStorage.getItem('gemini_api_key') || '');
      setCohereKey(localStorage.getItem('cohere_api_key') || '');
    }
  }, [isOpen]);

  const handleSaveAll = () => {
    if (typeof window !== 'undefined') {
      if (geminiKey.trim()) {
        localStorage.setItem('gemini_api_key', geminiKey.trim());
      } else {
        localStorage.removeItem('gemini_api_key');
      }
      if (cohereKey.trim()) {
        localStorage.setItem('cohere_api_key', cohereKey.trim());
      } else {
        localStorage.removeItem('cohere_api_key');
      }
    }
    setSavedAlert(true);
    setTimeout(() => {
      setSavedAlert(false);
      onClose();
    }, 600);
  };

  if (!isOpen) return null;

  const fontOptions: { id: FontSizeScale; name: string; desc: string; sample: string }[] = [
    {
      id: 'sm',
      name: 'Nhỏ (90% - Gọn gàng)',
      desc: 'Tối ưu mật độ dữ liệu, phù hợp laptop nhỏ',
      sample: 'Aa (14px)',
    },
    {
      id: 'md',
      name: 'Tiêu Chuẩn (100% - Khuyên dùng)',
      desc: 'Kích thước chuẩn y khoa, hài hòa và cân đối',
      sample: 'Aa (16px)',
    },
    {
      id: 'lg',
      name: 'To Rõ (115% - Dễ đọc)',
      desc: 'Toàn bộ cỡ chữ to đồng nhất, rất dễ nhìn',
      sample: 'Aa (18px)',
    },
  ];

  return (
    <ModalPortal>
      <div className="fixed inset-0 z-[9999] w-screen h-screen min-h-screen min-w-full flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-md overflow-y-auto">
        <div className="bg-white rounded-3xl shadow-2xl border border-slate-200/80 w-full max-w-xl overflow-hidden flex flex-col max-h-[90vh] my-auto">
        {/* Modal Header */}
        <div className="relative bg-gradient-to-r from-blue-700 via-indigo-700 to-slate-800 px-6 py-5 text-white flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-white/20 backdrop-blur-md flex items-center justify-center text-white shadow-inner">
              <Sliders className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold tracking-tight">Cài Đặt Hệ Thống & Giao Diện</h2>
              <p className="text-blue-100 text-xs font-medium">Tùy biến hiển thị đồng nhất & trợ năng y tế</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-full text-white/80 hover:text-white hover:bg-white/10 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto custom-scrollbar flex flex-col gap-6">
          {/* Section 1: Font Size Scale */}
          <div className="flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-slate-800 font-bold text-sm">
                <Type className="w-4 h-4 text-blue-600" />
                <span>Kích Thước Chữ Hệ Thống (To / Nhỏ Đồng Nhất)</span>
              </div>
              <span className="text-[11px] font-semibold text-blue-600 bg-blue-50 px-2 py-0.5 rounded-full">
                Áp dụng toàn bộ ứng dụng
              </span>
            </div>
            <p className="text-xs text-slate-500 leading-relaxed">
              Khi thay đổi, thanh điều hướng, bảng điều khiển, tin nhắn bác sĩ và mọi thành phần sẽ tự động điều chỉnh tỷ lệ đồng đều mà không làm tràn hay vỡ khung hình.
            </p>

            {/* Selection Grid */}
            <div className="grid grid-cols-1 gap-2.5 mt-1">
              {fontOptions.map((opt) => {
                const isSelected = fontSizeScale === opt.id;
                return (
                  <button
                    key={opt.id}
                    type="button"
                    onClick={() => setFontSizeScale(opt.id)}
                    className={`flex items-center justify-between p-3.5 rounded-2xl border-2 transition-all text-left ${
                      isSelected
                        ? 'border-blue-600 bg-blue-50/70 shadow-sm'
                        : 'border-slate-200 hover:border-slate-300 bg-slate-50/60'
                    }`}
                  >
                    <div className="flex flex-col gap-0.5">
                      <div className="flex items-center gap-2">
                        <span className={`font-bold text-sm ${isSelected ? 'text-blue-900' : 'text-slate-800'}`}>
                          {opt.name}
                        </span>
                        {isSelected && (
                          <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-blue-600 text-white">
                            <Check className="w-3 h-3 stroke-[3]" />
                          </span>
                        )}
                      </div>
                      <span className="text-xs text-slate-500">{opt.desc}</span>
                    </div>

                    <div className={`px-3 py-1.5 rounded-xl font-bold border text-sm ${
                      isSelected ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-slate-600 border-slate-200'
                    }`}>
                      {opt.sample}
                    </div>
                  </button>
                );
              })}
            </div>

            {/* Live Preview Box */}
            <div className="mt-2 p-3.5 rounded-2xl bg-slate-100 border border-slate-200 flex flex-col gap-1.5">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
                Xem trước văn bản hiển thị thực tế:
              </span>
              <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-sm">
                <p className="font-bold text-slate-800 mb-0.5">
                  Bác sĩ AI MediBot: &quot;Chào bạn, kết quả xét nghiệm đường huyết của bạn ở mức 5.4 mmol/L (Bình thường)&quot;
                </p>
                <p className="text-xs text-slate-500">
                  Mã ICD-10: E11 (Đái tháo đường typ 2) • Khuyến nghị uống nhiều nước và tái khám định kỳ.
                </p>
              </div>
            </div>
          </div>

          <div className="h-px bg-slate-200" />

          {/* Section 2: Audio & Accessibility */}
          <div className="flex flex-col gap-3">
            <span className="text-slate-800 font-bold text-sm flex items-center gap-2">
              <Volume2 className="w-4 h-4 text-indigo-600" />
              <span>Trợ Năng Âm Thanh & Giọng Đọc</span>
            </span>

            <div className="flex flex-col gap-2.5">
              {/* TTS Voice Switch */}
              <div className="flex items-center justify-between p-3.5 rounded-2xl border border-slate-200 bg-slate-50">
                <div className="flex flex-col">
                  <span className="text-sm font-bold text-slate-800">Đọc phản hồi bác sĩ (TTS AI)</span>
                  <span className="text-xs text-slate-500">Tự động phát âm thanh khi bác sĩ AI tư vấn xong</span>
                </div>
                <button
                  type="button"
                  onClick={() => setVoiceEnabled(!voiceEnabled)}
                  className={`w-12 h-6 flex items-center rounded-full p-1 transition-colors ${
                    voiceEnabled ? 'bg-blue-600 justify-end' : 'bg-slate-300 justify-start'
                  }`}
                >
                  <div className="w-4 h-4 rounded-full bg-white shadow-md" />
                </button>
              </div>

              {/* Sound Alerts */}
              <div className="flex items-center justify-between p-3.5 rounded-2xl border border-slate-200 bg-slate-50">
                <div className="flex flex-col">
                  <span className="text-sm font-bold text-slate-800">Cảnh báo âm thanh Red Flag</span>
                  <span className="text-xs text-slate-500">Phát âm thanh cảnh báo khi phát hiện dấu hiệu cấp cứu</span>
                </div>
                <button
                  type="button"
                  onClick={() => setSoundAlerts(!soundAlerts)}
                  className={`w-12 h-6 flex items-center rounded-full p-1 transition-colors ${
                    soundAlerts ? 'bg-blue-600 justify-end' : 'bg-slate-300 justify-start'
                  }`}
                >
                  <div className="w-4 h-4 rounded-full bg-white shadow-md" />
                </button>
              </div>
            </div>
          </div>

          <div className="h-px bg-slate-200" />

          {/* Section 3: Dual AI API Keys */}
          <div className="flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <span className="text-slate-800 font-bold text-sm flex items-center gap-2">
                <KeyRound className="w-4 h-4 text-emerald-600" />
                <span>Khóa API Mô Hình AI (Chạy Song Song Google Gemini & Cohere)</span>
              </span>
              <span className="text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                Dual AI Race
              </span>
            </div>
            <p className="text-xs text-slate-500 leading-relaxed">
              Hệ thống gửi câu hỏi đồng thời đến cả 2 API: bên nào phản hồi trước sẽ ưu tiên hiển thị, bên còn lại lưu làm câu trả lời dự phòng để bạn chuyển đổi xem lại bất cứ lúc nào.
            </p>

            <div className="flex flex-col gap-3">
              {/* Gemini Key */}
              <div className="flex flex-col gap-1.5 p-3.5 rounded-2xl border border-slate-200 bg-slate-50">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-bold text-slate-700 flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-blue-600" />
                    <span>Google Gemini API Key</span>
                  </label>
                  <a
                    href="https://aistudio.google.com/app/apikey"
                    target="_blank"
                    rel="noreferrer"
                    className="text-[11px] font-semibold text-blue-600 hover:underline"
                  >
                    Lấy khóa Gemini miễn phí &rarr;
                  </a>
                </div>
                <input
                  type="password"
                  value={geminiKey}
                  onChange={(e) => setGeminiKey(e.target.value)}
                  placeholder="AIzaSy..."
                  className="w-full text-xs font-mono px-3 py-2 rounded-xl border border-slate-300 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-800"
                />
              </div>

              {/* Cohere Key */}
              <div className="flex flex-col gap-1.5 p-3.5 rounded-2xl border border-slate-200 bg-slate-50">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-bold text-slate-700 flex items-center gap-1.5">
                    <ShieldCheck className="w-3.5 h-3.5 text-teal-600" />
                    <span>Cohere API Key (Dự phòng song song)</span>
                  </label>
                  <a
                    href="https://dashboard.cohere.com/api-keys"
                    target="_blank"
                    rel="noreferrer"
                    className="text-[11px] font-semibold text-teal-600 hover:underline"
                  >
                    Lấy khóa Cohere &rarr;
                  </a>
                </div>
                <input
                  type="password"
                  value={cohereKey}
                  onChange={(e) => setCohereKey(e.target.value)}
                  placeholder="co_..."
                  className="w-full text-xs font-mono px-3 py-2 rounded-xl border border-slate-300 bg-white focus:outline-none focus:ring-2 focus:ring-teal-500 text-slate-800"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="p-4 bg-slate-50 border-t border-slate-200 flex items-center justify-between">
          <div>
            {savedAlert && (
              <span className="text-xs font-semibold text-emerald-600 flex items-center gap-1">
                <Check className="w-4 h-4 text-emerald-600" />
                Đã lưu cài đặt & API Keys!
              </span>
            )}
          </div>
          <button
            type="button"
            onClick={handleSaveAll}
            className="px-5 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 active:scale-95 text-white font-bold text-sm shadow-sm transition-all flex items-center gap-1.5"
          >
            <Check className="w-4 h-4" />
            <span>Đã Xong & Lưu Cài Đặt</span>
          </button>
        </div>
      </div>
    </div>
    </ModalPortal>
  );
}
