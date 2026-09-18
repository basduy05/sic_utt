'use client';

import React, { useEffect } from 'react';
import { AlertOctagon, PhoneCall } from 'lucide-react';
import { RedFlagAlert } from '../../types/chat';
import { ModalPortal } from '../common/ModalPortal';

interface RedFlagModalProps {
  isOpen: boolean;
  alerts: RedFlagAlert[];
  onClose: () => void;
}

export const RedFlagModal: React.FC<RedFlagModalProps> = ({ isOpen, alerts, onClose }) => {
  useEffect(() => {
    if (isOpen) {
      // Play audio buzzer / emergency tone via Web Audio API
      try {
        const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(440, audioCtx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(880, audioCtx.currentTime + 0.3);
        gain.gain.setValueAtTime(0.3, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.4);
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start();
        osc.stop(audioCtx.currentTime + 0.4);
      } catch (err) {
        console.error('Audio alert not supported:', err);
      }
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const primaryAlert = alerts[0] || {
    disease_group: 'Cấp cứu y khoa khẩn cấp',
    action_vi: 'Phát hiện dấu hiệu đe dọa tính mạng. Cần liên hệ hỗ trợ y tế ngay lập tức.',
    emergency_phone: '115'
  };

  return (
    <ModalPortal>
      <div className="fixed inset-0 z-[9999] w-screen h-screen min-h-screen min-w-full flex items-center justify-center p-4 bg-red-950/85 backdrop-blur-md overflow-y-auto">
        <div className="relative bg-white rounded-3xl max-w-lg w-full p-6 md:p-8 shadow-2xl border-4 border-red-500 my-auto">
        {/* Top Header Warning */}
        <div className="flex items-center space-x-3 mb-4">
          <div className="p-3 bg-red-100 text-red-600 rounded-2xl animate-pulse">
            <AlertOctagon className="w-8 h-8" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-red-600 uppercase tracking-wide">
              Báo Động Đỏ Cấp Cứu
            </h2>
            <p className="text-xs text-slate-500 font-medium">{primaryAlert.disease_group}</p>
          </div>
        </div>

        {/* Urgent Action Body */}
        <div className="bg-red-50 border border-red-200 rounded-2xl p-4 mb-6">
          <p className="text-sm font-semibold text-red-950 leading-relaxed">
            {primaryAlert.action_vi}
          </p>
        </div>

        {/* 115 Action Button */}
        <div className="space-y-3">
          <a
            href="tel:115"
            className="w-full bg-red-600 hover:bg-red-700 active:scale-98 text-white font-bold py-4 rounded-2xl shadow-lg shadow-red-600/30 flex items-center justify-center space-x-3 text-lg transition duration-150"
          >
            <PhoneCall className="w-6 h-6 animate-pulse" />
            <span>Gọi Cấp Cứu 115 Ngay</span>
          </a>

          <a
            href="/emergency"
            onClick={onClose}
            className="w-full bg-slate-100 hover:bg-slate-200 text-slate-800 font-bold py-2.5 rounded-xl flex items-center justify-center space-x-2 text-xs transition"
          >
            <span>Mở Trung Tâm Cấp Cứu & Sổ Tay Sơ Cứu</span>
          </a>

          <button
            type="button"
            onClick={onClose}
            className="w-full text-slate-500 hover:text-slate-700 text-xs py-2 text-center"
          >
            Tôi đã hiểu và đang xử lý an toàn
          </button>
        </div>
      </div>
    </div>
    </ModalPortal>
  );
};
