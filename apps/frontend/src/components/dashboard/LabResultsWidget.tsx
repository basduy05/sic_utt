'use client';

import React from 'react';
import { FlaskConical, CheckCircle2, AlertTriangle, ShieldAlert } from 'lucide-react';
import { LabIndicator } from '../../types/chat';

interface LabResultsWidgetProps {
  labIndicators: Record<string, LabIndicator>;
}

export const LabResultsWidget: React.FC<LabResultsWidgetProps> = ({ labIndicators }) => {
  const keys = Object.keys(labIndicators);

  return (
    <div className="bg-white/40 backdrop-blur-xl rounded-[2rem] p-5 border border-white/70 shadow-[0_8px_32px_0_rgba(31,38,135,0.06)] space-y-3">
      <div className="flex items-center justify-between pb-2 border-b border-slate-200/60">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 bg-blue-50 border border-blue-200 text-blue-700 rounded-xl shadow-xs">
            <FlaskConical className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-slate-800 uppercase tracking-wider">Chỉ Số Xét Nghiệm Máu (OCR)</h4>
            <p className="text-xs text-slate-400 font-mono">Biomarker Range Checker</p>
          </div>
        </div>
        {keys.length > 0 && (
          <span className="text-xs font-bold text-blue-800 bg-blue-50 px-2.5 py-0.5 rounded-full border border-blue-200">
            {keys.length} Chỉ Số
          </span>
        )}
      </div>

      {keys.length === 0 ? (
        <div className="py-6 text-center text-slate-400 text-sm italic">
          Chưa có dữ liệu xét nghiệm. Bấm vào biểu tượng kẹp ghim 📎 để tải ảnh/PDF phiếu máu.
        </div>
      ) : (
        <div className="space-y-2 max-h-[260px] overflow-y-auto custom-scrollbar pr-1">
          {keys.map((testName) => {
            const item = labIndicators[testName];

            const isDanger = item.status === 'CRITICAL_LOW' || item.status === 'CRITICAL_HIGH';
            const isWarning = item.status === 'LOW' || item.status === 'HIGH';

            return (
              <div
                key={testName}
                className={`flex items-center justify-between p-3 rounded-2xl border text-sm transition shadow-xs ${
                  isDanger
                    ? 'bg-red-50/80 border-red-200'
                    : isWarning
                    ? 'bg-amber-50/80 border-amber-200'
                    : 'bg-white/80 border-white/90'
                }`}
              >
                <div className="space-y-0.5">
                  <div className="flex items-center space-x-2">
                    {isDanger ? (
                      <ShieldAlert className="w-4 h-4 text-red-600 animate-pulse" />
                    ) : isWarning ? (
                      <AlertTriangle className="w-4 h-4 text-amber-600" />
                    ) : (
                      <CheckCircle2 className="w-4 h-4 text-teal-600" />
                    )}
                    <span className="font-bold text-slate-800">{testName}</span>
                  </div>
                  <div className="text-xs text-slate-500">{item.message}</div>
                </div>

                <div className="text-right space-y-0.5">
                  <div className="font-mono font-bold text-slate-800">
                    {item.value} <span className="text-xs text-slate-400 font-normal">{item.unit}</span>
                  </div>
                  <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-bold border ${
                    isDanger
                      ? 'bg-red-100 text-red-800 border-red-300'
                      : isWarning
                      ? 'bg-amber-100 text-amber-800 border-amber-300'
                      : 'bg-teal-100 text-teal-800 border-teal-300'
                  }`}>
                    {item.status}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
