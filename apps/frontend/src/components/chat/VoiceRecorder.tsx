'use client';

import React from 'react';
import { Mic, Square, Trash2, Send, Loader2 } from 'lucide-react';
import { useAudioRecorder } from '../../hooks/useAudioRecorder';
import { medicalService } from '../../services/medicalService';

interface VoiceRecorderProps {
  onTranscribed: (text: string) => void;
  onCancel: () => void;
}

export const VoiceRecorder: React.FC<VoiceRecorderProps> = ({ onTranscribed, onCancel }) => {
  const {
    isRecording,
    audioBlob,
    recordingDuration,
    startRecording,
    stopRecording,
    clearAudio,
    canvasRef,
  } = useAudioRecorder();

  const [isTranscribing, setIsTranscribing] = React.useState(false);

  const formatDuration = (sec: number) => {
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  const handleTranscribeAndSend = async () => {
    if (!audioBlob) return;
    setIsTranscribing(true);
    try {
      const res = await medicalService.transcribeAudio(audioBlob);
      if (res.text) {
        onTranscribed(res.text);
      }
    } catch (err) {
      console.error('Error transcribing audio:', err);
    } finally {
      setIsTranscribing(false);
      clearAudio();
      onCancel();
    }
  };

  return (
    <div className="bg-emerald-50 border border-emerald-200 rounded-2xl p-4 shadow-sm transition-all">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <div className={`w-3 h-3 rounded-full ${isRecording ? 'bg-red-500 animate-ping' : 'bg-emerald-500'}`} />
          <span className="text-sm font-medium text-slate-700">
            {isRecording ? 'Đang ghi âm giọng nói...' : audioBlob ? 'Bản ghi hoàn tất' : 'Sẵn sàng ghi âm'}
          </span>
        </div>
        <span className="text-xs font-mono bg-white px-2 py-1 rounded-md border text-slate-600">
          {formatDuration(recordingDuration)}
        </span>
      </div>

      {/* Realtime Waveform Canvas */}
      <div className="h-16 bg-white rounded-xl border border-emerald-100 overflow-hidden mb-3">
        <canvas ref={canvasRef} width={400} height={64} className="w-full h-full" />
      </div>

      {/* Controls */}
      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={() => { clearAudio(); onCancel(); }}
          className="text-xs text-slate-500 hover:text-slate-700 flex items-center space-x-1"
        >
          <Trash2 className="w-4 h-4" />
          <span>Hủy</span>
        </button>

        <div className="flex items-center space-x-2">
          {!isRecording && !audioBlob && (
            <button
              type="button"
              onClick={startRecording}
              className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-xl text-sm font-medium flex items-center space-x-2 shadow-sm transition"
            >
              <Mic className="w-4 h-4" />
              <span>Bắt đầu nói</span>
            </button>
          )}

          {isRecording && (
            <button
              type="button"
              onClick={stopRecording}
              className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-xl text-sm font-medium flex items-center space-x-2 shadow-sm transition"
            >
              <Square className="w-4 h-4" />
              <span>Dừng lại</span>
            </button>
          )}

          {audioBlob && !isRecording && (
            <button
              type="button"
              onClick={handleTranscribeAndSend}
              disabled={isTranscribing}
              className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-xl text-sm font-medium flex items-center space-x-2 shadow-sm transition"
            >
              {isTranscribing ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Đang bóc tách giọng nói...</span>
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  <span>Chuyển thành văn bản & Gửi</span>
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
