'use client';

import React, { useState } from 'react';
import { BookOpen, ChevronDown, ChevronUp, ShieldCheck } from 'lucide-react';

interface RagCitationsWidgetProps {
  citations: Array<{
    title: string;
    code?: string;
    department?: string;
    content: string;
    source: string;
    score?: number;
  }>;
}

export const RagCitationsWidget: React.FC<RagCitationsWidgetProps> = ({ citations }) => {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(0);

  if (!citations || citations.length === 0) return null;

  return (
    <div className="bg-white/40 backdrop-blur-xl rounded-[2rem] p-5 border border-white/70 shadow-[0_8px_32px_0_rgba(31,38,135,0.06)] space-y-3">
      <div className="flex items-center justify-between pb-2 border-b border-slate-200/60">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 bg-purple-50 border border-purple-200 text-purple-700 rounded-xl shadow-xs">
            <BookOpen className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-slate-800 uppercase tracking-wider">Trích Dẫn Tri Thức RAG (Bộ Y Tế)</h4>
            <p className="text-xs text-slate-400 font-mono">Vector Grounded Clinical KB</p>
          </div>
        </div>
        <span className="text-xs font-bold text-purple-800 bg-purple-50 px-2.5 py-0.5 rounded-full border border-purple-200">
          {citations.length} Tài Liệu
        </span>
      </div>

      <div className="space-y-2">
        {citations.map((doc, idx) => {
          const isExpanded = expandedIndex === idx;

          return (
            <div
              key={idx}
              className="rounded-2xl border border-white/80 bg-white/70 shadow-xs overflow-hidden transition"
            >
              <button
                type="button"
                onClick={() => setExpandedIndex(isExpanded ? null : idx)}
                className="w-full p-3 text-left flex items-center justify-between text-sm font-bold text-slate-800 hover:bg-white/90 transition"
              >
                <div className="flex items-center space-x-2 truncate">
                  <ShieldCheck className="w-4 h-4 text-teal-600 flex-shrink-0" />
                  <span className="truncate">{doc.title}</span>
                </div>
                {isExpanded ? (
                  <ChevronUp className="w-4 h-4 text-slate-400 flex-shrink-0" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-slate-400 flex-shrink-0" />
                )}
              </button>

              {isExpanded && (
                <div className="p-3.5 pt-0 text-sm text-slate-700 space-y-2 border-t border-slate-100 bg-white/80">
                  <p className="leading-relaxed text-xs text-slate-800 bg-slate-50 p-3 rounded-xl border border-slate-200/60">
                    {doc.content}
                  </p>
                  <div className="flex items-center justify-between text-xs text-slate-500 pt-1">
                    <span>Nguồn: <strong className="text-slate-700">{doc.source}</strong></span>
                    {doc.code && <span className="font-mono font-semibold text-teal-800 bg-teal-50 px-2 py-0.5 rounded border border-teal-200">{doc.code}</span>}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
