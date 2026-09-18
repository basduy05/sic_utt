'use client';

import React, { Suspense } from 'react';
import Link from 'next/link';
import { usePathname, useSearchParams } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { useTheme } from '@/context/ThemeContext';
import {
  LayoutDashboard,
  Bot,
  FileText,
  Search,
  BookOpen,
  FileSpreadsheet,
  ShieldAlert,
  Database,
  Pill,
  HeartPulse,
  ChevronLeft,
  ChevronRight,
  PanelLeftClose,
  PanelLeftOpen,
} from 'lucide-react';

interface NavItem {
  id: string;
  label: string;
  shortLabel?: string;
  path: string;
  mode?: string;
  icon: React.ElementType;
  badge?: string;
  badgeColor?: string;
  requireAdmin?: boolean;
}

const NAV_ITEMS: NavItem[] = [
  { id: 'overview', label: 'Tổng quan hệ thống', shortLabel: 'Tổng quan', path: '/', icon: LayoutDashboard },
  { id: 'chat_ai', label: 'Khám bệnh với AI', shortLabel: 'Khám AI', path: '/chat', icon: Bot, badge: 'HOT', badgeColor: 'bg-blue-50 text-blue-600 border-blue-200' },
  { id: 'records', label: 'Hồ sơ bệnh án điện tử', shortLabel: 'Hồ sơ', path: '/records', icon: FileText, badge: 'ICD-10', badgeColor: 'bg-indigo-50 text-indigo-600 border-indigo-200' },
  { id: 'emergency', label: 'Cấp cứu Red Flag 115', shortLabel: 'Cấp cứu', path: '/emergency', icon: ShieldAlert, badge: '115', badgeColor: 'bg-rose-50 text-rose-600 border-rose-200' },
  { id: 'protocol', label: 'Phác đồ điều trị Bộ Y Tế', shortLabel: 'Phác đồ', path: '/protocols', icon: BookOpen, badge: '640+', badgeColor: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
  { id: 'icd10', label: 'Tra cứu mã bệnh ICD-10', shortLabel: 'Tra cứu', path: '/lookup', icon: Search, badge: '211 Mã', badgeColor: 'bg-blue-50 text-blue-600 border-blue-200' },
  { id: 'drug', label: 'Dược thư & Đơn thuốc', shortLabel: 'Dược thư', path: '/drugs', icon: Pill, badge: 'Tương tác', badgeColor: 'bg-amber-50 text-amber-700 border-amber-200' },
  { id: 'admin', label: 'Quản trị & Kiểm định QA', shortLabel: 'Quản trị', path: '/admin', icon: Database, badge: 'Admin', badgeColor: 'bg-emerald-50 text-emerald-700 border-emerald-200', requireAdmin: true },
];

function SidebarContent() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const currentMode = searchParams.get('mode') || '';
  const { isAdmin } = useAuth();
  const { isSidebarCollapsed, toggleSidebar } = useTheme();

  // Filter items based on Admin role
  const visibleItems = NAV_ITEMS.filter((item) => {
    if (item.requireAdmin && !isAdmin) {
      return false; // Hide completely for non-admin users
    }
    return true;
  });

  return (
    <aside
      className={`bg-white border-r border-slate-200/80 flex flex-col h-full flex-shrink-0 select-none transition-all duration-300 ease-in-out relative overflow-hidden shadow-2xs z-20 ${
        isSidebarCollapsed ? 'w-[72px]' : 'w-72'
      }`}
    >
      {/* Category Section Header & Toggle Button */}
      <div
        className={`pt-5 pb-3 flex items-center transition-all ${
          isSidebarCollapsed ? 'justify-center px-2' : 'justify-between px-5'
        }`}
      >
        {!isSidebarCollapsed ? (
          <>
            <div className="flex items-center space-x-2 truncate">
              <span className="text-[11px] font-extrabold text-slate-400 uppercase tracking-wider truncate">
                TRỢ LÝ LÂM SÀNG
              </span>
              {isAdmin && (
                <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 flex-shrink-0">
                  Admin
                </span>
              )}
            </div>
            {/* Collapse toggle button */}
            <button
              type="button"
              onClick={toggleSidebar}
              className="p-1.5 rounded-xl text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors flex-shrink-0"
              title="Thu gọn menu"
            >
              <PanelLeftClose size={18} />
            </button>
          </>
        ) : (
          /* Collapsed Mode: Expand Button */
          <button
            type="button"
            onClick={toggleSidebar}
            className="p-2 rounded-xl text-slate-400 hover:text-blue-600 hover:bg-slate-100 transition-colors"
            title="Mở rộng menu"
          >
            <PanelLeftOpen size={20} />
          </button>
        )}
      </div>

      {/* Navigation Links */}
      <nav
        className={`flex-1 space-y-1.5 overflow-y-auto overflow-x-hidden custom-scrollbar pb-4 transition-all ${
          isSidebarCollapsed ? 'px-2' : 'px-3.5'
        }`}
      >
        {visibleItems.map((item) => {
          let isActive = false;
          if (item.path === '/') {
            isActive = pathname === '/';
          } else if (item.mode) {
            isActive = pathname === item.path && currentMode === item.mode;
          } else {
            isActive = pathname.startsWith(item.path);
          }

          const Icon = item.icon;
          const href = item.mode ? `${item.path}?mode=${item.mode}` : item.path;

          if (isSidebarCollapsed) {
            // Collapsed icon-only mode
            return (
              <Link
                key={item.id}
                href={href}
                title={`${item.label}${item.badge ? ` (${item.badge})` : ''}`}
                className={`w-11 h-11 mx-auto flex items-center justify-center rounded-2xl transition-all relative ${
                  isActive
                    ? 'bg-blue-600 text-white shadow-md shadow-blue-500/25 ring-2 ring-blue-400/40'
                    : 'text-slate-500 hover:bg-slate-100 hover:text-blue-600'
                }`}
              >
                <Icon
                  size={20}
                  className={`flex-shrink-0 transition-transform hover:scale-110 ${
                    isActive ? 'text-white stroke-[2.2]' : 'text-slate-500 hover:text-blue-600'
                  }`}
                />

                {/* Emergency pulse indicator */}
                {item.id === 'emergency' && !isActive && (
                  <span className="absolute top-2 right-2 w-2 h-2 rounded-full bg-rose-500 animate-ping" />
                )}

                {/* Badge dot */}
                {item.badge && !isActive && item.id !== 'emergency' && (
                  <span className="absolute top-2 right-2 w-1.5 h-1.5 rounded-full bg-blue-500" />
                )}
              </Link>
            );
          }

          // Expanded mode
          return (
            <Link
              key={item.id}
              href={href}
              className={`flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all group ${
                isActive
                  ? 'bg-blue-50 text-blue-600 font-bold shadow-2xs ring-1 ring-blue-200/80'
                  : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              }`}
            >
              <div className="flex items-center space-x-3 truncate min-w-0">
                <Icon
                  size={18}
                  className={`flex-shrink-0 transition-colors ${
                    isActive ? 'text-blue-600 stroke-[2.2]' : 'text-slate-400 group-hover:text-blue-600'
                  }`}
                />
                <span className="truncate">{item.label}</span>
              </div>

              {/* Active Indicator */}
              {isActive && (
                <span className="w-2 h-2 rounded-full bg-blue-600 flex-shrink-0 ml-2 shadow-xs" />
              )}

              {item.badge && !isActive && (
                <span
                  className={`text-[10px] font-bold font-mono px-2 py-0.5 rounded-md border flex-shrink-0 ml-2 ${
                    item.badgeColor || 'bg-blue-50 text-blue-600 border-blue-200'
                  }`}
                >
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Bottom Toggle Strip */}
      <div className="p-2 border-t border-slate-100 flex items-center justify-center overflow-hidden">
        <button
          type="button"
          onClick={toggleSidebar}
          className={`w-full flex items-center justify-center py-2 px-3 rounded-xl text-xs font-semibold text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition-colors ${
            isSidebarCollapsed ? 'gap-0' : 'gap-2'
          }`}
          title={isSidebarCollapsed ? 'Mở rộng thanh menu' : 'Thu gọn thanh menu'}
        >
          {isSidebarCollapsed ? (
            <ChevronRight size={18} className="text-slate-400 hover:text-blue-600" />
          ) : (
            <>
              <ChevronLeft size={16} className="text-slate-400" />
              <span className="text-xs text-slate-500">Thu gọn menu</span>
            </>
          )}
        </button>
      </div>
    </aside>
  );
}

export const AppSidebar: React.FC = () => {
  return (
    <Suspense fallback={<aside className="w-72 bg-white border-r border-slate-200/80 h-full" />}>
      <SidebarContent />
    </Suspense>
  );
};
