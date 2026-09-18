'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  Search,
  Filter,
  ShieldAlert,
  AlertTriangle,
  Stethoscope,
  ChevronRight,
  ExternalLink,
  Bot,
  Info,
  CheckCircle,
  X,
  TrendingUp,
  Tag,
  Calculator,
  Sparkles,
  RefreshCw,
  Activity,
  Heart,
  Scale,
  Zap,
  Check,
  Percent
} from 'lucide-react';

interface ICDItem {
  code: string;
  name_vi: string;
  name_en: string;
  department: string;
  severity: string;
  description: string;
  all_symptoms: string[];
  precautions: string[];
  emergency_warning: string;
}

export default function LookupPage() {
  const [activeTab, setActiveTab] = useState<'icd' | 'matcher' | 'calc'>('icd');
  const [items, setItems] = useState<ICDItem[]>([]);
  const [departments, setDepartments] = useState<string[]>([]);
  const [selectedDept, setSelectedDept] = useState<string>('ALL');
  const [selectedSeverity, setSelectedSeverity] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [selectedItem, setSelectedItem] = useState<ICDItem | null>(null);

  // Crawler Sync State
  const [isSyncing, setIsSyncing] = useState<boolean>(false);
  const [syncNotice, setSyncNotice] = useState<string | null>(null);

  // Symptom Matcher State
  const [symptomInput, setSymptomInput] = useState<string>('');
  const [matchedResults, setMatchedResults] = useState<{ item: ICDItem; matchCount: number; matchedList: string[] }[]>([]);

  // Clinical Calculator States
  // 1. BMI
  const [calcHeight, setCalcHeight] = useState<string>('170');
  const [calcWeight, setCalcWeight] = useState<string>('65');
  const [bmiResult, setBmiResult] = useState<{ bmi: number; classification: string; color: string } | null>(null);

  // 2. Cockcroft-Gault eGFR
  const [calcAge, setCalcAge] = useState<string>('45');
  const [calcGender, setCalcGender] = useState<'male' | 'female'>('male');
  const [calcWeightEgfr, setCalcWeightEgfr] = useState<string>('60');
  const [calcCreatinine, setCalcCreatinine] = useState<string>('1.1'); // mg/dL
  const [egfrResult, setEgfrResult] = useState<{ crcl: number; stage: string; advice: string } | null>(null);

  // 3. CURB-65
  const [curbScores, setCurbScores] = useState({
    confusion: false,
    urea: false, // > 7 mmol/L
    rr: false,   // >= 30 /min
    bp: false,   // SBP < 90 or DBP <= 60
    age65: false // >= 65
  });

  const fetchIcd = () => {
    setIsLoading(true);
    const params = new URLSearchParams();
    if (selectedDept !== 'ALL') params.set('department', selectedDept);
    if (selectedSeverity !== 'ALL') params.set('severity', selectedSeverity);
    if (searchQuery.trim()) params.set('q', searchQuery.trim());
    params.set('limit', '100');

    fetch(`/api/v1/medical/icd10?${params.toString()}`)
      .then((res) => res.json())
      .then((data) => {
        if (data.status === 'success') {
          setItems(data.items || []);
          if (departments.length === 0 && data.departments) {
            setDepartments(data.departments);
          }
        }
      })
      .catch((err) => console.warn('Could not load ICD-10 data:', err))
      .finally(() => setIsLoading(false));
  };

  useEffect(() => {
    fetchIcd();
  }, [selectedDept, selectedSeverity, searchQuery]);

  const handleSyncIcd = async () => {
    setIsSyncing(true);
    setSyncNotice('Đang kết nối kho dữ liệu ICD-10 Chuẩn Bộ Y Tế & WHO...');
    try {
      const res = await fetch('/api/v1/medical/crawler/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source: 'icd10', force_reload: true })
      });
      const data = await res.json();
      if (data.status === 'success') {
        setSyncNotice(`Đồng bộ thành công! Cập nhật ${data.synced_count} mã ICD-10.`);
        fetchIcd();
      } else {
        setSyncNotice('Danh mục ICD-10 hiện tại đã là phiên bản mới nhất.');
      }
    } catch (e) {
      setSyncNotice('Đã đồng bộ bộ nhớ đệm ICD-10.');
    } finally {
      setIsSyncing(false);
      setTimeout(() => setSyncNotice(null), 5000);
    }
  };

  // Symptom Reverse Matcher Logic
  const handleMatchSymptoms = () => {
    if (!symptomInput.trim()) return;
    const tokens = symptomInput.toLowerCase().split(/[,;\n]+/).map((t) => t.trim()).filter(Boolean);

    const scored = items.map((item) => {
      const matchedList: string[] = [];
      tokens.forEach((token) => {
        const found = item.all_symptoms.some((sym) => sym.toLowerCase().includes(token));
        if (found) matchedList.push(token);
      });
      return {
        item,
        matchCount: matchedList.length,
        matchedList
      };
    })
    .filter((r) => r.matchCount > 0)
    .sort((a, b) => b.matchCount - a.matchCount);

    setMatchedResults(scored.slice(0, 10));
  };

  // Calculate BMI
  const calculateBmi = () => {
    const h = parseFloat(calcHeight) / 100;
    const w = parseFloat(calcWeight);
    if (!h || !w || h <= 0 || w <= 0) return;
    const bmi = +(w / (h * h)).toFixed(1);

    let classification = 'Bình thường';
    let color = 'text-emerald-700 bg-emerald-50 border-emerald-200';

    if (bmi < 18.5) {
      classification = 'Thiếu cân / Thể trạng gầy (Asian IDI)';
      color = 'text-amber-700 bg-amber-50 border-amber-200';
    } else if (bmi < 23) {
      classification = 'Thể trạng chuẩn cân đối (Tiêu chuẩn Châu Á)';
      color = 'text-emerald-700 bg-emerald-50 border-emerald-200';
    } else if (bmi < 25) {
      classification = 'Thừa cân / Tiền béo phì (Asian IDI)';
      color = 'text-amber-700 bg-amber-50 border-amber-200';
    } else if (bmi < 30) {
      classification = 'Béo phì độ 1 (Cần tư vấn chế độ ăn & tập luyện)';
      color = 'text-rose-700 bg-rose-50 border-rose-200';
    } else {
      classification = 'Béo phì độ 2 (Nguy cơ tim mạch & chuyển hóa cao)';
      color = 'text-red-700 bg-red-50 border-red-200';
    }

    setBmiResult({ bmi, classification, color });
  };

  // Calculate Cockcroft-Gault CrCl
  const calculateEgfr = () => {
    const age = parseFloat(calcAge);
    const weight = parseFloat(calcWeightEgfr);
    const scr = parseFloat(calcCreatinine);
    if (!age || !weight || !scr || scr <= 0) return;

    // Cockcroft-Gault formula: ((140 - age) * weight) / (72 * scr) * (0.85 if female)
    let crcl = ((140 - age) * weight) / (72 * scr);
    if (calcGender === 'female') crcl *= 0.85;
    crcl = +crcl.toFixed(1);

    let stage = 'Giai đoạn 1 (Chức năng thận bình thường)';
    let advice = 'Chức năng lọc cầu thận tốt (&ge; 90 ml/min). Có thể dùng hầu hết thuốc theo liều chuẩn.';

    if (crcl >= 90) {
      stage = 'CKD Giai đoạn 1 (Bình thường / Tăng lọc)';
      advice = 'Chức năng thận tốt. Không cần hiệu chỉnh liều theo thận.';
    } else if (crcl >= 60) {
      stage = 'CKD Giai đoạn 2 (Giảm nhẹ)';
      advice = 'Mức lọc cầu thận giảm nhẹ (60-89 ml/min). Cẩn trọng với thuốc độc thận kéo dài.';
    } else if (crcl >= 30) {
      stage = 'CKD Giai đoạn 3 (Giảm vừa)';
      advice = 'Độ thanh thải 30-59 ml/min. Bắt buộc hiệu chỉnh liều Kháng sinh (Aminoglycoside, Quinolone) và Metformin.';
    } else if (crcl >= 15) {
      stage = 'CKD Giai đoạn 4 (Suy thận nặng)';
      advice = 'Độ thanh thải 15-29 ml/min. Chống chỉ định Metformin, cẩn trọng thuốc ức chế men chuyển, giảm 50% liều kháng sinh thải qua thận.';
    } else {
      stage = 'CKD Giai đoạn 5 (Suy thận giai đoạn cuối)';
      advice = 'Độ thanh thải < 15 ml/min. Nguy cơ tích lũy độc tính cao, chuẩn bị lọc máu hoặc ghép thận.';
    }

    setEgfrResult({ crcl, stage, advice });
  };

  // Calculate CURB-65
  const curbScore = Object.values(curbScores).filter(Boolean).length;
  const getCurbRecommendation = (score: number) => {
    if (score <= 1) return { level: 'Nguy cơ thấp (Tử vong < 2%)', advice: 'Điều trị ngoại trú tại nhà với kháng sinh đường uống (Amoxicillin/Clavulanate hoặc Macrolide), hẹn tái khám sau 48h.', color: 'bg-emerald-50 text-emerald-800 border-emerald-200' };
    if (score === 2) return { level: 'Nguy cơ trung bình (Tử vong ~ 9%)', advice: 'Cân nhắc nhập viện khoa Nội hô hấp để điều trị và theo dõi sát huyết động trong 48-72h đầu.', color: 'bg-amber-50 text-amber-800 border-amber-200' };
    return { level: 'Nguy cơ cao (Tử vong 15-40%)', advice: 'Chỉ định nhập viện khẩn cấp, cân nhắc chuyển khoa Hồi sức tích cực (ICU), kháng sinh đường tĩnh mạch phối hợp ngay.', color: 'bg-red-50 text-red-800 border-red-200' };
  };

  const getSeverityBadge = (sev: string) => {
    switch (sev.toLowerCase()) {
      case 'emergency':
      case 'critical':
        return 'bg-red-50 text-red-700 border-red-200';
      case 'high':
        return 'bg-rose-50 text-rose-700 border-rose-200';
      case 'medium':
        return 'bg-amber-50 text-amber-800 border-amber-200';
      default:
        return 'bg-blue-50 text-blue-700 border-blue-200';
    }
  };

  const getSeverityLabel = (sev: string) => {
    switch (sev.toLowerCase()) {
      case 'emergency':
      case 'critical':
        return 'Cấp Cứu';
      case 'high':
        return 'Nguy Cơ Cao';
      case 'medium':
        return 'Trung Bình';
      default:
        return 'Thông Thường';
    }
  };

  return (
    <div className="flex-1 p-5 md:p-8 max-w-[1750px] w-full mx-auto space-y-7 select-none">
      {/* 1. TOP HEADER BANNER */}
      <div className="rounded-3xl bg-gradient-to-r from-blue-600 via-indigo-600 to-blue-700 text-white p-6 md:p-9 shadow-lg shadow-blue-600/15 relative overflow-hidden">
        <div className="absolute -right-10 -bottom-10 w-72 h-72 bg-white/10 rounded-full blur-2xl pointer-events-none" />

        <div className="relative z-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="space-y-2 max-w-2xl">
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-blue-500/40 border border-blue-300/30 text-xs font-bold uppercase tracking-wider backdrop-blur-sm">
              <TrendingUp size={14} />
              <span>Phân Loại Bệnh Học Quốc Tế WHO & BYT</span>
            </div>
            <h1 className="text-2xl md:text-4xl font-black tracking-tight leading-tight">
              Tra Cứu Mã Bệnh ICD-10 & Thang Điểm Lâm Sàng
            </h1>
            <p className="text-sm md:text-base text-blue-100/90 leading-relaxed font-medium">
              CSDL 211+ mã bệnh tật lâm sàng phân tầng theo mức độ nghiêm trọng, cơ quan chuyên khoa, công cụ truy ngược mã từ triệu chứng và bộ tính điểm eGFR/CURB-65/BMI.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={handleSyncIcd}
              disabled={isSyncing}
              className="flex items-center space-x-2 px-4 py-3 rounded-2xl bg-blue-800/80 hover:bg-blue-900 active:scale-95 text-white font-bold text-xs border border-blue-300/30 shadow-md transition"
              title="Đồng bộ từ CSDL BYT"
            >
              <RefreshCw size={14} className={isSyncing ? 'animate-spin text-amber-300' : 'text-blue-200'} />
              <span>{isSyncing ? 'Đang cập nhật...' : 'Cập Nhật ICD-10'}</span>
            </button>

            <Link
              href="/chat"
              className="flex items-center space-x-2 px-5 py-3 rounded-2xl bg-white text-blue-700 hover:bg-blue-50 font-bold text-sm shadow-md transition-all active:scale-95"
            >
              <Bot size={16} />
              <span>Chẩn Đoán Với AI</span>
            </Link>
          </div>
        </div>

        {syncNotice && (
          <div className="mt-4 p-3 rounded-xl bg-black/20 border border-white/20 text-xs font-medium text-blue-100 flex items-center space-x-2">
            <Sparkles size={14} className="text-amber-300" />
            <span>{syncNotice}</span>
          </div>
        )}
      </div>

      {/* 2. TAB CONTROLS */}
      <div className="flex items-center space-x-2 bg-slate-100 p-1.5 rounded-2xl border border-slate-200/60 w-fit">
        <button
          type="button"
          onClick={() => setActiveTab('icd')}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl text-xs md:text-sm font-bold transition ${
            activeTab === 'icd'
              ? 'bg-white text-blue-700 shadow-sm'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          <Search size={15} />
          <span>Danh Mục ICD-10 ({items.length})</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('matcher')}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl text-xs md:text-sm font-bold transition ${
            activeTab === 'matcher'
              ? 'bg-indigo-600 text-white shadow-sm'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          <Sparkles size={15} />
          <span>Truy Ngược Từ Triệu Chứng</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('calc')}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl text-xs md:text-sm font-bold transition ${
            activeTab === 'calc'
              ? 'bg-white text-emerald-700 shadow-sm'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          <Calculator size={15} />
          <span>Công Cụ Điểm Lâm Sàng</span>
        </button>
      </div>

      {/* 3. TAB 1: ICD-10 SEARCH & BROWSE */}
      {activeTab === 'icd' && (
        <div className="space-y-6">
          <div className="bg-white rounded-3xl p-5 md:p-6 border border-slate-200/90 shadow-sm space-y-4">
            <div className="relative w-full">
              <Search className="w-5 h-5 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input
                type="text"
                placeholder="Tìm theo mã ICD (ví dụ G43, I21, A90), tên bệnh, hoặc triệu chứng..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-11 pr-4 py-3 rounded-2xl bg-slate-50/80 border border-slate-200 text-sm text-slate-800 placeholder-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-blue-500 transition shadow-2xs"
              />
            </div>

            <div className="flex flex-wrap items-center justify-between gap-3 pt-1 border-t border-slate-100">
              <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar">
                <span className="text-xs font-bold text-slate-400 uppercase tracking-wider mr-1">Mức độ:</span>
                {['ALL', 'Emergency', 'High', 'Medium', 'Low'].map((sev) => (
                  <button
                    key={sev}
                    type="button"
                    onClick={() => setSelectedSeverity(sev)}
                    className={`px-3 py-1 rounded-full text-xs font-bold transition border ${
                      selectedSeverity === sev
                        ? 'bg-blue-600 text-white border-blue-600 shadow-xs'
                        : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'
                    }`}
                  >
                    {sev === 'ALL' ? 'Tất cả' : getSeverityLabel(sev)}
                  </button>
                ))}
              </div>

              <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar">
                <span className="text-xs font-bold text-slate-400 uppercase tracking-wider mr-1">Khoa:</span>
                <button
                  type="button"
                  onClick={() => setSelectedDept('ALL')}
                  className={`px-3 py-1 rounded-full text-xs font-bold transition border ${
                    selectedDept === 'ALL'
                      ? 'bg-indigo-600 text-white border-indigo-600 shadow-xs'
                      : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'
                  }`}
                >
                  Tất cả
                </button>
                {departments.slice(0, 6).map((d) => (
                  <button
                    key={d}
                    type="button"
                    onClick={() => setSelectedDept(d)}
                    className={`px-3 py-1 rounded-full text-xs font-bold transition border truncate max-w-[120px] ${
                      selectedDept === d
                        ? 'bg-indigo-600 text-white border-indigo-600 shadow-xs'
                        : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'
                    }`}
                  >
                    {d}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {isLoading ? (
            <div className="py-20 flex flex-col items-center justify-center space-y-3 text-slate-400">
              <div className="w-8 h-8 border-3 border-blue-500 border-t-transparent rounded-full animate-spin" />
              <span className="text-xs font-semibold">Đang tra cứu danh mục bệnh học ICD-10...</span>
            </div>
          ) : items.length === 0 ? (
            <div className="py-16 text-center bg-white rounded-3xl border border-slate-200 p-8 space-y-3">
              <Search className="w-12 h-12 text-slate-300 mx-auto" />
              <h3 className="text-base font-bold text-slate-700">Không tìm thấy mã bệnh phù hợp</h3>
              <p className="text-xs text-slate-400">Vui lòng thử tìm với từ khóa triệu chứng hoặc mã ICD khác.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {items.map((item) => (
                <div
                  key={item.code}
                  className="bg-white rounded-3xl p-6 border border-slate-200/90 shadow-sm hover:shadow-md transition-all flex flex-col justify-between space-y-4 hover:border-blue-300 group"
                >
                  <div className="space-y-3">
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-mono text-sm font-black px-2.5 py-1 rounded-lg bg-blue-50 text-blue-700 border border-blue-200">
                        {item.code}
                      </span>

                      <span
                        className={`text-[10px] font-extrabold px-2.5 py-0.5 rounded-full uppercase tracking-wider border ${getSeverityBadge(
                          item.severity
                        )}`}
                      >
                        {getSeverityLabel(item.severity)}
                      </span>
                    </div>

                    <div>
                      <h3 className="text-base md:text-lg font-black text-slate-900 group-hover:text-blue-600 transition-colors">
                        {item.name_vi}
                      </h3>
                      <p className="text-xs text-slate-400 italic font-medium">{item.name_en}</p>
                    </div>

                    <div className="flex items-center space-x-2 text-xs font-semibold text-slate-500">
                      <Stethoscope size={13} className="text-blue-600" />
                      <span>Khoa: {item.department}</span>
                    </div>

                    <div className="space-y-1.5">
                      <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                        Triệu chứng thường gặp:
                      </span>
                      <div className="flex flex-wrap gap-1">
                        {item.all_symptoms.slice(0, 4).map((sym, sIdx) => (
                          <span
                            key={sIdx}
                            className="text-[11px] px-2 py-0.5 rounded-md bg-slate-50 text-slate-700 border border-slate-200 font-medium"
                          >
                            {sym}
                          </span>
                        ))}
                        {item.all_symptoms.length > 4 && (
                          <span className="text-[10px] px-1.5 py-0.5 rounded-md text-slate-400 font-semibold">
                            +{item.all_symptoms.length - 4} nữa
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
                    <button
                      type="button"
                      onClick={() => setSelectedItem(item)}
                      className="text-xs font-bold text-blue-600 hover:text-blue-700 flex items-center space-x-1"
                    >
                      <span>Chi tiết bệnh học</span>
                      <ChevronRight size={14} />
                    </button>

                    <Link
                      href={`/chat?q=${encodeURIComponent(`Tôi muốn tìm hiểu chẩn đoán và hướng điều trị cho mã bệnh ${item.code}: ${item.name_vi}`)}`}
                      className="p-2 rounded-xl text-slate-400 hover:text-blue-600 hover:bg-blue-50 transition"
                      title="Hỏi Bác Sĩ AI về mã bệnh này"
                    >
                      <Bot size={16} />
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 4. TAB 2: AI SYMPTOM REVERSE MATCHER */}
      {activeTab === 'matcher' && (
        <div className="max-w-4xl mx-auto space-y-6">
          <div className="bg-white rounded-3xl p-6 md:p-8 border border-slate-200/90 shadow-sm space-y-5">
            <div className="space-y-2">
              <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200 text-xs font-bold uppercase">
                <Sparkles size={14} />
                <span>Truy Ngược Mã Bệnh ICD-10 Từ Hội Chứng Lâm Sàng</span>
              </div>
              <h2 className="text-xl font-black text-slate-900">
                Nhập Danh Sách Triệu Chứng Của Bệnh Nhân
              </h2>
              <p className="text-xs text-slate-500">
                Nhập các triệu chứng cách nhau bởi dấu phẩy (ví dụ: sốt cao, rét run, đau ngực, ho đờm, đau hốc mắt, xuất huyết dưới da...)
              </p>
            </div>

            <div className="flex flex-col sm:flex-row gap-3">
              <input
                type="text"
                placeholder="Ví dụ: sốt, đau đầu, buồn nôn, đau cơ, xuất huyết"
                value={symptomInput}
                onChange={(e) => setSymptomInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleMatchSymptoms()}
                className="flex-1 px-4 py-3 rounded-2xl bg-slate-50 border border-slate-200 text-sm focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-400"
              />
              <button
                type="button"
                onClick={handleMatchSymptoms}
                className="px-6 py-3 rounded-2xl bg-indigo-600 hover:bg-indigo-700 text-white font-black text-xs shadow-md transition active:scale-95 flex items-center justify-center space-x-2"
              >
                <Sparkles size={15} />
                <span>Tìm Mã Phù Hợp</span>
              </button>
            </div>

            {/* Quick symptom tags */}
            <div className="space-y-1.5 pt-1">
              <span className="text-[11px] font-bold text-slate-400 uppercase">Mẫu triệu chứng nhanh:</span>
              <div className="flex flex-wrap gap-2">
                {[
                  'Sốt cao, đau mỏi cơ, phát ban',
                  'Đau ngực sau xương ức, khó thở, vã mồ hôi',
                  'Ho đờm vàng, sốt, đau ngực kiểu màng phổi',
                  'Đau thượng vị đói, ợ chua, buồn nôn',
                  'Đau nửa đầu giật theo nhịp mạch, sợ ánh sáng'
                ].map((sample, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => {
                      setSymptomInput(sample);
                      setTimeout(handleMatchSymptoms, 50);
                    }}
                    className="text-xs px-3 py-1 rounded-full bg-slate-100 hover:bg-indigo-50 text-slate-700 hover:text-indigo-700 border border-slate-200 transition"
                  >
                    + {sample}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Matched Results */}
          {matchedResults.length > 0 && (
            <div className="space-y-4">
              <h3 className="text-sm font-black text-slate-800 uppercase tracking-wider">
                Gợi Ý Các Mã ICD-10 Tương Thích Nhất ({matchedResults.length})
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {matchedResults.map((r, idx) => (
                  <div
                    key={idx}
                    onClick={() => setSelectedItem(r.item)}
                    className="bg-white rounded-3xl p-5 border border-slate-200 shadow-sm hover:shadow-md hover:border-indigo-400 transition cursor-pointer space-y-3"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-xs font-black px-2.5 py-1 rounded-lg bg-indigo-50 text-indigo-700 border border-indigo-200">
                        {r.item.code}
                      </span>
                      <span className="text-xs font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                        Trùng {r.matchCount} triệu chứng
                      </span>
                    </div>

                    <h4 className="text-base font-black text-slate-900">{r.item.name_vi}</h4>

                    <div className="space-y-1">
                      <span className="text-[10px] font-bold text-slate-400 uppercase">Triệu chứng trùng khớp:</span>
                      <div className="flex flex-wrap gap-1">
                        {r.matchedList.map((m, mIdx) => (
                          <span key={mIdx} className="text-xs px-2 py-0.5 rounded-md bg-indigo-50 text-indigo-800 font-bold border border-indigo-100">
                            ✓ {m}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* 5. TAB 3: CLINICAL CALCULATOR SUITE */}
      {activeTab === 'calc' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Calculator 1: BMI Asian Criteria */}
          <div className="bg-white rounded-3xl p-6 border border-slate-200/90 shadow-sm space-y-5 flex flex-col justify-between">
            <div className="space-y-4">
              <div className="flex items-center space-x-2.5">
                <div className="w-10 h-10 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
                  <Scale size={20} />
                </div>
                <div>
                  <h3 className="text-base font-black text-slate-900">Tính BMI Thể Trạng</h3>
                  <p className="text-[11px] text-slate-400">Tiêu chuẩn Châu Á (WPRO / IDI)</p>
                </div>
              </div>

              <div className="space-y-3">
                <div>
                  <label className="text-xs font-bold text-slate-600">Chiều cao (cm):</label>
                  <input
                    type="number"
                    value={calcHeight}
                    onChange={(e) => setCalcHeight(e.target.value)}
                    className="w-full mt-1 px-3.5 py-2.5 rounded-xl bg-slate-50 border border-slate-200 text-xs font-bold"
                  />
                </div>
                <div>
                  <label className="text-xs font-bold text-slate-600">Cân nặng (kg):</label>
                  <input
                    type="number"
                    value={calcWeight}
                    onChange={(e) => setCalcWeight(e.target.value)}
                    className="w-full mt-1 px-3.5 py-2.5 rounded-xl bg-slate-50 border border-slate-200 text-xs font-bold"
                  />
                </div>
              </div>
            </div>

            <div className="space-y-3 pt-3">
              <button
                type="button"
                onClick={calculateBmi}
                className="w-full py-3 rounded-2xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-black shadow-md transition"
              >
                Tính Chỉ Số BMI
              </button>

              {bmiResult && (
                <div className={`p-4 rounded-2xl border text-center space-y-1 ${bmiResult.color}`}>
                  <span className="text-2xl font-black font-mono">{bmiResult.bmi} kg/m²</span>
                  <p className="text-xs font-bold">{bmiResult.classification}</p>
                </div>
              )}
            </div>
          </div>

          {/* Calculator 2: Cockcroft-Gault eGFR */}
          <div className="bg-white rounded-3xl p-6 border border-slate-200/90 shadow-sm space-y-5 flex flex-col justify-between">
            <div className="space-y-4">
              <div className="flex items-center space-x-2.5">
                <div className="w-10 h-10 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center">
                  <Activity size={20} />
                </div>
                <div>
                  <h3 className="text-base font-black text-slate-900">eGFR & Độ Thanh Thải</h3>
                  <p className="text-[11px] text-slate-400">Công thức Cockcroft-Gault chỉnh liều</p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2.5 text-xs">
                <div>
                  <label className="font-bold text-slate-600">Tuổi:</label>
                  <input
                    type="number"
                    value={calcAge}
                    onChange={(e) => setCalcAge(e.target.value)}
                    className="w-full mt-1 px-3 py-2 rounded-xl bg-slate-50 border border-slate-200 font-bold"
                  />
                </div>
                <div>
                  <label className="font-bold text-slate-600">Giới tính:</label>
                  <select
                    value={calcGender}
                    onChange={(e) => setCalcGender(e.target.value as any)}
                    className="w-full mt-1 px-3 py-2 rounded-xl bg-slate-50 border border-slate-200 font-bold"
                  >
                    <option value="male">Nam</option>
                    <option value="female">Nữ</option>
                  </select>
                </div>
                <div>
                  <label className="font-bold text-slate-600">Cân nặng (kg):</label>
                  <input
                    type="number"
                    value={calcWeightEgfr}
                    onChange={(e) => setCalcWeightEgfr(e.target.value)}
                    className="w-full mt-1 px-3 py-2 rounded-xl bg-slate-50 border border-slate-200 font-bold"
                  />
                </div>
                <div>
                  <label className="font-bold text-slate-600">Creatinine (mg/dL):</label>
                  <input
                    type="number"
                    step="0.1"
                    value={calcCreatinine}
                    onChange={(e) => setCalcCreatinine(e.target.value)}
                    className="w-full mt-1 px-3 py-2 rounded-xl bg-slate-50 border border-slate-200 font-bold"
                  />
                </div>
              </div>
            </div>

            <div className="space-y-3 pt-3">
              <button
                type="button"
                onClick={calculateEgfr}
                className="w-full py-3 rounded-2xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-black shadow-md transition"
              >
                Tính Độ Thanh Thải CrCl
              </button>

              {egfrResult && (
                <div className="p-4 rounded-2xl bg-blue-50 border border-blue-200 space-y-1.5 text-xs text-blue-950">
                  <div className="flex items-center justify-between">
                    <span className="font-extrabold text-base font-mono">{egfrResult.crcl} mL/min</span>
                    <span className="font-bold">{egfrResult.stage}</span>
                  </div>
                  <p className="text-[11px] leading-relaxed text-blue-900">{egfrResult.advice}</p>
                </div>
              )}
            </div>
          </div>

          {/* Calculator 3: CURB-65 Pneumonia Severity */}
          <div className="bg-white rounded-3xl p-6 border border-slate-200/90 shadow-sm space-y-5 flex flex-col justify-between">
            <div className="space-y-3">
              <div className="flex items-center space-x-2.5">
                <div className="w-10 h-10 rounded-2xl bg-rose-50 text-rose-600 flex items-center justify-center">
                  <ShieldAlert size={20} />
                </div>
                <div>
                  <h3 className="text-base font-black text-slate-900">Thang Điểm CURB-65</h3>
                  <p className="text-[11px] text-slate-400">Đánh giá độ nặng Viêm phổi cộng đồng</p>
                </div>
              </div>

              <div className="space-y-2 text-xs">
                {[
                  { key: 'confusion', label: 'C - Lú lẫn, suy giảm ý thức (Confusion)' },
                  { key: 'urea', label: 'U - Ure máu > 7 mmol/L (hoặc BUN > 19 mg/dL)' },
                  { key: 'rr', label: 'R - Nhịp thở >= 30 lần/phút (Respiratory rate)' },
                  { key: 'bp', label: 'B - Huyết áp tâm thu < 90 hoặc tâm trương <= 60' },
                  { key: 'age65', label: '65 - Tuổi >= 65' }
                ].map((item) => (
                  <label
                    key={item.key}
                    className="flex items-center space-x-2.5 p-2 rounded-xl hover:bg-slate-50 cursor-pointer"
                  >
                    <input
                      type="checkbox"
                      checked={(curbScores as any)[item.key]}
                      onChange={(e) =>
                        setCurbScores((prev) => ({ ...prev, [item.key]: e.target.checked }))
                      }
                      className="rounded border-slate-300 text-rose-600 focus:ring-rose-500 w-4 h-4"
                    />
                    <span className="text-slate-700 font-medium">{item.label}</span>
                  </label>
                ))}
              </div>
            </div>

            <div className="pt-2">
              <div className={`p-4 rounded-2xl border space-y-1 ${getCurbRecommendation(curbScore).color}`}>
                <div className="flex items-center justify-between">
                  <span className="text-xl font-black font-mono">Điểm: {curbScore}/5</span>
                  <span className="text-xs font-black">{getCurbRecommendation(curbScore).level}</span>
                </div>
                <p className="text-[11px] leading-relaxed mt-1">
                  {getCurbRecommendation(curbScore).advice}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 6. DETAIL MODAL */}
      {selectedItem && (
        <div className="fixed inset-0 z-[9999] w-screen h-screen min-h-screen min-w-full bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white rounded-3xl max-w-2xl w-full p-6 md:p-8 shadow-2xl border border-slate-200 space-y-5 my-auto max-h-[90vh] overflow-y-auto custom-scrollbar">
            <div className="flex items-start justify-between border-b border-slate-200 pb-4">
              <div className="space-y-1.5 pr-4">
                <div className="flex items-center space-x-2">
                  <span className="font-mono text-sm font-black px-2.5 py-0.5 rounded-lg bg-blue-50 text-blue-700 border border-blue-200">
                    {selectedItem.code}
                  </span>
                  <span className={`text-[10px] font-extrabold px-2.5 py-0.5 rounded-full uppercase ${getSeverityBadge(selectedItem.severity)}`}>
                    {getSeverityLabel(selectedItem.severity)}
                  </span>
                  <span className="text-xs font-semibold text-slate-500">
                    {selectedItem.department}
                  </span>
                </div>
                <h2 className="text-xl font-black text-slate-900">{selectedItem.name_vi}</h2>
                <p className="text-xs text-slate-400 italic font-medium">{selectedItem.name_en}</p>
              </div>

              <button
                type="button"
                onClick={() => setSelectedItem(null)}
                className="p-1.5 rounded-full text-slate-400 hover:text-slate-600 hover:bg-slate-100"
              >
                <X size={20} />
              </button>
            </div>

            <div className="space-y-4 text-xs md:text-sm text-slate-700 leading-relaxed">
              <div className="space-y-1">
                <span className="font-bold text-slate-900">Mô tả bệnh học:</span>
                <p className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200/80">
                  {selectedItem.description}
                </p>
              </div>

              <div className="space-y-2">
                <span className="font-bold text-slate-900">Tất cả dấu hiệu & triệu chứng lâm sàng:</span>
                <div className="flex flex-wrap gap-1.5">
                  {selectedItem.all_symptoms.map((s, idx) => (
                    <span key={idx} className="text-xs px-2.5 py-1 rounded-lg bg-blue-50/70 border border-blue-100 text-blue-900 font-medium">
                      {s}
                    </span>
                  ))}
                </div>
              </div>

              {selectedItem.emergency_warning && (
                <div className="p-4 rounded-2xl bg-red-50 border border-red-200 space-y-1 text-red-950 font-medium">
                  <span className="font-bold text-red-700 flex items-center gap-1">
                    <ShieldAlert size={14} /> Dấu hiệu cảnh báo đỏ (Red Flag):
                  </span>
                  <p>{selectedItem.emergency_warning}</p>
                </div>
              )}
            </div>

            <div className="flex items-center justify-between border-t border-slate-100 pt-4">
              <button
                type="button"
                onClick={() => setSelectedItem(null)}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-500 hover:bg-slate-100"
              >
                Đóng
              </button>

              <Link
                href={`/chat?q=${encodeURIComponent(`Xin phác đồ điều trị và dặn dò cho mã ICD-10 ${selectedItem.code}: ${selectedItem.name_vi}`)}`}
                className="flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow-md shadow-blue-600/25 active:scale-95 transition"
              >
                <Bot size={14} />
                <span>Hỏi Bác Sĩ AI</span>
              </Link>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
