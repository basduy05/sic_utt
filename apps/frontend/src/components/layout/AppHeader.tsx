'use client';

import React from 'react';
import Link from 'next/link';
import { Search, ChevronDown, Stethoscope, ShieldCheck } from 'lucide-react';
import { UserDropdown } from './UserDropdown';

export const AppHeader: React.FC = () => {

  return (
    <header className="h-16 bg-white border-b border-slate-200/80 px-4 md:px-6 flex items-center justify-between flex-shrink-0 z-30 select-none">
      {/* Left: Brand Logo MediBot AI (Redirects to Landing Page) */}
      <Link href="/landing" className="flex items-center space-x-2.5 group" title="Về Trang Chủ Giới Thiệu (Landing Page)">
        <div className="flex items-center space-x-2">
          <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center text-white shadow-sm shadow-blue-500/20 group-hover:scale-105 transition">
            <Stethoscope size={22} />
          </div>
          <div className="flex flex-col">
            <div className="flex items-baseline space-x-1.5">
              <span className="text-xl font-black text-blue-600 tracking-tight">
                Medi<span className="text-slate-900">Bot</span>
              </span>
              <span className="text-xs font-bold text-blue-600 uppercase tracking-wider bg-blue-50 px-2 py-0.5 rounded-md border border-blue-200">
                AI Pro
              </span>
            </div>
            <span className="text-[11px] text-slate-500 font-medium">
              Trợ Lý Khám Bệnh Đa Phương Thức
            </span>
          </div>
        </div>
      </Link>

      {/* Right Actions: System Status & Profile */}
      <div className="flex items-center space-x-4">
        {/* System Online Status Badge */}
        <div className="hidden lg:flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-emerald-50 border border-emerald-200/90 text-emerald-800 text-[13px] font-semibold">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
          <span>AI Engine: Trực tuyến</span>
        </div>

        {/* ICD-10 Ministry of Health Standard Badge */}
        <div className="hidden sm:flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-blue-50 border border-blue-200/90 text-blue-800 text-[13px] font-semibold">
          <ShieldCheck size={16} className="text-blue-600" />
          <span>Chuẩn Bộ Y Tế & ICD-10</span>
        </div>

        {/* Medical Search Bar */}
        <div className="hidden md:flex items-center space-x-2.5 px-3.5 py-2 rounded-xl bg-slate-50 border border-slate-200 text-slate-500 text-sm w-72 hover:border-slate-300 transition cursor-pointer">
          <Search size={16} className="text-slate-400" />
          <span className="flex-1 text-slate-400 truncate text-[13px]">Tìm mã bệnh, triệu chứng...</span>
          <kbd className="px-2 py-0.5 text-xs font-mono font-bold bg-white border border-slate-200 rounded-md text-slate-600 shadow-2xs">
            ⌘K
          </kbd>
        </div>

        {/* User Profile Dropdown */}
        <UserDropdown />
      </div>
    </header>
  );
};
