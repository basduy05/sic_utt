'use client';

import React, { useState } from 'react';
import {
  X,
  FileText,
  Printer,
  Copy,
  Check,
  Building2,
  Calendar,
  User,
  Activity,
  AlertTriangle,
  Stethoscope,
  Sparkles,
  Download,
  ShieldCheck,
  Award,
  Save,
} from 'lucide-react';
import { ModalPortal } from '../common/ModalPortal';
import { renderRichMarkdown } from '../../utils/markdownRenderer';

interface MedicalRecordModalProps {
  isOpen: boolean;
  onClose: () => void;
  medicalRecordText: string;
  isGenerating: boolean;
  sessionId: string;
  onSaveRecord?: () => void;
}

export const MedicalRecordModal: React.FC<MedicalRecordModalProps> = ({
  isOpen,
  onClose,
  medicalRecordText,
  isGenerating,
  sessionId,
  onSaveRecord,
}) => {
  const [copied, setCopied] = useState(false);

  if (!isOpen) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(medicalRecordText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handlePrintPDF = () => {
    const printWindow = window.open('', '_blank');
    if (!printWindow) return;

    const todayStr = new Date().toLocaleDateString('vi-VN', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });

    // Format markdown text to clean HTML for executive PDF print
    const cleanHtml = medicalRecordText
      .replace(/^# (.*$)/gim, '<h1 class="main-title">$1</h1>')
      .replace(/^## (.*$)/gim, '<h2 class="section-title">$1</h2>')
      .replace(/^### (.*$)/gim, '<h3 class="sub-title">$1</h3>')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/`([^`]+)`/g, '<span class="icd-tag">$1</span>')
      .replace(/^- (.*$)/gim, '<li>$1</li>')
      .replace(/\n\n/g, '<p></p>')
      .replace(/\n/g, '<br/>');

    printWindow.document.write(`
      <!DOCTYPE html>
      <html lang="vi">
      <head>
        <meta charset="UTF-8" />
        <title>Benh_An_Dien_Tu_${sessionId}.pdf</title>
        <style>
          @page {
            size: A4;
            margin: 18mm 15mm 18mm 15mm;
          }
          * {
            box-sizing: border-box;
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
          }
          body {
            font-family: 'Times New Roman', 'Segoe UI', serif;
            color: #0f172a;
            line-height: 1.5;
            font-size: 13pt;
            background: #fff;
            margin: 0;
            padding: 0;
          }
          .header-table {
            width: 100%;
            border-bottom: 2px solid #0f766e;
            padding-bottom: 12px;
            margin-bottom: 18px;
          }
          .header-left {
            text-align: left;
            vertical-align: top;
            width: 55%;
          }
          .header-right {
            text-align: center;
            vertical-align: top;
            width: 45%;
          }
          .org-name {
            font-size: 11pt;
            font-weight: bold;
            text-transform: uppercase;
            color: #0f766e;
          }
          .hospital-name {
            font-size: 13pt;
            font-weight: bold;
            color: #0f172a;
            margin-top: 2px;
          }
          .motto-top {
            font-size: 10.5pt;
            font-weight: bold;
            text-transform: uppercase;
          }
          .motto-sub {
            font-size: 11pt;
            font-weight: bold;
            border-bottom: 1px solid #334155;
            display: inline-block;
            padding-bottom: 2px;
          }
          .doc-title {
            text-align: center;
            font-size: 16pt;
            font-weight: bold;
            color: #0f766e;
            text-transform: uppercase;
            margin: 15px 0 6px 0;
            letter-spacing: 0.5px;
          }
          .meta-box {
            background: #f8fafc;
            border: 1px solid #cbd5e1;
            border-radius: 6px;
            padding: 8px 12px;
            margin-bottom: 16px;
            font-size: 10.5pt;
            display: flex;
            justify-content: space-between;
          }
          .section-title {
            color: #0f766e;
            font-size: 12.5pt;
            font-weight: bold;
            text-transform: uppercase;
            border-left: 4px solid #0f766e;
            padding-left: 8px;
            margin-top: 16px;
            margin-bottom: 6px;
            background: #f0fdfa;
            padding-top: 3px;
            padding-bottom: 3px;
          }
          .sub-title {
            color: #1e293b;
            font-size: 11.5pt;
            font-weight: bold;
            margin-top: 10px;
            margin-bottom: 4px;
          }
          .icd-tag {
            background: #e0f2fe;
            color: #0369a1;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Consolas', monospace;
            font-weight: bold;
            font-size: 10.5pt;
            border: 1px solid #bae6fd;
          }
          ul {
            margin: 4px 0 8px 0;
            padding-left: 20px;
          }
          li {
            margin-bottom: 4px;
          }
          .signature-table {
            width: 100%;
            margin-top: 30px;
            page-break-inside: avoid;
          }
          .sig-col {
            text-align: center;
            vertical-align: top;
            width: 50%;
            font-size: 11pt;
          }
          .sig-title {
            font-weight: bold;
            text-transform: uppercase;
            margin-bottom: 4px;
          }
          .sig-sub {
            font-style: italic;
            font-size: 10pt;
            color: #64748b;
          }
          .stamp-box {
            display: inline-block;
            border: 2px dashed #0f766e;
            color: #0f766e;
            padding: 6px 14px;
            border-radius: 8px;
            font-weight: bold;
            font-size: 10pt;
            margin-top: 15px;
            text-transform: uppercase;
          }
          .footer-note {
            margin-top: 25px;
            border-top: 1px solid #e2e8f0;
            padding-top: 8px;
            font-size: 9pt;
            color: #64748b;
            text-align: center;
            font-style: italic;
          }
        </style>
      </head>
      <body>
        <table class="header-table">
          <tr>
            <td class="header-left">
              <div class="org-name">BỘ Y TẾ VIỆT NAM</div>
              <div class="hospital-name">HỆ THỐNG TRỢ LÝ Y TẾ AI (MEDIBOT)</div>
              <div style="font-size: 9.5pt; color: #64748b;">Mã Bệnh Án: ${sessionId}</div>
            </td>
            <td class="header-right">
              <div class="motto-top">CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM</div>
              <div class="motto-sub">Độc lập - Tự do - Hạnh phúc</div>
              <div style="font-size: 9.5pt; color: #64748b; margin-top: 4px;">Thời gian lập: ${todayStr}</div>
            </td>
          </tr>
        </table>

        <div class="doc-title">HỒ SƠ BỆNH ÁN NGOẠI TRÚ ĐIỆN TỬ</div>

        <div class="meta-box">
          <div><strong>Mã phiên khám:</strong> ${sessionId}</div>
          <div><strong>Chuẩn phân loại:</strong> ICD-10 & Phác Đồ Bộ Y Tế</div>
          <div><strong>Trạng thái:</strong> Đã Hội Chẩn Tự Động</div>
        </div>

        <div class="record-body">
          ${cleanHtml}
        </div>

        <table class="signature-table">
          <tr>
            <td class="sig-col">
              <div class="sig-title">HỆ THỐNG PHÂN TẦNG MEDIBOT AI</div>
              <div class="sig-sub">(Xác thực dữ liệu điện tử)</div>
              <div class="stamp-box">✓ VERIFIED BY MEDIBOT AI</div>
              <div style="margin-top: 45px; font-weight: bold;">Hội Đồng AI Triage Chuẩn Quốc Gia</div>
            </td>
            <td class="sig-col">
              <div class="sig-title">BÁC SĨ / HỘI ĐỒNG CHUYÊN MÔN</div>
              <div class="sig-sub">(Ký, ghi rõ họ tên và đóng dấu)</div>
              <div style="height: 65px;"></div>
              <div style="font-weight: bold;">TS. BS. Nguyễn Văn An</div>
            </td>
          </tr>
        </table>

        <div class="footer-note">
          Hồ sơ bệnh án điện tử này được trích xuất tự động từ phiên khám đa phương thức theo tiêu chuẩn dữ liệu y tế ICD-10 Bộ Y Tế.
        </div>
      </body>
      </html>
    `);

    printWindow.document.close();
    setTimeout(() => {
      printWindow.print();
    }, 400);
  };

  return (
    <ModalPortal>
      <div className="fixed inset-0 z-[9999] w-screen h-screen min-h-screen min-w-full bg-slate-900/60 backdrop-blur-md flex items-center justify-center p-3 md:p-6 overflow-y-auto">
        <div className="bg-white rounded-[2rem] max-w-4xl w-full max-h-[92vh] shadow-2xl border border-slate-200/80 flex flex-col overflow-hidden my-auto">
        {/* Executive Hospital Header Banner */}
        <div className="bg-gradient-to-r from-teal-700 via-teal-800 to-indigo-900 text-white p-5 md:p-6 flex-shrink-0 flex items-center justify-between border-b border-teal-600/50 shadow-md">
          <div className="flex items-center space-x-3.5">
            <div className="w-12 h-12 rounded-2xl bg-white/10 backdrop-blur-md border border-white/20 flex items-center justify-center text-white shadow-inner">
              <Building2 className="w-6 h-6 text-teal-200" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-[10px] uppercase tracking-widest font-bold px-2 py-0.5 rounded-full bg-teal-400/20 text-teal-200 border border-teal-300/30">
                  Chuẩn Bộ Y Tế Việt Nam
                </span>
                <span className="text-xs text-teal-200/80">• ICD-10 Standardized</span>
              </div>
              <h2 className="text-base md:text-lg font-extrabold text-white tracking-tight mt-0.5">
                HỒ SƠ BỆNH ÁN NGOẠI TRÚ ĐIỆN TỬ
              </h2>
              <p className="text-[11px] text-teal-100/70 font-mono">
                MÃ PHIÊN KHÁM: <span className="text-teal-200 font-bold">{sessionId}</span>
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-2 rounded-full bg-white/10 hover:bg-white/20 text-white transition hover:scale-105"
            title="Đóng cửa sổ"
          >
            <X size={20} />
          </button>
        </div>

        {/* Clinical Document Preview Area */}
        <div className="flex-1 overflow-y-auto custom-scrollbar p-5 md:p-8 bg-slate-50/70">
          {isGenerating ? (
            <div className="py-24 text-center text-slate-500 flex flex-col items-center justify-center space-y-4">
              <div className="relative">
                <div className="w-14 h-14 rounded-full border-4 border-teal-200 border-t-teal-600 animate-spin" />
                <Stethoscope className="w-6 h-6 text-teal-600 absolute inset-0 m-auto" />
              </div>
              <div className="space-y-1">
                <h4 className="font-bold text-slate-800 text-sm md:text-base">
                  Bác sĩ AI đang tổng hợp toàn bộ diễn biến lâm sàng...
                </h4>
                <p className="text-xs text-slate-500">
                  Đang bóc tách đa bệnh lý, đồng bộ mã ICD-10 và tra cứu phác đồ điều trị Bộ Y Tế.
                </p>
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-2xl p-6 md:p-8 shadow-sm border border-slate-200/80 space-y-6">
              {/* Official Vietnam National Header Box */}
              <div className="border-b-2 border-slate-200 pb-4 flex flex-col sm:flex-row items-center justify-between gap-3 text-center sm:text-left">
                <div>
                  <div className="text-[11px] font-bold text-teal-800 uppercase tracking-wider">BỘ Y TẾ VIỆT NAM</div>
                  <div className="text-xs font-bold text-slate-900">TRUNG TÂM KHÁM BỆNH ĐA PHƯƠNG THỨC MEDIBOT</div>
                </div>
                <div className="text-center">
                  <div className="text-[11px] font-bold text-slate-800 uppercase">CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM</div>
                  <div className="text-[11px] font-semibold text-slate-600 border-b border-slate-400 inline-block pb-0.5">
                    Độc lập - Tự do - Hạnh phúc
                  </div>
                </div>
              </div>

              {/* Rendered Medical Record Content with Rich Markdown */}
              <div className="text-slate-800 space-y-3 leading-relaxed">
                {renderRichMarkdown(medicalRecordText, true)}
              </div>

              {/* Official Doctor Signature & Stamp Box */}
              <div className="border-t border-slate-200 pt-6 grid grid-cols-1 sm:grid-cols-2 gap-6 text-center">
                <div className="space-y-2">
                  <div className="text-xs font-bold text-slate-700 uppercase">Xác Thực AI Triage Bộ Y Tế</div>
                  <div className="inline-flex items-center space-x-1.5 px-3 py-1 bg-teal-50 border border-teal-200 rounded-full text-teal-800 text-[11px] font-bold">
                    <ShieldCheck size={14} className="text-teal-600" />
                    <span>MEDIBOT AI VERIFIED</span>
                  </div>
                  <div className="text-[11px] text-slate-400 pt-8 font-semibold">
                    Hệ Thống Trí Tuệ Nhân Tạo Y Tế Quốc Gia
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="text-xs font-bold text-slate-700 uppercase">Bác Sĩ Phụ Trách Hội Chẩn</div>
                  <div className="text-[11px] text-slate-400 italic">(Ký điện tử và đóng dấu)</div>
                  <div className="h-10 flex items-center justify-center">
                    <span className="font-serif italic text-teal-900 text-lg">Nguyễn Văn An</span>
                  </div>
                  <div className="text-xs font-bold text-slate-800">TS. BS. Nguyễn Văn An</div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Modal Bottom Actions Bar */}
        <div className="p-4 md:px-6 bg-white border-t border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-3 flex-shrink-0">
          <div className="flex items-center space-x-2 text-xs text-slate-500">
            <Award className="w-4 h-4 text-teal-600" />
            <span>Bản quyền dữ liệu y tế thuộc Bộ Y Tế & Hệ thống MediBot AI</span>
          </div>

          <div className="flex items-center space-x-2.5 w-full sm:w-auto justify-end">
            <button
              type="button"
              onClick={handleCopy}
              disabled={isGenerating}
              className="flex-1 sm:flex-none px-4 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-bold transition flex items-center justify-center space-x-1.5"
            >
              {copied ? <Check size={15} className="text-emerald-600" /> : <Copy size={15} />}
              <span>{copied ? 'Đã Sao Chép!' : 'Sao Chép Bệnh Án'}</span>
            </button>

            {onSaveRecord && (
              <button
                type="button"
                onClick={onSaveRecord}
                disabled={isGenerating}
                className="flex-1 sm:flex-none px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold shadow-md shadow-blue-600/20 transition flex items-center justify-center space-x-1.5 active:scale-95"
              >
                <Save size={15} />
                <span>Lưu Vào Hồ Sơ Bệnh Án</span>
              </button>
            )}

            <button
              type="button"
              onClick={handlePrintPDF}
              disabled={isGenerating}
              className="flex-1 sm:flex-none px-5 py-2.5 bg-gradient-to-r from-teal-600 to-indigo-600 hover:from-teal-700 hover:to-indigo-700 text-white rounded-xl text-xs font-bold shadow-md shadow-teal-600/20 transition flex items-center justify-center space-x-2 hover:scale-105 active:scale-95"
            >
              <Printer size={16} />
              <span>In & Tải PDF Bệnh Án</span>
            </button>
          </div>
        </div>
      </div>
    </div>
    </ModalPortal>
  );
};
