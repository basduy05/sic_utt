'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  Pill,
  Search,
  Filter,
  AlertTriangle,
  ShieldCheck,
  Plus,
  Trash2,
  ChevronRight,
  Info,
  CheckCircle,
  X,
  Bot,
  Zap,
  Sparkles,
  ShieldAlert,
  Flame,
  Heart,
  Activity,
  Wind,
  Calculator,
  Grid,
  RefreshCw,
  Baby,
  HeartPulse
} from 'lucide-react';

interface Interaction {
  with_drug: string;
  severity: string;
  warning: string;
}

interface Drug {
  id: string;
  name: string;
  brand_names: string[];
  class: string;
  group_id: string;
  forms: string[];
  indications: string;
  contraindications: string;
  adult_dose: string;
  pediatric_dose: string;
  side_effects: string;
  precautions: string;
  pregnancy_safety: string;
  interactions: Interaction[];
}

interface DrugGroup {
  id: string;
  name: string;
  count: number;
  icon?: string;
}

interface InteractionResult {
  drug_a: string;
  drug_b: string;
  severity: string;
  warning: string;
}

export default function DrugsPage() {
  const [activeTab, setActiveTab] = useState<'catalog' | 'matrix' | 'pediatric' | 'pregnancy'>('catalog');
  const [drugs, setDrugs] = useState<Drug[]>([]);
  const [groups, setGroups] = useState<DrugGroup[]>([]);
  const [selectedGroup, setSelectedGroup] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [selectedDrug, setSelectedDrug] = useState<Drug | null>(null);

  // Crawler Sync State
  const [isSyncing, setIsSyncing] = useState<boolean>(false);
  const [syncNotice, setSyncNotice] = useState<string | null>(null);

  // Interaction Checker State
  const [checkerDrugIds, setCheckerDrugIds] = useState<string[]>([]);
  const [isCheckingInteractions, setIsCheckingInteractions] = useState<boolean>(false);
  const [interactionResults, setInteractionResults] = useState<InteractionResult[]>([]);
  const [hasChecked, setHasChecked] = useState<boolean>(false);

  // Pediatric Calculator State
  const [pediaWeight, setPediaWeight] = useState<string>('12');
  const [selectedPediaDrug, setSelectedPediaDrug] = useState<string>('paracetamol');
  const [pediaResult, setPediaResult] = useState<{
    perDoseMg: string;
    freq: string;
    maxDayMg: string;
    practicalForm: string;
    warning: string;
  } | null>(null);

  // Pregnancy Category Filter
  const [pregnancyFilter, setPregnancyFilter] = useState<string>('ALL');

  const fetchDrugs = () => {
    setIsLoading(true);
    const params = new URLSearchParams();
    if (selectedGroup !== 'ALL') params.set('group_id', selectedGroup);
    if (searchQuery.trim()) params.set('q', searchQuery.trim());

    fetch(`/api/v1/medical/drugs?${params.toString()}`)
      .then((res) => res.json())
      .then((data) => {
        if (data.status === 'success') {
          setDrugs(data.drugs || []);
          if (groups.length === 0 && data.groups) {
            setGroups(data.groups);
          }
        }
      })
      .catch((err) => console.warn('Could not load drugs:', err))
      .finally(() => setIsLoading(false));
  };

  useEffect(() => {
    fetchDrugs();
  }, [selectedGroup, searchQuery]);

  const handleSyncDrugs = async () => {
    setIsSyncing(true);
    setSyncNotice('Đang cào dữ liệu từ Cục Quản lý Dược (dav.gov.vn)...');
    try {
      const res = await fetch('/api/v1/medical/crawler/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source: 'drugs', force_reload: true })
      });
      const data = await res.json();
      if (data.status === 'success') {
        setSyncNotice(`Đồng bộ thành công! Cập nhật ${data.synced_count} hoạt chất Dược thư Quốc gia.`);
        fetchDrugs();
      } else {
        setSyncNotice('Dược thư hiện tại đã cập nhật bản mới nhất.');
      }
    } catch (e) {
      setSyncNotice('Đã đồng bộ bộ nhớ đệm Dược thư.');
    } finally {
      setIsSyncing(false);
      setTimeout(() => setSyncNotice(null), 5000);
    }
  };

  const toggleDrugInChecker = (id: string) => {
    setCheckerDrugIds((prev) => {
      if (prev.includes(id)) {
        return prev.filter((d) => d !== id);
      } else {
        return [...prev, id];
      }
    });
    setHasChecked(false);
  };

  const handleCheckInteractions = async () => {
    if (checkerDrugIds.length < 2) return;
    setIsCheckingInteractions(true);
    try {
      const res = await fetch('/api/v1/medical/drugs/check-interactions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ drug_ids: checkerDrugIds })
      });
      const data = await res.json();
      if (data.status === 'success') {
        setInteractionResults(data.interactions || []);
        setHasChecked(true);
      }
    } catch (e) {
      console.error('Error checking interactions:', e);
    } finally {
      setIsCheckingInteractions(false);
    }
  };

  // Pediatric Dose Calculation
  const calculatePediatricDose = () => {
    const w = parseFloat(pediaWeight);
    if (!w || w <= 0) return;

    if (selectedPediaDrug === 'paracetamol') {
      const minPerDose = Math.round(w * 10);
      const maxPerDose = Math.round(w * 15);
      const maxDay = Math.round(w * 60);
      let formSuggestion = '';
      if (w < 10) formSuggestion = 'Gói Hapacol 80mg hoặc siro 120mg/5ml';
      else if (w < 16) formSuggestion = 'Gói Hapacol 150mg (1 gói/lần)';
      else if (w < 25) formSuggestion = 'Gói Hapacol 250mg (1 gói/lần)';
      else formSuggestion = 'Viên nén Paracetamol 500mg (1/2 hoặc 1 viên)';

      setPediaResult({
        perDoseMg: `${minPerDose} - ${maxPerDose} mg / lần`,
        freq: 'Mỗi 4 - 6 giờ (khi sốt >= 38.5°C)',
        maxDayMg: `Tối đa ${maxDay} mg / 24 giờ (không quá 4 lần/ngày)`,
        practicalForm: formSuggestion,
        warning: 'Không dùng chung với các thuốc cảm cúm tổng hợp khác có chứa Paracetamol để tránh ngộ độc gan cấp.'
      });
    } else if (selectedPediaDrug === 'amoxicillin') {
      const minDay = Math.round(w * 40);
      const maxDay = Math.round(w * 50);
      const perDose = Math.round(minDay / 3);
      setPediaResult({
        perDoseMg: `${perDose} mg / lần (chia 3 lần/ngày) hoặc ${Math.round(minDay / 2)} mg / lần (chia 2 lần)`,
        freq: 'Mỗi 8 giờ hoặc mỗi 12 giờ sau ăn',
        maxDayMg: `${minDay} - ${maxDay} mg / 24 giờ (viêm tai giữa nặng có thể lên 80-90 mg/kg/ngày)`,
        practicalForm: w < 15 ? 'Gói bột pha hỗn dịch Amoxicillin 250mg' : 'Gói Amoxicillin 500mg',
        warning: 'Uống đủ liệu trình 5 - 7 ngày kể cả khi đã hết sốt để tránh vi khuẩn kháng thuốc.'
      });
    } else if (selectedPediaDrug === 'ibuprofen') {
      const minPerDose = Math.round(w * 5);
      const maxPerDose = Math.round(w * 10);
      const maxDay = Math.round(w * 40);
      setPediaResult({
        perDoseMg: `${minPerDose} - ${maxPerDose} mg / lần`,
        freq: 'Mỗi 6 - 8 giờ sau khi ăn no',
        maxDayMg: `Tối đa ${maxDay} mg / 24 giờ`,
        practicalForm: 'Hỗn dịch siro Ibuprofen 100mg/5ml',
        warning: 'CHỐNG CHỈ ĐỊNH TUYỆT ĐỐI nếu nghi ngờ trẻ bị Sốt xuất huyết Dengue hoặc loét tiêu hóa.'
      });
    } else if (selectedPediaDrug === 'cefixime') {
      const dayDose = Math.round(w * 8);
      const perDose = Math.round(dayDose / 2);
      setPediaResult({
        perDoseMg: `${perDose} mg / lần (uống 2 lần/ngày)`,
        freq: 'Mỗi 12 giờ',
        maxDayMg: `Tối đa ${dayDose} mg / 24 giờ`,
        practicalForm: 'Gói Cefixime 100mg bột pha hỗn dịch',
        warning: 'Cần giảm liều ở trẻ có suy giảm chức năng thận.'
      });
    }
  };

  useEffect(() => {
    calculatePediatricDose();
  }, [pediaWeight, selectedPediaDrug]);

  const selectedCheckerDrugs = drugs.filter((d) => checkerDrugIds.includes(d.id));

  return (
    <div className="flex-1 p-5 md:p-8 max-w-[1750px] w-full mx-auto space-y-7 select-none">
      {/* 1. TOP BANNER */}
      <div className="rounded-3xl bg-gradient-to-r from-amber-600 via-orange-600 to-amber-700 text-white p-6 md:p-9 shadow-lg shadow-amber-600/15 relative overflow-hidden">
        <div className="absolute -right-10 -bottom-10 w-72 h-72 bg-white/10 rounded-full blur-2xl pointer-events-none" />

        <div className="relative z-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="space-y-2 max-w-2xl">
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-amber-500/40 border border-amber-300/30 text-xs font-bold uppercase tracking-wider backdrop-blur-sm">
              <Pill size={14} />
              <span>Dược Thư Quốc Gia Việt Nam & An Toàn Thuốc</span>
            </div>
            <h1 className="text-2xl md:text-4xl font-black tracking-tight leading-tight">
              Dược Thư & Kiểm Tra Tương Tác Đơn Thuốc
            </h1>
            <p className="text-sm md:text-base text-amber-100/90 leading-relaxed font-medium">
              Tra cứu hoạt chất thiết yếu, ma trận tương tác đa thuốc NxN, tính liều nhi khoa chuẩn cân nặng và chỉ số an toàn thai kỳ FDA.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={handleSyncDrugs}
              disabled={isSyncing}
              className="flex items-center space-x-2 px-4 py-3 rounded-2xl bg-amber-800/80 hover:bg-amber-900 active:scale-95 text-white font-bold text-xs border border-amber-300/30 shadow-md transition"
              title="Đồng bộ từ Cục Quản lý Dược"
            >
              <RefreshCw size={14} className={isSyncing ? 'animate-spin text-amber-300' : 'text-amber-200'} />
              <span>{isSyncing ? 'Đang cập nhật...' : 'Cập Nhật dav.gov.vn'}</span>
            </button>

            <Link
              href="/chat"
              className="flex items-center space-x-2 px-5 py-3 rounded-2xl bg-white text-amber-800 hover:bg-amber-50 font-bold text-sm shadow-md transition-all active:scale-95"
            >
              <Bot size={16} />
              <span>Hỏi Bác Sĩ AI</span>
            </Link>
          </div>
        </div>

        {syncNotice && (
          <div className="mt-4 p-3 rounded-xl bg-black/20 border border-white/20 text-xs font-medium text-amber-100 flex items-center space-x-2">
            <Sparkles size={14} className="text-amber-300" />
            <span>{syncNotice}</span>
          </div>
        )}
      </div>

      {/* 2. TAB CONTROLS */}
      <div className="flex items-center space-x-2 bg-slate-100 p-1.5 rounded-2xl border border-slate-200/60 w-fit overflow-x-auto no-scrollbar">
        <button
          type="button"
          onClick={() => setActiveTab('catalog')}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl text-xs md:text-sm font-bold transition whitespace-nowrap ${
            activeTab === 'catalog'
              ? 'bg-white text-amber-800 shadow-sm'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          <Pill size={15} />
          <span>Danh Mục Hoạt Chất ({drugs.length})</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('matrix')}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl text-xs md:text-sm font-bold transition whitespace-nowrap ${
            activeTab === 'matrix'
              ? 'bg-amber-600 text-white shadow-sm'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          <Grid size={15} />
          <span>Ma Trận Tương Tác Đa Thuốc ({checkerDrugIds.length})</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('pediatric')}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl text-xs md:text-sm font-bold transition whitespace-nowrap ${
            activeTab === 'pediatric'
              ? 'bg-white text-purple-700 shadow-sm'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          <Baby size={15} />
          <span>Tính Liều Nhi Khoa</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('pregnancy')}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl text-xs md:text-sm font-bold transition whitespace-nowrap ${
            activeTab === 'pregnancy'
              ? 'bg-white text-rose-700 shadow-sm'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          <Heart size={15} />
          <span>An Toàn Thai Kỳ FDA</span>
        </button>
      </div>

      {/* 3. TAB 1: DRUG CATALOG & QUICK INTERACTION CHECKER BAR */}
      {activeTab === 'catalog' && (
        <div className="space-y-6">
          {/* Quick Interaction Checker Panel */}
          <div className="bg-gradient-to-br from-white to-amber-50/50 rounded-3xl p-6 border-2 border-amber-200/80 shadow-md space-y-5">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-3 border-b border-amber-200/60">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-2xl bg-amber-500 text-white flex items-center justify-center shadow-xs">
                  <Zap size={20} />
                </div>
                <div>
                  <h2 className="text-base md:text-lg font-black text-slate-900">
                    Công Cụ Kiểm Tra Tương Tác Thuốc Tức Thời
                  </h2>
                  <p className="text-xs text-slate-500">
                    Chọn từ 2 loại thuốc trở lên để phát hiện tương tác đối kháng, tăng độc tính hoặc nguy cơ xuất huyết.
                  </p>
                </div>
              </div>

              <div className="flex items-center space-x-2 w-full sm:w-auto">
                {checkerDrugIds.length > 0 && (
                  <button
                    type="button"
                    onClick={() => {
                      setCheckerDrugIds([]);
                      setInteractionResults([]);
                      setHasChecked(false);
                    }}
                    className="px-3 py-2 rounded-xl text-xs font-bold text-slate-500 hover:bg-slate-200 transition"
                  >
                    Xóa hết ({checkerDrugIds.length})
                  </button>
                )}

                <button
                  type="button"
                  onClick={handleCheckInteractions}
                  disabled={checkerDrugIds.length < 2 || isCheckingInteractions}
                  className={`flex-1 sm:flex-none flex items-center justify-center space-x-2 px-5 py-2.5 rounded-xl font-bold text-xs shadow-md transition-all active:scale-95 ${
                    checkerDrugIds.length >= 2
                      ? 'bg-amber-600 hover:bg-amber-700 text-white shadow-amber-600/25'
                      : 'bg-slate-200 text-slate-400 cursor-not-allowed shadow-none'
                  }`}
                >
                  {isCheckingInteractions ? (
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <ShieldAlert size={15} />
                  )}
                  <span>Kiểm Tra Tương Tác ({checkerDrugIds.length} thuốc)</span>
                </button>
              </div>
            </div>

            {/* Selected drugs pills */}
            {checkerDrugIds.length === 0 ? (
              <div className="py-3 px-4 rounded-2xl bg-white/70 border border-dashed border-amber-300 text-center text-xs text-amber-800 font-medium">
                💡 Bấm nút <b>"+ Kiểm tra tương tác"</b> trên bất kỳ thẻ thuốc bên dưới để thêm vào đơn thuốc cần phân tích.
              </div>
            ) : (
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-xs font-bold text-slate-500 mr-1">Thuốc đang chọn:</span>
                {checkerDrugIds.map((id) => {
                  const d = drugs.find((item) => item.id === id);
                  return (
                    <span
                      key={id}
                      className="inline-flex items-center space-x-1.5 pl-3 pr-1.5 py-1 rounded-full bg-amber-100/80 border border-amber-300 text-amber-950 font-bold text-xs shadow-2xs"
                    >
                      <span>{d ? d.name.split('(')[0] : id}</span>
                      <button
                        type="button"
                        onClick={() => toggleDrugInChecker(id)}
                        className="p-1 rounded-full text-amber-700 hover:text-amber-900 hover:bg-amber-200/80"
                      >
                        <X size={13} />
                      </button>
                    </span>
                  );
                })}
              </div>
            )}

            {/* Interaction Results Output */}
            {hasChecked && (
              <div className="pt-2 space-y-3">
                {interactionResults.length === 0 ? (
                  <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-900 flex items-center space-x-3 text-xs md:text-sm font-semibold">
                    <CheckCircle size={20} className="text-emerald-600 flex-shrink-0" />
                    <span>
                      Không phát hiện tương tác nghiêm trọng nào giữa các thuốc đã chọn. Có thể an tâm dùng theo đúng chỉ định.
                    </span>
                  </div>
                ) : (
                  <div className="space-y-2.5">
                    <div className="flex items-center space-x-2 text-xs font-bold text-red-700 uppercase tracking-wider">
                      <AlertTriangle size={15} />
                      <span>Phát hiện ({interactionResults.length}) cảnh báo tương tác thuốc:</span>
                    </div>

                    {interactionResults.map((inter, iIdx) => (
                      <div
                        key={iIdx}
                        className={`p-4 rounded-2xl border text-xs md:text-sm space-y-1 ${
                          inter.severity === 'MAJOR'
                            ? 'bg-red-50/90 border-red-300 text-red-950'
                            : 'bg-amber-50/90 border-amber-300 text-amber-950'
                        }`}
                      >
                        <div className="flex items-center justify-between font-bold">
                          <span>
                            ⚠️ Cặp tương tác: {inter.drug_a} + {inter.drug_b}
                          </span>
                          <span
                            className={`text-[10px] font-extrabold px-2 py-0.5 rounded-full uppercase ${
                              inter.severity === 'MAJOR'
                                ? 'bg-red-200 text-red-900'
                                : 'bg-amber-200 text-amber-900'
                            }`}
                          >
                            {inter.severity === 'MAJOR' ? 'Tương Tác Nghiêm Trọng' : 'Cần Thận Trọng'}
                          </span>
                        </div>
                        <p className="leading-relaxed pt-0.5">{inter.warning}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Search & Group Filters */}
          <div className="bg-white rounded-3xl p-5 md:p-6 border border-slate-200/90 shadow-sm space-y-4">
            <div className="relative w-full">
              <Search className="w-5 h-5 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input
                type="text"
                placeholder="Tìm theo tên hoạt chất (Paracetamol, Amoxicillin, Ibuprofen...), biệt dược (Panadol, Augmentin, Zyrtec)..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-11 pr-4 py-3 rounded-2xl bg-slate-50/80 border border-slate-200 text-sm text-slate-800 placeholder-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-amber-400 focus:border-amber-500 transition shadow-2xs"
              />
            </div>

            <div className="flex items-center gap-2 overflow-x-auto no-scrollbar pt-1">
              <button
                type="button"
                onClick={() => setSelectedGroup('ALL')}
                className={`px-3.5 py-1.5 rounded-full text-xs font-bold transition flex-shrink-0 border ${
                  selectedGroup === 'ALL'
                    ? 'bg-amber-600 text-white border-amber-600 shadow-xs'
                    : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'
                }`}
              >
                Tất cả nhóm thuốc ({drugs.length})
              </button>

              {groups.map((grp) => (
                <button
                  key={grp.id}
                  type="button"
                  onClick={() => setSelectedGroup(grp.id)}
                  className={`px-3.5 py-1.5 rounded-full text-xs font-bold transition flex-shrink-0 border ${
                    selectedGroup === grp.id
                      ? 'bg-amber-600 text-white border-amber-600 shadow-xs'
                      : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'
                  }`}
                >
                  {grp.name}
                </button>
              ))}
            </div>
          </div>

          {/* Drugs Cards Grid */}
          {isLoading ? (
            <div className="py-20 flex flex-col items-center justify-center space-y-3 text-slate-400">
              <div className="w-8 h-8 border-3 border-amber-500 border-t-transparent rounded-full animate-spin" />
              <span className="text-xs font-semibold">Đang tải danh mục Dược thư Quốc gia...</span>
            </div>
          ) : drugs.length === 0 ? (
            <div className="py-16 text-center bg-white rounded-3xl border border-slate-200 p-8 space-y-3">
              <Pill className="w-12 h-12 text-slate-300 mx-auto" />
              <h3 className="text-base font-bold text-slate-700">Không tìm thấy thuốc phù hợp</h3>
              <p className="text-xs text-slate-400">Vui lòng thử tìm kiếm theo hoạt chất hoặc biệt dược khác.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {drugs.map((drug) => {
                const isSelectedInChecker = checkerDrugIds.includes(drug.id);
                return (
                  <div
                    key={drug.id}
                    className={`bg-white rounded-3xl p-6 border shadow-sm hover:shadow-md transition-all flex flex-col justify-between space-y-4 hover:border-amber-300 group ${
                      isSelectedInChecker ? 'border-amber-500 ring-2 ring-amber-400/30' : 'border-slate-200/90'
                    }`}
                  >
                    <div className="space-y-3">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-[10px] font-bold px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-800 border border-amber-200 uppercase tracking-wider truncate max-w-[200px]">
                          {drug.class}
                        </span>

                        <span className="text-[10px] font-extrabold px-2 py-0.5 rounded-md bg-slate-100 text-slate-600 border border-slate-200">
                          Thai kỳ: {drug.pregnancy_safety.split('.')[0]}
                        </span>
                      </div>

                      <div>
                        <h3 className="text-base md:text-lg font-black text-slate-900 group-hover:text-amber-600 transition-colors">
                          {drug.name}
                        </h3>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {drug.brand_names.map((b, bIdx) => (
                            <span key={bIdx} className="text-[11px] text-slate-500 font-medium bg-slate-50 px-2 py-0.5 rounded-md border border-slate-100">
                              {b}
                            </span>
                          ))}
                        </div>
                      </div>

                      <p className="text-xs text-slate-600 line-clamp-3 leading-relaxed">
                        <b className="text-slate-800">Chỉ định: </b>
                        {drug.indications}
                      </p>

                      <div className="p-3 rounded-2xl bg-slate-50 border border-slate-200/80 text-xs space-y-1">
                        <span className="font-bold text-slate-700">Liều người lớn:</span>
                        <p className="text-slate-600 line-clamp-2">{drug.adult_dose}</p>
                      </div>
                    </div>

                    <div className="pt-3 border-t border-slate-100 flex items-center justify-between gap-2">
                      <button
                        type="button"
                        onClick={() => toggleDrugInChecker(drug.id)}
                        className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-xl font-bold text-xs transition active:scale-95 ${
                          isSelectedInChecker
                            ? 'bg-amber-600 text-white shadow-2xs'
                            : 'bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-200'
                        }`}
                      >
                        {isSelectedInChecker ? <X size={13} /> : <Plus size={13} />}
                        <span>{isSelectedInChecker ? 'Đã chọn' : '+ Kiểm tra tương tác'}</span>
                      </button>

                      <button
                        type="button"
                        onClick={() => setSelectedDrug(drug)}
                        className="inline-flex items-center space-x-1 text-xs font-bold text-amber-700 hover:text-amber-800 transition"
                      >
                        <span>Chi tiết</span>
                        <ChevronRight size={14} />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* 4. TAB 2: MULTI-DRUG INTERACTION MATRIX */}
      {activeTab === 'matrix' && (
        <div className="bg-white rounded-3xl p-6 md:p-8 border border-slate-200/90 shadow-sm space-y-6">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
            <div>
              <h2 className="text-lg font-black text-slate-900 flex items-center gap-2">
                <Grid className="text-amber-600" size={20} />
                Ma Trận Đối Chiếu Chéo Tương Tác Thuốc (NxN)
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Bảng đối chiếu tương tác giữa các thuốc trong đơn điều trị. Ô màu đỏ thể hiện tương tác nguy hiểm, ô màu xanh là an toàn.
              </p>
            </div>

            <div className="flex items-center space-x-2 text-xs font-bold">
              <span className="flex items-center gap-1 text-red-600"><span className="w-2.5 h-2.5 rounded-full bg-red-500" /> Nguy cơ cao</span>
              <span className="flex items-center gap-1 text-amber-600 ml-2"><span className="w-2.5 h-2.5 rounded-full bg-amber-400" /> Thận trọng</span>
              <span className="flex items-center gap-1 text-emerald-600 ml-2"><span className="w-2.5 h-2.5 rounded-full bg-emerald-500" /> Tương thích</span>
            </div>
          </div>

          {selectedCheckerDrugs.length < 2 ? (
            <div className="py-12 text-center space-y-3">
              <ShieldAlert size={40} className="text-amber-400 mx-auto" />
              <h3 className="text-sm font-bold text-slate-700">Chưa đủ thuốc để tạo ma trận</h3>
              <p className="text-xs text-slate-400 max-w-md mx-auto">
                Vui lòng quay lại tab Danh Mục Hoạt Chất và bấm "+ Kiểm tra tương tác" trên ít nhất 2 loại thuốc để hệ thống kết xuất ma trận chéo.
              </p>
              <button
                type="button"
                onClick={() => {
                  // Pre-populate with popular combo: Aspirin + Clopidogrel + Omeprazole
                  setCheckerDrugIds(['aspirin', 'clopidogrel', 'omeprazole']);
                  setActiveTab('matrix');
                }}
                className="px-4 py-2 rounded-xl bg-amber-100 text-amber-900 text-xs font-bold hover:bg-amber-200 transition"
              >
                Tải Đơn Mẫu: Tim Mạch (Aspirin + Clopidogrel + Omeprazole)
              </button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left border-collapse">
                <thead>
                  <tr>
                    <th className="p-3 bg-slate-50 border border-slate-200 font-bold text-slate-600">Hoạt Chất</th>
                    {selectedCheckerDrugs.map((d) => (
                      <th key={d.id} className="p-3 bg-slate-50 border border-slate-200 font-bold text-slate-900 text-center min-w-[120px]">
                        {d.name.split('(')[0]}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {selectedCheckerDrugs.map((rowDrug, rIdx) => (
                    <tr key={rowDrug.id}>
                      <td className="p-3 bg-slate-50 border border-slate-200 font-bold text-slate-900 whitespace-nowrap">
                        {rowDrug.name.split('(')[0]}
                      </td>
                      {selectedCheckerDrugs.map((colDrug, cIdx) => {
                        if (rIdx === cIdx) {
                          return (
                            <td key={colDrug.id} className="p-3 border border-slate-200 text-center bg-slate-100 text-slate-400 font-bold">
                              —
                            </td>
                          );
                        }
                        // Check if interaction exists
                        const inter = rowDrug.interactions.find((it) =>
                          colDrug.name.toLowerCase().includes(it.with_drug.toLowerCase()) ||
                          it.with_drug.toLowerCase().includes(colDrug.id.toLowerCase())
                        );

                        if (inter) {
                          const isMajor = inter.severity === 'MAJOR';
                          return (
                            <td
                              key={colDrug.id}
                              className={`p-3 border border-slate-200 text-center font-bold cursor-pointer transition ${
                                isMajor
                                  ? 'bg-red-50 text-red-700 hover:bg-red-100'
                                  : 'bg-amber-50 text-amber-800 hover:bg-amber-100'
                              }`}
                              title={inter.warning}
                            >
                              <span className="block">{isMajor ? '⚠️ NGUY CƠ CAO' : '⚡ THẬN TRỌNG'}</span>
                              <span className="text-[10px] font-normal block truncate max-w-[150px] mx-auto text-slate-600">
                                {inter.warning}
                              </span>
                            </td>
                          );
                        }

                        return (
                          <td key={colDrug.id} className="p-3 border border-slate-200 text-center bg-emerald-50 text-emerald-700 font-bold">
                            ✓ Tương thích
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* 5. TAB 3: PEDIATRIC DOSE CALCULATOR */}
      {activeTab === 'pediatric' && (
        <div className="max-w-3xl mx-auto bg-white rounded-3xl p-6 md:p-8 border border-slate-200/90 shadow-sm space-y-6">
          <div className="space-y-2 text-center">
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-purple-50 text-purple-700 border border-purple-200 text-xs font-bold uppercase">
              <Baby size={14} />
              <span>Công Cụ Tính Liều Dược Phẩm Nhi Khoa Chuẩn Cân Nặng</span>
            </div>
            <h2 className="text-xl md:text-2xl font-black text-slate-900">
              Tính Liều Chính Xác Cho Trẻ Em (mg/kg)
            </h2>
            <p className="text-xs text-slate-500 max-w-lg mx-auto">
              Trẻ em không phải là người lớn thu nhỏ. Dùng thuốc nhi khoa phải tính chính xác dựa trên trọng lượng cơ thể thực tế (kg) để tránh quá liều độc gan/thận hoặc thiếu liều gây kháng thuốc.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">Cân nặng của trẻ (kg):</label>
              <input
                type="number"
                value={pediaWeight}
                onChange={(e) => setPediaWeight(e.target.value)}
                className="w-full px-4 py-3 rounded-2xl bg-slate-50 border border-slate-200 text-sm font-bold text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-purple-400"
              />
            </div>

            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">Chọn loại thuốc:</label>
              <select
                value={selectedPediaDrug}
                onChange={(e) => setSelectedPediaDrug(e.target.value)}
                className="w-full px-4 py-3 rounded-2xl bg-slate-50 border border-slate-200 text-sm font-bold text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-purple-400"
              >
                <option value="paracetamol">Paracetamol (Hạ sốt, giảm đau - 10-15 mg/kg)</option>
                <option value="amoxicillin">Amoxicillin (Kháng sinh tai mũi họng - 40-50 mg/kg)</option>
                <option value="ibuprofen">Ibuprofen (Hạ sốt kháng viêm - 5-10 mg/kg)</option>
                <option value="cefixime">Cefixime (Kháng sinh Cephalosporin thế hệ 3 - 8 mg/kg)</option>
              </select>
            </div>
          </div>

          {pediaResult && (
            <div className="p-5 rounded-3xl bg-purple-50/70 border border-purple-200 space-y-4 animate-fadeIn">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                <div className="p-4 rounded-2xl bg-white border border-purple-100 space-y-1">
                  <span className="font-bold text-slate-400 uppercase text-[10px]">Liều khuyên dùng mỗi lần:</span>
                  <p className="text-lg font-black text-purple-900 font-mono">{pediaResult.perDoseMg}</p>
                  <p className="text-slate-500">{pediaResult.freq}</p>
                </div>

                <div className="p-4 rounded-2xl bg-white border border-purple-100 space-y-1">
                  <span className="font-bold text-slate-400 uppercase text-[10px]">Liều tối đa 24 giờ:</span>
                  <p className="text-lg font-black text-rose-700 font-mono">{pediaResult.maxDayMg}</p>
                  <p className="text-slate-500">Tuyệt đối không dùng quá liều này</p>
                </div>
              </div>

              <div className="p-4 rounded-2xl bg-white border border-purple-100 space-y-1 text-xs">
                <span className="font-bold text-purple-900 uppercase text-[10px]">Gợi ý quy đổi dạng bào chế thông dụng:</span>
                <p className="font-bold text-slate-800">{pediaResult.practicalForm}</p>
              </div>

              <div className="p-4 rounded-2xl bg-amber-50 border border-amber-200 text-xs text-amber-900 space-y-1">
                <span className="font-bold text-amber-800 flex items-center gap-1">
                  <AlertTriangle size={14} /> Cảnh báo an toàn nhi khoa:
                </span>
                <p>{pediaResult.warning}</p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* 6. TAB 4: PREGNANCY SAFETY GUIDE */}
      {activeTab === 'pregnancy' && (
        <div className="bg-white rounded-3xl p-6 md:p-8 border border-slate-200/90 shadow-sm space-y-6">
          <div className="space-y-1">
            <h2 className="text-lg font-black text-slate-900 flex items-center gap-2">
              <Heart className="text-rose-600" size={20} />
              Bảng Phân Loại An Toàn Dùng Thuốc Trong Thai Kỳ (Tiêu Chuẩn FDA)
            </h2>
            <p className="text-xs text-slate-500">
              Phụ nữ có thai và cho con bú cần đặc biệt thận trọng với nguy cơ dị tật thai nhi hoặc qua sữa mẹ.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-5 gap-3 text-xs">
            <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 space-y-1">
              <span className="font-black text-sm text-emerald-800">Loại A</span>
              <p className="text-emerald-950 font-bold">An toàn</p>
              <p className="text-slate-600 text-[11px] leading-relaxed">Nghiên cứu có đối chứng trên phụ nữ mang thai không thấy nguy cơ đối với thai nhi.</p>
            </div>

            <div className="p-4 rounded-2xl bg-blue-50 border border-blue-200 space-y-1">
              <span className="font-black text-sm text-blue-800">Loại B</span>
              <p className="text-blue-950 font-bold">Tương đối an toàn</p>
              <p className="text-slate-600 text-[11px] leading-relaxed">Thử nghiệm động vật không thấy nguy cơ (ví dụ: Paracetamol, Amoxicillin, Cefuroxime).</p>
            </div>

            <div className="p-4 rounded-2xl bg-amber-50 border border-amber-200 space-y-1">
              <span className="font-black text-sm text-amber-800">Loại C</span>
              <p className="text-amber-950 font-bold">Cân nhắc lợi ích/nguy cơ</p>
              <p className="text-slate-600 text-[11px] leading-relaxed">Động vật có độc tính nhưng chưa có nghiên cứu kiểm soát tốt trên người (Omeprazole, Ciprofloxacin).</p>
            </div>

            <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 space-y-1">
              <span className="font-black text-sm text-rose-800">Loại D</span>
              <p className="text-rose-950 font-bold">Có bằng chứng nguy cơ</p>
              <p className="text-slate-600 text-[11px] leading-relaxed">Chỉ dùng khi tính mạng người mẹ bị đe dọa và không có thuốc thay thế (Aspirin liều cao, Captopril, Enalapril).</p>
            </div>

            <div className="p-4 rounded-2xl bg-red-100 border border-red-300 space-y-1">
              <span className="font-black text-sm text-red-900">Loại X</span>
              <p className="text-red-950 font-bold">CHỐNG CHỈ ĐỊNH</p>
              <p className="text-red-800 text-[11px] leading-relaxed">Nguy cơ gây quái thai hoặc tử vong thai nhi cao hơn hẳn bất kỳ lợi ích nào (Warfarin, Isotretinoin, Methotrexate).</p>
            </div>
          </div>
        </div>
      )}

      {/* 7. DRUG DETAIL MODAL */}
      {selectedDrug && (
        <div className="fixed inset-0 z-[9999] w-screen h-screen min-h-screen min-w-full bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white rounded-3xl max-w-2xl w-full p-6 md:p-8 shadow-2xl border border-slate-200 space-y-5 my-auto max-h-[90vh] overflow-y-auto custom-scrollbar">
            <div className="flex items-start justify-between border-b border-slate-200 pb-4">
              <div className="space-y-1.5 pr-4">
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-800 border border-amber-200 uppercase">
                    {selectedDrug.class}
                  </span>
                  <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
                    Thai kỳ: {selectedDrug.pregnancy_safety}
                  </span>
                </div>
                <h2 className="text-xl md:text-2xl font-black text-slate-900">{selectedDrug.name}</h2>
                <p className="text-xs text-slate-500 font-medium">
                  Biệt dược phổ biến: {selectedDrug.brand_names.join(', ')}
                </p>
              </div>

              <button
                type="button"
                onClick={() => setSelectedDrug(null)}
                className="p-1.5 rounded-full text-slate-400 hover:text-slate-600 hover:bg-slate-100"
              >
                <X size={20} />
              </button>
            </div>

            <div className="space-y-4 text-xs md:text-sm text-slate-700 leading-relaxed">
              <div className="space-y-1">
                <span className="font-bold text-slate-900 uppercase text-xs tracking-wider">Dạng bào chế:</span>
                <div className="flex flex-wrap gap-1.5">
                  {selectedDrug.forms.map((f, fIdx) => (
                    <span key={fIdx} className="px-2.5 py-1 rounded-lg bg-slate-100 text-slate-800 font-medium">
                      {f}
                    </span>
                  ))}
                </div>
              </div>

              <div className="space-y-1">
                <span className="font-bold text-slate-900 uppercase text-xs tracking-wider">Chỉ định điều trị:</span>
                <p className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200/80 leading-relaxed">
                  {selectedDrug.indications}
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div className="p-3.5 rounded-2xl bg-blue-50/70 border border-blue-100 space-y-1">
                  <span className="font-bold text-blue-900 text-xs uppercase">Liều dùng người lớn:</span>
                  <p className="text-blue-950 font-medium">{selectedDrug.adult_dose}</p>
                </div>

                <div className="p-3.5 rounded-2xl bg-purple-50/70 border border-purple-100 space-y-1">
                  <span className="font-bold text-purple-900 text-xs uppercase">Liều dùng trẻ em:</span>
                  <p className="text-purple-950 font-medium">{selectedDrug.pediatric_dose}</p>
                </div>
              </div>

              <div className="p-3.5 rounded-2xl bg-red-50/80 border border-red-200 text-red-950 space-y-1">
                <span className="font-bold text-red-700 flex items-center gap-1.5">
                  <AlertTriangle size={15} /> Chống chỉ định tuyệt đối:
                </span>
                <p className="font-medium leading-relaxed">{selectedDrug.contraindications}</p>
              </div>

              <div className="space-y-1">
                <span className="font-bold text-slate-900 uppercase text-xs tracking-wider">Lưu ý dặn dò an toàn:</span>
                <p className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200/80 leading-relaxed text-slate-700">
                  {selectedDrug.precautions}
                </p>
              </div>
            </div>

            <div className="flex items-center justify-between border-t border-slate-100 pt-4">
              <button
                type="button"
                onClick={() => setSelectedDrug(null)}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-500 hover:bg-slate-100"
              >
                Đóng
              </button>

              <Link
                href={`/chat?q=${encodeURIComponent(
                  `Xin bác sĩ tư vấn hướng dẫn sử dụng và tương tác của thuốc: ${selectedDrug.name}`
                )}`}
                className="flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-amber-600 hover:bg-amber-700 text-white font-bold text-xs shadow-md shadow-amber-600/25 active:scale-95 transition"
              >
                <Bot size={14} />
                <span>Hỏi Bác Sĩ AI Về Thuốc Này</span>
              </Link>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
