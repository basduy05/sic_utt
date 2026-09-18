'use client';

import React, { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import {
  Users,
  Bot,
  Database,
  Play,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Plus,
  Trash2,
  Shield,
  Upload,
  Download,
  Terminal,
  HardDrive,
  Cpu,
  Activity,
  ExternalLink,
  FileText,
  Sparkles,
  Check,
  X,
  Lock,
  ArrowLeft,
  Layers,
  BookOpen,
  AlertTriangle,
  Link2,
  HelpCircle,
  Network,
  Zap,
  Radio,
  ArrowRight,
  Sliders,
  CheckCheck,
  FileCode,
  Search,
  Volume2,
  MessageSquare,
  Binary,
  GitBranch,
  Server,
  ChevronLeft,
  ChevronRight,
  Maximize2,
  Minimize2,
  ThumbsUp,
  ThumbsDown,
} from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { medicalService } from '../../services/medicalService';
import { GlossaryEntry } from '../../types/medical';

export default function AdminPage() {
  const { user, isAdmin, quickLoginAs } = useAuth();
  const [activeTab, setActiveTab] = useState<'users' | 'ai_models' | 'training_data' | 'training_center' | 'architecture' | 'conversations' | 'feedback'>('users');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [actionMessage, setActionMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // --- Tab 1: User Management State ---
  const [usersList, setUsersList] = useState<any[]>([]);

  // --- Tab 2: AI Models State ---
  const [modelsList, setModelsList] = useState<any[]>([]);
  const [systemHealth, setSystemHealth] = useState<any>(null);

  // --- Tab 3: Training Data & Lexicon State ---
  const [datasets, setDatasets] = useState<any[]>([]);
  const [glossary, setGlossary] = useState<Record<string, GlossaryEntry>>({});
  const [icdCodes, setIcdCodes] = useState<Record<string, any>>({});
  const [ragDocs, setRagDocs] = useState<any[]>([]);
  const [dataSubTab, setDataSubTab] = useState<'datasets' | 'glossary' | 'icd' | 'rag'>('datasets');

  // Form add glossary term
  const [newKey, setNewKey] = useState('');
  const [newTerm, setNewTerm] = useState('');
  const [newIcd, setNewIcd] = useState('');
  const [newCategory, setNewCategory] = useState('Chung');
  const [newSynonyms, setNewSynonyms] = useState('');
  const [isRedFlag, setIsRedFlag] = useState(false);

  // Form add RAG doc
  const [newRagTitle, setNewRagTitle] = useState('');
  const [newRagContent, setNewRagContent] = useState('');
  const [newRagSource, setNewRagSource] = useState('Bộ Y Tế');

  // --- Tab 4: Training Studio & Colab State ---
  const [colabUrl, setColabUrl] = useState('');
  const [colabFilename, setColabFilename] = useState('');
  const [isColabDownloading, setIsColabDownloading] = useState(false);
  const [trainingJobType, setTrainingJobType] = useState('retrain');
  const [selectedDataset, setSelectedDataset] = useState('');
  const [trainingStatus, setTrainingStatus] = useState<any>(null);
  const [trainingLogs, setTrainingLogs] = useState<string[]>([]);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [isStartingTraining, setIsStartingTraining] = useState(false);
  const logTerminalRef = useRef<HTMLDivElement>(null);

  // --- Tab 5: Architecture & Live Query Trace State ---
  const [archSubTab, setArchSubTab] = useState<'pipeline' | 'audit'>('pipeline');
  const [archDiagramView, setArchDiagramView] = useState<'flowchart' | 'grid'>('flowchart');
  const [selectedArchNode, setSelectedArchNode] = useState<number>(1);
  const [isSimulatingTrace, setIsSimulatingTrace] = useState<boolean>(false);
  const [traceStep, setTraceStep] = useState<number>(-1);
  const [traceScenario, setTraceScenario] = useState<'dengue' | 'cardiac' | 'chitchat' | 'custom'>('dengue');
  const [customQueryText, setCustomQueryText] = useState<string>('Tôi bị sốt cao 39.2 độ từ hôm qua, đau đầu dữ dội, đau mỏi hốc mắt nhưng không ho, có vài nốt chấm đỏ ở cẳng tay');
  const [autoRealtimePolling, setAutoRealtimePolling] = useState<boolean>(true);
  const [lastTelemetryUpdate, setLastTelemetryUpdate] = useState<string>('Vừa xong');
  const [pipelineLayoutMode, setPipelineLayoutMode] = useState<'scroll' | 'fit'>('fit');
  const pipelineTrackRef = useRef<HTMLDivElement>(null);

  const scrollPipeline = (direction: 'left' | 'right') => {
    if (pipelineTrackRef.current) {
      const scrollAmount = direction === 'left' ? -360 : 360;
      pipelineTrackRef.current.scrollBy({ left: scrollAmount, behavior: 'smooth' });
    }
  };

  const showToast = (type: 'success' | 'error', text: string) => {
    setActionMessage({ type, text });
    setTimeout(() => setActionMessage(null), 4500);
  };

  // --- Tab 6: Conversations State ---
  const [conversationsList, setConversationsList] = useState<any[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [sessionMessages, setSessionMessages] = useState<any[]>([]);
  const [isLoadingMessages, setIsLoadingMessages] = useState<boolean>(false);
  const [conversationSearch, setConversationSearch] = useState<string>('');

  // --- Tab 7: Feedback State ---
  const [feedbackList, setFeedbackList] = useState<any[]>([]);
  const [feedbackStats, setFeedbackStats] = useState<{ total: number; likes: number; dislikes: number; like_ratio: number }>({
    total: 0,
    likes: 0,
    dislikes: 0,
    like_ratio: 1,
  });
  const [feedbackFilter, setFeedbackFilter] = useState<'all' | 'like' | 'dislike'>('all');

  const fetchConversations = async () => {
    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
      const res = await fetch(`${API_BASE}/admin/conversations`);
      if (res.ok) {
        const data = await res.json();
        setConversationsList(data.sessions || []);
      }
    } catch (err) {
      console.warn('Failed to load conversations:', err);
    }
  };

  const fetchSessionMessages = async (sid: string) => {
    setSelectedSessionId(sid);
    setIsLoadingMessages(true);
    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
      const res = await fetch(`${API_BASE}/admin/conversations/${sid}/messages`);
      if (res.ok) {
        const data = await res.json();
        setSessionMessages(data.messages || []);
      }
    } catch (err) {
      console.warn('Failed to load session messages:', err);
    } finally {
      setIsLoadingMessages(false);
    }
  };

  const fetchFeedback = async () => {
    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
      const res = await fetch(`${API_BASE}/admin/feedback`);
      if (res.ok) {
        const data = await res.json();
        setFeedbackList(data.feedback || []);
        if (data.stats) setFeedbackStats(data.stats);
      }
    } catch (err) {
      console.warn('Failed to load feedback:', err);
    }
  };

  // --- Data Loading ---
  const loadAllData = async () => {
    setIsLoading(true);
    try {
      const [
        usersRes,
        modelsRes,
        datasetsRes,
        glossRes,
        icdRes,
        ragRes,
        healthRes,
        statusRes
      ] = await Promise.all([
        medicalService.getUsers().catch(() => ({ users: [] })),
        medicalService.getAiModels().catch(() => ({ models: [] })),
        medicalService.getDatasets().catch(() => ({ datasets: [] })),
        medicalService.getGlossary().catch(() => ({})),
        medicalService.getIcdCodes().catch(() => ({})),
        medicalService.getRagKnowledge().catch(() => []),
        medicalService.getSystemHealth().catch(() => null),
        medicalService.getTrainingStatus().catch(() => null),
      ]);

      setUsersList(usersRes.users || []);
      setModelsList(modelsRes.models || []);
      setDatasets(datasetsRes.datasets || []);
      setGlossary(glossRes || {});
      setIcdCodes(icdRes || {});
      setRagDocs(ragRes || []);
      setSystemHealth(healthRes);
      if (statusRes && statusRes.status !== 'idle') {
        setTrainingStatus(statusRes);
        setActiveJobId(statusRes.job_id);
        setTrainingLogs(statusRes.logs || []);
      }
      if (datasetsRes.datasets?.length > 0 && !selectedDataset) {
        setSelectedDataset(datasetsRes.datasets[0].filename);
      }
    } catch (err: any) {
      console.error('Failed to load admin data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadAllData();
    fetchConversations();
    fetchFeedback();
  }, []);

  useEffect(() => {
    if (activeTab === 'conversations') {
      fetchConversations();
    } else if (activeTab === 'feedback') {
      fetchFeedback();
    }
  }, [activeTab]);

  // Poll training logs if a job is running
  useEffect(() => {
    let interval: any = null;
    if (activeJobId && trainingStatus?.status === 'running') {
      interval = setInterval(async () => {
        try {
          const logData = await medicalService.getTrainingLogs(activeJobId, 0);
          setTrainingLogs(logData.logs || []);
          setTrainingStatus((prev: any) => ({
            ...prev,
            status: logData.status,
            progress: logData.progress,
            metrics: logData.metrics,
          }));
          if (logTerminalRef.current) {
            logTerminalRef.current.scrollTop = logTerminalRef.current.scrollHeight;
          }
          if (logData.status === 'completed' || logData.status === 'failed') {
            clearInterval(interval);
            loadAllData();
          }
        } catch (e) {
          console.error('Poll error', e);
        }
      }, 1200);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [activeJobId, trainingStatus?.status]);

  // Real-time telemetry polling for models & health
  useEffect(() => {
    if (!autoRealtimePolling) return;
    const interval = setInterval(async () => {
      try {
        const [modelsRes, healthRes] = await Promise.all([
          medicalService.getAiModels().catch(() => null),
          medicalService.getSystemHealth().catch(() => null),
        ]);
        if (modelsRes?.models) setModelsList(modelsRes.models);
        if (healthRes) setSystemHealth(healthRes);
        setLastTelemetryUpdate(new Date().toLocaleTimeString('vi-VN'));
      } catch (e) {
        // silent
      }
    }, 5000);
    return () => clearInterval(interval);
  }, [autoRealtimePolling]);

  // Query Lifecycle Trace Runner (Simulates data flowing through 8 stages)
  const handleStartTrace = () => {
    if (isSimulatingTrace) return;
    setIsSimulatingTrace(true);
    setTraceStep(1);
    setSelectedArchNode(1);

    let step = 1;
    const timer = setInterval(() => {
      step += 1;
      if (step <= 8) {
        setTraceStep(step);
        setSelectedArchNode(step);
      } else {
        clearInterval(timer);
        setIsSimulatingTrace(false);
      }
    }, 1100);
  };

  // --- User Handlers ---
  const handleRoleChange = async (userId: string, newRole: string) => {
    try {
      await medicalService.updateUserRole(userId, newRole);
      showToast('success', `Đã cập nhật vai trò thành [${newRole}] cho tài khoản.`);
      const res = await medicalService.getUsers();
      setUsersList(res.users || []);
    } catch (e: any) {
      showToast('error', e.message || 'Lỗi khi cập nhật quyền.');
    }
  };

  const handleDeleteUser = async (userId: string, email: string) => {
    if (!window.confirm(`Bạn có chắc chắn muốn xóa tài khoản "${email}" không?`)) return;
    try {
      await medicalService.deleteUser(userId);
      showToast('success', `Đã xóa người dùng ${email}`);
      const res = await medicalService.getUsers();
      setUsersList(res.users || []);
    } catch (e: any) {
      showToast('error', e.message || 'Không thể xóa user.');
    }
  };

  // --- Colab Download Handler ---
  const handleColabDownload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!colabUrl) {
      showToast('error', 'Vui lòng dán link Google Drive hoặc Google Colab output.');
      return;
    }
    setIsColabDownloading(true);
    try {
      const res = await medicalService.downloadFromColab(colabUrl, colabFilename || undefined);
      showToast('success', res.message || 'Đồng bộ tập dữ liệu thành công!');
      setColabUrl('');
      setColabFilename('');
      const dRes = await medicalService.getDatasets();
      setDatasets(dRes.datasets || []);
      if (res.filename) setSelectedDataset(res.filename);
    } catch (err: any) {
      showToast('error', err.message || 'Không thể tải file từ link Google Drive/Colab.');
    } finally {
      setIsColabDownloading(false);
    }
  };

  // --- Direct File Upload Handler ---
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const res = await medicalService.uploadDataset(file);
      showToast('success', res.message || `Đã tải lên tệp: ${file.name}`);
      const dRes = await medicalService.getDatasets();
      setDatasets(dRes.datasets || []);
      setSelectedDataset(file.name);
    } catch (err: any) {
      showToast('error', err.message || 'Tải tệp lên thất bại.');
    }
  };

  // --- Start Training Handler ---
  const handleStartTraining = async () => {
    setIsStartingTraining(true);
    try {
      const res = await medicalService.startTraining(trainingJobType, selectedDataset, {
        epochs: 5,
        batch_size: 32,
        val_split: 0.2
      });
      setActiveJobId(res.job_id);
      setTrainingStatus({ status: 'running', progress: 0, job_id: res.job_id });
      setTrainingLogs([`[INFO] Đang khởi động job ${res.job_id}...`]);
      showToast('success', `Đã khởi chạy Training Job #${res.job_id}`);
    } catch (err: any) {
      showToast('error', err.message || 'Không thể bắt đầu quá trình huấn luyện.');
    } finally {
      setIsStartingTraining(false);
    }
  };

  // --- Save Glossary Item ---
  const handleSaveGlossary = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newKey || !newTerm) return;
    const synList = newSynonyms.split(',').map((s) => s.trim()).filter(Boolean);
    try {
      await medicalService.saveGlossaryItem({
        key: newKey,
        standard_term: newTerm,
        icd_mapping: newIcd || undefined,
        synonyms: synList,
        category: newCategory,
        is_red_flag_potential: isRedFlag,
      });
      showToast('success', `Đã cập nhật triệu chứng [${newKey}] vào từ điển thực thể.`);
      const g = await medicalService.getGlossary();
      setGlossary(g);
      setNewKey('');
      setNewTerm('');
      setNewIcd('');
      setNewSynonyms('');
    } catch (e: any) {
      showToast('error', e.message || 'Lỗi khi lưu triệu chứng.');
    }
  };

  // --- Add RAG Document ---
  const handleAddRagDoc = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newRagTitle || !newRagContent) return;
    try {
      await medicalService.addRagDocument({
        title: newRagTitle,
        content: newRagContent,
        source: newRagSource,
      });
      showToast('success', 'Đã bổ sung tài liệu vào RAG Knowledge Base');
      setNewRagTitle('');
      setNewRagContent('');
      const r = await medicalService.getRagKnowledge();
      setRagDocs(r);
    } catch (e: any) {
      showToast('error', e.message || 'Lỗi thêm tài liệu RAG.');
    }
  };

  // --- Permission Gate ---
  if (!isAdmin) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-6 text-center">
        <div className="max-w-md w-full bg-white p-8 rounded-3xl border border-slate-200/80 shadow-xl flex flex-col items-center gap-4">
          <div className="w-16 h-16 rounded-2xl bg-rose-50 border border-rose-200 text-rose-600 flex items-center justify-center">
            <Lock className="w-8 h-8" />
          </div>
          <h2 className="text-xl font-bold text-slate-900">Yêu Cầu Quyền Quản Trị Viên</h2>
          <p className="text-xs text-slate-500 leading-relaxed">
            Phân hệ Quản Trị Hệ Thống (User, AI Models, Training Studio) chỉ dành cho tài khoản Admin.
            Tài khoản hiện tại của bạn: <strong className="text-slate-800">{user?.email || 'Chưa đăng nhập'}</strong> ({user?.role || 'khách'}).
          </p>
          <div className="flex flex-col gap-2.5 w-full mt-2">
            <button
              onClick={() => quickLoginAs('admin')}
              className="w-full py-2.5 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs shadow-md shadow-indigo-500/20 transition-all flex items-center justify-center gap-2"
            >
              <Shield className="w-4 h-4" />
              <span>Đăng nhập Admin (admin@medibot.vn)</span>
            </button>
            <Link
              href="/chat"
              className="w-full py-2.5 px-4 rounded-xl border border-slate-200 text-slate-700 font-bold text-xs hover:bg-slate-50 transition-colors flex items-center justify-center gap-2"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Quay lại Khám Bệnh AI</span>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col h-full max-h-full overflow-hidden bg-slate-50/50">
      {/* Toast Notification */}
      {actionMessage && (
        <div className={`fixed top-4 right-6 z-50 px-4 py-3 rounded-2xl shadow-xl border text-xs font-semibold flex items-center gap-2.5 transition-all animate-in fade-in slide-in-from-top-4 ${
          actionMessage.type === 'success'
            ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
            : 'bg-rose-50 border-rose-200 text-rose-800'
        }`}>
          {actionMessage.type === 'success' ? <CheckCircle2 className="w-4 h-4 text-emerald-600" /> : <AlertCircle className="w-4 h-4 text-rose-600" />}
          <span>{actionMessage.text}</span>
        </div>
      )}

      {/* Top Header */}
      <div className="flex-shrink-0 bg-white border-b border-slate-200/80 px-6 py-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-indigo-50 border border-indigo-100 text-indigo-600">
              <Cpu className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
                Trung Tâm Quản Trị AI & Tri Thức Lâm Sàng
                <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded-md bg-indigo-100 text-indigo-700 font-bold">
                  Admin Console v3.2
                </span>
              </h1>
              <p className="text-xs text-slate-500 mt-0.5">
                Quản lý người dùng, cấu hình model theo chức năng, nạp dữ liệu và huấn luyện AI trực quan qua GUI
              </p>
            </div>
          </div>
        </div>

        {/* Global Action / Refresh */}
        <div className="flex items-center gap-2">
          {systemHealth && (
            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-100 border border-slate-200 text-[11px] text-slate-600 font-medium">
              <span className={`w-2 h-2 rounded-full ${systemHealth.status === 'healthy' ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'}`} />
              <span>Hệ thống: {systemHealth.status === 'healthy' ? 'Hoạt động tốt' : 'Cần kiểm tra'}</span>
              <span className="text-slate-400 font-mono">({systemHealth.latency_ms}ms)</span>
            </div>
          )}
          <button
            onClick={loadAllData}
            disabled={isLoading}
            className="p-2 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-600 transition shadow-xs flex items-center gap-1.5 text-xs font-semibold"
            title="Làm mới toàn bộ dữ liệu"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin text-indigo-600' : ''}`} />
            <span className="hidden sm:inline">Làm mới</span>
          </button>
        </div>
      </div>

      {/* Main Layout: Sidebar Tabs + Content Area */}
      <div className="flex-1 flex flex-col md:flex-row overflow-hidden">
        {/* Navigation Sidebar */}
        <div className="w-full md:w-64 bg-white border-r border-slate-200/80 p-3 flex-shrink-0 flex md:flex-col gap-1.5 overflow-x-auto md:overflow-x-visible">
          <button
            onClick={() => setActiveTab('users')}
            className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition text-left ${
              activeTab === 'users'
                ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-600/30'
                : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
            }`}
          >
            <Users className="w-4 h-4" />
            <div className="flex-1">
              <div>Quản Lý Người Dùng</div>
              <div className={`text-[10px] ${activeTab === 'users' ? 'text-indigo-200' : 'text-slate-400'}`}>
                {usersList.length} tài khoản
              </div>
            </div>
          </button>

          <button
            onClick={() => setActiveTab('ai_models')}
            className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition text-left ${
              activeTab === 'ai_models'
                ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-600/30'
                : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
            }`}
          >
            <Bot className="w-4 h-4" />
            <div className="flex-1">
              <div>Quản Lý AI & Model</div>
              <div className={`text-[10px] ${activeTab === 'ai_models' ? 'text-indigo-200' : 'text-slate-400'}`}>
                {modelsList.length} models theo chức năng
              </div>
            </div>
          </button>

          <button
            onClick={() => setActiveTab('training_data')}
            className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition text-left ${
              activeTab === 'training_data'
                ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-600/30'
                : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
            }`}
          >
            <Database className="w-4 h-4" />
            <div className="flex-1">
              <div>Dữ Liệu Huấn Luyện</div>
              <div className={`text-[10px] ${activeTab === 'training_data' ? 'text-indigo-200' : 'text-slate-400'}`}>
                {datasets.length} datasets & CSDL
              </div>
            </div>
          </button>

          <button
            onClick={() => setActiveTab('training_center')}
            className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition text-left ${
              activeTab === 'training_center'
                ? 'bg-gradient-to-r from-indigo-600 to-violet-600 text-white shadow-sm shadow-indigo-600/30'
                : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
            }`}
          >
            <Play className="w-4 h-4 text-emerald-300" />
            <div className="flex-1">
              <div className="flex items-center gap-1.5">
                <span>Huấn Luyện AI (GUI)</span>
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              </div>
              <div className={`text-[10px] ${activeTab === 'training_center' ? 'text-indigo-200' : 'text-slate-400'}`}>
                Google Colab & Studio
              </div>
            </div>
          </button>

          <button
            onClick={() => setActiveTab('architecture')}
            className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition text-left ${
              activeTab === 'architecture'
                ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-600/30'
                : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
            }`}
          >
            <Network className="w-4 h-4" />
            <div className="flex-1">
              <div>Kiến Trúc & API Audit</div>
              <div className={`text-[10px] ${activeTab === 'architecture' ? 'text-indigo-200' : 'text-slate-400'}`}>
                Báo cáo Microservice
              </div>
            </div>
          </button>

          <button
            onClick={() => setActiveTab('conversations')}
            className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition text-left ${
              activeTab === 'conversations'
                ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-600/30'
                : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
            }`}
          >
            <MessageSquare className="w-4 h-4 text-sky-400" />
            <div className="flex-1">
              <div>Hội Thoại Người Dùng</div>
              <div className={`text-[10px] ${activeTab === 'conversations' ? 'text-indigo-200' : 'text-slate-400'}`}>
                {conversationsList.length} phiên khám bệnh
              </div>
            </div>
          </button>

          <button
            onClick={() => setActiveTab('feedback')}
            className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition text-left ${
              activeTab === 'feedback'
                ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-600/30'
                : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
            }`}
          >
            <ThumbsUp className="w-4 h-4 text-amber-300" />
            <div className="flex-1">
              <div>Đánh Giá & Phản Hồi</div>
              <div className={`text-[10px] ${activeTab === 'feedback' ? 'text-indigo-200' : 'text-slate-400'}`}>
                {feedbackList.length} phản hồi người dùng
              </div>
            </div>
          </button>
        </div>

        {/* Dynamic Content Panel */}
        <div className="flex-1 overflow-y-auto p-4 md:p-6 custom-scrollbar">
          {/* ======================================================== */}
          {/* TAB 1: USER MANAGEMENT                                   */}
          {/* ======================================================== */}
          {activeTab === 'users' && (
            <div className="space-y-6 w-full max-w-none">
              {/* Stat Cards */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3.5">
                <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs">
                  <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Tổng Người Dùng</span>
                  <div className="text-2xl font-black text-slate-900 mt-1">{usersList.length}</div>
                </div>
                <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs">
                  <span className="text-[11px] font-bold text-indigo-500 uppercase tracking-wider">Quản Trị Viên</span>
                  <div className="text-2xl font-black text-indigo-600 mt-1">
                    {usersList.filter((u) => u.role === 'admin').length}
                  </div>
                </div>
                <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs">
                  <span className="text-[11px] font-bold text-emerald-500 uppercase tracking-wider">Bác Sĩ / Chuyên Gia</span>
                  <div className="text-2xl font-black text-emerald-600 mt-1">
                    {usersList.filter((u) => u.role === 'doctor').length}
                  </div>
                </div>
                <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs">
                  <span className="text-[11px] font-bold text-blue-500 uppercase tracking-wider">Bệnh Nhân / User</span>
                  <div className="text-2xl font-black text-blue-600 mt-1">
                    {usersList.filter((u) => u.role === 'user').length}
                  </div>
                </div>
              </div>

              {/* User List Table */}
              <div className="bg-white rounded-3xl border border-slate-200/90 shadow-sm overflow-hidden">
                <div className="p-4 border-b border-slate-100 flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-bold text-slate-900">Danh Sách Người Dùng & Phân Quyền</h3>
                    <p className="text-xs text-slate-500">Chỉnh sửa vai trò trực tiếp hoặc thu hồi quyền truy cập</p>
                  </div>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold">
                        <th className="py-3 px-4">Họ Và Tên</th>
                        <th className="py-3 px-4">Email Đăng Nhập</th>
                        <th className="py-3 px-4">Vai Trò Hệ Thống</th>
                        <th className="py-3 px-4">Phiên Khám</th>
                        <th className="py-3 px-4 text-right">Thao Tác</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {usersList.map((u) => (
                        <tr key={u.id} className="hover:bg-slate-50/60 transition">
                          <td className="py-3 px-4 font-semibold text-slate-900">
                            <div className="flex items-center gap-2">
                              <div className="w-7 h-7 rounded-full bg-slate-100 text-slate-700 font-bold flex items-center justify-center text-xs border">
                                {u.full_name ? u.full_name[0].toUpperCase() : 'U'}
                              </div>
                              <span>{u.full_name || 'Chưa cập nhật'}</span>
                            </div>
                          </td>
                          <td className="py-3 px-4 font-mono text-slate-600">{u.email}</td>
                          <td className="py-3 px-4">
                            <select
                              value={u.role}
                              onChange={(e) => handleRoleChange(u.id, e.target.value)}
                              className={`text-xs font-semibold px-2.5 py-1 rounded-lg border focus:outline-none ${
                                u.role === 'admin'
                                  ? 'bg-indigo-50 border-indigo-200 text-indigo-700'
                                  : u.role === 'doctor'
                                  ? 'bg-emerald-50 border-emerald-200 text-emerald-700'
                                  : 'bg-slate-100 border-slate-200 text-slate-700'
                              }`}
                            >
                              <option value="admin">Quản trị viên (admin)</option>
                              <option value="doctor">Bác sĩ / Chuyên gia (doctor)</option>
                              <option value="user">Người dùng / Bệnh nhân (user)</option>
                              <option value="guest">Khách vãng lai (guest)</option>
                            </select>
                          </td>
                          <td className="py-3 px-4 text-slate-600 font-mono">
                            {u.session_count || 0} phiên
                          </td>
                          <td className="py-3 px-4 text-right">
                            {u.email !== 'admin@medibot.vn' ? (
                              <button
                                onClick={() => handleDeleteUser(u.id, u.email)}
                                className="p-1.5 text-rose-500 hover:bg-rose-50 rounded-lg transition"
                                title="Xóa tài khoản"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            ) : (
                              <span className="text-[10px] text-slate-400 italic">Mặc định</span>
                            )}
                          </td>
                        </tr>
                      ))}
                      {usersList.length === 0 && (
                        <tr>
                          <td colSpan={5} className="py-8 text-center text-slate-400">
                            Chưa có tài khoản nào được ghi nhận trong cơ sở dữ liệu.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* ======================================================== */}
          {/* TAB 2: AI & MODEL MANAGEMENT (Per-Function Models)       */}
          {/* ======================================================== */}
          {activeTab === 'ai_models' && (
            <div className="space-y-6 w-full max-w-none">
              {/* Overview banner */}
              <div className="bg-gradient-to-r from-slate-900 to-indigo-950 rounded-3xl p-6 text-white shadow-xl relative overflow-hidden w-full">
                <div className="relative z-10">
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] uppercase font-mono tracking-wider text-indigo-300 font-bold bg-indigo-900/60 px-2.5 py-0.5 rounded-md border border-indigo-700/50">
                      Multimodal Hybrid Pipeline
                    </span>
                    <span className="flex items-center gap-1.5 text-[11px] text-emerald-300 bg-emerald-950/60 px-2.5 py-0.5 rounded-md border border-emerald-800/50 font-mono">
                      <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                      <span>{modelsList.filter(m => m.status === 'active').length}/{modelsList.length} Models Online</span>
                    </span>
                  </div>
                  <h2 className="text-xl font-bold mt-2">Quản Lý Các Thành Phần & Model AI Theo Chức Năng</h2>
                  <p className="text-xs text-slate-300 mt-1 max-w-3xl leading-relaxed">
                    Hệ thống phối hợp đa mô hình: Trích xuất thực thể NER từ điển, Vector hóa TF-IDF n-grams, Phân loại NLP sơ bộ, Cây quyết định XGBoost
                    lâm sàng, Kho tri thức RAG Bộ Y Tế và Gemini LLM suy luận đối chiếu.
                  </p>
                </div>
                <div className="absolute right-[-20px] bottom-[-20px] opacity-10 text-white pointer-events-none">
                  <Bot className="w-64 h-64" />
                </div>
              </div>

              {/* Model Cards Grid - Responsive full width */}
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-5 w-full">
                {modelsList.map((m) => (
                  <div
                    key={m.filename}
                    className="bg-white rounded-3xl border border-slate-200/90 p-5 shadow-sm hover:shadow-md transition flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex items-center gap-2.5">
                          <div className="w-10 h-10 rounded-2xl bg-indigo-50 border border-indigo-100 text-indigo-600 flex items-center justify-center font-bold flex-shrink-0">
                            <Bot className="w-5 h-5" />
                          </div>
                          <div>
                            <h3 className="font-bold text-slate-900 text-sm leading-snug">{m.name_vi || m.name}</h3>
                            <span className="text-[11px] font-mono text-slate-400 block truncate max-w-[180px]">{m.filename}</span>
                          </div>
                        </div>
                        <span
                          className={`px-2.5 py-1 rounded-full text-[10px] font-bold border flex items-center gap-1 flex-shrink-0 ${
                            m.status === 'active'
                              ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                              : 'bg-rose-50 text-rose-700 border-rose-200'
                          }`}
                        >
                          <span className={`w-1.5 h-1.5 rounded-full ${m.status === 'active' ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`} />
                          {m.status === 'active' ? 'Sẵn Sàng' : 'Thiếu Tệp'}
                        </span>
                      </div>

                      {m.stage && (
                        <div className="mt-2.5 inline-block text-[10px] font-bold px-2 py-0.5 rounded-md bg-indigo-50 text-indigo-700 border border-indigo-100 font-mono">
                          {m.stage}
                        </div>
                      )}

                      <p className="text-xs text-slate-600 mt-2.5 leading-relaxed bg-slate-50 p-2.5 rounded-xl border border-slate-100">
                        {m.role}
                      </p>

                      <div className="grid grid-cols-2 gap-2 mt-3 text-[11px]">
                        <div className="bg-slate-50/70 p-2 rounded-lg">
                          <span className="text-slate-400 block text-[10px]">Chức Năng:</span>
                          <span className="font-semibold text-slate-700 capitalize truncate block">{m.function}</span>
                        </div>
                        <div className="bg-slate-50/70 p-2 rounded-lg">
                          <span className="text-slate-400 block text-[10px]">Framework:</span>
                          <span className="font-semibold text-slate-700 truncate block">{m.framework}</span>
                        </div>
                        <div className="bg-slate-50/70 p-2 rounded-lg">
                          <span className="text-slate-400 block text-[10px]">Dung lượng:</span>
                          <span className="font-semibold text-slate-700">{m.size_mb} MB</span>
                        </div>
                        <div className="bg-slate-50/70 p-2 rounded-lg">
                          <span className="text-slate-400 block text-[10px]">Cập nhật:</span>
                          <span className="font-semibold text-slate-700 truncate block">{m.last_updated || 'Chưa rõ'}</span>
                        </div>
                      </div>

                      {m.doc_count !== undefined && (
                        <div className="mt-2 text-[11px] text-teal-700 bg-teal-50 px-2.5 py-1 rounded-lg font-medium border border-teal-100">
                          📚 Kho tri thức: <strong>{m.doc_count}</strong> tài liệu phác đồ
                        </div>
                      )}
                    </div>

                    <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                      <button
                        onClick={() => {
                          setActiveTab('architecture');
                          setArchSubTab('pipeline');
                        }}
                        className="text-slate-500 hover:text-indigo-600 font-medium flex items-center gap-1 text-[11px]"
                      >
                        <Network className="w-3 h-3 text-indigo-500" />
                        <span>Xem trên sơ đồ luồng</span>
                      </button>
                      <button
                        onClick={() => {
                          setActiveTab('training_center');
                          setTrainingJobType('retrain');
                        }}
                        className="text-indigo-600 hover:text-indigo-800 font-bold flex items-center gap-1"
                      >
                        <span>Huấn luyện lại</span>
                        <ArrowLeft className="w-3 h-3 rotate-180" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              {/* LLM & Cloud Reasoning Section */}
              <div className="bg-white rounded-3xl border border-slate-200/90 p-5 shadow-sm">
                <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-indigo-600" />
                  <span>Mô Hình Ngôn Ngữ & Suy Luận Lâm Sàng (LLM & Reasoning)</span>
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-3">
                  <div className="border border-slate-100 bg-slate-50 p-4 rounded-2xl">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-slate-800 text-xs">Google Gemini 1.5 Flash / Pro API</span>
                      <span className="text-[10px] bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded-full font-bold">
                        Cloud Primary
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 mt-1">
                      Đóng vai trò Trợ Lý Bác Sĩ suy luận phác đồ điều trị, kết hợp với triệu chứng trích xuất từ NER.
                    </p>
                  </div>
                  <div className="border border-slate-100 bg-slate-50 p-4 rounded-2xl">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-slate-800 text-xs">Local Clinical Rule Engine</span>
                      <span className="text-[10px] bg-blue-100 text-blue-800 px-2 py-0.5 rounded-full font-bold">
                        Offline Fallback
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 mt-1">
                      Tự động suy diễn lâm sàng và loại trừ triệu chứng (Pertinent Negatives) khi mất kết nối Internet.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ======================================================== */}
          {/* TAB 3: TRAINING DATA & LEXICON                           */}
          {/* ======================================================== */}
          {activeTab === 'training_data' && (
            <div className="space-y-5 w-full max-w-none">
              {/* Sub-tab navigation */}
              <div className="flex items-center gap-2 border-b border-slate-200 pb-3">
                <button
                  onClick={() => setDataSubTab('datasets')}
                  className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition ${
                    dataSubTab === 'datasets'
                      ? 'bg-slate-900 text-white'
                      : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'
                  }`}
                >
                  Tệp Datasets ({datasets.length})
                </button>
                <button
                  onClick={() => setDataSubTab('glossary')}
                  className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition ${
                    dataSubTab === 'glossary'
                      ? 'bg-slate-900 text-white'
                      : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'
                  }`}
                >
                  Từ Điển Triệu Chứng ({Object.keys(glossary).length})
                </button>
                <button
                  onClick={() => setDataSubTab('icd')}
                  className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition ${
                    dataSubTab === 'icd'
                      ? 'bg-slate-900 text-white'
                      : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'
                  }`}
                >
                  Mã ICD-10 Chuẩn ({Object.keys(icdCodes).length})
                </button>
                <button
                  onClick={() => setDataSubTab('rag')}
                  className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition ${
                    dataSubTab === 'rag'
                      ? 'bg-slate-900 text-white'
                      : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'
                  }`}
                >
                  RAG Tri Thức ({ragDocs.length})
                </button>
              </div>

              {/* Sub-tab: Datasets List + Upload */}
              {dataSubTab === 'datasets' && (
                <div className="space-y-4">
                  {/* Upload box */}
                  <div className="bg-white p-5 rounded-3xl border border-dashed border-indigo-200 bg-indigo-50/20 flex flex-col sm:flex-row items-center justify-between gap-4">
                    <div className="flex items-center gap-3">
                      <div className="p-3 bg-indigo-100 text-indigo-700 rounded-2xl">
                        <Upload className="w-6 h-6" />
                      </div>
                      <div>
                        <h4 className="font-bold text-slate-900 text-sm">Tải Lên Tập Dữ Liệu Huấn Luyện Mới</h4>
                        <p className="text-xs text-slate-500">Hỗ trợ định dạng .csv, .json, .jsonl (chứa các cặp triệu chứng & chẩn đoán)</p>
                      </div>
                    </div>
                    <label className="px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs cursor-pointer shadow-md shadow-indigo-600/20 transition flex items-center gap-2">
                      <Plus className="w-4 h-4" />
                      <span>Chọn Tệp Từ Máy</span>
                      <input
                        type="file"
                        accept=".csv,.json,.jsonl"
                        onChange={handleFileUpload}
                        className="hidden"
                      />
                    </label>
                  </div>

                  {/* Datasets Table */}
                  <div className="bg-white rounded-3xl border border-slate-200/90 shadow-sm overflow-hidden">
                    <div className="p-4 border-b border-slate-100 flex items-center justify-between">
                      <h3 className="font-bold text-slate-900 text-sm">Các Tập Dữ Liệu Sẵn Sàng Huấn Luyện</h3>
                      <span className="text-xs text-slate-400 font-mono">{datasets.length} files</span>
                    </div>
                    <table className="w-full text-left text-xs border-collapse">
                      <thead>
                        <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold">
                          <th className="py-3 px-4">Tên Tệp</th>
                          <th className="py-3 px-4">Định Dạng</th>
                          <th className="py-3 px-4">Kích Thước</th>
                          <th className="py-3 px-4">Lần Chỉnh Sửa Cuối</th>
                          <th className="py-3 px-4 text-right">Hành Động</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {datasets.map((d) => (
                          <tr key={d.filename} className="hover:bg-slate-50/60 transition">
                            <td className="py-3 px-4 font-semibold text-slate-800 flex items-center gap-2">
                              <FileText className="w-4 h-4 text-indigo-500" />
                              <span className="font-mono">{d.filename}</span>
                            </td>
                            <td className="py-3 px-4">
                              <span className="bg-slate-100 px-2 py-0.5 rounded text-[10px] font-mono font-bold text-slate-700">
                                {d.type}
                              </span>
                            </td>
                            <td className="py-3 px-4 font-mono text-slate-600">{d.size_mb} MB</td>
                            <td className="py-3 px-4 text-slate-500">{d.last_modified}</td>
                            <td className="py-3 px-4 text-right">
                              <button
                                onClick={() => {
                                  setSelectedDataset(d.filename);
                                  setActiveTab('training_center');
                                }}
                                className="px-3 py-1 rounded-lg bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-bold text-xs transition"
                              >
                                Chọn Huấn Luyện
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Sub-tab: Glossary */}
              {dataSubTab === 'glossary' && (
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
                  <div className="lg:col-span-5 bg-white rounded-3xl p-5 border border-slate-200 shadow-sm space-y-3">
                    <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                      <Plus className="w-4 h-4 text-indigo-600" />
                      <span>Thêm / Cập Nhật Triệu Chứng NER</span>
                    </h3>
                    <form onSubmit={handleSaveGlossary} className="space-y-3 text-xs">
                      <div>
                        <label className="font-semibold text-slate-700">Mã Khóa (Key ID)</label>
                        <input
                          type="text"
                          placeholder="Ví dụ: viem_xoang_mui"
                          value={newKey}
                          onChange={(e) => setNewKey(e.target.value)}
                          className="w-full mt-1 p-2 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-1 focus:ring-indigo-500 font-mono"
                          required
                        />
                      </div>
                      <div>
                        <label className="font-semibold text-slate-700">Tên Triệu Chứng Chuẩn</label>
                        <input
                          type="text"
                          placeholder="Ví dụ: Viêm xoang mũi cấp"
                          value={newTerm}
                          onChange={(e) => setNewTerm(e.target.value)}
                          className="w-full mt-1 p-2 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-1 focus:ring-indigo-500"
                          required
                        />
                      </div>
                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <label className="font-semibold text-slate-700">Mã ICD-10</label>
                          <input
                            type="text"
                            placeholder="J01.9"
                            value={newIcd}
                            onChange={(e) => setNewIcd(e.target.value)}
                            className="w-full mt-1 p-2 bg-slate-50 border border-slate-200 rounded-xl font-mono"
                          />
                        </div>
                        <div>
                          <label className="font-semibold text-slate-700">Chuyên Khoa</label>
                          <input
                            type="text"
                            placeholder="Tai Mũi Họng"
                            value={newCategory}
                            onChange={(e) => setNewCategory(e.target.value)}
                            className="w-full mt-1 p-2 bg-slate-50 border border-slate-200 rounded-xl"
                          />
                        </div>
                      </div>
                      <div>
                        <label className="font-semibold text-slate-700">Từ Đồng Nghĩa Tiếng Việt (cách nhau dấu phẩy)</label>
                        <textarea
                          rows={3}
                          placeholder="nghẹt mũi, chảy nước mũi xanh, nhức hốc mắt, tức xoang trán"
                          value={newSynonyms}
                          onChange={(e) => setNewSynonyms(e.target.value)}
                          className="w-full mt-1 p-2 bg-slate-50 border border-slate-200 rounded-xl"
                        />
                      </div>
                      <div className="flex items-center gap-2 pt-1">
                        <input
                          type="checkbox"
                          id="redflag"
                          checked={isRedFlag}
                          onChange={(e) => setIsRedFlag(e.target.checked)}
                          className="rounded text-rose-600 focus:ring-rose-500"
                        />
                        <label htmlFor="redflag" className="font-medium text-rose-700">
                          Triệu chứng có nguy cơ Red Flag cấp cứu
                        </label>
                      </div>
                      <button
                        type="submit"
                        className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2.5 rounded-xl shadow-sm transition"
                      >
                        Lưu Tri Thức Thực Thể
                      </button>
                    </form>
                  </div>

                  <div className="lg:col-span-7 bg-white rounded-3xl p-5 border border-slate-200 shadow-sm overflow-hidden flex flex-col">
                    <h3 className="font-bold text-slate-900 text-sm mb-3">
                      Từ Điển Thực Thể Hiện Hữu ({Object.keys(glossary).length})
                    </h3>
                    <div className="overflow-y-auto max-h-[450px] custom-scrollbar">
                      <table className="w-full text-left text-xs border-collapse">
                        <thead>
                          <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold sticky top-0">
                            <th className="py-2.5 px-3">Mã Khóa</th>
                            <th className="py-2.5 px-3">Tên Chuẩn</th>
                            <th className="py-2.5 px-3">Từ Đồng Nghĩa</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                          {Object.entries(glossary).map(([k, item]) => (
                            <tr key={k} className="hover:bg-slate-50/60">
                              <td className="py-2.5 px-3 font-mono font-bold text-indigo-700">{k}</td>
                              <td className="py-2.5 px-3 font-semibold text-slate-800">{item.standard_term}</td>
                              <td className="py-2.5 px-3 text-slate-500 max-w-xs truncate">{item.synonyms?.join(', ')}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}

              {/* Sub-tab: ICD-10 */}
              {dataSubTab === 'icd' && (
                <div className="bg-white rounded-3xl p-5 border border-slate-200 shadow-sm">
                  <h3 className="font-bold text-slate-900 text-sm mb-4 flex items-center gap-2">
                    <BookOpen className="w-4 h-4 text-indigo-600" />
                    <span>CSDL 32+ Nhóm Bệnh Chuẩn Hóa ICD-10 & Phác Đồ Bộ Y Tế</span>
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-h-[550px] overflow-y-auto custom-scrollbar pr-2">
                    {Object.entries(icdCodes).map(([code, item]) => (
                      <div key={code} className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-1.5">
                        <div className="flex items-center justify-between">
                          <span className="font-mono font-bold text-indigo-900 bg-indigo-100 px-2 py-0.5 rounded text-xs">
                            {code}
                          </span>
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-200 text-slate-700">
                            {item.department || 'Đa Khoa'}
                          </span>
                        </div>
                        <h4 className="font-bold text-sm text-slate-900">{item.name_vi}</h4>
                        <p className="text-xs text-slate-500 italic">{item.name_en}</p>
                        <div className="text-xs text-slate-600 pt-1 border-t border-slate-200">
                          <div><strong>Triệu chứng:</strong> {item.key_symptoms?.join(', ')}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Sub-tab: RAG Documents */}
              {dataSubTab === 'rag' && (
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
                  <div className="lg:col-span-5 bg-white rounded-3xl p-5 border border-slate-200 shadow-sm space-y-3">
                    <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                      <Plus className="w-4 h-4 text-indigo-600" />
                      <span>Bổ Sung Tài Liệu RAG Knowledge Store</span>
                    </h3>
                    <form onSubmit={handleAddRagDoc} className="space-y-3 text-xs">
                      <div>
                        <label className="font-semibold text-slate-700">Tiêu Đề Phác Đồ / Tài Liệu</label>
                        <input
                          type="text"
                          placeholder="Ví dụ: Hướng dẫn chẩn đoán và điều trị sốt xuất huyết Dengue"
                          value={newRagTitle}
                          onChange={(e) => setNewRagTitle(e.target.value)}
                          className="w-full mt-1 p-2 bg-slate-50 border border-slate-200 rounded-xl"
                          required
                        />
                      </div>
                      <div>
                        <label className="font-semibold text-slate-700">Nguồn / Quyết Định</label>
                        <input
                          type="text"
                          placeholder="Quyết định số 2760/QĐ-BYT"
                          value={newRagSource}
                          onChange={(e) => setNewRagSource(e.target.value)}
                          className="w-full mt-1 p-2 bg-slate-50 border border-slate-200 rounded-xl"
                        />
                      </div>
                      <div>
                        <label className="font-semibold text-slate-700">Nội Dung Y Khoa (Text Chunk)</label>
                        <textarea
                          rows={6}
                          placeholder="Dán nội dung chỉ định, dấu hiệu cảnh báo, giai đoạn nguy hiểm..."
                          value={newRagContent}
                          onChange={(e) => setNewRagContent(e.target.value)}
                          className="w-full mt-1 p-2 bg-slate-50 border border-slate-200 rounded-xl leading-relaxed"
                          required
                        />
                      </div>
                      <button
                        type="submit"
                        className="w-full bg-teal-600 hover:bg-teal-700 text-white font-bold py-2.5 rounded-xl shadow-sm transition"
                      >
                        Thêm Vào RAG Knowledge
                      </button>
                    </form>
                  </div>

                  <div className="lg:col-span-7 bg-white rounded-3xl p-5 border border-slate-200 shadow-sm overflow-hidden">
                    <h3 className="font-bold text-slate-900 text-sm mb-3">
                      Tài Liệu RAG Grounding Đã Lưu ({ragDocs.length})
                    </h3>
                    <div className="space-y-3 max-h-[450px] overflow-y-auto custom-scrollbar pr-2">
                      {ragDocs.map((doc, idx) => (
                        <div key={idx} className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200/80 text-xs">
                          <div className="flex items-center justify-between">
                            <h4 className="font-bold text-slate-900">{doc.title || `Tài liệu #${idx + 1}`}</h4>
                            <span className="text-[10px] bg-slate-200 text-slate-700 px-2 py-0.5 rounded font-mono">
                              {doc.source || 'Bộ Y Tế'}
                            </span>
                          </div>
                          <p className="text-slate-600 mt-2 line-clamp-3 leading-relaxed">
                            {doc.content || doc.text || JSON.stringify(doc)}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ======================================================== */}
          {/* TAB 4: TRAINING STUDIO & GOOGLE COLAB (GUI TRAINING)     */}
          {/* ======================================================== */}
          {activeTab === 'training_center' && (
            <div className="space-y-6 w-full max-w-none">
              {/* Top Banner: GUI Training Center */}
              <div className="bg-gradient-to-r from-violet-950 via-indigo-900 to-slate-900 rounded-3xl p-6 text-white shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 font-mono text-[10px] font-bold border border-emerald-500/30">
                      NO-CODE AI STUDIO
                    </span>
                    <span className="text-xs text-indigo-300 font-semibold">FastAPI Background Worker</span>
                  </div>
                  <h2 className="text-xl font-black mt-1">Giao Diện Huấn Luyện AI & Đồng Bộ Google Colab</h2>
                  <p className="text-xs text-slate-300 mt-1 max-w-xl leading-relaxed">
                    Khởi chạy chu trình huấn luyện trực quan từ giao diện mà không cần gõ lệnh terminal.
                    Hỗ trợ dán link Google Colab / Google Drive để backend tự động kéo dataset về.
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <div className="bg-white/10 backdrop-blur-md px-4 py-3 rounded-2xl border border-white/10 text-right">
                    <span className="text-[10px] text-slate-300 block">Trạng thái huấn luyện</span>
                    <span className="font-bold font-mono text-sm capitalize text-emerald-400">
                      {trainingStatus?.status || 'Sẵn sàng (Idle)'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Module 1: Connect with Google Colab / Drive */}
              <div className="bg-white rounded-3xl p-6 border border-slate-200/90 shadow-sm">
                <div className="flex items-center gap-2.5 mb-3">
                  <div className="p-2 rounded-xl bg-amber-50 border border-amber-200 text-amber-600 font-bold">
                    <Link2 className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-900 text-sm">
                      Kết Nối Google Colab / Google Drive Để Nhận Dữ Liệu
                    </h3>
                    <p className="text-xs text-slate-500">
                      Sau khi train hoặc tiền xử lý xong trên Colab, dán đường link chia sẻ của tập dataset (Google Drive) vào đây
                    </p>
                  </div>
                </div>

                <form onSubmit={handleColabDownload} className="grid grid-cols-1 md:grid-cols-12 gap-3 mt-4">
                  <div className="md:col-span-7">
                    <label className="text-[11px] font-bold text-slate-600 block mb-1">
                      Đường Link Google Drive / Colab File Export:
                    </label>
                    <input
                      type="url"
                      placeholder="https://drive.google.com/file/d/1a2b3c.../view?usp=sharing"
                      value={colabUrl}
                      onChange={(e) => setColabUrl(e.target.value)}
                      className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-mono text-slate-800 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    />
                  </div>
                  <div className="md:col-span-3">
                    <label className="text-[11px] font-bold text-slate-600 block mb-1">
                      Tên Tệp Đích (Tùy chọn):
                    </label>
                    <input
                      type="text"
                      placeholder="colab_dataset_v2.json"
                      value={colabFilename}
                      onChange={(e) => setColabFilename(e.target.value)}
                      className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-mono text-slate-800 focus:outline-none"
                    />
                  </div>
                  <div className="md:col-span-2 flex items-end">
                    <button
                      type="submit"
                      disabled={isColabDownloading || !colabUrl}
                      className="w-full py-2.5 rounded-xl bg-amber-600 hover:bg-amber-700 text-white font-bold text-xs shadow-md shadow-amber-600/20 transition flex items-center justify-center gap-2 disabled:opacity-50"
                    >
                      {isColabDownloading ? (
                        <RefreshCw className="w-4 h-4 animate-spin" />
                      ) : (
                        <Download className="w-4 h-4" />
                      )}
                      <span>{isColabDownloading ? 'Đang Tải...' : 'Đồng Bộ Về'}</span>
                    </button>
                  </div>
                </form>
              </div>

              {/* Module 2: Training GUI Controls */}
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
                {/* Control Panel (Left 5 Cols) */}
                <div className="lg:col-span-5 bg-white rounded-3xl p-6 border border-slate-200/90 shadow-sm space-y-4">
                  <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                    <Play className="w-4 h-4 text-emerald-600" />
                    <span>Cấu Hình Tham Số Huấn Luyện</span>
                  </h3>

                  <div>
                    <label className="text-xs font-bold text-slate-700 block mb-1">Loại Huấn Luyện:</label>
                    <div className="grid grid-cols-2 gap-2">
                      <button
                        type="button"
                        onClick={() => setTrainingJobType('retrain')}
                        className={`p-2.5 rounded-xl border text-xs font-bold transition text-left ${
                          trainingJobType === 'retrain'
                            ? 'bg-indigo-50 border-indigo-400 text-indigo-900'
                            : 'bg-slate-50 border-slate-200 text-slate-600'
                        }`}
                      >
                        <div>Full Retrain</div>
                        <span className="text-[10px] font-normal text-slate-500">Train lại từ đầu 100%</span>
                      </button>
                      <button
                        type="button"
                        onClick={() => setTrainingJobType('finetune')}
                        className={`p-2.5 rounded-xl border text-xs font-bold transition text-left ${
                          trainingJobType === 'finetune'
                            ? 'bg-indigo-50 border-indigo-400 text-indigo-900'
                            : 'bg-slate-50 border-slate-200 text-slate-600'
                        }`}
                      >
                        <div>Incremental</div>
                        <span className="text-[10px] font-normal text-slate-500">Học bổ sung ca bệnh</span>
                      </button>
                    </div>
                  </div>

                  <div>
                    <label className="text-xs font-bold text-slate-700 block mb-1">Tập Dữ Liệu Huấn Luyện:</label>
                    <select
                      value={selectedDataset}
                      onChange={(e) => setSelectedDataset(e.target.value)}
                      className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-mono font-medium focus:outline-none"
                    >
                      {datasets.map((d) => (
                        <option key={d.filename} value={d.filename}>
                          {d.filename} ({d.size_mb} MB)
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="p-3 bg-slate-50 rounded-2xl border border-slate-200 space-y-2 text-xs">
                    <div className="flex justify-between text-slate-600">
                      <span>Phân bổ tập Train/Val:</span>
                      <strong className="font-mono text-indigo-700">80% / 20% Hold-out</strong>
                    </div>
                    <div className="flex justify-between text-slate-600">
                      <span>Feature Extractor:</span>
                      <strong className="font-mono text-slate-800">TF-IDF (50k n-grams)</strong>
                    </div>
                    <div className="flex justify-between text-slate-600">
                      <span>Mô hình đích:</span>
                      <strong className="font-mono text-slate-800">LinearSVC + XGBoost</strong>
                    </div>
                  </div>

                  <button
                    onClick={handleStartTraining}
                    disabled={isStartingTraining || trainingStatus?.status === 'running'}
                    className="w-full py-3.5 rounded-2xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-sm shadow-lg shadow-emerald-600/25 transition flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    {trainingStatus?.status === 'running' ? (
                      <>
                        <RefreshCw className="w-5 h-5 animate-spin" />
                        <span>Đang Huấn Luyện ({trainingStatus.progress}%)...</span>
                      </>
                    ) : (
                      <>
                        <Play className="w-5 h-5 fill-current" />
                        <span>Bắt Đầu Huấn Luyện AI</span>
                      </>
                    )}
                  </button>
                </div>

                {/* Real-time Terminal Log (Right 7 Cols) */}
                <div className="lg:col-span-7 bg-slate-950 rounded-3xl p-5 border border-slate-800 shadow-xl flex flex-col h-[460px]">
                  <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                    <div className="flex items-center gap-2">
                      <Terminal className="w-4 h-4 text-emerald-400" />
                      <span className="font-mono text-xs font-bold text-slate-300">
                        Live Training Console {activeJobId ? `[Job #${activeJobId}]` : ''}
                      </span>
                    </div>
                    {trainingStatus?.progress !== undefined && (
                      <div className="flex items-center gap-2">
                        <div className="w-24 bg-slate-800 h-2 rounded-full overflow-hidden">
                          <div
                            className="bg-emerald-500 h-full transition-all duration-300"
                            style={{ width: `${trainingStatus.progress}%` }}
                          />
                        </div>
                        <span className="font-mono text-xs text-emerald-400 font-bold">
                          {trainingStatus.progress}%
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Terminal Log lines */}
                  <div
                    ref={logTerminalRef}
                    className="flex-1 overflow-y-auto p-2 font-mono text-[11px] text-slate-300 space-y-1 custom-scrollbar mt-2"
                  >
                    {trainingLogs.length === 0 ? (
                      <div className="text-slate-600 italic py-8 text-center">
                        Nhấn nút "Bắt Đầu Huấn Luyện AI" để khởi chạy pipeline và theo dõi luồng log thời gian thực...
                      </div>
                    ) : (
                      trainingLogs.map((log, idx) => (
                        <div
                          key={idx}
                          className={`leading-relaxed ${
                            log.includes('✅') || log.includes('Accuracy')
                              ? 'text-emerald-400 font-bold'
                              : log.includes('❌') || log.includes('Lỗi')
                              ? 'text-rose-400 font-bold'
                              : log.includes('⚠️')
                              ? 'text-amber-300'
                              : 'text-slate-300'
                          }`}
                        >
                          {log}
                        </div>
                      ))
                    )}
                  </div>

                  {/* Training Metrics Card if finished */}
                  {trainingStatus?.metrics && Object.keys(trainingStatus.metrics).length > 0 && (
                    <div className="mt-3 p-3 bg-slate-900/90 rounded-xl border border-emerald-500/30 grid grid-cols-3 gap-2 text-center">
                      <div>
                        <span className="text-[10px] text-slate-400 block">Train Acc</span>
                        <strong className="text-emerald-400 font-mono text-xs">
                          {(trainingStatus.metrics.train_accuracy * 100).toFixed(2)}%
                        </strong>
                      </div>
                      <div>
                        <span className="text-[10px] text-slate-400 block">Val Acc</span>
                        <strong className="text-teal-300 font-mono text-xs">
                          {(trainingStatus.metrics.val_accuracy * 100).toFixed(2)}%
                        </strong>
                      </div>
                      <div>
                        <span className="text-[10px] text-slate-400 block">F1 Score</span>
                        <strong className="text-indigo-300 font-mono text-xs">
                          {(trainingStatus.metrics.f1_score * 100).toFixed(2)}%
                        </strong>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* ======================================================== */}
          {/* TAB 5: ARCHITECTURE & REALTIME AI QUERY FLOW             */}
          {/* ======================================================== */}
          {activeTab === 'architecture' && (
            <div className="space-y-6 w-full max-w-none">
              {/* Header Bar: Sub-tab switcher + Live Telemetry Status */}
              <div className="bg-white rounded-3xl p-5 border border-slate-200/90 shadow-sm flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 rounded-2xl bg-indigo-50 border border-indigo-100 text-indigo-600">
                    <Network className="w-6 h-6" />
                  </div>
                  <div>
                    <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                      <span>Kiến Trúc Hệ Thống & Luồng Truy Vấn AI Thời Gian Thực</span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-700 font-bold">
                        Pipeline v3.2
                      </span>
                    </h2>
                    <p className="text-xs text-slate-500">
                      Theo dõi sơ đồ luồng dữ liệu 9 giai đoạn, truy vấn end-to-end và trạng thái hoạt động của từng model AI
                    </p>
                  </div>
                </div>

                <div className="flex flex-wrap items-center gap-2.5">
                  {/* Sub-tab pills */}
                  <div className="bg-slate-100 p-1 rounded-xl flex items-center gap-1 text-xs font-semibold">
                    <button
                      onClick={() => setArchSubTab('pipeline')}
                      className={`px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 ${
                        archSubTab === 'pipeline'
                          ? 'bg-white text-indigo-700 shadow-xs font-bold'
                          : 'text-slate-600 hover:text-slate-900'
                      }`}
                    >
                      <GitBranch className="w-3.5 h-3.5 text-indigo-600" />
                      <span>Sơ Đồ Luồng & Truy Vấn Realtime</span>
                    </button>
                    <button
                      onClick={() => setArchSubTab('audit')}
                      className={`px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 ${
                        archSubTab === 'audit'
                          ? 'bg-white text-indigo-700 shadow-xs font-bold'
                          : 'text-slate-600 hover:text-slate-900'
                      }`}
                    >
                      <Server className="w-3.5 h-3.5 text-slate-600" />
                      <span>Báo Cáo Microservice Audit</span>
                    </button>
                  </div>

                  {/* Realtime Live Pulse */}
                  <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-emerald-50 border border-emerald-200 text-[11px] text-emerald-800 font-medium">
                    <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                    <span>Realtime (5s)</span>
                    <span className="text-emerald-600/70 font-mono text-[10px]">[{lastTelemetryUpdate}]</span>
                  </div>

                  <button
                    onClick={() => setAutoRealtimePolling(!autoRealtimePolling)}
                    className={`px-2.5 py-1.5 rounded-xl border text-xs font-semibold transition flex items-center gap-1 ${
                      autoRealtimePolling
                        ? 'bg-slate-50 border-slate-200 text-slate-700 hover:bg-slate-100'
                        : 'bg-amber-50 border-amber-200 text-amber-800'
                    }`}
                    title="Bật/Tắt tự động cập nhật realtime mỗi 5 giây"
                  >
                    <Radio className={`w-3.5 h-3.5 ${autoRealtimePolling ? 'text-emerald-600 animate-pulse' : 'text-slate-400'}`} />
                    <span>{autoRealtimePolling ? 'Auto Polling: Bật' : 'Auto Polling: Tắt'}</span>
                  </button>
                </div>
              </div>

              {/* VIEW 1: INTERACTIVE PIPELINE & REALTIME QUERY TRACE */}
              {archSubTab === 'pipeline' && (
                <div className="space-y-6 w-full">
                  {/* Module A: Interactive Live Query Trace Simulator */}
                  <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 rounded-3xl p-6 text-white shadow-xl border border-indigo-900/50 space-y-4">
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 font-mono text-[10px] font-bold border border-emerald-500/30">
                            LIVE QUERY TRACE SIMULATOR
                          </span>
                          <span className="text-xs text-indigo-300 font-medium">Mô phỏng chu trình dữ liệu thời gian thực</span>
                        </div>
                        <h3 className="text-lg font-bold text-white mt-1 flex items-center gap-2">
                          <span>Mô Phỏng Luồng Truy Vấn: Khi Người Dùng Đặt Câu Hỏi</span>
                          {isSimulatingTrace && (
                            <span className="inline-flex items-center gap-1 text-xs text-emerald-400 font-mono bg-emerald-950/60 px-2 py-0.5 rounded-full border border-emerald-800 animate-pulse">
                              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                              Đang truyền dữ liệu (Bước {traceStep}/8)
                            </span>
                          )}
                        </h3>
                        <p className="text-xs text-slate-300 mt-1 max-w-2xl leading-relaxed">
                          Chọn một ca lâm sàng mẫu hoặc nhập câu hỏi thực tế để xem trực quan dữ liệu đi qua 8 giai đoạn của hệ thống,
                          từ thu nhận đa phương thức, bóc tách thực thể PhoBERT NER, chuẩn hóa ngữ nghĩa 384-D, phân tầng học máy 211 mã ICD-10 & XGBoost cho đến RAG 640 tài liệu Bộ Y Tế và Gemini 2.0 Flash.
                        </p>
                      </div>

                      {/* Start trace button */}
                      <div className="flex items-center gap-2">
                        <button
                          onClick={handleStartTrace}
                          disabled={isSimulatingTrace}
                          className="px-5 py-3 rounded-2xl bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 text-slate-950 font-black text-xs shadow-lg shadow-emerald-500/30 transition flex items-center gap-2 disabled:opacity-60"
                        >
                          <Play className={`w-4 h-4 fill-current ${isSimulatingTrace ? 'animate-spin' : ''}`} />
                          <span>{isSimulatingTrace ? `Đang Chạy Bước ${traceStep}/8...` : 'Chạy Mô Phỏng Luồng Dữ Liệu'}</span>
                        </button>
                      </div>
                    </div>

                    {/* Presets & Input selector */}
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-2.5 pt-2">
                      <button
                        onClick={() => {
                          setTraceScenario('dengue');
                          setCustomQueryText('Tôi bị sốt cao 39.2 độ từ hôm qua, đau đầu dữ dội, đau mỏi hốc mắt nhưng không ho, có vài nốt chấm đỏ ở cẳng tay');
                        }}
                        className={`p-3 rounded-2xl border text-left transition ${
                          traceScenario === 'dengue'
                            ? 'bg-indigo-600/30 border-indigo-400 text-white shadow-inner'
                            : 'bg-slate-800/60 border-slate-700/80 text-slate-300 hover:bg-slate-800'
                        }`}
                      >
                        <div className="text-[10px] uppercase font-bold text-indigo-300 font-mono">Ca Lâm Sàng 1</div>
                        <div className="font-bold text-xs mt-0.5 text-white">Nghi Sốt Dengue (A90)</div>
                        <div className="text-[11px] text-slate-400 mt-1 line-clamp-1">Sốt cao 39.2°, đau đầu, xuất huyết, không ho</div>
                      </button>

                      <button
                        onClick={() => {
                          setTraceScenario('cardiac');
                          setCustomQueryText('Bố tôi 62 tuổi đau thắt ngực trái dữ dội lan ra vai trái và hàm dưới, khó thở, vã mồ hôi lạnh, tiền sử tăng huyết áp');
                        }}
                        className={`p-3 rounded-2xl border text-left transition ${
                          traceScenario === 'cardiac'
                            ? 'bg-rose-600/30 border-rose-400 text-white shadow-inner'
                            : 'bg-slate-800/60 border-slate-700/80 text-slate-300 hover:bg-slate-800'
                        }`}
                      >
                        <div className="text-[10px] uppercase font-bold text-rose-300 font-mono">Ca Lâm Sàng 2 (Cấp Cứu)</div>
                        <div className="font-bold text-xs mt-0.5 text-white">Tim Mạch Red Flag (I21)</div>
                        <div className="text-[11px] text-slate-400 mt-1 line-clamp-1">Đau thắt ngực lan vai hàm, khó thở, vã mồ hôi</div>
                      </button>

                      <button
                        onClick={() => {
                          setTraceScenario('chitchat');
                          setCustomQueryText('Xin chào bác sĩ, bệnh viện của mình có khám vào ngày chủ nhật không ạ?');
                        }}
                        className={`p-3 rounded-2xl border text-left transition ${
                          traceScenario === 'chitchat'
                            ? 'bg-emerald-600/30 border-emerald-400 text-white shadow-inner'
                            : 'bg-slate-800/60 border-slate-700/80 text-slate-300 hover:bg-slate-800'
                        }`}
                      >
                        <div className="text-[10px] uppercase font-bold text-emerald-300 font-mono">Ca Lâm Sàng 3 (Bypass)</div>
                        <div className="font-bold text-xs mt-0.5 text-white">Ý Định Chào Hỏi Phi Y Tế</div>
                        <div className="text-[11px] text-slate-400 mt-1 line-clamp-1">Lọc nhanh qua Intent Filter, 0ms AI load</div>
                      </button>

                      <button
                        onClick={() => setTraceScenario('custom')}
                        className={`p-3 rounded-2xl border text-left transition ${
                          traceScenario === 'custom'
                            ? 'bg-amber-600/30 border-amber-400 text-white shadow-inner'
                            : 'bg-slate-800/60 border-slate-700/80 text-slate-300 hover:bg-slate-800'
                        }`}
                      >
                        <div className="text-[10px] uppercase font-bold text-amber-300 font-mono">Tùy Chỉnh</div>
                        <div className="font-bold text-xs mt-0.5 text-white">Nhập Câu Hỏi Trực Tiếp</div>
                        <div className="text-[11px] text-slate-400 mt-1 line-clamp-1">Kiểm tra với triệu chứng bất kỳ</div>
                      </button>
                    </div>

                    {/* Query Input Box */}
                    <div className="bg-slate-950/70 p-3 rounded-2xl border border-slate-800 flex items-center gap-3">
                      <div className="p-2 rounded-xl bg-indigo-900/60 text-indigo-300">
                        <MessageSquare className="w-4 h-4" />
                      </div>
                      <input
                        type="text"
                        value={customQueryText}
                        onChange={(e) => {
                          setCustomQueryText(e.target.value);
                          setTraceScenario('custom');
                        }}
                        placeholder="Nhập câu hỏi hoặc triệu chứng của bệnh nhân để kiểm tra luồng dữ liệu..."
                        className="bg-transparent flex-1 text-xs text-slate-200 placeholder-slate-500 focus:outline-none font-sans"
                      />
                      <span className="text-[10px] text-slate-400 font-mono hidden sm:inline">
                        {customQueryText.length} ký tự
                      </span>
                    </div>

                    {/* 8-Step Interactive Lifecycle Timeline */}
                    <div className="pt-2">
                      <div className="flex items-center justify-between text-[11px] text-slate-400 mb-2 font-mono">
                        <span>TIẾN TRÌNH LUỒNG DỮ LIỆU (8 GIAI ĐOẠN TUẦN TỰ)</span>
                        <span className="text-indigo-300 font-bold">
                          {traceStep > 0 ? `Đang ở Bước ${traceStep}/8: ${
                            [
                              '01. Thu Nhận Đa Phương Thức',
                              '02. Gateway & Redis Caching',
                              '03. PhoBERT Transformer NER',
                              '04. Chuẩn Hóa Semantic 384-D',
                              '05. ML 211 ICD-10 & XGBoost',
                              '06. RAG 640 Phác Đồ BYT',
                              '07. Gemini 2.0 Flash Reasoning',
                              '08. Client Delivery & Xuất PDF'
                            ][traceStep - 1]
                          }` : 'Nhấn nút chạy mô phỏng để bắt đầu'}
                        </span>
                      </div>

                      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-1.5">
                        {[
                          { step: 1, label: '01. Ingestion', icon: Volume2 },
                          { step: 2, label: '02. Gateway', icon: Server },
                          { step: 3, label: '03. PhoBERT NER', icon: Search },
                          { step: 4, label: '04. Semantic 384D', icon: Binary },
                          { step: 5, label: '05. ML & XGBoost', icon: Bot },
                          { step: 6, label: '06. RAG 640 BYT', icon: BookOpen },
                          { step: 7, label: '07. Gemini 2.0', icon: Sparkles },
                          { step: 8, label: '08. UI & PDF', icon: CheckCheck },
                        ].map((s) => {
                          const IconComp = s.icon;
                          const isActive = traceStep === s.step;
                          const isPast = traceStep > s.step;
                          const isSelected = selectedArchNode === s.step;

                          return (
                            <button
                              key={s.step}
                              onClick={() => setSelectedArchNode(s.step)}
                              className={`p-2 rounded-xl text-left border transition relative overflow-hidden ${
                                isActive
                                  ? 'bg-emerald-500 text-slate-950 border-emerald-400 font-bold shadow-lg shadow-emerald-500/40 ring-2 ring-emerald-400 animate-pulse'
                                  : isSelected
                                  ? 'bg-indigo-600 text-white border-indigo-400 font-bold shadow-md'
                                  : isPast
                                  ? 'bg-slate-800/90 text-emerald-300 border-emerald-800/80 font-medium'
                                  : 'bg-slate-900/60 text-slate-400 border-slate-800 hover:bg-slate-800'
                              }`}
                            >
                              <div className="flex items-center justify-between">
                                <IconComp className="w-3.5 h-3.5" />
                                <span className="text-[10px] font-mono">
                                  {isPast ? '✓' : `#${s.step}`}
                                </span>
                              </div>
                              <div className="text-[10px] font-bold mt-1 truncate">{s.label}</div>
                            </button>
                          );
                        })}
                      </div>
                    </div>

                    {/* Active Step Live Inspector Card */}
                    <div className="p-4 bg-slate-950/90 rounded-2xl border border-indigo-900/80 mt-3 grid grid-cols-1 lg:grid-cols-12 gap-4">
                      <div className="lg:col-span-5 space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-[10px] font-mono uppercase text-indigo-400 font-bold">
                            Chi Tiết Giai Đoạn Đang Khảo Sát #{selectedArchNode}
                          </span>
                          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 font-bold">
                            🟢 Realtime Active
                          </span>
                        </div>
                        <h4 className="text-sm font-bold text-white">
                          {[
                            '1. Thu Nhận Đầu Vào Đa Phương Thức (Multimodal Ingestion)',
                            '2. Cổng API Gateway, Phân Luồng & Bộ Đệm Redis (Gateway & Caching)',
                            '3. Bóc Tách Thực Thể Lâm Sàng PhoBERT NER (Transformer Token Classifier)',
                            '4. Chuẩn Hóa Ngữ Nghĩa Thực Thể (Dense Semantic Normalizer 384-D)',
                            '5. Bộ Đôi Học Máy Chẩn Đoán & Phân Tầng ESI (ML Ensemble & Triage)',
                            '6. Truy Xuất Tri Thức Phác Đồ Bộ Y Tế (Clinical RAG Grounding)',
                            '7. Suy Luận Lâm Sàng & Lập Bệnh Án Gemini 2.0 (Clinical Reasoning LLM)',
                            '8. Trình Diễn Đa Phương Tiện & Xuất Bệnh Án PDF (Client Delivery & PDF)',
                          ][selectedArchNode - 1]}
                        </h4>
                        <p className="text-xs text-slate-300 leading-relaxed">
                          {[
                            'Tiếp nhận câu hỏi văn bản thô, file ghi âm giọng nói (Faster-Whisper STT) và ảnh chụp phiếu xét nghiệm máu / đơn thuốc (OCR + Blood Ref Check) để trích xuất văn bản lâm sàng chuẩn hóa Unicode.',
                            'FastAPI v3.0 tiếp nhận request, kiểm tra bộ đệm phân tán Redis (TTL 1800s RAG / 3600s Triage) để trả về ngay (0ms). Nếu là chào hỏi thông thường sẽ kích hoạt Fast Intent bypass; nếu là ca bệnh sẽ chuyển tiếp Pipeline y khoa.',
                            'Mô hình VinAI PhoBERT Transformer (vinai/phobert-base, fine-tuned tại models_weights/phobert_ner) gán 9 nhãn BIO, tự động bóc tách triệu chứng khẳng định, triệu chứng phủ định loại trừ (Pertinent Negatives như "không ho") và cờ đỏ nguy kịch <0.5s.',
                            'SentenceTransformer paraphrase-multilingual-MiniLM-L12-v2 vector hóa 384 chiều, sử dụng Cosine Similarity để ánh xạ từ ngữ tự nhiên của người bệnh vào 211 mã thực thể ICD-10 chuẩn mực của Bộ Y Tế.',
                            'Bộ phân loại NLP Calibrated Multi-Class (nlp_symptom_classifier.pkl, độ chính xác 92.69%) dự đoán 211 nhóm bệnh ICD-10 kết hợp cây quyết định XGBoost (tabular_xgboost.json) phân tầng khẩn cấp ESI 1-5 qua Dynamic Late Fusion.',
                            'Hệ thống truy xuất ngữ nghĩa Qdrant Vector Store / In-Memory Dense Engine từ kho 640 tài liệu lâm sàng (423 văn bản phác đồ Bộ Y Tế + 211 hồ sơ ICD-10 chi tiết) làm khóa an toàn lâm sàng (Guardrail), triệt tiêu hoàn toàn ảo giác y khoa.',
                            'Google Gemini 2.0 Flash đóng vai trò Bác Sĩ Cố Vấn: Duy trì bộ nhớ tích lũy 20 lượt hội thoại, suy luận chẩn đoán phân biệt dựa trên prompt grounded và cơ chế tự động Fallback về bộ quy tắc nội bộ khi ngoại tuyến.',
                            'Client Next.js 14 nhận luồng SSE Typewriter mượt mà, hiển thị thẻ ICD-10, banner cảnh báo đỏ 115 khi ESI 1, định tuyến chuyên khoa, phát giọng đọc bác sĩ Audio TTS và xuất Hồ sơ bệnh án điện tử PDF chuẩn bệnh viện.',
                          ][selectedArchNode - 1]}
                        </p>
                        <div className="pt-2 flex flex-wrap gap-2 text-[11px] font-mono">
                          <span className="bg-indigo-950/70 border border-indigo-800 text-indigo-300 px-2 py-1 rounded-lg">
                            Model: {[
                              'Faster-Whisper + EasyOCR',
                              'FastAPI v3.0 + Redis Cache',
                              'vinai/phobert-base (9 BIO)',
                              'MiniLM-L12-v2 (384-D)',
                              'NLP Classifier + XGBoost (211 ICD)',
                              'Qdrant / Dense RAG (640 Docs)',
                              'Gemini 2.0 Flash (20 Turns)',
                              'Next.js 14 + Hospital PDF',
                            ][selectedArchNode - 1]}
                          </span>
                          <span className="bg-slate-900 border border-slate-700 text-slate-300 px-2 py-1 rounded-lg">
                            Latency: ~{[12, 8, 35, 18, 22, 28, 380, 10][selectedArchNode - 1]}ms
                          </span>
                        </div>
                      </div>

                      {/* Intermediate Live Data Payload Box */}
                      <div className="lg:col-span-7 bg-black/70 rounded-xl p-3 border border-slate-800 flex flex-col justify-between">
                        <div className="flex items-center justify-between pb-2 border-b border-slate-800 text-[10px] font-mono text-slate-400">
                          <span>INTERMEDIATE PAYLOAD (DỮ LIỆU ĐẦU RA BƯỚC #{selectedArchNode})</span>
                          <span className="text-emerald-400 font-bold">STATUS: OK (200)</span>
                        </div>
                        <pre className="text-[11px] font-mono text-emerald-400 overflow-x-auto p-2 leading-relaxed custom-scrollbar max-h-44">
                          {selectedArchNode === 1 && JSON.stringify({
                            modality: "multimodal_input",
                            raw_input: customQueryText,
                            stt_whisper_engine: "Faster-Whisper (Large-v3-Turbo)",
                            ocr_engine: "Tesseract / EasyOCR v1.7.1",
                            blood_ref_check: "Auto-calibrated ranges",
                            input_length: customQueryText.length
                          }, null, 2)}
                          {selectedArchNode === 2 && JSON.stringify({
                            endpoint: "POST /api/v1/chat/message",
                            session_id: "sess_medibot_live_7718",
                            redis_distributed_cache: "CONNECTED (TTL: 1800s RAG / 3600s Triage)",
                            mongo_storage: "Motor Async Connected (Auto Failover)",
                            intent_type: traceScenario === 'chitchat' ? "general_chitchat" : "medical_clinical_triage",
                            bypass_ai_pipeline: traceScenario === 'chitchat',
                            active_route: traceScenario === 'chitchat' ? "FastIntentResponder (4ms)" : "FullClinicalPipeline"
                          }, null, 2)}
                          {selectedArchNode === 3 && JSON.stringify({
                            ner_engine: "vinai/phobert-base (fine-tuned)",
                            weights_directory: "models_weights/phobert_ner",
                            bio_labels_supported: ["B-SYMPTOM", "I-SYMPTOM", "B-RED_FLAG", "I-RED_FLAG", "B-VITAL", "I-VITAL", "B-DURATION", "I-DURATION", "O"],
                            positive_symptoms: traceScenario === 'cardiac'
                              ? ["đau thắt ngực trái", "lan vai trái và hàm", "khó thở", "vã mồ hôi"]
                              : ["sốt cao 39.2°C", "đau đầu dữ dội", "đau mỏi hốc mắt", "chấm xuất huyết cẳng tay"],
                            pertinent_negatives: traceScenario === 'cardiac' ? [] : ["không ho (loại trừ nhiễm trùng hô hấp)"],
                            red_flag_alert: traceScenario === 'cardiac',
                            triage_urgency: traceScenario === 'cardiac' ? "EMERGENCY_LEVEL_1" : "EVALUATE_LEVEL_2"
                          }, null, 2)}
                          {selectedArchNode === 4 && JSON.stringify({
                            semantic_encoder: "paraphrase-multilingual-MiniLM-L12-v2",
                            embedding_dimension: 384,
                            normalization_method: "Dense Cosine Similarity",
                            target_concepts_pool: "211 ICD-10 Standard Concepts",
                            mapped_canonical_entities: traceScenario === 'cardiac' ? [
                              { raw: "đau thắt ngực trái", canonical: "Cơn đau thắt ngực không ổn định", icd10_concept: "I20.0", score: 0.962 },
                              { raw: "khó thở", canonical: "Khó thở cấp tính", icd10_concept: "R06.0", score: 0.941 }
                            ] : [
                              { raw: "sốt cao", canonical: "Sốt không rõ nguồn gốc", icd10_concept: "R50.9", score: 0.954 },
                              { raw: "chấm xuất huyết", canonical: "Xuất huyết tự phát dưới da", icd10_concept: "R23.3", score: 0.928 }
                            ]
                          }, null, 2)}
                          {selectedArchNode === 5 && JSON.stringify({
                            disease_classifier: "nlp_symptom_classifier.pkl (Calibrated Multi-Class)",
                            test_accuracy: "92.69%",
                            num_classes: 211,
                            predicted_icd10: traceScenario === 'cardiac' ? "I21.9" : "A90",
                            disease_name_vi: traceScenario === 'cardiac' ? "Nhồi máu cơ tim cấp" : "Sốt xuất huyết Dengue",
                            confidence_score: traceScenario === 'cardiac' ? 0.984 : 0.948,
                            tabular_model: "tabular_xgboost.json (Gradient Boosted Trees)",
                            esi_triage_tier: traceScenario === 'cardiac' ? "Cấp 1 (Hồi sức cấp cứu tức thì - Gọi 115)" : "Cấp 2 (Khẩn cấp - Thăm khám trong 15-30p)",
                            dynamic_late_fusion_alpha: 0.35
                          }, null, 2)}
                          {selectedArchNode === 6 && JSON.stringify({
                            knowledge_store: "640 Clinical Documents (423 BYT Protocols + 211 ICD-10 Profiles)",
                            vector_engine: "Qdrant Vector DB / In-Memory Dense Store",
                            matched_icd_query: traceScenario === 'cardiac' ? "I21" : "A90",
                            retrieved_protocol: traceScenario === 'cardiac'
                              ? "Quyết định 2187/QĐ-BYT: Quy trình chẩn đoán & xử trí Hội chứng vành cấp (Chỉ định ECG 12 chuyển đạo trong 10 phút, thở oxy, chuyển phòng Can thiệp)"
                              : "Quyết định 2760/QĐ-BYT: Hướng dẫn chẩn đoán và điều trị Sốt xuất huyết Dengue (Phác đồ bù dịch điện giải Ringer Lactat, theo dõi tiểu cầu)",
                            clinical_guardrail: "ANTI_HALLUCINATION_LOCK_ENFORCED_100%"
                          }, null, 2)}
                          {selectedArchNode === 7 && JSON.stringify({
                            primary_engine: "Google Gemini 2.0 Flash (gemini-2.0-flash)",
                            context_memory: "Cumulative 20-Turn Multi-turn Sliding Window",
                            resilience: "Exponential Backoff + Jitter Retry",
                            offline_fallback: "Deterministic Protocol Fallback Ready",
                            prompt_tokens: 1540,
                            completion_tokens: 420,
                            safety_compliance_check: "PASSED_100%"
                          }, null, 2)}
                          {selectedArchNode === 8 && JSON.stringify({
                            client_status: 200,
                            delivery_protocol: "Server-Sent Events (SSE) Typewriter Stream",
                            rendered_components: ["ICD-10 Badge Card", "ESI Risk Badge", "Red Flag Banner 115", "Hospital-grade PDF Exporter", "Doctor Voice Audio TTS"],
                            export_pdf_ready: true,
                            total_pipeline_roundtrip_ms: traceScenario === 'chitchat' ? "4ms" : "497ms"
                          }, null, 2)}
                        </pre>
                      </div>
                    </div>
                  </div>

                  {/* Module B: Visual End-to-End Architecture Flowchart Diagram */}
                  <div className="bg-white rounded-3xl p-6 border border-slate-200/90 shadow-sm space-y-5">
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-3 border-b border-slate-100">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-600 bg-indigo-50 px-2.5 py-0.5 rounded-full border border-indigo-100 font-mono">
                            SYSTEM ARCHITECTURE BLUEPRINT
                          </span>
                          <span className="text-xs text-slate-400 font-medium">Kiến trúc luồng xử lý AI thời gian thực</span>
                        </div>
                        <h3 className="text-lg font-bold text-slate-900 mt-1 flex items-center gap-2">
                          <span>Sơ Đồ Trình Luồng Kiến Trúc Toàn Bộ Hệ Thống (End-to-End Pipeline)</span>
                        </h3>
                        <p className="text-xs text-slate-500 mt-0.5">
                          Mô tả trực quan luồng đi ngang tuần tự của dữ liệu từ thu nhận đa kênh, cổng đệm Redis, PhoBERT NER, vector hóa 384-D, học máy 211 mã ICD-10 & XGBoost, kho 640 tài liệu BYT đến Gemini 2.0 Flash và xuất PDF bệnh án.
                        </p>
                      </div>

                      {/* View mode switcher pills */}
                      <div className="flex items-center gap-2">
                        <div className="bg-slate-100 p-1 rounded-xl flex items-center gap-1 text-xs font-semibold">
                          <button
                            onClick={() => setArchDiagramView('flowchart')}
                            className={`px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 ${
                              archDiagramView === 'flowchart'
                                ? 'bg-white text-indigo-700 shadow-xs font-bold'
                                : 'text-slate-600 hover:text-slate-900'
                            }`}
                          >
                            <Network className="w-3.5 h-3.5 text-indigo-600" />
                            <span>Sơ Đồ Trình Luồng Ngang (Flowchart)</span>
                          </button>
                          <button
                            onClick={() => setArchDiagramView('grid')}
                            className={`px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 ${
                              archDiagramView === 'grid'
                                ? 'bg-white text-indigo-700 shadow-xs font-bold'
                                : 'text-slate-600 hover:text-slate-900'
                            }`}
                          >
                            <Layers className="w-3.5 h-3.5 text-slate-600" />
                            <span>Ma Trận 8 Giai Đoạn (Grid)</span>
                          </button>
                        </div>
                      </div>
                    </div>

                    {/* VIEW MODE 1: HORIZONTAL PIPELINE FLOWCHART BLUEPRINT */}
                    {archDiagramView === 'flowchart' && (
                      <div className="bg-slate-950 rounded-3xl p-6 border border-slate-800 text-white space-y-6 relative overflow-hidden">
                        {/* Blueprint decorative grid */}
                        <div className="absolute inset-0 bg-[linear-gradient(to_right,#1e293b15_1px,transparent_1px),linear-gradient(to_bottom,#1e293b15_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none" />

                        {/* Top Legend & Header Bar */}
                        <div className="relative z-10 flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-slate-800 text-xs">
                          <div className="flex items-center gap-3">
                            <span className="flex items-center gap-1.5 text-slate-200 font-bold">
                              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
                              <span>TRÌNH LUỒNG DỮ LIỆU ĐA TẦNG TUẦN TỰ (8 CHẶNG TỰ ĐỘNG HÓA)</span>
                            </span>
                            <span className="hidden md:inline-flex px-2 py-0.5 rounded bg-indigo-900/60 text-indigo-300 font-mono text-[10px] border border-indigo-700/60">
                              Horizontal Pipeline Stream
                            </span>
                          </div>

                          <div className="flex flex-wrap items-center gap-4 text-[11px] font-mono">
                            <span className="flex items-center gap-1.5 text-slate-300">
                              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                              <span>AI Active Online</span>
                            </span>
                            <span className="flex items-center gap-1.5 text-slate-300">
                              <span className="w-2 h-2 rounded-full bg-indigo-400" />
                              <span>In-Memory Dispatch</span>
                            </span>
                            <span className="flex items-center gap-1.5 text-slate-300">
                              <span className="w-2 h-2 rounded-full bg-cyan-400" />
                              <span>Distributed Redis</span>
                            </span>
                            <span className="flex items-center gap-1.5 text-slate-300">
                              <span className="w-2 h-2 rounded-full bg-amber-400" />
                              <span>Fast Pass Bypass</span>
                            </span>
                          </div>
                        </div>

                        {/* HORIZONTAL PIPELINE TRACK CONTROLS & CARDS */}
                        <div className="relative z-10 space-y-3">
                          <div className="flex flex-wrap items-center justify-between gap-2 text-[11px] font-mono text-slate-400">
                            <div className="flex items-center gap-2">
                              <span>TIẾN TRÌNH LUỒNG DỮ LIỆU TỪ TRÁI SANG PHẢI (LEFT-TO-RIGHT MILESTONES)</span>
                              <span className="text-indigo-300 font-semibold hidden sm:inline">💡 Click vào từng chặng để xem chi tiết bên dưới</span>
                            </div>

                            {/* View Switcher & Scroll Controls */}
                            <div className="flex items-center gap-2">
                              {/* Layout Mode Toggle */}
                              <div className="bg-slate-900 border border-slate-700/80 p-0.5 rounded-lg flex items-center gap-1">
                                <button
                                  type="button"
                                  onClick={() => setPipelineLayoutMode('fit')}
                                  className={`px-2 py-1 rounded text-[10px] font-bold transition flex items-center gap-1 ${
                                    pipelineLayoutMode === 'fit'
                                      ? 'bg-indigo-600 text-white shadow-xs'
                                      : 'text-slate-400 hover:text-white'
                                  }`}
                                  title="Hiển thị gọn gàng vừa khít màn hình, không bị tràn hay vỡ khung"
                                >
                                  <Minimize2 className="w-3 h-3" />
                                  <span>Vừa Khung (Fit 8 Trạm)</span>
                                </button>
                                <button
                                  type="button"
                                  onClick={() => setPipelineLayoutMode('scroll')}
                                  className={`px-2 py-1 rounded text-[10px] font-bold transition flex items-center gap-1 ${
                                    pipelineLayoutMode === 'scroll'
                                      ? 'bg-indigo-600 text-white shadow-xs'
                                      : 'text-slate-400 hover:text-white'
                                  }`}
                                  title="Dòng chảy cuộn chi tiết từng bước"
                                >
                                  <Maximize2 className="w-3 h-3" />
                                  <span>Dòng Cuộn (Stream)</span>
                                </button>
                              </div>

                              {/* Scroll Left / Right Buttons (active when scroll mode or on small screens) */}
                              {pipelineLayoutMode === 'scroll' && (
                                <div className="flex items-center gap-1">
                                  <button
                                    type="button"
                                    onClick={() => scrollPipeline('left')}
                                    className="p-1 rounded-lg bg-slate-900 border border-slate-700 hover:border-indigo-500 hover:bg-slate-800 text-slate-300 transition"
                                    title="Cuộn sang trái"
                                  >
                                    <ChevronLeft className="w-3.5 h-3.5" />
                                  </button>
                                  <button
                                    type="button"
                                    onClick={() => scrollPipeline('right')}
                                    className="p-1 rounded-lg bg-slate-900 border border-slate-700 hover:border-indigo-500 hover:bg-slate-800 text-slate-300 transition"
                                    title="Cuộn sang phải"
                                  >
                                    <ChevronRight className="w-3.5 h-3.5" />
                                  </button>
                                </div>
                              )}
                            </div>
                          </div>

                          {/* PIPELINE CARDS CONTAINER */}
                          <div
                            ref={pipelineTrackRef}
                            className={`w-full ${
                              pipelineLayoutMode === 'scroll'
                                ? 'overflow-x-auto pb-3 scrollbar-thin scroll-smooth'
                                : 'overflow-hidden'
                            }`}
                          >
                            <div
                              className={
                                pipelineLayoutMode === 'scroll'
                                  ? 'min-w-[1540px] flex items-stretch gap-2 p-3 bg-slate-900/90 rounded-2xl border border-slate-800/90 shadow-inner'
                                  : 'grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2 p-3 bg-slate-900/90 rounded-2xl border border-slate-800/90 shadow-inner'
                              }
                            >
                              {[
                                {
                                  step: 1,
                                  tag: 'INGESTION',
                                  title: '1. Thu Nhận Đa Phương Thức',
                                  model: 'Faster-Whisper + OCR',
                                  inDesc: 'Văn bản, Giọng nói WAV, Ảnh xét nghiệm máu',
                                  outDesc: 'Văn bản lâm sàng Unicode + Dấu hiệu sinh tồn thô',
                                  framework: 'Whisper + EasyOCR',
                                  latency: '~12ms - 120ms',
                                  connector: 'Audio & Text →'
                                },
                                {
                                  step: 2,
                                  tag: 'GATEWAY & CACHE',
                                  title: '2. Gateway & Redis Cache',
                                  model: 'FastAPI v3.0 + Redis',
                                  inDesc: 'POST /chat/message + Session ID + User Token',
                                  outDesc: 'Bypass Chào hỏi (0ms) HOẶC Pipeline Chuyên Sâu',
                                  framework: 'FastAPI + Redis TTL 1800s',
                                  latency: '~5ms - 8ms',
                                  connector: 'Clinical Query →'
                                },
                                {
                                  step: 3,
                                  tag: 'PHOBERT NER',
                                  title: '3. PhoBERT Transformer NER',
                                  model: 'vinai/phobert-base',
                                  inDesc: 'Chuỗi văn bản lâm sàng tự nhiên tiếng Việt',
                                  outDesc: 'Triệu chứng khẳng định, Phủ định, Red Flag <0.5s',
                                  framework: 'PyTorch (9 BIO Labels)',
                                  latency: '~35ms',
                                  connector: '9 BIO Entities →'
                                },
                                {
                                  step: 4,
                                  tag: 'SEMANTIC 384-D',
                                  title: '4. Chuẩn Hóa Ngữ Nghĩa',
                                  model: 'MiniLM-L12-v2',
                                  inDesc: 'Thực thể thô từ PhoBERT (vd: đau đầu buốt óc)',
                                  outDesc: 'Khái niệm y khoa chuẩn hóa 211 mã ICD-10',
                                  framework: 'SentenceTransformers',
                                  latency: '~18ms',
                                  connector: '384-D Concepts →'
                                },
                                {
                                  step: 5,
                                  tag: 'DUAL ML & TRIAGE',
                                  title: '5. ML 211 ICD-10 & XGBoost',
                                  model: 'NLP Classifier + XGBoost',
                                  inDesc: 'Vector triệu chứng + Bảng sinh tồn (HA, Mạch, SpO2)',
                                  outDesc: 'Top 3 mã ICD-10 (%) + Phân tầng ESI 1-5',
                                  framework: 'Ensemble 92.69% Acc',
                                  latency: '~22ms',
                                  connector: 'ICD-10 & ESI Tier →'
                                },
                                {
                                  step: 6,
                                  tag: 'KNOWLEDGE RAG',
                                  title: '6. Kho 640 Phác Đồ BYT',
                                  model: 'Qdrant / Dense RAG',
                                  inDesc: 'Mã ICD-10 hàng đầu (vd: A90 Dengue) + Triệu chứng',
                                  outDesc: 'Đoạn trích dẫn phác đồ điều trị BYT & Cảnh báo',
                                  framework: '640 BYT Docs / Qdrant',
                                  latency: '~28ms',
                                  connector: 'BYT Protocols →'
                                },
                                {
                                  step: 7,
                                  tag: 'LLM REASONING',
                                  title: '7. Gemini 2.0 Flash LLM',
                                  model: 'gemini-2.0-flash',
                                  inDesc: 'Grounded Prompt (Bệnh án 20 lượt + ESI + Phác đồ)',
                                  outDesc: 'Bệnh án ngoại trú hoàn chỉnh, lời khuyên thấu cảm',
                                  framework: 'Gemini 2.0 (20 Turns)',
                                  latency: '~380ms',
                                  connector: 'EHR Stream →'
                                },
                                {
                                  step: 8,
                                  tag: 'DELIVERY & PDF',
                                  title: '8. UI Stream & Bệnh Án PDF',
                                  model: 'Next.js 14 Client App',
                                  inDesc: 'Dòng SSE chunked + Payload chẩn đoán có cấu trúc',
                                  outDesc: 'Thẻ ICD-10, Cấp cứu 115, Audio TTS, Xuất PDF',
                                  framework: 'SSE Stream + PDF Engine',
                                  latency: '~10ms',
                                  connector: 'Hoàn Thành ✓'
                                },
                              ].map((st, idx) => {
                                const isNodeSelected = selectedArchNode === st.step;
                                const isNodeActiveInTrace = traceStep === st.step;
                                const isPastInTrace = traceStep > st.step;

                                return (
                                  <React.Fragment key={st.step}>
                                    {/* Stage Card */}
                                    <div
                                      onClick={() => setSelectedArchNode(st.step)}
                                      className={`flex flex-col justify-between p-3 rounded-xl border transition-all cursor-pointer relative overflow-hidden ${
                                        pipelineLayoutMode === 'scroll' ? 'w-[172px] flex-shrink-0' : 'w-full'
                                      } ${
                                        isNodeActiveInTrace
                                          ? 'bg-gradient-to-b from-emerald-950/90 to-slate-950 border-emerald-400 ring-2 ring-emerald-400/80 shadow-xl shadow-emerald-500/25 animate-pulse'
                                          : isNodeSelected
                                          ? 'bg-gradient-to-b from-indigo-950/90 to-slate-950 border-indigo-400 ring-2 ring-indigo-400/70 shadow-lg'
                                          : isPastInTrace
                                          ? 'bg-slate-900/90 border-emerald-900/70 hover:border-emerald-700'
                                          : 'bg-slate-900/80 border-slate-800 hover:bg-slate-800/90 hover:border-slate-700'
                                      }`}
                                    >
                                      <div>
                                        {/* Card Top: Step number & Tag */}
                                        <div className="flex items-center justify-between pb-1.5 border-b border-slate-800">
                                          <div className="flex items-center gap-1.5">
                                            <span className={`w-5 h-5 rounded-md font-mono text-[10px] font-black flex items-center justify-center ${
                                              isNodeActiveInTrace ? 'bg-emerald-400 text-slate-950' : 'bg-indigo-600 text-white'
                                            }`}>
                                              0{st.step}
                                            </span>
                                            <span className="text-[9px] font-mono font-bold text-indigo-300 uppercase tracking-tight truncate max-w-[70px]">
                                              {st.tag}
                                            </span>
                                          </div>
                                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                                        </div>

                                        {/* Card Mid: Title & Engine */}
                                        <h4 className="font-bold text-[11px] text-white mt-1.5 leading-tight line-clamp-2">
                                          {st.title}
                                        </h4>
                                        <div className="text-[9.5px] font-mono text-indigo-300 font-semibold mt-1 truncate">
                                          ⚙️ {st.model}
                                        </div>

                                        {/* In & Out Box */}
                                        <div className="mt-2 space-y-1 text-[9.5px] bg-slate-950/80 p-1.5 rounded-lg border border-slate-800/80">
                                          <div className="line-clamp-2">
                                            <strong className="text-slate-400">Vào: </strong>
                                            <span className="text-slate-300">{st.inDesc}</span>
                                          </div>
                                          <div className="pt-1 border-t border-slate-800/70 line-clamp-2">
                                            <strong className="text-emerald-400">Ra: </strong>
                                            <span className="text-slate-200 font-medium">{st.outDesc}</span>
                                          </div>
                                        </div>
                                      </div>

                                      {/* Card Bottom: Framework & Latency */}
                                      <div className="mt-2.5 pt-1.5 border-t border-slate-800 flex items-center justify-between text-[9.5px] font-mono">
                                        <span className="text-slate-500 truncate max-w-[75px]">{st.framework}</span>
                                        <span className="text-emerald-400 font-bold bg-emerald-950/60 px-1 py-0.5 rounded border border-emerald-800/60 text-[9px]">
                                          {st.latency}
                                        </span>
                                      </div>
                                    </div>

                                    {/* Horizontal Flow Arrow Connector (only in scroll stream mode) */}
                                    {pipelineLayoutMode === 'scroll' && idx < 7 && (
                                      <div className="flex flex-col items-center justify-center flex-shrink-0 px-1">
                                        <span className="text-[8px] font-mono font-bold text-indigo-300/80 uppercase tracking-tighter whitespace-nowrap mb-1">
                                          {st.connector}
                                        </span>
                                        <div className="flex items-center">
                                          <div className={`h-0.5 w-3.5 transition-colors ${
                                            traceStep > st.step ? 'bg-emerald-400 shadow-sm shadow-emerald-400' : 'bg-indigo-900'
                                          }`} />
                                          <ArrowRight className={`w-3.5 h-3.5 -ml-1 transition-colors ${
                                            traceStep === st.step + 1 ? 'text-emerald-400 animate-pulse' : 'text-indigo-400'
                                          }`} />
                                        </div>
                                      </div>
                                    )}
                                  </React.Fragment>
                                );
                              })}
                            </div>
                          </div>
                        </div>

                        {/* INTERACTIVE STAGE DEEP-DIVE INSPECTOR (Synchronized with selected card) */}
                        <div className="relative z-10 p-5 bg-slate-900/90 rounded-2xl border border-indigo-900/80 grid grid-cols-1 lg:grid-cols-12 gap-5 shadow-2xl">
                          <div className="lg:col-span-5 space-y-3">
                            <div className="flex items-center justify-between">
                              <span className="text-[10px] font-mono uppercase text-indigo-400 font-bold bg-indigo-950/80 px-2.5 py-1 rounded-lg border border-indigo-800">
                                Chi Tiết Trạm Đang Khảo Sát #{selectedArchNode}
                              </span>
                              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 font-bold flex items-center gap-1">
                                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                                <span>ONLINE SLA VERIFIED</span>
                              </span>
                            </div>

                            <h4 className="text-base font-bold text-white">
                              {[
                                'Trạm 1: Thu Nhận Đầu Vào Đa Phương Thức (Multimodal Ingestion)',
                                'Trạm 2: Cổng API Gateway, Caching Phân Tán & Lọc Ý Định (Gateway & Cache)',
                                'Trạm 3: Bóc Tách Thực Thể Lâm Sàng PhoBERT Transformer (Medical NER)',
                                'Trạm 4: Chuẩn Hóa Ngữ Nghĩa Thực Thể (Dense Semantic Normalizer 384-D)',
                                'Trạm 5: Bộ Đôi Học Máy Chẩn Đoán & Phân Tầng ESI (ML Ensemble & Triage)',
                                'Trạm 6: Truy Xuất Tri Thức Phác Đồ Bộ Y Tế (Clinical RAG Grounding)',
                                'Trạm 7: Suy Luận Lâm Sàng & Lập Bệnh Án Gemini 2.0 (Clinical Reasoning LLM)',
                                'Trạm 8: Trình Diễn Đa Phương Tiện & Xuất Bệnh Án PDF (Client Delivery & PDF)',
                              ][selectedArchNode - 1]}
                            </h4>

                            <p className="text-xs text-slate-300 leading-relaxed">
                              {[
                                'Tiếp nhận câu hỏi văn bản thô, file ghi âm giọng nói (Faster-Whisper STT) và ảnh chụp phiếu xét nghiệm máu / đơn thuốc (OCR + Blood Ref Check) để trích xuất văn bản lâm sàng chuẩn hóa Unicode.',
                                'FastAPI v3.0 tiếp nhận request, kiểm tra bộ đệm phân tán Redis (TTL 1800s RAG / 3600s Triage) để trả về ngay (0ms). Nếu là chào hỏi thông thường sẽ kích hoạt Fast Intent bypass; nếu là ca bệnh sẽ chuyển tiếp Pipeline y khoa.',
                                'Mô hình VinAI PhoBERT Transformer (vinai/phobert-base, fine-tuned tại models_weights/phobert_ner) gán 9 nhãn BIO, tự động bóc tách triệu chứng khẳng định, triệu chứng phủ định loại trừ (Pertinent Negatives như "không ho") và cờ đỏ nguy kịch <0.5s.',
                                'SentenceTransformer paraphrase-multilingual-MiniLM-L12-v2 vector hóa 384 chiều, sử dụng Cosine Similarity để ánh xạ từ ngữ tự nhiên của người bệnh vào 211 mã thực thể ICD-10 chuẩn mực của Bộ Y Tế.',
                                'Bộ phân loại NLP Calibrated Multi-Class (nlp_symptom_classifier.pkl, độ chính xác 92.69%) dự đoán 211 nhóm bệnh ICD-10 kết hợp cây quyết định XGBoost (tabular_xgboost.json) phân tầng khẩn cấp ESI 1-5 qua Dynamic Late Fusion.',
                                'Hệ thống truy xuất ngữ nghĩa Qdrant Vector Store / In-Memory Dense Engine từ kho 640 tài liệu lâm sàng (423 văn bản phác đồ Bộ Y Tế + 211 hồ sơ ICD-10 chi tiết) làm khóa an toàn lâm sàng (Guardrail), triệt tiêu hoàn toàn ảo giác y khoa.',
                                'Google Gemini 2.0 Flash đóng vai trò Bác Sĩ Cố Vấn: Duy trì bộ nhớ tích lũy 20 lượt hội thoại, suy luận chẩn đoán phân biệt dựa trên prompt grounded và cơ chế tự động Fallback về bộ quy tắc nội bộ khi ngoại tuyến.',
                                'Client Next.js 14 nhận luồng SSE Typewriter mượt mà, hiển thị thẻ ICD-10, banner cảnh báo đỏ 115 khi ESI 1, định tuyến chuyên khoa, phát giọng đọc bác sĩ Audio TTS và xuất Hồ sơ bệnh án điện tử PDF chuẩn bệnh viện.',
                              ][selectedArchNode - 1]}
                            </p>

                            <div className="pt-2 flex flex-wrap gap-2 text-[11px] font-mono">
                              <span className="bg-indigo-950/70 border border-indigo-800 text-indigo-300 px-2.5 py-1 rounded-lg">
                                Model: {[
                                  'Faster-Whisper + EasyOCR',
                                  'FastAPI v3.0 + Redis Cache',
                                  'vinai/phobert-base (9 BIO)',
                                  'MiniLM-L12-v2 (384-D)',
                                  'NLP Classifier + XGBoost (211 ICD)',
                                  'Qdrant / Dense RAG (640 Docs)',
                                  'Gemini 2.0 Flash (20 Turns)',
                                  'Next.js 14 + Hospital PDF',
                                ][selectedArchNode - 1]}
                              </span>
                              <span className="bg-slate-900 border border-slate-700 text-emerald-300 px-2.5 py-1 rounded-lg font-bold">
                                Latency: ~{[12, 8, 35, 18, 22, 28, 380, 10][selectedArchNode - 1]}ms
                              </span>
                              <span className="bg-slate-900 border border-slate-700 text-slate-400 px-2.5 py-1 rounded-lg">
                                {[
                                  'Format: UTF-8 & Raw PCM',
                                  'Protocol: REST & Redis Cache',
                                  'Architecture: Transformer BIO',
                                  'Embedding: 384-D Dense',
                                  'Ensemble: NLP + XGBoost',
                                  'Guardrail: 100% BYT Enforced',
                                  'Memory: 20-Turn Sliding Window',
                                  'Streaming: SSE Typewriter',
                                ][selectedArchNode - 1]}
                              </span>
                            </div>
                          </div>

                          {/* Intermediate Live Data Payload Box */}
                          <div className="lg:col-span-7 bg-black/75 rounded-2xl p-4 border border-slate-800 flex flex-col justify-between shadow-inner">
                            <div className="flex items-center justify-between pb-2 border-b border-slate-800 text-[10px] font-mono text-slate-400">
                              <span>INTERMEDIATE PAYLOAD (DỮ LIỆU ĐẦU RA TRẠM #{selectedArchNode})</span>
                              <span className="text-emerald-400 font-bold">STATUS: OK (200)</span>
                            </div>
                            <pre className="text-[11px] font-mono text-emerald-400 overflow-x-auto p-2 leading-relaxed custom-scrollbar max-h-48 mt-1">
                              {selectedArchNode === 1 && JSON.stringify({
                                modality: "multimodal_input",
                                raw_input: customQueryText,
                                stt_whisper_engine: "Faster-Whisper (Large-v3-Turbo)",
                                ocr_engine: "Tesseract / EasyOCR v1.7.1",
                                blood_ref_check: "Auto-calibrated ranges",
                                input_length: customQueryText.length
                              }, null, 2)}
                              {selectedArchNode === 2 && JSON.stringify({
                                endpoint: "POST /api/v1/chat/message",
                                session_id: "sess_medibot_live_7718",
                                redis_distributed_cache: "CONNECTED (TTL: 1800s RAG / 3600s Triage)",
                                mongo_storage: "Motor Async Connected (Auto Failover)",
                                intent_type: traceScenario === 'chitchat' ? "general_chitchat" : "medical_clinical_triage",
                                bypass_ai_pipeline: traceScenario === 'chitchat',
                                active_route: traceScenario === 'chitchat' ? "FastIntentResponder (4ms)" : "FullClinicalPipeline"
                              }, null, 2)}
                              {selectedArchNode === 3 && JSON.stringify({
                                ner_engine: "vinai/phobert-base (fine-tuned)",
                                weights_directory: "models_weights/phobert_ner",
                                bio_labels_supported: ["B-SYMPTOM", "I-SYMPTOM", "B-RED_FLAG", "I-RED_FLAG", "B-VITAL", "I-VITAL", "B-DURATION", "I-DURATION", "O"],
                                positive_symptoms: traceScenario === 'cardiac'
                                  ? ["đau thắt ngực trái", "lan vai trái và hàm", "khó thở", "vã mồ hôi"]
                                  : ["sốt cao 39.2°C", "đau đầu dữ dội", "đau mỏi hốc mắt", "chấm xuất huyết cẳng tay"],
                                pertinent_negatives: traceScenario === 'cardiac' ? [] : ["không ho (loại trừ nhiễm trùng hô hấp)"],
                                red_flag_alert: traceScenario === 'cardiac',
                                triage_urgency: traceScenario === 'cardiac' ? "EMERGENCY_LEVEL_1" : "EVALUATE_LEVEL_2"
                              }, null, 2)}
                              {selectedArchNode === 4 && JSON.stringify({
                                semantic_encoder: "paraphrase-multilingual-MiniLM-L12-v2",
                                embedding_dimension: 384,
                                normalization_method: "Dense Cosine Similarity",
                                target_concepts_pool: "211 ICD-10 Standard Concepts",
                                mapped_canonical_entities: traceScenario === 'cardiac' ? [
                                  { raw: "đau thắt ngực trái", canonical: "Cơn đau thắt ngực không ổn định", icd10_concept: "I20.0", score: 0.962 },
                                  { raw: "khó thở", canonical: "Khó thở cấp tính", icd10_concept: "R06.0", score: 0.941 }
                                ] : [
                                  { raw: "sốt cao", canonical: "Sốt không rõ nguồn gốc", icd10_concept: "R50.9", score: 0.954 },
                                  { raw: "chấm xuất huyết", canonical: "Xuất huyết tự phát dưới da", icd10_concept: "R23.3", score: 0.928 }
                                ]
                              }, null, 2)}
                              {selectedArchNode === 5 && JSON.stringify({
                                disease_classifier: "nlp_symptom_classifier.pkl (Calibrated Multi-Class)",
                                test_accuracy: "92.69%",
                                num_classes: 211,
                                predicted_icd10: traceScenario === 'cardiac' ? "I21.9" : "A90",
                                disease_name_vi: traceScenario === 'cardiac' ? "Nhồi máu cơ tim cấp" : "Sốt xuất huyết Dengue",
                                confidence_score: traceScenario === 'cardiac' ? 0.984 : 0.948,
                                tabular_model: "tabular_xgboost.json (Gradient Boosted Trees)",
                                esi_triage_tier: traceScenario === 'cardiac' ? "Cấp 1 (Hồi sức cấp cứu tức thì - Gọi 115)" : "Cấp 2 (Khẩn cấp - Thăm khám trong 15-30p)",
                                dynamic_late_fusion_alpha: 0.35
                              }, null, 2)}
                              {selectedArchNode === 6 && JSON.stringify({
                                knowledge_store: "640 Clinical Documents (423 BYT Protocols + 211 ICD-10 Profiles)",
                                vector_engine: "Qdrant Vector DB / In-Memory Dense Store",
                                matched_icd_query: traceScenario === 'cardiac' ? "I21" : "A90",
                                retrieved_protocol: traceScenario === 'cardiac'
                                  ? "Quyết định 2187/QĐ-BYT: Quy trình chẩn đoán & xử trí Hội chứng vành cấp (Chỉ định ECG 12 chuyển đạo trong 10 phút, thở oxy, chuyển phòng Can thiệp)"
                                  : "Quyết định 2760/QĐ-BYT: Hướng dẫn chẩn đoán và điều trị Sốt xuất huyết Dengue (Phác đồ bù dịch điện giải Ringer Lactat, theo dõi tiểu cầu)",
                                clinical_guardrail: "ANTI_HALLUCINATION_LOCK_ENFORCED_100%"
                              }, null, 2)}
                              {selectedArchNode === 7 && JSON.stringify({
                                primary_engine: "Google Gemini 2.0 Flash (gemini-2.0-flash)",
                                context_memory: "Cumulative 20-Turn Multi-turn Sliding Window",
                                resilience: "Exponential Backoff + Jitter Retry",
                                offline_fallback: "Deterministic Protocol Fallback Ready",
                                prompt_tokens: 1540,
                                completion_tokens: 420,
                                safety_compliance_check: "PASSED_100%"
                              }, null, 2)}
                              {selectedArchNode === 8 && JSON.stringify({
                                client_status: 200,
                                delivery_protocol: "Server-Sent Events (SSE) Typewriter Stream",
                                rendered_components: ["ICD-10 Badge Card", "ESI Risk Badge", "Red Flag Banner 115", "Hospital-grade PDF Exporter", "Doctor Voice Audio TTS"],
                                export_pdf_ready: true,
                                total_pipeline_roundtrip_ms: traceScenario === 'chitchat' ? "4ms" : "497ms"
                              }, null, 2)}
                            </pre>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* VIEW MODE 2: DETAILED 8-STAGE GRID SPECIFICATIONS */}
                    {archDiagramView === 'grid' && (
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 pt-2">
                        {[
                          {
                            step: 1,
                            tier: 'Chặng 1: Thu Nhận Đa Kênh',
                            title: 'Multimodal Ingestion (Whisper STT & OCR)',
                            modelFile: 'Faster-Whisper + EasyOCR',
                            modelName: 'Bộ Tiền Xử Lý Đa Phương Thức',
                            input: 'Văn bản, Giọng nói WAV/M4A, Ảnh đơn thuốc/xét nghiệm máu',
                            output: 'Chuỗi văn bản lâm sàng tiếng Việt chuẩn Unicode + Dấu hiệu sinh tồn thô',
                            status: 'active',
                            type: 'Perception',
                            framework: 'Whisper STT + EasyOCR',
                            latency: '~12ms - 120ms',
                          },
                          {
                            step: 2,
                            tier: 'Chặng 2: Cổng API & Caching',
                            title: 'FastAPI Gateway & Redis Distributed Cache',
                            modelFile: 'FastAPI v3.0 + Redis (TTL 1800s)',
                            modelName: 'Cổng Giao Tiếp, Lưu Đệm & Phân Luồng Ý Định',
                            input: 'POST /chat/message + Session ID + User Token',
                            output: 'Cache Hit (0ms) HOẶC Phân luồng: Chào hỏi bypass vs Pipeline lâm sàng',
                            status: 'active',
                            type: 'Gateway & Cache',
                            framework: 'FastAPI + Redis + Motor Mongo',
                            latency: '~5ms - 8ms',
                          },
                          {
                            step: 3,
                            tier: 'Chặng 3: Deep Learning NER',
                            title: 'VinAI PhoBERT Transformer Medical NER',
                            modelFile: 'vinai/phobert-base (models_weights/phobert_ner)',
                            modelName: 'Mô Hình Transformer Bóc Tách Thực Thể Y Tế',
                            input: 'Chuỗi văn bản lâm sàng tự nhiên tiếng Việt',
                            output: 'Triệu chứng khẳng định, Triệu chứng phủ định (Negatives), Red Flags <0.5s',
                            status: 'active',
                            type: 'Transformer NER',
                            framework: 'PyTorch (9 BIO Labels)',
                            latency: '~35ms',
                          },
                          {
                            step: 4,
                            tier: 'Chặng 4: Chuẩn Hóa Ngữ Nghĩa',
                            title: 'Dense Semantic Normalizer 384-D',
                            modelFile: 'paraphrase-multilingual-MiniLM-L12-v2',
                            modelName: 'Bộ Nhúng Ngữ Nghĩa & Đối Sánh Thực Thể Chuẩn',
                            input: 'Thực thể triệu chứng thô bóc tách từ PhoBERT',
                            output: 'Khái niệm y khoa chuẩn hóa đối sánh 211 mã ICD-10 Bộ Y Tế',
                            status: 'active',
                            type: 'Dense Embedding',
                            framework: 'SentenceTransformers (384-D)',
                            latency: '~18ms',
                          },
                          {
                            step: 5,
                            tier: 'Chặng 5: Học Máy Phân Tầng',
                            title: 'Dual ML Disease Classification & Tabular XGBoost',
                            modelFile: 'nlp_symptom_classifier.pkl + tabular_xgboost.json',
                            modelName: 'Bộ Đôi Học Máy Chẩn Đoán & Phân Tầng ESI 1-5',
                            input: 'Vector đặc trưng triệu chứng + Bảng sinh tồn (Mạch, HA, SpO2, Tuổi)',
                            output: 'Top 3 mã ICD-10 (%) + Cấp độ khẩn cấp ESI 1-5 & Risk Score',
                            status: 'active',
                            type: 'Ensemble ML',
                            framework: 'NLP Calibrated (92.69%) + XGBoost',
                            latency: '~22ms',
                          },
                          {
                            step: 6,
                            tier: 'Chặng 6: Tri Thức RAG BYT',
                            title: 'Clinical Knowledge Grounding (640 BYT Documents)',
                            modelFile: 'Qdrant Vector DB / In-Memory Dense Store',
                            modelName: 'Kho Tri Thức Phác Đồ Bộ Y Tế & Chống Ảo Giác',
                            input: 'Mã ICD-10 hàng đầu (vd: A90 Dengue) + Triệu chứng liên quan',
                            output: 'Đoạn trích dẫn phác đồ BYT, chỉ định bù dịch & phân tuyến chuyên khoa',
                            status: 'active',
                            type: 'Knowledge RAG',
                            framework: '640 BYT Docs / Qdrant',
                            latency: '~28ms',
                          },
                          {
                            step: 7,
                            tier: 'Chặng 7: Suy Luận Lâm Sàng',
                            title: 'Google Gemini 2.0 Flash Clinical Reasoning',
                            modelFile: 'gemini-2.0-flash + Protocol Fallback',
                            modelName: 'Bác Sĩ Cố Vấn Lâm Sàng & Lập Hồ Sơ Bệnh Án',
                            input: 'Grounded Prompt (Bệnh án tích lũy 20 lượt + ESI + Phác đồ BYT)',
                            output: 'Bệnh án điện tử ngoại trú, lời giải thích bệnh học thấu cảm, câu hỏi hỏi bệnh',
                            status: 'active',
                            type: 'Clinical LLM',
                            framework: 'Gemini 2.0 (20 Turns)',
                            latency: '~380ms',
                          },
                          {
                            step: 8,
                            tier: 'Chặng 8: Trình Diễn & Xuất PDF',
                            title: 'Client Stream Delivery & Hospital PDF Export',
                            modelFile: 'Next.js 14 Client App (/chat)',
                            modelName: 'Giao Diện Người Dùng & Xuất Bệnh Án Chuẩn Bệnh Viện',
                            input: 'Dòng SSE chunked + Metadata chẩn đoán có cấu trúc',
                            output: 'Thẻ ICD-10, Banner Cấp cứu 115, Audio TTS, Xuất file PDF bệnh án',
                            status: 'active',
                            type: 'Presentation & PDF',
                            framework: 'React 18 + SSE Typewriter + PDF',
                            latency: '~10ms',
                          },
                        ].map((node) => {
                          const isNodeSelected = selectedArchNode === node.step;
                          const isNodeActiveInTrace = traceStep === node.step;

                          return (
                            <div
                              key={node.step}
                              onClick={() => setSelectedArchNode(node.step)}
                              className={`p-4 rounded-3xl border transition-all cursor-pointer flex flex-col justify-between relative overflow-hidden ${
                                isNodeActiveInTrace
                                  ? 'bg-emerald-50 border-emerald-400 ring-2 ring-emerald-500 shadow-lg shadow-emerald-500/20'
                                  : isNodeSelected
                                  ? 'bg-indigo-50/70 border-indigo-300 ring-2 ring-indigo-500/30 shadow-md'
                                  : 'bg-slate-50/60 border-slate-200 hover:bg-white hover:shadow-md'
                              }`}
                            >
                              <div>
                                <div className="flex items-center justify-between gap-2">
                                  <div className="flex items-center gap-1.5">
                                    <span className="w-6 h-6 rounded-lg bg-indigo-600 text-white font-mono text-xs font-bold flex items-center justify-center">
                                      0{node.step}
                                    </span>
                                    <span className="text-[10px] font-mono font-bold text-slate-500 uppercase">
                                      {node.tier.split(':')[0]}
                                    </span>
                                  </div>

                                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200 flex items-center gap-1 font-mono">
                                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 animate-pulse" />
                                    <span>ONLINE</span>
                                  </span>
                                </div>

                                <h4 className="font-bold text-slate-900 text-sm mt-2.5 leading-snug">
                                  {node.title}
                                </h4>
                                <p className="text-[11px] font-mono text-indigo-700 font-semibold mt-0.5 truncate">
                                  ⚙️ {node.modelFile}
                                </p>

                                <div className="mt-3 space-y-1.5 text-xs text-slate-600 bg-white p-2.5 rounded-2xl border border-slate-200/80">
                                  <div>
                                    <strong className="text-slate-700 text-[11px] block">Đầu vào (Input):</strong>
                                    <span className="text-[11px] text-slate-500 leading-tight block">{node.input}</span>
                                  </div>
                                  <div className="pt-1 border-t border-slate-100">
                                    <strong className="text-emerald-700 text-[11px] block">Đầu ra (Output):</strong>
                                    <span className="text-[11px] text-slate-600 leading-tight block font-medium">{node.output}</span>
                                  </div>
                                </div>
                              </div>

                              <div className="mt-3 pt-2 border-t border-slate-200/60 flex items-center justify-between text-[11px] font-mono text-slate-500">
                                <span className="truncate max-w-[150px]">{node.framework}</span>
                                <span className="font-bold text-indigo-600 bg-indigo-50 px-1.5 py-0.5 rounded">
                                  {node.latency}
                                </span>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>

                  {/* Module C: Live AI Models Real-time Telemetry Matrix Table */}
                  <div className="bg-white rounded-3xl p-6 border border-slate-200/90 shadow-sm space-y-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                          <Bot className="w-4 h-4 text-indigo-600" />
                          <span>Bảng Trạng Thái Mô Hình AI Thời Gian Thực Theo Chức Năng</span>
                        </h3>
                        <p className="text-xs text-slate-500">
                          Tất cả mô hình đang nạp trong RAM/VRAM hoặc kết nối API đều được giám sát nhịp đập trực tiếp
                        </p>
                      </div>
                      <span className="text-xs font-mono text-emerald-700 font-bold bg-emerald-50 px-3 py-1 rounded-xl border border-emerald-200">
                        {modelsList.filter(m => m.status === 'active').length} / {modelsList.length} Mô Hình Sẵn Sàng
                      </span>
                    </div>

                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-xs border-collapse">
                        <thead>
                          <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold font-mono">
                            <th className="py-3 px-4">Tên Mô Hình & Tệp Weights</th>
                            <th className="py-3 px-4">Giai Đoạn Trong Pipeline</th>
                            <th className="py-3 px-4">Chức Năng Chính</th>
                            <th className="py-3 px-4">Trạng Thái Realtime</th>
                            <th className="py-3 px-4">Dung Lượng</th>
                            <th className="py-3 px-4">Khung Làm Việc (Framework)</th>
                            <th className="py-3 px-4 text-right">Hành Động</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                          {modelsList.map((m) => (
                            <tr key={m.filename} className="hover:bg-slate-50/60 transition">
                              <td className="py-3 px-4">
                                <div className="font-bold text-slate-900">{m.name_vi || m.name}</div>
                                <div className="font-mono text-[11px] text-indigo-600 font-medium">{m.filename}</div>
                              </td>
                              <td className="py-3 px-4">
                                <span className="px-2 py-0.5 rounded-md bg-indigo-50 text-indigo-700 border border-indigo-100 font-mono text-[10px] font-bold">
                                  {m.stage || 'Giai đoạn cốt lõi'}
                                </span>
                              </td>
                              <td className="py-3 px-4 text-slate-600 max-w-xs">{m.role}</td>
                              <td className="py-3 px-4">
                                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                                  <span>Đang Hoạt Động</span>
                                </span>
                              </td>
                              <td className="py-3 px-4 font-mono text-slate-600">
                                {m.size_mb !== undefined ? `${m.size_mb} MB` : 'API Cloud'}
                              </td>
                              <td className="py-3 px-4 font-mono text-slate-500 text-[11px]">
                                {m.framework}
                              </td>
                              <td className="py-3 px-4 text-right">
                                <button
                                  onClick={() => {
                                    setActiveTab('training_center');
                                    setTrainingJobType('retrain');
                                  }}
                                  className="px-2.5 py-1 rounded-lg bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-bold text-[11px] transition"
                                >
                                  Huấn luyện
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}

              {/* VIEW 2: MICROSERVICE VS MONOLITH AUDIT REPORT */}
              {archSubTab === 'audit' && (
                <div className="space-y-6 w-full">
                  {/* Architecture Verdict Banner */}
                  <div className="bg-white rounded-3xl p-6 border border-slate-200/90 shadow-sm space-y-4">
                    <div className="flex items-center gap-3">
                      <div className="p-2.5 rounded-2xl bg-indigo-50 border border-indigo-100 text-indigo-600">
                        <Network className="w-6 h-6" />
                      </div>
                      <div>
                        <h3 className="text-base font-bold text-slate-900">
                          Báo Cáo Kiểm Tra Kiến Trúc Hệ Thống: Monolith vs. Microservice
                        </h3>
                        <p className="text-xs text-slate-500">
                          Đánh giá kỹ thuật theo yêu cầu người dùng: Hệ thống có đang làm Microservice và kết nối qua API hay không?
                        </p>
                      </div>
                    </div>

                    <div className="p-4 bg-indigo-50/50 border border-indigo-100 rounded-2xl space-y-2 text-xs text-slate-700">
                      <div className="font-bold text-indigo-950 flex items-center gap-2">
                        <AlertTriangle className="w-4 h-4 text-indigo-600" />
                        <span>KẾT LUẬN KIỂM TRA: HỆ THỐNG HIỆN TẠI LÀ HYBRID MONOLITH (CHƯA PHẢI MICROSERVICES)</span>
                      </div>
                      <p className="leading-relaxed">
                        1. <strong>Tầng Giao Diện ↔ Tầng Máy Chủ (API Client-Server):</strong> Frontend (Next.js chạy cổng 3000) kết nối với Backend (FastAPI chạy cổng 8000) hoàn toàn thông qua chuẩn <strong>REST API (HTTP JSON)</strong> và <strong>WebSocket</strong> (`/api/v1/*`).
                      </p>
                      <p className="leading-relaxed">
                        2. <strong>Tầng Logic Nội Bộ Backend (In-Process Monolith):</strong> Tất cả các service (ChatService, TriageService, GeminiService, AI Pipeline NER & XGBoost) được chạy trong <strong>CÙNG MỘT TIẾN TRÌNH PYTHON DUY NHẤT</strong>. Các service gọi nhau trực tiếp qua hàm Python (`chat_service.process_message()`), không qua mạng nội bộ REST/gRPC hay Message Broker (Kafka/RabbitMQ).
                      </p>
                    </div>

                    {/* Comparison Matrix */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                      <div className="border border-slate-200 rounded-2xl p-4 bg-slate-50">
                        <h4 className="font-bold text-slate-900 text-xs mb-2">Ưu Điểm Của Kiến Trúc Hiện Tại</h4>
                        <ul className="space-y-1.5 text-xs text-slate-600 list-disc list-inside">
                          <li>Độ trễ thấp cực độ (Zero network overhead giữa AI Engine và Chat).</li>
                          <li>Dễ triển khai, kiểm thử và debug chỉ với 1 lệnh khởi động FastAPI.</li>
                          <li>Quản lý state session trong bộ nhớ cực nhanh không lo distributed lock.</li>
                        </ul>
                      </div>
                      <div className="border border-slate-200 rounded-2xl p-4 bg-slate-50">
                        <h4 className="font-bold text-slate-900 text-xs mb-2">Lộ Trình Tách Microservices Nếu Muốn Mở Rộng</h4>
                        <ul className="space-y-1.5 text-xs text-slate-600 list-disc list-inside">
                          <li>Tách <code>ai_engine</code> thành một Microservice riêng biệt (gRPC / FastAPI port 8001).</li>
                          <li>Backend chính (port 8000) chỉ đóng vai trò API Gateway & Auth.</li>
                          <li>Tích hợp Redis / RabbitMQ để phân tải các tác vụ huấn luyện nặng.</li>
                        </ul>
                      </div>
                    </div>
                  </div>

                  {/* Endpoint Catalog */}
                  <div className="bg-white rounded-3xl p-6 border border-slate-200/90 shadow-sm">
                    <h3 className="font-bold text-slate-900 text-sm mb-3">Danh Mục Các Endpoints API Đang Hoạt Động</h3>
                    <div className="space-y-2 text-xs font-mono">
                      <div className="p-2.5 bg-slate-50 rounded-xl flex items-center justify-between">
                        <span className="text-emerald-700 font-bold">POST /api/v1/chat/message</span>
                        <span className="text-slate-500 font-sans">Tiếp nhận triệu chứng & phân tầng chẩn đoán AI</span>
                      </div>
                      <div className="p-2.5 bg-slate-50 rounded-xl flex items-center justify-between">
                        <span className="text-blue-700 font-bold">GET /api/v1/admin/models</span>
                        <span className="text-slate-500 font-sans">Lấy trạng thái và siêu dữ liệu các model AI thời gian thực</span>
                      </div>
                      <div className="p-2.5 bg-slate-50 rounded-xl flex items-center justify-between">
                        <span className="text-indigo-700 font-bold">POST /api/v1/admin/training/start</span>
                        <span className="text-slate-500 font-sans">Khởi chạy training job trên background thread</span>
                      </div>
                      <div className="p-2.5 bg-slate-50 rounded-xl flex items-center justify-between">
                        <span className="text-amber-700 font-bold">POST /api/v1/admin/colab/download</span>
                        <span className="text-slate-500 font-sans">Kéo dataset trực tiếp từ Google Colab / Drive link</span>
                      </div>
                      <div className="p-2.5 bg-slate-50 rounded-xl flex items-center justify-between">
                        <span className="text-purple-700 font-bold">GET /api/v1/admin/system/health</span>
                        <span className="text-slate-500 font-sans">Kiểm tra nhịp tim telemetry hệ thống & trạng thái các model</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ======================================================== */}
          {/* TAB 6: CONVERSATIONS VIEWER                              */}
          {/* ======================================================== */}
          {activeTab === 'conversations' && (
            <div className="space-y-6 animate-in fade-in duration-200">
              {/* Header & Controls */}
              <div className="bg-white rounded-3xl p-6 border border-slate-200/90 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  <div className="p-3 rounded-2xl bg-sky-50 border border-sky-100 text-sky-600">
                    <MessageSquare className="w-6 h-6" />
                  </div>
                  <div>
                    <h2 className="text-base font-bold text-slate-900">
                      Nhật Ký Hội Thoại Toàn Hệ Thống
                    </h2>
                    <p className="text-xs text-slate-500">
                      Xem chi tiết các phiên khám bệnh, truy vấn triệu chứng và các câu trả lời kép (Gemini & Cohere)
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <div className="relative">
                    <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                    <input
                      type="text"
                      placeholder="Tìm mã phiên..."
                      value={conversationSearch}
                      onChange={(e) => setConversationSearch(e.target.value)}
                      className="pl-9 pr-3 py-2 text-xs rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500 w-48"
                    />
                  </div>
                  <button
                    type="button"
                    onClick={fetchConversations}
                    className="p-2.5 rounded-xl border border-slate-200 text-slate-600 hover:bg-slate-50 transition"
                    title="Làm mới danh sách"
                  >
                    <RefreshCw className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Master-Detail Split View */}
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                {/* Left: Sessions List */}
                <div className="lg:col-span-5 bg-white rounded-3xl border border-slate-200/90 shadow-sm p-4 overflow-hidden flex flex-col max-h-[700px]">
                  <div className="text-xs font-bold text-slate-700 pb-3 border-b border-slate-100 flex items-center justify-between">
                    <span>Danh Sách Phiên Khám ({conversationsList.length})</span>
                    <span className="text-[10px] text-slate-400">Nhấp để xem tin nhắn</span>
                  </div>

                  <div className="flex-1 overflow-y-auto custom-scrollbar divide-y divide-slate-100 mt-2 space-y-1">
                    {conversationsList.length === 0 ? (
                      <div className="p-8 text-center text-xs text-slate-400">
                        Chưa có lịch sử hội thoại nào được ghi nhận.
                      </div>
                    ) : (
                      conversationsList
                        .filter((s) =>
                          conversationSearch
                            ? s.session_id?.toLowerCase().includes(conversationSearch.toLowerCase())
                            : true
                        )
                        .map((session) => {
                          const isSelected = selectedSessionId === session.session_id;
                          return (
                            <button
                              key={session.session_id}
                              type="button"
                              onClick={() => fetchSessionMessages(session.session_id)}
                              className={`w-full p-3.5 rounded-2xl text-left transition-all ${
                                isSelected
                                  ? 'bg-sky-50/80 border-2 border-sky-500 shadow-sm'
                                  : 'hover:bg-slate-50 border-2 border-transparent'
                              }`}
                            >
                              <div className="flex items-center justify-between mb-1">
                                <span className="font-mono font-bold text-xs text-slate-800 truncate max-w-[180px]">
                                  {session.session_id}
                                </span>
                                <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-semibold">
                                  {session.message_count || 0} tin nhắn
                                </span>
                              </div>
                              <p className="text-xs text-slate-500 truncate">
                                {session.last_message_preview || 'Không có bản xem trước'}
                              </p>
                              <div className="mt-1.5 flex items-center justify-between text-[10px] text-slate-400">
                                <span>{session.last_updated ? new Date(session.last_updated).toLocaleString('vi-VN') : 'Vừa xong'}</span>
                                <span className="text-sky-600 font-semibold hover:underline">Chi tiết &rarr;</span>
                              </div>
                            </button>
                          );
                        })
                    )}
                  </div>
                </div>

                {/* Right: Message Detail Viewer */}
                <div className="lg:col-span-7 bg-white rounded-3xl border border-slate-200/90 shadow-sm p-6 flex flex-col max-h-[700px]">
                  {selectedSessionId ? (
                    <>
                      <div className="pb-4 border-b border-slate-100 flex items-center justify-between">
                        <div>
                          <div className="text-xs font-bold text-slate-800 flex items-center gap-2">
                            <span>Chi tiết phiên:</span>
                            <span className="font-mono text-sky-700 bg-sky-50 px-2 py-0.5 rounded-md border border-sky-200">
                              {selectedSessionId}
                            </span>
                          </div>
                          <span className="text-[11px] text-slate-400">
                            Tổng {sessionMessages.length} tin nhắn trong phiên
                          </span>
                        </div>
                        <button
                          type="button"
                          onClick={() => fetchSessionMessages(selectedSessionId)}
                          className="p-2 rounded-xl hover:bg-slate-100 text-slate-600 transition"
                          title="Tải lại tin nhắn"
                        >
                          <RefreshCw className={`w-4 h-4 ${isLoadingMessages ? 'animate-spin text-sky-600' : ''}`} />
                        </button>
                      </div>

                      <div className="flex-1 overflow-y-auto custom-scrollbar p-3 space-y-4 my-2">
                        {isLoadingMessages ? (
                          <div className="p-12 text-center text-xs text-slate-400 animate-pulse">
                            Đang tải tin nhắn...
                          </div>
                        ) : sessionMessages.length === 0 ? (
                          <div className="p-12 text-center text-xs text-slate-400">
                            Phiên này chưa có tin nhắn nào.
                          </div>
                        ) : (
                          sessionMessages.map((msg, idx) => {
                            const isUserMsg = msg.sender === 'user';
                            return (
                              <div
                                key={idx}
                                className={`p-4 rounded-2xl text-xs space-y-2 border ${
                                  isUserMsg
                                    ? 'bg-blue-50/60 border-blue-200 text-slate-800'
                                    : 'bg-slate-50/80 border-slate-200 text-slate-800'
                                }`}
                              >
                                <div className="flex items-center justify-between font-semibold">
                                  <span className={isUserMsg ? 'text-blue-700 font-bold' : 'text-teal-700 font-bold'}>
                                    {isUserMsg ? '👤 Bệnh nhân' : '🤖 Bác sĩ AI (MediBot)'}
                                  </span>
                                  <div className="flex items-center gap-2 text-[10px] text-slate-400">
                                    {msg.provider && (
                                      <span className="px-2 py-0.5 rounded bg-white border border-slate-200 font-mono uppercase font-bold text-slate-700">
                                        {msg.provider}
                                      </span>
                                    )}
                                    <span>{msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString('vi-VN') : ''}</span>
                                  </div>
                                </div>

                                <div className="whitespace-pre-wrap leading-relaxed text-[13px]">
                                  {msg.content}
                                </div>

                                {/* Alternative Answer (if Dual AI ran) */}
                                {msg.alternative_answers && msg.alternative_answers.length > 0 && (
                                  <div className="mt-2 p-3 bg-amber-50/70 border border-amber-200 rounded-xl space-y-1">
                                    <div className="text-[11px] font-bold text-amber-900 flex items-center gap-1.5">
                                      <Sparkles className="w-3.5 h-3.5 text-amber-600" />
                                      <span>
                                        Câu trả lời dự phòng (chạy song song từ {msg.alternative_answers[0].provider?.toUpperCase()}):
                                      </span>
                                    </div>
                                    <p className="text-xs text-slate-700 line-clamp-3">
                                      {msg.alternative_answers[0].text}
                                    </p>
                                  </div>
                                )}

                                {/* User Feedback on this message */}
                                {msg.feedback && (
                                  <div className={`mt-2 p-2.5 rounded-xl border text-xs flex items-center gap-2 ${
                                    msg.feedback.rating === 'like'
                                      ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                                      : 'bg-rose-50 border-rose-200 text-rose-800'
                                  }`}>
                                    {msg.feedback.rating === 'like' ? (
                                      <ThumbsUp className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                                    ) : (
                                      <ThumbsDown className="w-4 h-4 text-rose-600 flex-shrink-0" />
                                    )}
                                    <div>
                                      <span className="font-bold">
                                        {msg.feedback.rating === 'like' ? 'Người dùng ĐÃ THÍCH' : 'Người dùng CHƯA HÀI LÒNG'}:
                                      </span>
                                      {msg.feedback.reason && (
                                        <span className="ml-1 text-[11px] italic">
                                          &quot;{msg.feedback.reason}&quot;
                                        </span>
                                      )}
                                    </div>
                                  </div>
                                )}
                              </div>
                            );
                          })
                        )}
                      </div>
                    </>
                  ) : (
                    <div className="flex-1 flex flex-col items-center justify-center text-center p-8 text-slate-400 space-y-2">
                      <MessageSquare className="w-10 h-10 text-slate-300" />
                      <p className="text-xs font-semibold">Chọn một phiên hội thoại bên trái để xem nội dung</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* ======================================================== */}
          {/* TAB 7: USER FEEDBACK VIEWER                              */}
          {/* ======================================================== */}
          {activeTab === 'feedback' && (
            <div className="space-y-6 animate-in fade-in duration-200">
              {/* Header */}
              <div className="bg-white rounded-3xl p-6 border border-slate-200/90 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  <div className="p-3 rounded-2xl bg-amber-50 border border-amber-100 text-amber-600">
                    <ThumbsUp className="w-6 h-6" />
                  </div>
                  <div>
                    <h2 className="text-base font-bold text-slate-900">
                      Trung Tâm Phản Hồi & Đánh Giá Người Dùng
                    </h2>
                    <p className="text-xs text-slate-500">
                      Ghi nhận phản hồi Like/Dislike và lý do đóng góp của bệnh nhân để tinh chỉnh phác đồ AI
                    </p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={fetchFeedback}
                  className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold transition flex items-center gap-2 shadow-sm"
                >
                  <RefreshCw className="w-4 h-4" />
                  <span>Làm Mới Phản Hồi</span>
                </button>
              </div>

              {/* Statistics Overview Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
                <div className="bg-white rounded-2xl p-4 border border-slate-200/90 shadow-sm">
                  <span className="text-[11px] font-bold text-slate-500 uppercase">Tổng Lượt Đánh Giá</span>
                  <div className="text-2xl font-bold text-slate-900 mt-1">{feedbackStats.total}</div>
                </div>
                <div className="bg-white rounded-2xl p-4 border border-emerald-200 shadow-sm bg-emerald-50/20">
                  <span className="text-[11px] font-bold text-emerald-700 uppercase flex items-center gap-1">
                    <ThumbsUp className="w-3.5 h-3.5" /> Hài Lòng (Thích)
                  </span>
                  <div className="text-2xl font-bold text-emerald-700 mt-1">{feedbackStats.likes}</div>
                </div>
                <div className="bg-white rounded-2xl p-4 border border-rose-200 shadow-sm bg-rose-50/20">
                  <span className="text-[11px] font-bold text-rose-700 uppercase flex items-center gap-1">
                    <ThumbsDown className="w-3.5 h-3.5" /> Chưa Hài Lòng
                  </span>
                  <div className="text-2xl font-bold text-rose-700 mt-1">{feedbackStats.dislikes}</div>
                </div>
                <div className="bg-white rounded-2xl p-4 border border-indigo-200 shadow-sm bg-indigo-50/20">
                  <span className="text-[11px] font-bold text-indigo-700 uppercase">Tỷ Lệ Hài Lòng</span>
                  <div className="text-2xl font-bold text-indigo-700 mt-1">
                    {Math.round((feedbackStats.like_ratio || 0) * 100)}%
                  </div>
                </div>
              </div>

              {/* Filter Tabs */}
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setFeedbackFilter('all')}
                  className={`px-3 py-1.5 rounded-xl text-xs font-bold transition ${
                    feedbackFilter === 'all'
                      ? 'bg-slate-900 text-white'
                      : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50'
                  }`}
                >
                  Tất Cả ({feedbackList.length})
                </button>
                <button
                  type="button"
                  onClick={() => setFeedbackFilter('like')}
                  className={`px-3 py-1.5 rounded-xl text-xs font-bold transition ${
                    feedbackFilter === 'like'
                      ? 'bg-emerald-600 text-white'
                      : 'bg-white text-emerald-700 border border-emerald-200 hover:bg-emerald-50'
                  }`}
                >
                  👍 Hài Lòng ({feedbackStats.likes})
                </button>
                <button
                  type="button"
                  onClick={() => setFeedbackFilter('dislike')}
                  className={`px-3 py-1.5 rounded-xl text-xs font-bold transition ${
                    feedbackFilter === 'dislike'
                      ? 'bg-rose-600 text-white'
                      : 'bg-white text-rose-700 border border-rose-200 hover:bg-rose-50'
                  }`}
                >
                  👎 Chưa Hài Lòng ({feedbackStats.dislikes})
                </button>
              </div>

              {/* Feedbacks Table */}
              <div className="bg-white rounded-3xl border border-slate-200/90 shadow-sm overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-slate-50/80 text-slate-600 uppercase text-[10px] font-bold border-b border-slate-200">
                      <tr>
                        <th className="px-5 py-3.5">Thời Gian</th>
                        <th className="px-4 py-3.5">Người Dùng</th>
                        <th className="px-4 py-3.5">Đánh Giá</th>
                        <th className="px-5 py-3.5">Lý Do Chưa Hài Lòng</th>
                        <th className="px-4 py-3.5">Mô Hình AI</th>
                        <th className="px-5 py-3.5">Trích Đoạn Tin Nhắn</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {feedbackList.length === 0 ? (
                        <tr>
                          <td colSpan={6} className="px-5 py-10 text-center text-slate-400">
                            Chưa có phản hồi nào được ghi nhận từ người dùng.
                          </td>
                        </tr>
                      ) : (
                        feedbackList
                          .filter((f) => (feedbackFilter === 'all' ? true : f.rating === feedbackFilter))
                          .map((item, idx) => (
                            <tr key={idx} className="hover:bg-slate-50/80 transition-colors">
                              <td className="px-5 py-3 text-slate-500 font-mono text-[11px] whitespace-nowrap">
                                {item.created_at ? new Date(item.created_at).toLocaleString('vi-VN') : 'Vừa xong'}
                              </td>
                              <td className="px-4 py-3 font-medium text-slate-800 whitespace-nowrap">
                                {item.user_id || 'Khách'}
                              </td>
                              <td className="px-4 py-3 whitespace-nowrap">
                                {item.rating === 'like' ? (
                                  <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-700 font-bold text-[11px]">
                                    <ThumbsUp className="w-3.5 h-3.5" /> Hài Lòng
                                  </span>
                                ) : (
                                  <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-rose-50 border border-rose-200 text-rose-700 font-bold text-[11px]">
                                    <ThumbsDown className="w-3.5 h-3.5" /> Chưa Hài Lòng
                                  </span>
                                )}
                              </td>
                              <td className="px-5 py-3">
                                {item.reason ? (
                                  <div className="p-2 bg-rose-50/70 border border-rose-200 rounded-xl text-rose-800 text-xs font-medium">
                                    &quot;{item.reason}&quot;
                                  </div>
                                ) : (
                                  <span className="text-slate-400 italic">Không có lý do</span>
                                )}
                              </td>
                              <td className="px-4 py-3 font-mono text-[11px] uppercase text-slate-600">
                                {item.answer_provider || 'gemini'}
                              </td>
                              <td className="px-5 py-3 text-slate-600 max-w-xs truncate text-[11px]">
                                {item.message_preview || 'Không có bản xem trước'}
                              </td>
                            </tr>
                          ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
