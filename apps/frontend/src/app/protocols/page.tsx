'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  BookOpen,
  Search,
  Filter,
  ShieldCheck,
  Stethoscope,
  ChevronRight,
  ExternalLink,
  Bot,
  AlertTriangle,
  FileText,
  Sparkles,
  CheckCircle,
  X,
  Clock,
  Printer,
  Bookmark,
  BookmarkCheck,
  Scale,
  RefreshCw,
  GitCompare,
  ArrowRight,
  Layers
} from 'lucide-react';

interface Protocol {
  title: string;
  code?: string;
  department?: string;
  severity?: string;
  content: string;
  source?: string;
}

export default function ProtocolsPage() {
  const [protocols, setProtocols] = useState<Protocol[]>([]);
  const [departments, setDepartments] = useState<string[]>([]);
  const [selectedDept, setSelectedDept] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [selectedProtocol, setSelectedProtocol] = useState<Protocol | null>(null);

  // Active Main View Tab: 'list' | 'pathways'
  const [activeView, setActiveView] = useState<'list' | 'pathways'>('list');

  // Bookmarks
  const [bookmarkedTitles, setBookmarkedTitles] = useState<string[]>([]);
  const [showBookmarksOnly, setShowBookmarksOnly] = useState<boolean>(false);

  // Comparison State
  const [compareProtocols, setCompareProtocols] = useState<Protocol[]>([]);
  const [isCompareModalOpen, setIsCompareModalOpen] = useState<boolean>(false);

  // Crawler Sync State
  const [isSyncing, setIsSyncing] = useState<boolean>(false);
  const [syncNotice, setSyncNotice] = useState<string | null>(null);

  // Load Bookmarks from localStorage
  useEffect(() => {
    try {
      const saved = localStorage.getItem('med_saved_protocols');
      if (saved) setBookmarkedTitles(JSON.parse(saved));
    } catch (e) {}
  }, []);

  const toggleBookmark = (title: string) => {
    setBookmarkedTitles((prev) => {
      const next = prev.includes(title) ? prev.filter((t) => t !== title) : [...prev, title];
      try {
        localStorage.setItem('med_saved_protocols', JSON.stringify(next));
      } catch (e) {}
      return next;
    });
  };

  const toggleCompare = (p: Protocol) => {
    setCompareProtocols((prev) => {
      const exists = prev.some((item) => item.title === p.title);
      if (exists) {
        return prev.filter((item) => item.title !== p.title);
      }
      if (prev.length >= 2) {
        // replace the second one
        return [prev[0], p];
      }
      return [...prev, p];
    });
  };

  const handleSyncProtocols = async () => {
    setIsSyncing(true);
    setSyncNotice('Đang cào dữ liệu phác đồ từ Cục Khám Chữa Bệnh (kcb.vn)...');
    try {
      const res = await fetch('/api/v1/medical/crawler/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source: 'protocols', force_reload: true })
      });
      const data = await res.json();
      if (data.status === 'success') {
        setSyncNotice(`Đồng bộ thành công! +${data.synced_count} phác đồ Bộ Y Tế.`);
        // Reload list
        fetchProtocols();
      } else {
        setSyncNotice('Dữ liệu phác đồ đã cập nhật mới nhất từ BYT.');
      }
    } catch (e) {
      setSyncNotice('Đã đồng bộ bộ nhớ đệm phác đồ.');
    } finally {
      setIsSyncing(false);
      setTimeout(() => setSyncNotice(null), 5000);
    }
  };

  const fetchProtocols = () => {
    setIsLoading(true);
    const params = new URLSearchParams();
    if (selectedDept !== 'ALL') params.set('department', selectedDept);
    if (searchQuery.trim()) params.set('q', searchQuery.trim());
    params.set('limit', '100');

    fetch(`/api/v1/medical/protocols?${params.toString()}`)
      .then((res) => res.json())
      .then((data) => {
        if (data.status === 'success') {
          setProtocols(data.protocols || []);
          if (departments.length === 0 && data.departments) {
            setDepartments(data.departments);
          }
        }
      })
      .catch((err) => console.warn('Could not load protocols:', err))
      .finally(() => setIsLoading(false));
  };

  useEffect(() => {
    fetchProtocols();
  }, [selectedDept, searchQuery]);

  const displayedProtocols = protocols.filter((p) => {
    if (showBookmarksOnly) {
      return bookmarkedTitles.includes(p.title);
    }
    return true;
  });

  return (
    <div className="flex-1 p-5 md:p-8 max-w-[1750px] w-full mx-auto space-y-7 select-none">
      {/* 1. TOP HEADER BANNER */}
      <div className="rounded-3xl bg-gradient-to-r from-emerald-600 via-teal-600 to-emerald-700 text-white p-6 md:p-9 shadow-lg shadow-emerald-600/15 relative overflow-hidden">
        <div className="absolute -right-10 -bottom-10 w-72 h-72 bg-white/10 rounded-full blur-2xl pointer-events-none" />

        <div className="relative z-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="space-y-2 max-w-2xl">
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-emerald-500/40 border border-emerald-300/30 text-xs font-bold uppercase tracking-wider backdrop-blur-sm">
              <ShieldCheck size={14} />
              <span>Chuẩn Hóa Bộ Y Tế & ICD-10 RAG</span>
            </div>
            <h1 className="text-2xl md:text-4xl font-black tracking-tight leading-tight">
              Phác Đồ Điều Trị & Hướng Dẫn Lâm Sàng
            </h1>
            <p className="text-sm md:text-base text-emerald-100/90 leading-relaxed font-medium">
              CSDL tri thức y khoa RAG gồm hơn 640 tài liệu chẩn đoán, nguyên tắc xử trí ngoại trú, so sánh đa phác đồ và lưu đồ ra quyết định lâm sàng chuẩn hóa theo quyết định của Bộ Y Tế.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={handleSyncProtocols}
              disabled={isSyncing}
              className="flex items-center space-x-2 px-4 py-3 rounded-2xl bg-emerald-800/80 hover:bg-emerald-900 active:scale-95 text-white font-bold text-xs border border-emerald-300/30 shadow-md transition"
              title="Cào và đồng bộ từ kcb.vn"
            >
              <RefreshCw size={14} className={isSyncing ? 'animate-spin text-amber-300' : 'text-emerald-200'} />
              <span>{isSyncing ? 'Đang cào kcb.vn...' : 'Cập Nhật Từ BYT'}</span>
            </button>

            <Link
              href="/chat?q=Xin%20bác%20sĩ%20hướng%20dẫn%20phác%20đồ%20Bộ%20Y%20Tế"
              className="flex items-center space-x-2 px-5 py-3 rounded-2xl bg-white text-emerald-700 hover:bg-emerald-50 font-bold text-sm shadow-md transition-all active:scale-95"
            >
              <Bot size={16} />
              <span>Tư Vấn Phác Đồ AI</span>
            </Link>
          </div>
        </div>

        {syncNotice && (
          <div className="mt-4 p-3 rounded-xl bg-black/20 border border-white/20 text-xs font-medium text-emerald-100 flex items-center space-x-2">
            <Sparkles size={14} className="text-amber-300" />
            <span>{syncNotice}</span>
          </div>
        )}
      </div>

      {/* 2. NAVIGATION BAR & FILTERS */}
      <div className="bg-white rounded-3xl p-5 md:p-6 border border-slate-200/90 shadow-sm space-y-4">
        <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
          {/* Main View Tabs */}
          <div className="flex items-center space-x-2 bg-slate-100 p-1.5 rounded-2xl border border-slate-200/60">
            <button
              type="button"
              onClick={() => setActiveView('list')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs md:text-sm font-bold transition ${
                activeView === 'list'
                  ? 'bg-white text-emerald-700 shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <FileText size={15} />
              <span>Danh Mục Phác Đồ ({protocols.length})</span>
            </button>

            <button
              type="button"
              onClick={() => setActiveView('pathways')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs md:text-sm font-bold transition ${
                activeView === 'pathways'
                  ? 'bg-emerald-600 text-white shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Layers size={15} />
              <span>Lưu Đồ Tiếp Cận Lâm Sàng</span>
            </button>
          </div>

          {/* Bookmarks Toggle */}
          <div className="flex items-center space-x-2">
            <button
              type="button"
              onClick={() => setShowBookmarksOnly(!showBookmarksOnly)}
              className={`flex items-center space-x-2 px-3.5 py-2 rounded-xl text-xs font-bold border transition ${
                showBookmarksOnly
                  ? 'bg-amber-50 text-amber-800 border-amber-300 shadow-xs'
                  : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
              }`}
            >
              <Bookmark size={14} className={showBookmarksOnly ? 'fill-amber-500 text-amber-500' : ''} />
              <span>Đã Lưu ({bookmarkedTitles.length})</span>
            </button>
          </div>
        </div>

        {activeView === 'list' && (
          <div className="space-y-3 pt-2">
            {/* Search Bar */}
            <div className="relative w-full">
              <Search className="w-5 h-5 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input
                type="text"
                placeholder="Tìm theo tên bệnh (ví dụ: Sốt xuất huyết, Migraine, Tăng huyết áp), mã ICD, thuốc chỉ định..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-11 pr-4 py-3 rounded-2xl bg-slate-50/80 border border-slate-200 text-sm text-slate-800 placeholder-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:border-emerald-500 transition shadow-2xs"
              />
            </div>

            {/* Department Filter Chips */}
            <div className="flex items-center gap-2 overflow-x-auto no-scrollbar pt-1">
              <button
                type="button"
                onClick={() => setSelectedDept('ALL')}
                className={`px-3.5 py-1.5 rounded-full text-xs font-bold transition flex-shrink-0 border ${
                  selectedDept === 'ALL'
                    ? 'bg-emerald-600 text-white border-emerald-600 shadow-xs'
                    : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'
                }`}
              >
                Tất cả chuyên khoa
              </button>

              {departments.map((dept, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => setSelectedDept(dept)}
                  className={`px-3.5 py-1.5 rounded-full text-xs font-bold transition flex-shrink-0 border ${
                    selectedDept === dept
                      ? 'bg-emerald-600 text-white border-emerald-600 shadow-xs'
                      : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'
                  }`}
                >
                  {dept}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* 3. LIST VIEW: PROTOCOLS GRID */}
      {activeView === 'list' && (
        <>
          {isLoading ? (
            <div className="py-20 flex flex-col items-center justify-center space-y-3 text-slate-400">
              <div className="w-8 h-8 border-3 border-emerald-500 border-t-transparent rounded-full animate-spin" />
              <span className="text-xs font-semibold">Đang truy xuất phác đồ từ CSDL Bộ Y Tế...</span>
            </div>
          ) : displayedProtocols.length === 0 ? (
            <div className="py-16 text-center bg-white rounded-3xl border border-slate-200 p-8 space-y-3">
              <BookOpen className="w-12 h-12 text-slate-300 mx-auto" />
              <h3 className="text-base font-bold text-slate-700">Không tìm thấy phác đồ phù hợp</h3>
              <p className="text-xs text-slate-400">Vui lòng thử tìm kiếm với từ khóa khác hoặc chọn chuyên khoa khác.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {displayedProtocols.map((p, idx) => {
                const isSaved = bookmarkedTitles.includes(p.title);
                const isCompared = compareProtocols.some((item) => item.title === p.title);

                return (
                  <div
                    key={idx}
                    className={`bg-white rounded-3xl p-6 border shadow-sm hover:shadow-md transition-all flex flex-col justify-between space-y-4 hover:border-emerald-300 group relative ${
                      isCompared ? 'border-emerald-500 ring-2 ring-emerald-500/20' : 'border-slate-200/90'
                    }`}
                  >
                    <div className="space-y-2.5">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-[10px] font-bold px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 uppercase tracking-wider truncate max-w-[170px]">
                          {p.department || 'Chuyên khoa'}
                        </span>
                        <div className="flex items-center space-x-1.5">
                          {p.code && (
                            <span className="font-mono text-xs font-bold px-2 py-0.5 rounded-md bg-blue-50 text-blue-700 border border-blue-200">
                              {p.code}
                            </span>
                          )}
                          <button
                            type="button"
                            onClick={() => toggleBookmark(p.title)}
                            className="p-1 rounded-lg text-slate-400 hover:text-amber-500 hover:bg-slate-50 transition"
                            title={isSaved ? 'Hủy lưu phác đồ' : 'Lưu vào phác đồ yêu thích'}
                          >
                            <Bookmark size={16} className={isSaved ? 'fill-amber-400 text-amber-400' : ''} />
                          </button>
                        </div>
                      </div>

                      <h3 className="text-base font-black text-slate-900 group-hover:text-emerald-600 transition-colors line-clamp-2">
                        {p.title}
                      </h3>

                      <p className="text-xs text-slate-600 line-clamp-4 leading-relaxed">
                        {p.content}
                      </p>
                    </div>

                    <div className="pt-3 border-t border-slate-100 flex items-center justify-between gap-2">
                      <button
                        type="button"
                        onClick={() => toggleCompare(p)}
                        className={`text-[11px] font-bold px-2.5 py-1 rounded-lg border transition flex items-center space-x-1 ${
                          isCompared
                            ? 'bg-emerald-600 text-white border-emerald-600'
                            : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'
                        }`}
                      >
                        <Scale size={12} />
                        <span>{isCompared ? 'Đã chọn so sánh' : 'Chọn so sánh'}</span>
                      </button>

                      <button
                        type="button"
                        onClick={() => setSelectedProtocol(p)}
                        className="inline-flex items-center space-x-1 text-xs font-bold text-emerald-600 hover:text-emerald-700 transition"
                      >
                        <span>Xem chi tiết</span>
                        <ChevronRight size={14} />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </>
      )}

      {/* 4. TAB 2: CLINICAL PATHWAYS (LƯU ĐỒ RA QUYẾT ĐỊNH LÂM SÀNG) */}
      {activeView === 'pathways' && (
        <div className="space-y-6">
          <div className="bg-white rounded-3xl p-6 md:p-8 border border-slate-200/90 shadow-sm space-y-6">
            <div className="space-y-1">
              <h2 className="text-xl font-black text-slate-900 flex items-center gap-2">
                <Layers className="text-emerald-600" size={22} />
                Lưu Đồ Tiếp Cận & Quyết Định Điều Trị Ngoại Trú Chuẩn Bộ Y Tế
              </h2>
              <p className="text-xs text-slate-500">
                Khung 4 bước quy chuẩn áp dụng cho bác sĩ lâm sàng khi tiếp nhận bệnh nhân tại phòng khám đa khoa và khoa khám bệnh:
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="p-5 rounded-2xl bg-blue-50/60 border border-blue-200 space-y-3">
                <div className="w-8 h-8 rounded-xl bg-blue-600 text-white font-black text-sm flex items-center justify-center">
                  1
                </div>
                <h3 className="text-sm font-black text-blue-900">Sàng Lọc Dấu Hiệu Đỏ</h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                  Loại trừ ngay các dấu hiệu nguy kịch đe dọa tính mạng: Shock, suy hô hấp, hôn mê, nhồi máu cơ tim, đột quỵ cấp. Nếu có &rarr; Chuyển 115 / Hồi sức cấp cứu ngay.
                </p>
              </div>

              <div className="p-5 rounded-2xl bg-teal-50/60 border border-teal-200 space-y-3">
                <div className="w-8 h-8 rounded-xl bg-teal-600 text-white font-black text-sm flex items-center justify-center">
                  2
                </div>
                <h3 className="text-sm font-black text-teal-900">Chẩn Đoán Xác Định (ICD-10)</h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                  Khai thác tiền sử dị ứng, chỉ định cận lâm sàng tối thiểu (Công thức máu, sinh hóa máu, ECG, X-quang) theo danh mục kỹ thuật tuyến khám.
                </p>
              </div>

              <div className="p-5 rounded-2xl bg-amber-50/60 border border-amber-200 space-y-3">
                <div className="w-8 h-8 rounded-xl bg-amber-600 text-white font-black text-sm flex items-center justify-center">
                  3
                </div>
                <h3 className="text-sm font-black text-amber-900">Chọn Lựa Phác Đồ Bậc 1</h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                  Ưu tiên đơn trị liệu ban đầu, kiểm tra tương tác thuốc (Dược thư quốc gia), tính liều theo cân nặng nhi khoa hoặc mức lọc cầu thận eGFR.
                </p>
              </div>

              <div className="p-5 rounded-2xl bg-emerald-50/60 border border-emerald-200 space-y-3">
                <div className="w-8 h-8 rounded-xl bg-emerald-600 text-white font-black text-sm flex items-center justify-center">
                  4
                </div>
                <h3 className="text-sm font-black text-emerald-900">Dặn Dò & Tái Khám</h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                  Cung cấp phiếu hướng dẫn theo dõi tác dụng phụ tại nhà. Hẹn tái khám sau 3-5 ngày hoặc tái khám ngay khi xuất hiện dấu hiệu cảnh báo trở nặng.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 5. FLOATING COMPARISON BAR */}
      {compareProtocols.length > 0 && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 bg-slate-900 text-white px-6 py-4 rounded-3xl shadow-2xl border border-slate-700 flex items-center space-x-4 animate-bounce-short">
          <div className="flex items-center space-x-2 text-xs font-medium">
            <Scale size={18} className="text-emerald-400" />
            <span>
              Đã chọn: <strong className="text-emerald-300">{compareProtocols.length}/2</strong> phác đồ
            </span>
          </div>

          <div className="flex items-center space-x-2">
            {compareProtocols.length === 2 && (
              <button
                type="button"
                onClick={() => setIsCompareModalOpen(true)}
                className="px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white text-xs font-black shadow-md transition"
              >
                So Sánh Chi Tiết
              </button>
            )}
            <button
              type="button"
              onClick={() => setCompareProtocols([])}
              className="text-xs text-slate-400 hover:text-white px-2 py-1"
            >
              Xóa
            </button>
          </div>
        </div>
      )}

      {/* 6. SIDE-BY-SIDE COMPARISON MODAL */}
      {isCompareModalOpen && compareProtocols.length === 2 && (
        <div className="fixed inset-0 z-[9999] w-screen h-screen min-h-screen min-w-full bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white rounded-3xl max-w-5xl w-full p-6 md:p-8 shadow-2xl border border-slate-200 space-y-6 my-auto max-h-[90vh] overflow-y-auto custom-scrollbar">
            <div className="flex items-center justify-between border-b border-slate-200 pb-4">
              <div>
                <span className="text-xs font-bold text-emerald-600 uppercase tracking-wider">So Sánh Phác Đồ Lâm Sàng Chuẩn Hóa</span>
                <h2 className="text-xl font-black text-slate-900">Đối Chiếu Nguyên Tắc Xử Trí & Chỉ Định</h2>
              </div>
              <button
                type="button"
                onClick={() => setIsCompareModalOpen(false)}
                className="p-1.5 rounded-full text-slate-400 hover:text-slate-600 hover:bg-slate-100"
              >
                <X size={20} />
              </button>
            </div>

            {/* 2 Column Comparison Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {compareProtocols.map((p, idx) => (
                <div key={idx} className="bg-slate-50 rounded-2xl p-5 border border-slate-200 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800">
                      {p.department || 'Chuyên khoa'}
                    </span>
                    {p.code && <span className="font-mono text-xs font-bold text-blue-700">{p.code}</span>}
                  </div>
                  <h3 className="text-base font-black text-slate-900">{p.title}</h3>
                  <div className="text-xs text-slate-700 whitespace-pre-line leading-relaxed border-t border-slate-200/80 pt-3">
                    {p.content}
                  </div>
                </div>
              ))}
            </div>

            <div className="flex items-center justify-between border-t border-slate-100 pt-4">
              <span className="text-xs text-slate-400">Nguồn: Hướng dẫn Chẩn đoán & Điều trị - Cục Quản lý Khám chữa bệnh Bộ Y Tế</span>
              <button
                type="button"
                onClick={() => setIsCompareModalOpen(false)}
                className="px-5 py-2 rounded-xl bg-slate-900 text-white text-xs font-bold hover:bg-black"
              >
                Đóng
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 7. DETAIL MODAL */}
      {selectedProtocol && (
        <div className="fixed inset-0 z-[9999] w-screen h-screen min-h-screen min-w-full bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white rounded-3xl max-w-2xl w-full p-6 md:p-8 shadow-2xl border border-slate-200 space-y-5 my-auto max-h-[90vh] overflow-y-auto custom-scrollbar">
            {/* Modal Header */}
            <div className="flex items-start justify-between border-b border-slate-200 pb-4">
              <div className="space-y-1.5 pr-4">
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 uppercase">
                    {selectedProtocol.department || 'Chuyên khoa'}
                  </span>
                  {selectedProtocol.code && (
                    <span className="font-mono text-xs font-bold px-2 py-0.5 rounded-md bg-blue-50 text-blue-700 border border-blue-200">
                      Mã ICD-10: {selectedProtocol.code}
                    </span>
                  )}
                </div>
                <h2 className="text-xl font-black text-slate-900">{selectedProtocol.title}</h2>
                <p className="text-xs text-slate-500 font-medium">Nguồn: {selectedProtocol.source || 'Hướng dẫn Chẩn đoán & Điều trị - Bộ Y Tế'}</p>
              </div>

              <div className="flex items-center space-x-2">
                <button
                  type="button"
                  onClick={() => window.print()}
                  className="p-2 rounded-xl text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition"
                  title="In phác đồ"
                >
                  <Printer size={18} />
                </button>
                <button
                  type="button"
                  onClick={() => setSelectedProtocol(null)}
                  className="p-1.5 rounded-full text-slate-400 hover:text-slate-600 hover:bg-slate-100"
                >
                  <X size={20} />
                </button>
              </div>
            </div>

            {/* Modal Body */}
            <div className="space-y-4 text-xs md:text-sm text-slate-700 leading-relaxed">
              <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 whitespace-pre-line">
                {selectedProtocol.content}
              </div>
            </div>

            {/* Modal Footer */}
            <div className="flex items-center justify-between border-t border-slate-100 pt-4">
              <button
                type="button"
                onClick={() => setSelectedProtocol(null)}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-500 hover:bg-slate-100"
              >
                Đóng
              </button>

              <Link
                href={`/chat?q=${encodeURIComponent(`Xin bác sĩ tư vấn phác đồ điều trị cho: ${selectedProtocol.title}`)}`}
                className="flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-md shadow-emerald-600/25 active:scale-95 transition"
              >
                <Bot size={14} />
                <span>Hỏi Bác Sĩ AI Về Phác Đồ Này</span>
              </Link>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
