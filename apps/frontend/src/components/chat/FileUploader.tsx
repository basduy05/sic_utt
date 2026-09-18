'use client';

import React, { useState } from 'react';
import {
  UploadCloud,
  FileText,
  Image as ImageIcon,
  ZoomIn,
  ZoomOut,
  RotateCw,
  CheckCircle2,
  Loader2,
  X,
  Plus,
  AlertCircle,
  FileCheck2,
  Activity,
  Edit3,
  ArrowRight,
  Sparkles,
  ChevronLeft,
  ChevronRight,
  Eye,
  Table
} from 'lucide-react';
import { ModalPortal } from '../common/ModalPortal';
import { medicalService } from '../../services/medicalService';
import { OCRResult } from '../../types/medical';

interface FileUploaderProps {
  onOCRComplete: (ocrResult: OCRResult, fileName: string) => void;
  onClose: () => void;
}

export const FileUploader: React.FC<FileUploaderProps> = ({ onOCRComplete, onClose }) => {
  const [files, setFiles] = useState<File[]>([]);
  const [activePreviewIndex, setActivePreviewIndex] = useState<number>(0);
  const [previewUrls, setPreviewUrls] = useState<string[]>([]);
  const [zoomLevel, setZoomLevel] = useState<number>(1);
  const [rotation, setRotation] = useState<number>(0);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Review step state
  const [step, setStep] = useState<'upload' | 'review'>('upload');
  const [ocrData, setOcrData] = useState<OCRResult | null>(null);
  const [editableIndicators, setEditableIndicators] = useState<Record<string, { value: number; unit?: string; status?: string; message?: string }>>({});

  // Quick-input additions
  const [customKey, setCustomKey] = useState<string>('WBC');
  const [customValue, setCustomValue] = useState<string>('');

  const handleFilesChange = (newFileList: FileList | null) => {
    if (!newFileList || newFileList.length === 0) return;
    setErrorMessage(null);
    const addedFiles = Array.from(newFileList);
    const updatedFiles = [...files, ...addedFiles];
    setFiles(updatedFiles);

    const updatedUrls = updatedFiles.map((f) =>
      f.type.startsWith('image/') ? URL.createObjectURL(f) : ''
    );
    setPreviewUrls(updatedUrls);
  };

  const handleRemoveFile = (index: number) => {
    const updatedFiles = files.filter((_, i) => i !== index);
    const updatedUrls = previewUrls.filter((_, i) => i !== index);
    setFiles(updatedFiles);
    setPreviewUrls(updatedUrls);
    if (activePreviewIndex >= updatedFiles.length) {
      setActivePreviewIndex(Math.max(0, updatedFiles.length - 1));
    }
  };

  const handleUploadAndAnalyze = async () => {
    if (files.length === 0) return;
    setIsProcessing(true);
    setErrorMessage(null);
    try {
      const res = await medicalService.uploadAndAnalyzeLabDocument(files);
      setOcrData(res);
      setEditableIndicators(res.parsed_indicators || {});
      setStep('review');
    } catch (err: any) {
      console.error('Error in Multi-file OCR Analysis:', err);
      setErrorMessage(err?.message || 'Không thể xử lý tệp xét nghiệm. Vui lòng thử lại.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleAddCustomIndicator = () => {
    if (!customKey || !customValue) return;
    const num = parseFloat(customValue.replace(',', '.'));
    if (isNaN(num)) return;

    let defaultUnit = '10^9/L';
    if (customKey === 'PLT') defaultUnit = '10^9/L';
    else if (customKey === 'RBC') defaultUnit = '10^12/L';
    else if (customKey === 'GLUCOSE') defaultUnit = 'mmol/L';
    else if (customKey === 'AST' || customKey === 'ALT') defaultUnit = 'U/L';
    else if (customKey === 'CREATININE') defaultUnit = 'umol/L';

    setEditableIndicators((prev) => ({
      ...prev,
      [customKey]: {
        value: num,
        unit: defaultUnit,
        status: 'MANUAL_ENTRY',
        message: 'Chỉ số do người bệnh nhập bổ sung'
      }
    }));
    setCustomValue('');
  };

  const handleRemoveIndicator = (key: string) => {
    setEditableIndicators((prev) => {
      const updated = { ...prev };
      delete updated[key];
      return updated;
    });
  };

  const handleConfirmAndSend = () => {
    const finalResult: OCRResult = {
      parsed_indicators: editableIndicators,
      critical_flags: ocrData?.critical_flags || [],
      total_indicators_found: Object.keys(editableIndicators).length,
      raw_text: ocrData?.raw_text || ''
    };
    const fileNames = files.map((f) => f.name).join(', ');
    onOCRComplete(finalResult, fileNames);
    onClose();
  };

  const currentActiveUrl = previewUrls[activePreviewIndex];

  return (
    <ModalPortal>
      <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-md z-[9999] w-screen h-screen min-h-screen min-w-full flex items-center justify-center p-4 overflow-y-auto">
        <div className="bg-white rounded-[2rem] max-w-xl w-full p-6 shadow-2xl border border-slate-100 flex flex-col max-h-[90vh] my-auto">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-100 flex-shrink-0">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-teal-100 text-teal-700 rounded-2xl">
              <FileCheck2 className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-slate-800 text-lg">
                {step === 'upload' ? 'Tải Lên Phiếu Xét Nghiệm Máu (OCR)' : 'Kết Quả Bóc Tách Chỉ Số'}
              </h3>
              <p className="text-xs text-slate-500">
                {step === 'upload'
                  ? 'Hỗ trợ tải đồng thời nhiều ảnh (PNG, JPG) hoặc tài liệu PDF'
                  : 'Kiểm tra và xác nhận các chỉ số xét nghiệm trước khi gửi'}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 p-2 rounded-full hover:bg-slate-100 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Area */}
        <div className="mt-4 space-y-4 overflow-y-auto custom-scrollbar flex-1 pr-1">
          {step === 'upload' ? (
            <>
              {/* Dropzone */}
              <label className="border-2 border-dashed border-teal-300 hover:border-teal-500 bg-teal-50/40 hover:bg-teal-50/80 rounded-2xl p-6 flex flex-col items-center justify-center cursor-pointer transition text-center group">
                <UploadCloud className="w-10 h-10 text-teal-600 mb-2 group-hover:scale-110 transition-transform" />
                <p className="text-sm font-semibold text-slate-700">Kéo thả hoặc bấm để chọn tệp xét nghiệm</p>
                <p className="text-xs text-slate-400 mt-1">Hỗ trợ: PDF, JPG, PNG, WebP (Có thể chọn nhiều tệp cùng lúc)</p>
                <input
                  type="file"
                  multiple
                  accept=".pdf,image/*"
                  onChange={(e) => handleFilesChange(e.target.files)}
                  className="hidden"
                />
              </label>

              {/* Files List Gallery */}
              {files.length > 0 && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                      Danh sách tệp đính kèm ({files.length}):
                    </span>
                    <label className="text-xs text-teal-600 hover:text-teal-800 font-semibold cursor-pointer flex items-center gap-1">
                      <Plus size={14} /> Thêm tệp
                      <input
                        type="file"
                        multiple
                        accept=".pdf,image/*"
                        onChange={(e) => handleFilesChange(e.target.files)}
                        className="hidden"
                      />
                    </label>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {files.map((f, idx) => (
                      <div
                        key={idx}
                        onClick={() => setActivePreviewIndex(idx)}
                        className={`flex items-center justify-between p-2.5 rounded-xl border text-xs cursor-pointer transition ${
                          activePreviewIndex === idx
                            ? 'border-teal-500 bg-teal-50/80 shadow-xs'
                            : 'border-slate-200 bg-slate-50/70 hover:bg-slate-100'
                        }`}
                      >
                        <div className="flex items-center space-x-2 truncate">
                          {f.type.startsWith('image/') ? (
                            <ImageIcon className="w-4 h-4 text-blue-600 flex-shrink-0" />
                          ) : (
                            <FileText className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                          )}
                          <div className="truncate">
                            <p className="font-semibold text-slate-800 truncate">{f.name}</p>
                            <p className="text-[10px] text-slate-400">{(f.size / 1024).toFixed(1)} KB</p>
                          </div>
                        </div>
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleRemoveFile(idx);
                          }}
                          className="text-slate-400 hover:text-red-500 p-1 rounded-md transition"
                          title="Xóa tệp"
                        >
                          <X size={14} />
                        </button>
                      </div>
                    ))}
                  </div>

                  {/* Active Image Previewer */}
                  {currentActiveUrl && (
                    <div className="relative bg-slate-900 rounded-2xl overflow-hidden h-44 flex items-center justify-center border border-slate-700">
                      <img
                        src={currentActiveUrl}
                        alt="Lab Result Preview"
                        style={{ transform: `scale(${zoomLevel}) rotate(${rotation}deg)` }}
                        className="max-h-full max-w-full object-contain transition-transform duration-200"
                      />
                      <div className="absolute bottom-2 right-2 flex items-center space-x-1 bg-black/70 backdrop-blur-md rounded-lg p-1 text-white">
                        <button
                          onClick={() => setZoomLevel((z) => Math.max(0.5, z - 0.2))}
                          className="p-1 hover:bg-white/20 rounded"
                          title="Thu nhỏ"
                        >
                          <ZoomOut className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => setZoomLevel((z) => Math.min(2.5, z + 0.2))}
                          className="p-1 hover:bg-white/20 rounded"
                          title="Phóng to"
                        >
                          <ZoomIn className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => setRotation((r) => (r + 90) % 360)}
                          className="p-1 hover:bg-white/20 rounded"
                          title="Xoay ảnh"
                        >
                          <RotateCw className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {errorMessage && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700 flex items-center gap-2">
                  <AlertCircle size={16} className="text-red-500 flex-shrink-0" />
                  <span>{errorMessage}</span>
                </div>
              )}
            </>
          ) : (
            /* Review & Verification Step */
            <div className="space-y-4">
              {Object.keys(editableIndicators).length > 0 ? (
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-teal-800 uppercase tracking-wider flex items-center gap-1.5">
                      <Sparkles size={14} className="text-amber-500" />
                      Đã bóc tách được ({Object.keys(editableIndicators).length}) chỉ số:
                    </span>
                    <span className="text-[11px] text-slate-400">Có thể xóa hoặc bổ sung bên dưới</span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {Object.entries(editableIndicators).map(([key, data]) => {
                      const isAbnormal = data.status && data.status !== 'NORMAL';
                      return (
                        <div
                          key={key}
                          className={`p-3 rounded-2xl border flex items-center justify-between text-xs transition ${
                            isAbnormal
                              ? 'bg-amber-50/80 border-amber-300 text-amber-900'
                              : 'bg-emerald-50/80 border-emerald-300 text-emerald-900'
                          }`}
                        >
                          <div>
                            <div className="flex items-center space-x-1.5 font-bold">
                              <span>{key}:</span>
                              <span className="text-sm font-extrabold">{data.value}</span>
                              <span className="text-[10px] opacity-75">{data.unit}</span>
                            </div>
                            <p className="text-[10px] text-slate-500 mt-0.5">{data.message || 'Chỉ số xét nghiệm'}</p>
                          </div>
                          <button
                            type="button"
                            onClick={() => handleRemoveIndicator(key)}
                            className="text-slate-400 hover:text-red-500 p-1 rounded-md transition"
                            title="Xóa chỉ số này"
                          >
                            <X size={14} />
                          </button>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ) : (
                <div className="p-4 bg-amber-50/80 border border-amber-200 rounded-2xl text-xs text-amber-900 space-y-2">
                  <div className="flex items-center space-x-2 font-bold text-amber-800">
                    <AlertCircle size={16} className="text-amber-600 flex-shrink-0" />
                    <span>Chưa tự động nhận diện được bảng chỉ số chuẩn từ ảnh/tệp này</span>
                  </div>
                  <p className="text-slate-600 leading-relaxed">
                    Ảnh có thể bị mờ, góc chụp nghiêng hoặc là ảnh đơn thuốc/siêu âm. Bạn có thể nhập nhanh các chỉ số quan trọng bên dưới hoặc gửi trực tiếp để Bác sĩ AI hỗ trợ!
                  </p>
                </div>
              )}

              {/* Quick Input Helper */}
              <div className="bg-slate-50 border border-slate-200 p-3.5 rounded-2xl space-y-2.5">
                <span className="text-xs font-bold text-slate-700 flex items-center gap-1.5">
                  <Edit3 size={13} className="text-teal-600" />
                  Nhập nhanh chỉ số bổ sung:
                </span>
                <div className="flex items-center space-x-2">
                  <select
                    value={customKey}
                    onChange={(e) => setCustomKey(e.target.value)}
                    className="p-2 bg-white border border-slate-300 rounded-xl text-xs font-semibold text-slate-800 focus:outline-none focus:ring-2 focus:ring-teal-400"
                  >
                    <option value="WBC">Bạch cầu (WBC)</option>
                    <option value="PLT">Tiểu cầu (PLT)</option>
                    <option value="GLUCOSE">Đường huyết (Glucose)</option>
                    <option value="AST">Men gan (AST/SGOT)</option>
                    <option value="ALT">Men gan (ALT/SGPT)</option>
                    <option value="RBC">Hồng cầu (RBC)</option>
                    <option value="HGB">Huyết sắc tố (HGB)</option>
                    <option value="CREATININE">Creatinine</option>
                    <option value="UREA">Ure máu</option>
                  </select>

                  <input
                    type="text"
                    placeholder="Giá trị (VD: 12.5)"
                    value={customValue}
                    onChange={(e) => setCustomValue(e.target.value)}
                    className="flex-1 p-2 bg-white border border-slate-300 rounded-xl text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-teal-400"
                  />

                  <button
                    type="button"
                    onClick={handleAddCustomIndicator}
                    className="px-3 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-xl text-xs font-bold transition flex items-center gap-1"
                  >
                    <Plus size={14} /> Thêm
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer Action */}
        <div className="pt-4 border-t border-slate-100 flex-shrink-0 flex items-center space-x-3">
          {step === 'review' && (
            <button
              type="button"
              onClick={() => setStep('upload')}
              className="px-4 py-3 rounded-2xl border border-slate-200 text-xs font-semibold text-slate-600 hover:bg-slate-100 transition"
            >
              Chọn lại tệp
            </button>
          )}

          {step === 'upload' ? (
            <button
              type="button"
              onClick={handleUploadAndAnalyze}
              disabled={isProcessing || files.length === 0}
              className={`flex-1 font-bold py-3.5 rounded-2xl shadow-md flex items-center justify-center space-x-2 transition ${
                files.length > 0 && !isProcessing
                  ? 'bg-gradient-to-r from-teal-600 to-blue-600 hover:from-teal-700 hover:to-blue-700 text-white shadow-teal-600/20'
                  : 'bg-slate-200 text-slate-400 cursor-not-allowed shadow-none'
              }`}
            >
              {isProcessing ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>Đang bóc tách & phân tích OCR ({files.length} tệp)...</span>
                </>
              ) : (
                <>
                  <CheckCircle2 className="w-5 h-5" />
                  <span>Xác nhận & Bóc tách chỉ số ({files.length} tệp)</span>
                </>
              )}
            </button>
          ) : (
            <button
              type="button"
              onClick={handleConfirmAndSend}
              className="flex-1 font-bold py-3.5 rounded-2xl bg-gradient-to-r from-teal-600 to-blue-600 hover:from-teal-700 hover:to-blue-700 text-white shadow-md shadow-teal-600/20 flex items-center justify-center space-x-2 transition"
            >
              <span>Gửi Kết Quả Vào Cuộc Khám</span>
              <ArrowRight className="w-5 h-5" />
            </button>
          )}
        </div>
      </div>
    </div>
    </ModalPortal>
  );
};
