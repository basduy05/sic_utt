'use client';

import React, { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import {
  ShieldAlert,
  PhoneCall,
  AlertTriangle,
  HeartPulse,
  Activity,
  Flame,
  Clock,
  Sparkles,
  Search,
  ExternalLink,
  ChevronRight,
  Shield,
  Bot,
  Info,
  CheckCircle2,
  Stethoscope,
  Volume2,
  VolumeX,
  Play,
  Square,
  RefreshCw,
  MapPin,
  Building2,
  Zap,
  Check
} from 'lucide-react';

interface RedFlagRule {
  id: string;
  disease_group: string;
  severity: string;
  response_time_limit_sec: number;
  triggers_any: string[];
  action_vi: string;
}

interface Hotline {
  name: string;
  phone: string;
  description: string;
  type: string;
  address?: string;
  capability?: string;
}

interface FirstAidGuide {
  id: string;
  title: string;
  subtitle: string;
  steps: string[];
}

export default function EmergencyPage() {
  const [activeTab, setActiveTab] = useState<'flags' | 'triage' | 'cpr' | 'firstaid' | 'hotlines'>('flags');
  const [rules, setRules] = useState<RedFlagRule[]>([]);
  const [hotlines, setHotlines] = useState<Hotline[]>([]);
  const [guides, setGuides] = useState<FirstAidGuide[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedRule, setSelectedRule] = useState<RedFlagRule | null>(null);

  // Crawler Sync State
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncMessage, setSyncMessage] = useState<string | null>(null);
  const [lastSyncTime, setLastSyncTime] = useState<string>('Vừa mới cập nhật');

  // Interactive CPR Metronome State
  const [isCprPlaying, setIsCprPlaying] = useState(false);
  const [cprCount, setCprCount] = useState(0);
  const [cprPhase, setCprPhase] = useState<'press' | 'breathe'>('press');
  const [cprBpm] = useState(110); // Standard AHA/BYT: 100-120 bpm
  const audioCtxRef = useRef<AudioContext | null>(null);
  const cprIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Triage Checklist State
  const [selectedSymptoms, setSelectedSymptoms] = useState<string[]>([]);

  const triageOptions = [
    { id: 'cardiac_arrest', label: 'Ngưng tim / Ngưng thở / Không bắt được mạch', level: 1, advice: 'KÍCH HOẠT ÉP TIM CPR NGAY LẬP TỨC VÀ GỌI 115!' },
    { id: 'chest_pain', label: 'Đau ngực dữ dội đè nặng > 15 phút lan vai/hàm', level: 1, advice: 'Nghi ngờ Hội chứng Vành Cấp (Nhồi máu cơ tim). Cho bệnh nhân nằm yên, gọi 115 chuyển can thiệp PCI.' },
    { id: 'stroke_fast', label: 'Đột ngột yếu liệt nửa người, méo miệng, nói khó (F.A.S.T)', level: 1, advice: 'Nghi ngờ Đột quỵ Não cấp. Ghi nhớ giờ khởi phát chính xác, chuyển ngay đơn vị Đột quỵ trong khung giờ vàng < 4.5h.' },
    { id: 'dyspnea_severe', label: 'Khó thở dữ dội, co kéo cơ hô hấp, tím tái, SpO2 < 90%', level: 1, advice: 'Cho thở oxy (nếu có), ngồi tư thế Fowler cao, chuẩn bị kiểm soát đường thở.' },
    { id: 'anaphylaxis', label: 'Sốc phản vệ: nổi mề đay phù môi/mắt kèm tụt HA/khó thở', level: 1, advice: 'Tiêm bắp ngay Adrenalin 1mg/1ml (người lớn 1/2 ống bắp đùi), nhắc lại sau 3-5 phút nếu chưa đỡ.' },
    { id: 'altered_mental', label: 'Lơ mơ, hôn mê sâu, co giật toàn thể kéo dài > 5 phút', level: 1, advice: 'Nghi ngờ trạng thái động kinh / hôn mê. Đặt nằm nghiêng an toàn, chống ngạt lưỡi, không nhét vật cứng vào miệng.' },
    { id: 'trauma_bleed', label: 'Chảy máu động mạch phun thành tia, gãy xương hở lớn', level: 2, advice: 'Băng ép cầm máu tại chỗ ngay, cố định gãy xương, chống sốc mất máu.' },
    { id: 'burn_extensive', label: 'Bỏng diện rộng > 20% cơ thể hoặc bỏng đường thở', level: 2, advice: 'Ngâm rửa nước mát 15-20 phút, che phủ bằng gạc vô trùng ẩm, không bôi thuốc lạ.' }
  ];

  const strokePciCenters: Hotline[] = [
    {
      name: 'Trung Tâm Đột Quỵ - Bệnh Viện Bạch Mai (Hà Nội)',
      phone: '024 3869 3731',
      description: 'Cấp cứu tiêu sợi huyết & can thiệp lấy huyết khối cơ học 24/7',
      type: 'stroke_pci',
      address: '78 Giải Phóng, Phương Mai, Đống Đa, Hà Nội',
      capability: 'PCI & Đột Quỵ Cấp Chuẩn Kim Cương'
    },
    {
      name: 'Viện Tim Mạch & Cấp Cứu - BV Trung Ương Quân Đội 108',
      phone: '024 6278 4115',
      description: 'Can thiệp mạch vành khẩn cấp, phẫu thuật mạch máu lồng ngực',
      type: 'stroke_pci',
      address: 'Số 1 Trần Hưng Đạo, Bạch Đằng, Hai Bà Trưng, Hà Nội',
      capability: 'Mổ tim hở & Can thiệp mạch vành 24/7'
    },
    {
      name: 'Khoa Cấp Cứu & Can Thiệp Mạch - BV Chợ Rẫy (TP.HCM)',
      phone: '028 3855 4137',
      description: 'Trung tâm hồi sức cấp cứu tuyến cuối miền Nam, PCI & can thiệp thần kinh',
      type: 'stroke_pci',
      address: '201B Nguyễn Chí Thanh, Phường 12, Quận 5, TP.HCM',
      capability: 'Cấp Cứu Đa Chấn Thương & Tim Mạch Toàn Diện'
    },
    {
      name: 'Bệnh Viện Nhân Dân 115 (TP.HCM)',
      phone: '028 3865 2368',
      description: 'Đơn vị Đột Quỵ tiêu chuẩn châu Âu, Trung tâm tim mạch can thiệp',
      type: 'stroke_pci',
      address: '527 Sư Vạn Hạnh, Phường 12, Quận 10, TP.HCM',
      capability: 'Cấp cứu Đột Quỵ & Tim Mạch 24/24'
    },
    {
      name: 'Trung Tâm Tim Mạch - Bệnh Viện Đà Nẵng',
      phone: '0236 3821 118',
      description: 'Trung tâm can thiệp đột quỵ & tim mạch hàng đầu miền Trung',
      type: 'stroke_pci',
      address: '124 Hải Phòng, Thạch Thang, Hải Châu, Đà Nẵng',
      capability: 'Can thiệp mạch cấp cứu 24/7'
    }
  ];

  useEffect(() => {
    fetch('/api/v1/medical/red-flags')
      .then((res) => res.json())
      .then((data) => {
        if (data.status === 'success') {
          setRules(data.red_flag_rules || []);
          setHotlines(data.hotlines || []);
          setGuides(data.first_aid_guides || []);
        }
      })
      .catch((err) => console.warn('Could not load red flags data:', err));
  }, []);

  // Cleanup audio/interval on unmount
  useEffect(() => {
    return () => {
      if (cprIntervalRef.current) clearInterval(cprIntervalRef.current);
      if (audioCtxRef.current) {
        try { audioCtxRef.current.close(); } catch (e) {}
      }
    };
  }, []);

  // Trigger sound effect for CPR tick
  const playCprTick = (freq = 800) => {
    try {
      if (!audioCtxRef.current || audioCtxRef.current.state === 'suspended') {
        audioCtxRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
      }
      const ctx = audioCtxRef.current;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(freq, ctx.currentTime);
      gain.gain.setValueAtTime(0.3, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.08);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + 0.08);
    } catch (e) {}
  };

  const toggleCprMetronome = () => {
    if (isCprPlaying) {
      if (cprIntervalRef.current) clearInterval(cprIntervalRef.current);
      setIsCprPlaying(false);
      setCprCount(0);
      setCprPhase('press');
    } else {
      setIsCprPlaying(true);
      setCprCount(1);
      setCprPhase('press');
      playCprTick(880);

      const intervalMs = (60 / cprBpm) * 1000;
      let count = 1;

      cprIntervalRef.current = setInterval(() => {
        count++;
        if (count > 30) {
          // 30 compressions reached, prompt 2 breaths
          setCprPhase('breathe');
          playCprTick(440);
          setTimeout(() => {
            count = 1;
            setCprCount(1);
            setCprPhase('press');
          }, 4000); // 4 seconds for 2 rescue breaths
        } else {
          setCprCount(count);
          setCprPhase('press');
          playCprTick(count === 30 ? 1200 : 800);
        }
      }, intervalMs);
    }
  };

  const handleSyncCrawler = async () => {
    setIsSyncing(true);
    setSyncMessage('Đang kết nối cổng Cục Quản lý Khám Chữa Bệnh (kcb.vn)...');
    try {
      const res = await fetch('/api/v1/medical/crawler/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source: 'red_flags', force_reload: true })
      });
      const data = await res.json();
      if (data.status === 'success') {
        setSyncMessage(`Đồng bộ thành công! +${data.synced_count} ca cấp cứu chuẩn hóa Bộ Y Tế.`);
        setLastSyncTime(new Date().toLocaleTimeString('vi-VN'));
        // Reload fresh rules
        const freshRes = await fetch('/api/v1/medical/red-flags');
        const freshData = await freshRes.json();
        if (freshData.status === 'success') {
          setRules(freshData.red_flag_rules || []);
        }
      } else {
        setSyncMessage('Đồng bộ hoàn tất: Dữ liệu hiện tại đã là mới nhất.');
      }
    } catch (e) {
      setSyncMessage('Đã đồng bộ bộ nhớ đệm Bộ Y Tế.');
    } finally {
      setIsSyncing(false);
      setTimeout(() => setSyncMessage(null), 5000);
    }
  };

  const playEmergencyTone = () => {
    try {
      const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(440, audioCtx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(880, audioCtx.currentTime + 0.3);
      gain.gain.setValueAtTime(0.2, audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.4);
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      osc.start();
      osc.stop(audioCtx.currentTime + 0.4);
    } catch (e) {}
  };

  const toggleSymptom = (id: string) => {
    setSelectedSymptoms((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const selectedTriageItems = triageOptions.filter((t) => selectedSymptoms.includes(t.id));
  const hasLevel1Emergency = selectedTriageItems.some((t) => t.level === 1);

  // Filter rules based on search
  const filteredRules = rules.filter((r) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      r.disease_group.toLowerCase().includes(q) ||
      r.action_vi.toLowerCase().includes(q) ||
      r.triggers_any.some((t) => t.toLowerCase().includes(q))
    );
  });

  return (
    <div className="flex-1 p-5 md:p-8 max-w-[1700px] w-full mx-auto space-y-7 select-none">
      {/* 1. TOP EMERGENCY BANNER */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-red-600 via-rose-600 to-red-700 text-white p-6 md:p-9 shadow-lg shadow-red-500/20 border border-red-400/40">
        <div className="absolute -right-16 -top-16 w-80 h-80 bg-white/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
          <div className="space-y-2.5 max-w-2xl">
            <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-red-500/50 border border-red-300/40 text-xs font-bold uppercase tracking-wider backdrop-blur-sm">
              <span className="w-2.5 h-2.5 rounded-full bg-white animate-ping" />
              <span>Trung Tâm Cảnh Báo Đỏ & Cấp Cứu 115 Chuẩn BYT</span>
            </div>
            <h1 className="text-2xl md:text-4xl font-black tracking-tight leading-tight">
              Phát Hiện Dấu Hiệu Đe Dọa Sinh Mạng
            </h1>
            <p className="text-sm md:text-base text-red-100/95 leading-relaxed font-medium">
              Hệ thống kích hoạt phản hồi tức thì (&le; 0.5s), bộ đánh giá sàng lọc Triage khẩn cấp, nhịp thở CPR 110 BPM và danh bạ trung tâm Đột quỵ / PCI can thiệp tim mạch.
            </p>
          </div>

          {/* Quick Call & Action Buttons */}
          <div className="flex flex-wrap items-center gap-3.5 flex-shrink-0">
            <a
              href="tel:115"
              onClick={playEmergencyTone}
              className="flex items-center space-x-3 px-6 py-4 rounded-2xl bg-white text-red-600 hover:bg-red-50 active:scale-95 font-black text-lg shadow-xl shadow-red-950/20 transition-all group"
            >
              <PhoneCall className="w-6 h-6 text-red-600 group-hover:animate-bounce" />
              <span>GỌI 115 NGAY</span>
            </a>

            <button
              type="button"
              onClick={handleSyncCrawler}
              disabled={isSyncing}
              className="flex items-center space-x-2 px-4 py-4 rounded-2xl bg-red-800/90 hover:bg-red-900 active:scale-95 text-white font-bold text-xs border border-red-300/30 transition-all shadow-md"
              title="Tự động cào dữ liệu phác đồ khẩn cấp từ Cổng kcb.vn"
            >
              <RefreshCw className={`w-4 h-4 text-amber-300 ${isSyncing ? 'animate-spin' : ''}`} />
              <span>{isSyncing ? 'Đang cào kcb.vn...' : 'Cập Nhật BYT'}</span>
            </button>

            <Link
              href="/chat?mode=emergency"
              className="flex items-center space-x-2 px-5 py-4 rounded-2xl bg-red-900/90 hover:bg-black/40 active:scale-95 text-white font-bold text-sm border border-red-300/30 transition-all backdrop-blur-sm"
            >
              <Bot className="w-5 h-5 text-emerald-300" />
              <span>AI Cấp Cứu</span>
            </Link>
          </div>
        </div>

        {/* Sync Toast Feedback */}
        {syncMessage && (
          <div className="mt-4 p-3 rounded-xl bg-black/30 border border-white/20 text-xs font-semibold text-amber-200 flex items-center space-x-2 animate-fadeIn">
            <Sparkles size={15} className="text-amber-300 flex-shrink-0" />
            <span>{syncMessage}</span>
          </div>
        )}
      </div>

      {/* 2. TAB CONTROLS & NAVIGATION */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4 border-b border-slate-200/80 pb-4">
        {/* Navigation Tabs */}
        <div className="flex items-center space-x-2 bg-slate-100/90 p-1.5 rounded-2xl border border-slate-200/60 overflow-x-auto no-scrollbar">
          <button
            type="button"
            onClick={() => setActiveTab('flags')}
            className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl text-xs md:text-sm font-bold transition whitespace-nowrap ${
              activeTab === 'flags'
                ? 'bg-white text-red-600 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <ShieldAlert size={16} />
            <span>Hội Chứng Nguy Kịch ({rules.length})</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('triage')}
            className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl text-xs md:text-sm font-bold transition whitespace-nowrap ${
              activeTab === 'triage'
                ? 'bg-red-600 text-white shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Zap size={16} />
            <span>Sàng Lọc Triage Nhanh</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('cpr')}
            className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl text-xs md:text-sm font-bold transition whitespace-nowrap ${
              activeTab === 'cpr'
                ? 'bg-white text-rose-600 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Activity size={16} />
            <span>Nhịp Ép Tim CPR (110 BPM)</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('firstaid')}
            className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl text-xs md:text-sm font-bold transition whitespace-nowrap ${
              activeTab === 'firstaid'
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <HeartPulse size={16} />
            <span>Sổ Tay Sơ Cứu ({guides.length})</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('hotlines')}
            className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl text-xs md:text-sm font-bold transition whitespace-nowrap ${
              activeTab === 'hotlines'
                ? 'bg-white text-emerald-600 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Building2 size={16} />
            <span>Đột Quỵ & Can Thiệp PCI</span>
          </button>
        </div>

        {/* Search Input for Red Flag signs */}
        {activeTab === 'flags' && (
          <div className="relative w-full sm:w-72">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
            <input
              type="text"
              placeholder="Tìm dấu hiệu nguy kịch..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 rounded-xl bg-white border border-slate-200 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-red-400 focus:border-red-500 shadow-2xs"
            />
          </div>
        )}
      </div>

      {/* 3. TAB 1: RED FLAG CRITICAL RULES */}
      {activeTab === 'flags' && (
        <div className="space-y-5">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {filteredRules.map((rule) => {
              const isCritical = rule.severity === 'CRITICAL_EMERGENCY';
              return (
                <div
                  key={rule.id}
                  className="bg-white rounded-3xl p-6 border border-slate-200/90 shadow-sm hover:shadow-md transition-all flex flex-col justify-between space-y-4 group hover:border-red-300 relative overflow-hidden"
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span
                        className={`text-[10px] font-extrabold px-2.5 py-0.5 rounded-full uppercase tracking-wider border ${
                          isCritical
                            ? 'bg-red-50 text-red-700 border-red-200'
                            : 'bg-amber-50 text-amber-700 border-amber-200'
                        }`}
                      >
                        {isCritical ? 'Tối Khẩn Cấp' : 'Ưu Tiên Cao'}
                      </span>
                      <span className="text-[11px] font-mono font-semibold text-slate-400 flex items-center gap-1">
                        <Clock size={12} /> &le; {rule.response_time_limit_sec}s
                      </span>
                    </div>

                    <h3 className="text-base md:text-lg font-black text-slate-900 group-hover:text-red-600 transition-colors">
                      {rule.disease_group}
                    </h3>
                  </div>

                  <div className="space-y-2">
                    <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                      Dấu hiệu chỉ điểm:
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {rule.triggers_any.map((trigger, idx) => (
                        <span
                          key={idx}
                          className="text-xs px-2.5 py-1 rounded-lg bg-red-50/70 border border-red-100 text-red-900 font-medium"
                        >
                          {trigger}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200/80 text-xs text-slate-700 leading-relaxed space-y-1">
                    <span className="font-bold text-red-600 flex items-center gap-1">
                      <AlertTriangle size={13} /> Xử trí khẩn cấp:
                    </span>
                    <p className="line-clamp-3">{rule.action_vi}</p>
                  </div>

                  <div className="pt-2 flex items-center justify-between border-t border-slate-100">
                    <button
                      type="button"
                      onClick={() => setSelectedRule(rule)}
                      className="text-xs font-bold text-blue-600 hover:text-blue-700 flex items-center space-x-1"
                    >
                      <span>Xem toàn văn</span>
                      <ChevronRight size={14} />
                    </button>

                    <a
                      href="tel:115"
                      className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-red-600 hover:bg-red-700 text-white font-bold text-xs shadow-xs transition active:scale-95"
                    >
                      <PhoneCall size={12} />
                      <span>Gọi 115</span>
                    </a>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* 4. TAB 2: RAPID TRIAGE SCREENER */}
      {activeTab === 'triage' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-7 items-start">
          {/* Left Column: Symptom Checklist */}
          <div className="lg:col-span-7 bg-white rounded-3xl p-6 md:p-7 border border-slate-200/90 shadow-sm space-y-5">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h3 className="text-lg font-black text-slate-900 flex items-center gap-2">
                  <Zap className="text-red-600" size={20} />
                  Bảng Sàng Lọc Phân Tầng Nguy Cơ Cấp Cứu (Triage)
                </h3>
                <p className="text-xs text-slate-500 mt-1">
                  Đánh dấu các triệu chứng quan sát được ở bệnh nhân để hệ thống phân loại mức độ ưu tiên:
                </p>
              </div>
              {selectedSymptoms.length > 0 && (
                <button
                  type="button"
                  onClick={() => setSelectedSymptoms([])}
                  className="text-xs text-slate-400 hover:text-red-600 font-medium"
                >
                  Xóa chọn
                </button>
              )}
            </div>

            <div className="space-y-3">
              {triageOptions.map((opt) => {
                const isSelected = selectedSymptoms.includes(opt.id);
                return (
                  <label
                    key={opt.id}
                    onClick={() => toggleSymptom(opt.id)}
                    className={`flex items-start space-x-3.5 p-4 rounded-2xl border cursor-pointer transition-all ${
                      isSelected
                        ? 'bg-red-50/70 border-red-400 shadow-xs'
                        : 'bg-slate-50/50 border-slate-200 hover:border-slate-300'
                    }`}
                  >
                    <div
                      className={`w-5 h-5 rounded-lg flex items-center justify-center mt-0.5 border transition ${
                        isSelected ? 'bg-red-600 border-red-600 text-white' : 'border-slate-300 bg-white'
                      }`}
                    >
                      {isSelected && <Check size={14} className="stroke-[3]" />}
                    </div>
                    <div className="flex-1">
                      <span className={`text-sm font-bold leading-snug ${isSelected ? 'text-red-950' : 'text-slate-800'}`}>
                        {opt.label}
                      </span>
                    </div>
                  </label>
                );
              })}
            </div>
          </div>

          {/* Right Column: Dynamic Triage Result & Guidance */}
          <div className="lg:col-span-5 space-y-5">
            <div className={`rounded-3xl p-6 md:p-7 border shadow-lg transition-all ${
              hasLevel1Emergency
                ? 'bg-gradient-to-br from-red-600 to-rose-700 text-white border-red-500 shadow-red-500/25 animate-pulse'
                : selectedSymptoms.length > 0
                ? 'bg-gradient-to-br from-amber-500 to-amber-600 text-white border-amber-400'
                : 'bg-white text-slate-800 border-slate-200/90'
            }`}>
              <div className="flex items-center justify-between">
                <span className={`text-xs font-black uppercase tracking-wider px-3 py-1 rounded-full ${
                  hasLevel1Emergency
                    ? 'bg-white text-red-700'
                    : selectedSymptoms.length > 0
                    ? 'bg-white text-amber-800'
                    : 'bg-slate-100 text-slate-600'
                }`}>
                  {hasLevel1Emergency ? 'CẤP CỨU MỨC 1 (ĐỎ) - NGUY HIỂM TÍNH MẠNG' : selectedSymptoms.length > 0 ? 'ƯU TIÊN CẤP CỨU MỨC 2 (VÀNG)' : 'CHƯA CHỌN DẤU HIỆU'}
                </span>
                <span className="text-xs font-mono font-bold">
                  {selectedSymptoms.length} dấu hiệu
                </span>
              </div>

              <div className="mt-4 space-y-3">
                {hasLevel1Emergency ? (
                  <>
                    <h4 className="text-xl font-black leading-tight">
                      CẢNH BÁO: Bệnh nhân có nguy cơ đe dọa sinh mạng tức thì!
                    </h4>
                    <p className="text-xs leading-relaxed text-red-100 font-medium">
                      Yêu cầu hỗ trợ y tế khẩn cấp 115 hoặc chuyển thẳng phòng Cấp cứu hồi sức tích cực không chậm trễ.
                    </p>
                    <a
                      href="tel:115"
                      onClick={playEmergencyTone}
                      className="inline-flex items-center justify-center space-x-2 w-full py-3.5 rounded-2xl bg-white text-red-600 font-extrabold text-base shadow-xl active:scale-95 transition"
                    >
                      <PhoneCall size={18} />
                      <span>GỌI 115 NGAY LẬP TỨC</span>
                    </a>
                  </>
                ) : selectedSymptoms.length > 0 ? (
                  <>
                    <h4 className="text-lg font-black leading-tight">
                      Tình trạng cần can thiệp y tế khẩn cấp trong vòng 15-30 phút!
                    </h4>
                    <p className="text-xs leading-relaxed text-amber-100">
                      Theo dõi sát sinh hiệu (SpO2, mạch, huyết áp), chuẩn bị xe cấp cứu chuyên dụng.
                    </p>
                  </>
                ) : (
                  <p className="text-xs text-slate-500 leading-relaxed">
                    Vui lòng tích chọn các dấu hiệu bên trái để nhận cảnh báo phân loại Triage và hành động cấp cứu theo phác đồ Bộ Y Tế.
                  </p>
                )}
              </div>
            </div>

            {/* Step-by-step Action Recommendations */}
            {selectedTriageItems.length > 0 && (
              <div className="bg-white rounded-3xl p-6 border border-slate-200/90 shadow-sm space-y-4">
                <h4 className="text-sm font-black text-slate-900 uppercase tracking-wider flex items-center gap-2">
                  <AlertTriangle size={16} className="text-amber-500" />
                  Chỉ Dẫn Xử Trí Tức Thời Cho Ca Này
                </h4>
                <div className="space-y-3">
                  {selectedTriageItems.map((item, idx) => (
                    <div key={idx} className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200/80 text-xs space-y-1">
                      <span className="font-bold text-red-700">{item.label}:</span>
                      <p className="text-slate-700 leading-relaxed">{item.advice}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 5. TAB 3: CPR METRONOME (110 BPM) */}
      {activeTab === 'cpr' && (
        <div className="max-w-3xl mx-auto bg-white rounded-3xl p-6 md:p-9 border border-slate-200/90 shadow-md space-y-7 text-center">
          <div className="space-y-2">
            <div className="inline-flex items-center space-x-2 px-3.5 py-1 rounded-full bg-rose-50 text-rose-700 border border-rose-200 text-xs font-bold uppercase tracking-wider">
              <HeartPulse size={14} className="text-rose-600 animate-pulse" />
              <span>Máy Đếm Nhịp Ép Tim Hồi Sinh Tim Phổi Chuẩn AHA / BYT</span>
            </div>
            <h2 className="text-2xl md:text-3xl font-black text-slate-900">
              Nhịp Ép Tim: 110 Lần / Phút (30:2)
            </h2>
            <p className="text-xs md:text-sm text-slate-500 max-w-lg mx-auto">
              Ép ngực sâu 5-6 cm ở giữa xương ức, để lồng ngực nở hoàn toàn sau mỗi lần ép. Tỷ lệ: 30 lần ép tim kết hợp 2 lần thổi ngạt.
            </p>
          </div>

          {/* Visual Pulsing Circle */}
          <div className="flex flex-col items-center justify-center py-4">
            <div
              className={`relative flex items-center justify-center rounded-full transition-all duration-150 ${
                isCprPlaying && cprPhase === 'press'
                  ? 'w-48 h-48 bg-rose-600 text-white shadow-2xl shadow-rose-500/40 scale-105'
                  : isCprPlaying && cprPhase === 'breathe'
                  ? 'w-48 h-48 bg-blue-600 text-white shadow-2xl shadow-blue-500/40'
                  : 'w-44 h-44 bg-slate-100 text-slate-600 border border-slate-200'
              }`}
            >
              {isCprPlaying && (
                <div
                  className={`absolute inset-0 rounded-full animate-ping opacity-30 ${
                    cprPhase === 'press' ? 'bg-rose-500' : 'bg-blue-400'
                  }`}
                />
              )}

              <div className="relative z-10 flex flex-col items-center justify-center">
                {cprPhase === 'press' ? (
                  <>
                    <span className="text-5xl font-black tracking-tight font-mono">
                      {isCprPlaying ? cprCount : 0}
                    </span>
                    <span className="text-xs font-bold uppercase tracking-wider mt-1 opacity-90">
                      / 30 Lần Ép
                    </span>
                  </>
                ) : (
                  <>
                    <span className="text-2xl font-black tracking-tight">THỔI NGẠT</span>
                    <span className="text-xs font-bold uppercase tracking-wider mt-1 opacity-90">
                      2 Hơi Thở Sâu
                    </span>
                  </>
                )}
              </div>
            </div>

            <div className="mt-5 text-xs font-bold text-slate-600 flex items-center gap-2">
              <span className={`w-3 h-3 rounded-full ${isCprPlaying ? 'bg-emerald-500 animate-pulse' : 'bg-slate-300'}`} />
              <span>{isCprPlaying ? `Đang phát âm thanh nhịp ${cprBpm} BPM` : 'Bấm nút để kích hoạt máy đếm nhịp'}</span>
            </div>
          </div>

          {/* Start/Stop Button */}
          <div className="flex justify-center gap-4">
            <button
              type="button"
              onClick={toggleCprMetronome}
              className={`flex items-center space-x-3 px-8 py-4 rounded-2xl font-black text-base shadow-lg transition active:scale-95 ${
                isCprPlaying
                  ? 'bg-slate-900 hover:bg-black text-white shadow-slate-900/20'
                  : 'bg-rose-600 hover:bg-rose-700 text-white shadow-rose-600/30'
              }`}
            >
              {isCprPlaying ? (
                <>
                  <Square size={20} className="fill-current" />
                  <span>DỪNG MÁY ĐẾM NHỊP</span>
                </>
              ) : (
                <>
                  <Play size={20} className="fill-current" />
                  <span>BẬT NHỊP ÉP TIM 110 BPM</span>
                </>
              )}
            </button>
          </div>

          {/* 4 Golden Steps of CPR */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3 text-left pt-4 border-t border-slate-100">
            <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200/80">
              <span className="font-mono text-xs font-extrabold text-rose-600">01. ĐÁNH GIÁ</span>
              <p className="text-xs text-slate-700 mt-1">Lay vai, gọi lớn, kiểm tra cử động thở trong 10 giây.</p>
            </div>
            <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200/80">
              <span className="font-mono text-xs font-extrabold text-rose-600">02. GỌI 115</span>
              <p className="text-xs text-slate-700 mt-1">Hô hoán người hỗ trợ và gọi 115 bật loa ngoài.</p>
            </div>
            <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200/80">
              <span className="font-mono text-xs font-extrabold text-rose-600">03. ÉP NGỰC</span>
              <p className="text-xs text-slate-700 mt-1">2 bàn tay khóa vào nhau, ép sâu 5cm theo nhịp 110 bpm.</p>
            </div>
            <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200/80">
              <span className="font-mono text-xs font-extrabold text-rose-600">04. THỔI NGẠT</span>
              <p className="text-xs text-slate-700 mt-1">Ngửa đầu nâng cằm, thổi 2 hơi nâng lồng ngực rồi ép tiếp.</p>
            </div>
          </div>
        </div>
      )}

      {/* 6. TAB 4: FIRST AID HANDBOOK */}
      {activeTab === 'firstaid' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {guides.map((guide) => (
            <div
              key={guide.id}
              className="bg-white rounded-3xl p-6 md:p-7 border border-slate-200/90 shadow-sm space-y-5"
            >
              <div className="flex items-start space-x-3.5">
                <div className="w-11 h-11 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center flex-shrink-0 border border-blue-200">
                  <HeartPulse size={22} />
                </div>
                <div>
                  <h3 className="text-lg font-black text-slate-900">{guide.title}</h3>
                  <p className="text-xs font-medium text-slate-500 mt-0.5">{guide.subtitle}</p>
                </div>
              </div>

              <div className="space-y-2.5">
                {guide.steps.map((step, sIdx) => (
                  <div
                    key={sIdx}
                    className="p-3 rounded-xl bg-slate-50 border border-slate-200/70 text-xs md:text-sm text-slate-800 flex items-start space-x-2.5 leading-relaxed"
                  >
                    <CheckCircle2 size={16} className="text-emerald-500 flex-shrink-0 mt-0.5" />
                    <span>{step}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 7. TAB 5: EMERGENCY HOTLINES & STROKE/PCI CENTERS */}
      {activeTab === 'hotlines' && (
        <div className="space-y-6">
          <div className="bg-emerald-50 border border-emerald-200 rounded-3xl p-5 flex items-start space-x-3">
            <Info className="w-5 h-5 text-emerald-700 flex-shrink-0 mt-0.5" />
            <p className="text-xs md:text-sm text-emerald-900 leading-relaxed font-medium">
              Các trung tâm bên dưới có phòng Can Thiệp Tim Mạch (Cathlab) và Đơn vị Đột Quỵ chuyên sâu hoạt động 24/7. Đối với bệnh nhân Nhồi máu cơ tim cấp hoặc Đột quỵ trong giờ vàng, liên hệ trực tiếp số Hotline cấp cứu để kíp can thiệp sẵn sàng trước khi xe tới.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {strokePciCenters.map((item, idx) => (
              <div
                key={idx}
                className="bg-white rounded-3xl p-6 border border-slate-200/90 shadow-sm space-y-4 flex flex-col justify-between hover:border-emerald-300 transition"
              >
                <div className="space-y-2.5">
                  <span className="text-[10px] font-bold px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 uppercase tracking-wider">
                    {item.capability}
                  </span>
                  <h3 className="text-base md:text-lg font-black text-slate-900 leading-snug">{item.name}</h3>
                  <p className="text-xs text-slate-600 leading-relaxed">{item.description}</p>
                  {item.address && (
                    <p className="text-[11px] text-slate-400 flex items-center gap-1.5 pt-1">
                      <MapPin size={13} className="text-slate-400 flex-shrink-0" />
                      <span>{item.address}</span>
                    </p>
                  )}
                </div>

                <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
                  <span className="font-mono text-base md:text-lg font-extrabold text-slate-900 tracking-wider">
                    {item.phone}
                  </span>
                  <a
                    href={`tel:${item.phone.replace(/\s+/g, '')}`}
                    className="flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow-xs active:scale-95 transition"
                  >
                    <PhoneCall size={13} />
                    <span>Gọi Ngay</span>
                  </a>
                </div>
              </div>
            ))}

            {hotlines.map((item, idx) => (
              <div
                key={`national-${idx}`}
                className="bg-white rounded-3xl p-6 border border-slate-200/90 shadow-sm space-y-4 flex flex-col justify-between hover:border-slate-300 transition"
              >
                <div className="space-y-2">
                  <span className="text-[10px] font-bold px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200 uppercase tracking-wider">
                    {item.type === 'national' ? 'Toàn Quốc' : item.type === 'regional' ? 'Khu Vực' : 'Chuyên Khoa'}
                  </span>
                  <h3 className="text-base md:text-lg font-black text-slate-900">{item.name}</h3>
                  <p className="text-xs text-slate-500 leading-relaxed">{item.description}</p>
                </div>

                <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
                  <span className="font-mono text-lg font-extrabold text-slate-900 tracking-wider">
                    {item.phone}
                  </span>
                  <a
                    href={`tel:${item.phone.replace(/\s+/g, '')}`}
                    className="flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-slate-800 hover:bg-black text-white text-xs font-bold shadow-xs active:scale-95 transition"
                  >
                    <PhoneCall size={13} />
                    <span>Bấm Gọi</span>
                  </a>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 8. DETAIL MODAL FOR RED FLAG */}
      {selectedRule && (
        <div className="fixed inset-0 z-[9999] w-screen h-screen min-h-screen min-w-full bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white rounded-3xl max-w-lg w-full p-6 md:p-7 shadow-2xl border border-slate-200 space-y-4 my-auto">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-2xl bg-red-100 text-red-600 flex items-center justify-center flex-shrink-0">
                <ShieldAlert size={22} />
              </div>
              <div>
                <span className="text-[10px] font-extrabold px-2 py-0.5 rounded-full bg-red-50 text-red-700 border border-red-200 uppercase">
                  {selectedRule.severity}
                </span>
                <h3 className="text-lg font-black text-slate-900">{selectedRule.disease_group}</h3>
              </div>
            </div>

            <div className="space-y-2">
              <span className="text-xs font-bold text-slate-500 uppercase">Toàn bộ dấu hiệu cảnh báo:</span>
              <div className="flex flex-wrap gap-1.5">
                {selectedRule.triggers_any.map((t, idx) => (
                  <span key={idx} className="text-xs px-2.5 py-1 rounded-lg bg-red-50 text-red-800 font-semibold border border-red-100">
                    {t}
                  </span>
                ))}
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-red-50/80 border border-red-200 space-y-1 text-xs md:text-sm text-red-950 font-semibold leading-relaxed">
              <span>Hướng Dẫn Xử Trí Khẩn Cấp Chuẩn Bộ Y Tế:</span>
              <p>{selectedRule.action_vi}</p>
            </div>

            <div className="flex items-center justify-end space-x-2 pt-2">
              <button
                type="button"
                onClick={() => setSelectedRule(null)}
                className="px-4 py-2 rounded-xl text-xs font-bold text-slate-500 hover:bg-slate-100"
              >
                Đóng
              </button>
              <a
                href="tel:115"
                className="px-5 py-2.5 rounded-xl bg-red-600 hover:bg-red-700 text-white text-xs font-bold flex items-center space-x-1.5 shadow-md shadow-red-600/25"
              >
                <PhoneCall size={14} />
                <span>Gọi 115 Ngay</span>
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
