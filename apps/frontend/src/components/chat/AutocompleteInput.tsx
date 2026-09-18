'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Sparkles } from 'lucide-react';

const COMMON_SYMPTOMS = [
  'Sốt cao 39 độ', 'Sốt rét run', 'Đau đầu dữ dội', 'Đau nửa đầu',
  'Đau ngực tức ngực', 'Khó thở thở dốc', 'Đau quặn bụng', 'Đau thượng vị',
  'Buồn nôn và nôn ói', 'Tiêu chảy đi ngoài phân lỏng', 'Chảy máu chân răng',
  'Méo miệng yếu tay chân', 'Chóng mặt hoa mắt', 'Mệt mỏi kéo dài'
];

interface AutocompleteInputProps {
  value: string;
  onChange: (val: string) => void;
  onSelectSuggestion: (val: string) => void;
}

export const AutocompleteInput: React.FC<AutocompleteInputProps> = ({
  value,
  onChange,
  onSelectSuggestion,
}) => {
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const wrapperRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (value.trim().length > 1) {
      const lower = value.toLowerCase();
      const matched = COMMON_SYMPTOMS.filter((s) => s.toLowerCase().includes(lower));
      setSuggestions(matched);
      setIsOpen(matched.length > 0);
    } else {
      setSuggestions([]);
      setIsOpen(false);
    }
  }, [value]);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div ref={wrapperRef} className="relative w-full">
      {isOpen && suggestions.length > 0 && (
        <div className="absolute bottom-full mb-2 left-0 right-0 bg-white/95 backdrop-blur-md rounded-2xl shadow-xl border border-emerald-100 p-2 z-30 animate-in fade-in slide-in-from-bottom-2 duration-150">
          <div className="flex items-center space-x-1.5 px-2 py-1 text-xs font-semibold text-emerald-700">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Gợi ý triệu chứng liên quan</span>
          </div>
          <div className="mt-1 space-y-1 max-h-48 overflow-y-auto">
            {suggestions.map((item, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => {
                  onSelectSuggestion(item);
                  setIsOpen(false);
                }}
                className="w-full text-left px-3 py-2 rounded-xl text-sm text-slate-700 hover:bg-emerald-50 hover:text-emerald-900 transition flex items-center justify-between"
              >
                <span>{item}</span>
                <span className="text-[10px] bg-emerald-100/60 text-emerald-800 px-2 py-0.5 rounded-full">Chọn nhanh</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
