'use client';

import React from 'react';
import { BarChart3, Activity } from 'lucide-react';
import { DiseasePrediction } from '../../types/chat';

interface ProbabilityChartProps {
  predictions: DiseasePrediction[];
}

export const ProbabilityChart: React.FC<ProbabilityChartProps> = ({ predictions }) => {
  return (
    <div className="bg-white/40 backdrop-blur-xl rounded-[2rem] p-5 border border-white/70 shadow-[0_8px_32px_0_rgba(31,38,135,0.06)] space-y-3.5">
      <div className="flex items-center justify-between pb-2 border-b border-slate-200/60">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 bg-teal-50 border border-teal-200 text-teal-700 rounded-xl shadow-xs">
            <BarChart3 className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-slate-800 uppercase tracking-wider">Phân Tầng Nguy Cơ Bệnh (AI Triage)</h4>
            <p className="text-xs text-slate-400 font-mono">Neural Late Fusion Matrix</p>
          </div>
        </div>
        {predictions.length > 0 && (
          <span className="text-xs font-bold text-teal-800 bg-teal-50 px-2.5 py-0.5 rounded-full border border-teal-200">
            Top {predictions.length} Nguy Cơ
          </span>
        )}
      </div>

      {predictions.length === 0 ? (
        <div className="py-8 text-center text-slate-400 text-sm italic flex flex-col items-center justify-center space-y-2">
          <Activity className="w-5 h-5 text-slate-300 animate-pulse" />
          <span>Đang chờ dữ liệu triệu chứng để tính toán phân tầng nguy cơ...</span>
        </div>
      ) : (
        <div className="space-y-2.5">
          {predictions.map((item, idx) => {
            const percentageNumber = item.probability * 100;
            const isTop1 = item.rank === 1;

            return (
              <div key={item.icd_code || idx} className="space-y-1.5 p-3 rounded-2xl bg-white/70 border border-white/90 shadow-xs hover:shadow-sm transition">
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center space-x-2 truncate">
                    <span className="font-mono font-bold text-teal-900 bg-teal-50 px-2 py-0.5 rounded-md text-xs border border-teal-200">
                      {item.icd_code}
                    </span>
                    <span className="font-bold text-slate-800 truncate">{item.disease_name_vi}</span>
                  </div>
                  <span className={`font-mono font-extrabold text-sm flex-shrink-0 ${isTop1 ? 'text-teal-700' : 'text-slate-500'}`}>
                    {item.probability_percentage}
                  </span>
                </div>

                {/* Progress Bar */}
                <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden p-0.5 border border-slate-200/60">
                  <div
                    className={`h-full rounded-full transition-all duration-700 ${
                      isTop1
                        ? 'bg-gradient-to-r from-teal-400 to-blue-500 shadow-xs'
                        : item.rank === 2
                        ? 'bg-gradient-to-r from-indigo-400 to-blue-400'
                        : 'bg-slate-300'
                    }`}
                    style={{ width: `${Math.min(100, Math.max(6, percentageNumber))}%` }}
                  />
                </div>

                <div className="flex items-center justify-between text-xs text-slate-500 pt-0.5">
                  <span>Khoa: <strong className="text-slate-700 font-semibold">{item.department}</strong></span>
                  <span className={`px-2 py-0.5 rounded-full font-medium ${
                    item.severity === 'Emergency' || item.severity === 'High' ? 'bg-red-50 text-red-700 border border-red-200' : 'bg-slate-100 text-slate-600'
                  }`}>
                    {item.severity || 'Theo dõi'}
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
