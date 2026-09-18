'use client';

import React, { useState } from 'react';
import { HelpCircle, CheckSquare, Square, Send, RotateCcw, Sparkles } from 'lucide-react';
import { ClarificationPayload } from '../../types/chat';

interface ClarificationWidgetProps {
  clarification: ClarificationPayload | null | undefined;
  onSelectAnswer: (answer: string) => void;
}

export const ClarificationWidget: React.FC<ClarificationWidgetProps> = ({
  clarification,
  onSelectAnswer,
}) => {
  // Lưu danh sách options đã chọn theo từng question id: { [questionId]: string[] }
  const [selectedMap, setSelectedMap] = useState<Record<string, string[]>>({});

  if (!clarification || !clarification.needs_clarification || !clarification.questions?.length) {
    return null;
  }

  // Toggle selection của 1 option trong 1 question
  const toggleOption = (qId: string, opt: string) => {
    setSelectedMap((prev) => {
      const currentList = prev[qId] || [];
      if (currentList.includes(opt)) {
        // Bỏ chọn
        const updated = currentList.filter((item) => item !== opt);
        return { ...prev, [qId]: updated };
      } else {
        // Thêm chọn (multi-select)
        return { ...prev, [qId]: [...currentList, opt] };
      }
    });
  };

  // Tổng số mục đã chọn trên tất cả các câu hỏi
  const allSelected: string[] = Object.values(selectedMap).flat();
  const totalSelectedCount = allSelected.length;

  // Xóa toàn bộ lựa chọn
  const handleReset = () => {
    setSelectedMap({});
  };

  // Gửi toàn bộ các câu trả lời đã tích chọn
  const handleSubmit = () => {
    if (totalSelectedCount === 0) return;

    // Định dạng nội dung phản hồi tổng hợp từ các câu hỏi
    const responseParts: string[] = [];
    clarification.questions.forEach((q, idx) => {
      const answersForQ = selectedMap[q.id] || [];
      if (answersForQ.length > 0) {
        responseParts.push(`${q.question}: ${answersForQ.join(', ')}`);
      }
    });

    const fullAnswerText = `Tôi xin bổ sung thông tin lâm sàng: ${responseParts.join(' | ')}`;
    onSelectAnswer(fullAnswerText);
    setSelectedMap({});
  };

  return (
    <div className="bg-amber-50/90 backdrop-blur-xl border border-amber-200/90 rounded-[2rem] p-5 shadow-[0_8px_32px_0_rgba(31,38,135,0.06)] space-y-4 animate-in fade-in slide-in-from-top-2 duration-150">
      {/* Header */}
      <div className="flex items-center justify-between pb-2 border-b border-amber-200/70">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 bg-amber-500/15 text-amber-900 rounded-xl shadow-xs">
            <HelpCircle className="w-4 h-4 text-amber-700" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h4 className="text-sm font-bold text-amber-950 uppercase tracking-wider flex items-center gap-1.5">
                <span>Hỏi Bổ Sung Lâm Sàng (Multi-Select)</span>
                <Sparkles className="w-4 h-4 text-amber-600" />
              </h4>
              {clarification.clinical_stage === 'provisional_assumption' ? (
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-blue-100 text-blue-800 border border-blue-200">
                  🩺 Giả định Lâm sàng (40% - 75%)
                </span>
              ) : (
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-amber-100 text-amber-900 border border-amber-300">
                  🔍 Sàng lọc ban đầu (&lt; 40%)
                </span>
              )}
            </div>
            <p className="text-xs text-amber-800 font-medium mt-0.5">
              Chưa đủ ngưỡng kết luận (yêu cầu &ge; 75% và &ge; 3 triệu chứng). Vui lòng chọn đáp án để làm rõ bệnh án:
            </p>
          </div>
        </div>

        {totalSelectedCount > 0 && (
          <button
            type="button"
            onClick={handleReset}
            className="flex items-center space-x-1 text-xs font-semibold text-amber-800 hover:text-amber-950 bg-amber-100 hover:bg-amber-200/80 px-2.5 py-1 rounded-lg transition"
            title="Bỏ chọn tất cả"
          >
            <RotateCcw size={13} />
            <span>Đặt lại</span>
          </button>
        )}
      </div>

      {/* Danh sách câu hỏi */}
      <div className="space-y-3">
        {clarification.questions.map((q, qIdx) => {
          const selectedForThisQ = selectedMap[q.id] || [];
          return (
            <div
              key={q.id}
              className="bg-white/95 rounded-2xl p-4 border border-amber-100/90 space-y-3 shadow-xs"
            >
              <div className="flex items-start justify-between gap-2">
                <p className="text-sm font-bold text-slate-800 flex items-center gap-2">
                  <span className="w-5 h-5 rounded-full bg-amber-100 text-amber-900 text-xs font-extrabold flex items-center justify-center flex-shrink-0">
                    {qIdx + 1}
                  </span>
                  <span>{q.question}</span>
                </p>
                {selectedForThisQ.length > 0 && (
                  <span className="text-xs font-semibold bg-teal-50 text-teal-700 border border-teal-200 px-2.5 py-0.5 rounded-full flex-shrink-0">
                    Đã chọn {selectedForThisQ.length}
                  </span>
                )}
              </div>

              {/* Các options có thể chọn nhiều */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {q.options.map((opt, optIdx) => {
                  const isChecked = selectedForThisQ.includes(opt);
                  return (
                    <button
                      key={optIdx}
                      type="button"
                      onClick={() => toggleOption(q.id, opt)}
                      className={`text-left text-sm px-3.5 py-2.5 rounded-xl border transition-all flex items-center justify-between gap-2 shadow-2xs ${
                        isChecked
                          ? 'bg-teal-50/95 border-teal-500 text-teal-950 font-semibold ring-1 ring-teal-400'
                          : 'bg-slate-50/80 hover:bg-amber-50/60 border-slate-200 text-slate-700 hover:border-amber-300'
                      }`}
                    >
                      <span className="leading-snug">{opt}</span>
                      {isChecked ? (
                        <CheckSquare className="w-4 h-4 text-teal-600 flex-shrink-0" />
                      ) : (
                        <Square className="w-4 h-4 text-slate-400 flex-shrink-0" />
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>

      {/* Action Footer: Submit Multi-select */}
      <div className="pt-1 flex items-center justify-between gap-3">
        <div className="text-xs text-amber-900 font-medium">
          {totalSelectedCount > 0 ? (
            <span>
              Đã chọn: <strong className="text-teal-700 font-bold">{totalSelectedCount}</strong> dấu hiệu
            </span>
          ) : (
            <span className="text-slate-500 italic text-xs">Vui lòng tích chọn các dấu hiệu bạn có</span>
          )}
        </div>

        <button
          type="button"
          disabled={totalSelectedCount === 0}
          onClick={handleSubmit}
          className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold transition shadow-sm ${
            totalSelectedCount > 0
              ? 'bg-gradient-to-r from-teal-600 to-emerald-600 hover:from-teal-700 hover:to-emerald-700 text-white shadow-teal-600/20 hover:scale-[1.02] active:scale-[0.98]'
              : 'bg-slate-200 text-slate-400 cursor-not-allowed'
          }`}
        >
          <Send size={13} />
          <span>Gửi câu trả lời ({totalSelectedCount})</span>
        </button>
      </div>
    </div>
  );
};
