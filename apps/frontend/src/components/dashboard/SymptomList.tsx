'use client';

import React from 'react';
import { Activity, CheckCircle } from 'lucide-react';
import { SymptomEntity } from '../../types/chat';

interface SymptomListProps {
  symptoms: SymptomEntity[];
}

export const SymptomList: React.FC<SymptomListProps> = ({ symptoms }) => {
  return (
    <div className="bg-white/40 backdrop-blur-xl rounded-[2rem] p-5 border border-white/70 shadow-[0_8px_32px_0_rgba(31,38,135,0.06)] space-y-3">
      <div className="flex items-center justify-between pb-2 border-b border-slate-200/60">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 bg-emerald-50 border border-emerald-200 text-emerald-700 rounded-xl shadow-xs">
            <Activity className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-slate-800 uppercase tracking-wider">Triệu Chứng Đã Bóc Tách (NER)</h4>
            <p className="text-xs text-slate-400 font-mono">PhoBERT Token Classification</p>
          </div>
        </div>
        {symptoms.length > 0 && (
          <span className="text-xs font-bold text-emerald-800 bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-200">
            {symptoms.length} Thực Thể
          </span>
        )}
      </div>

      {symptoms.length === 0 ? (
        <div className="py-6 text-center text-slate-400 text-sm italic">
          Chưa phát hiện thực thể triệu chứng trong cuộc hội thoại.
        </div>
      ) : (
        <div className="flex flex-wrap gap-2 pt-1">
          {symptoms.map((symptom, idx) => (
            <span
              key={idx}
              className="inline-flex items-center space-x-1.5 bg-white/80 text-teal-800 border border-teal-200/80 px-3.5 py-1.5 rounded-full text-sm font-semibold shadow-xs hover:bg-white transition"
            >
              <CheckCircle className="w-3.5 h-3.5 text-teal-600 flex-shrink-0" />
              <span>{symptom.standard_term}</span>
            </span>
          ))}
        </div>
      )}
    </div>
  );
};
