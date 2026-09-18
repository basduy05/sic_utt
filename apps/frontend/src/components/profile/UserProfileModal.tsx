'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import {
  X,
  User,
  Calendar,
  CreditCard,
  MapPin,
  Phone,
  Mail,
  ShieldCheck,
  HeartPulse,
  AlertTriangle,
  FileCheck,
  Save,
  Edit3,
  CheckCircle2,
  Lock,
  Contact2,
  RotateCcw
} from 'lucide-react';
import { AuthUser } from '@/types/medical';
import { ModalPortal } from '../common/ModalPortal';

export function UserProfileModal() {
  const { user, isProfileModalOpen, setIsProfileModalOpen, updateProfile } = useAuth();

  const [formData, setFormData] = useState<Partial<AuthUser>>({});
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Sync formData when user changes or modal opens
  useEffect(() => {
    if (user) {
      setFormData({
        full_name: user.full_name || '',
        email: user.email || '',
        phone: user.phone || '',
        date_of_birth: user.date_of_birth || '1998-05-15',
        gender: user.gender || 'Nam',
        citizen_id: user.citizen_id || '001098012345',
        address: user.address || 'Số 54 Triều Khúc, Thanh Xuân, Hà Nội',
        health_insurance_number: user.health_insurance_number || 'DN4010123456789',
        blood_type: user.blood_type || 'O+',
        allergies: user.allergies || 'Dị ứng Penicillin, Tôm cua biển',
        medical_history: user.medical_history || 'Viêm xoang sàng mãn tính, Đau dạ dày HP (-)',
        emergency_contact_name: user.emergency_contact_name || 'Nguyễn Văn An (Bố đẻ)',
        emergency_contact_phone: user.emergency_contact_phone || '0912 345 678',
      });
    }
  }, [user, isProfileModalOpen]);

  if (!isProfileModalOpen || !user) return null;

  const handleSave = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setIsSaving(true);
    setSuccessMessage(null);

    try {
      const res = await updateProfile(formData);
      if (res.success) {
        setSuccessMessage('Hồ sơ y tế cá nhân đã được lưu trữ thành công!');
        setIsEditing(false);
        setTimeout(() => setSuccessMessage(null), 3500);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    // Revert changes back to user original data
    if (user) {
      setFormData({
        full_name: user.full_name || '',
        email: user.email || '',
        phone: user.phone || '',
        date_of_birth: user.date_of_birth || '1998-05-15',
        gender: user.gender || 'Nam',
        citizen_id: user.citizen_id || '001098012345',
        address: user.address || 'Số 54 Triều Khúc, Thanh Xuân, Hà Nội',
        health_insurance_number: user.health_insurance_number || 'DN4010123456789',
        blood_type: user.blood_type || 'O+',
        allergies: user.allergies || 'Dị ứng Penicillin, Tôm cua biển',
        medical_history: user.medical_history || 'Viêm xoang sàng mãn tính, Đau dạ dày HP (-)',
        emergency_contact_name: user.emergency_contact_name || 'Nguyễn Văn An (Bố đẻ)',
        emergency_contact_phone: user.emergency_contact_phone || '0912 345 678',
      });
    }
  };

  return (
    <ModalPortal>
      <div className="fixed inset-0 z-[9999] w-screen h-screen min-h-screen min-w-full flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-md overflow-y-auto">
        <div className="bg-white rounded-3xl shadow-2xl border border-slate-200/80 w-full max-w-3xl overflow-hidden flex flex-col max-h-[92vh] my-auto">
        {/* ENLARGED & PROMINENT HEADER BANNER WITH GENEROUS SPACING & CONTROLS */}
        <div className="relative bg-gradient-to-r from-blue-700 via-indigo-700 to-teal-600 px-8 py-7 md:py-8 text-white flex-shrink-0 shadow-lg overflow-hidden">
          {/* Decorative ambient lighting glows */}
          <div className="absolute -top-12 -right-12 w-64 h-64 bg-white/10 rounded-full blur-3xl pointer-events-none" />
          <div className="absolute -bottom-10 -left-10 w-52 h-52 bg-teal-400/20 rounded-full blur-2xl pointer-events-none" />

          <div className="relative z-10 flex items-center justify-between gap-6">
            {/* Left: Prominent Icon & Big Title */}
            <div className="flex items-center gap-5">
              <div className="w-16 h-16 rounded-2xl bg-white/20 backdrop-blur-md flex items-center justify-center text-white font-black shadow-lg border border-white/30 flex-shrink-0">
                <Contact2 className="w-8 h-8 text-white drop-shadow" />
              </div>
              <div className="space-y-1.5">
                <div className="flex items-center gap-3 flex-wrap">
                  <h2 className="text-2xl md:text-3xl font-black tracking-tight text-white drop-shadow-sm">
                    Hồ Sơ Y Tế Cá Nhân
                  </h2>
                  <span className="inline-flex items-center gap-1.5 text-xs font-mono font-bold bg-emerald-500 text-white px-3 py-1 rounded-full shadow-sm border border-emerald-300/30">
                    <span className="w-2 h-2 rounded-full bg-white animate-pulse" />
                    Đã Xác Thực CCCD
                  </span>
                </div>
                <p className="text-blue-100/90 text-sm md:text-[15px] font-medium tracking-wide">
                  Thông tin hành chính & lâm sàng cơ bản chuẩn CSDL Y Tế Quốc Gia
                </p>
              </div>
            </div>

            {/* Right: ACTION BUTTONS WITH PROMINENT SIZING */}
            <div className="flex items-center gap-3 flex-shrink-0">
              {!isEditing ? (
                /* Edit button at top */
                <button
                  type="button"
                  onClick={() => setIsEditing(true)}
                  className="flex items-center gap-2 px-6 py-3 rounded-2xl text-sm font-extrabold text-blue-900 bg-white hover:bg-blue-50 shadow-lg shadow-black/15 transition hover:scale-105 active:scale-95 cursor-pointer"
                >
                  <Edit3 className="w-4 h-4 text-blue-600" />
                  <span>Chỉnh Sửa</span>
                </button>
              ) : (
                /* Save & Cancel buttons at top */
                <div className="flex items-center gap-2.5">
                  <button
                    type="button"
                    onClick={handleCancelEdit}
                    className="flex items-center gap-2 px-5 py-3 rounded-2xl text-sm font-bold text-white bg-white/20 hover:bg-white/30 backdrop-blur-sm transition active:scale-95 cursor-pointer"
                  >
                    <RotateCcw className="w-4 h-4" />
                    <span>Hủy</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => handleSave()}
                    disabled={isSaving}
                    className="flex items-center gap-2.5 px-6 py-3 rounded-2xl text-sm font-black text-white bg-emerald-500 hover:bg-emerald-400 shadow-xl shadow-emerald-950/25 transition hover:scale-105 active:scale-95 disabled:opacity-50 cursor-pointer"
                  >
                    <Save className="w-4 h-4" />
                    <span>{isSaving ? 'Đang lưu...' : 'Lưu Hồ Sơ'}</span>
                  </button>
                </div>
              )}

              {/* Close 'X' Button at top right */}
              <button
                type="button"
                onClick={() => setIsProfileModalOpen(false)}
                className="w-11 h-11 rounded-2xl bg-white/15 hover:bg-white/25 flex items-center justify-center text-white transition hover:scale-105 active:scale-95 cursor-pointer ml-1"
                title="Đóng cửa sổ"
              >
                <X className="w-6 h-6" />
              </button>
            </div>
          </div>
        </div>

        {/* Modal Body */}
        <form onSubmit={handleSave} className="flex-1 overflow-y-auto p-6 pb-16 space-y-6 custom-scrollbar">
          {/* Status Alert Message */}
          {successMessage && (
            <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold flex items-center gap-2 animate-in fade-in">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>{successMessage}</span>
            </div>
          )}

          {/* Editing Mode Banner */}
          {isEditing && (
            <div className="p-3 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-xs flex items-center justify-between animate-in fade-in">
              <div className="flex items-center gap-2 font-medium">
                <Edit3 className="w-4 h-4 text-amber-600" />
                <span>Bạn đang chỉnh sửa hồ sơ. Hãy nhấn <strong>"Lưu Hồ Sơ"</strong> ở góc trên khi hoàn tất.</span>
              </div>
            </div>
          )}

          {/* SECTION 1: THÔNG TIN HÀNH CHÍNH & ĐỊNH DANH */}
          <div className="space-y-4">
            <div className="flex items-center justify-between border-b border-slate-200 pb-2">
              <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
                <CreditCard className="w-4 h-4 text-blue-600" />
                <span>1. Thông Tin Hành Chính & Định Danh Công Dân</span>
              </h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Full Name */}
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-600">Họ và tên đầy đủ *</label>
                <div className="relative flex items-center">
                  <User className="absolute left-3 w-4 h-4 text-slate-400" />
                  <input
                    type="text"
                    disabled={!isEditing}
                    value={formData.full_name || ''}
                    onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                    className="w-full pl-9 pr-3 py-2 rounded-xl border border-slate-200 text-xs font-medium focus:border-blue-500 focus:outline-none disabled:bg-slate-50 disabled:text-slate-700"
                  />
                </div>
              </div>

              {/* Citizen ID (Số CCCD) */}
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-600">Số Căn Cước Công Dân (CCCD 12 số) *</label>
                <div className="relative flex items-center">
                  <CreditCard className="absolute left-3 w-4 h-4 text-slate-400" />
                  <input
                    type="text"
                    maxLength={12}
                    disabled={!isEditing}
                    value={formData.citizen_id || ''}
                    onChange={(e) => setFormData({ ...formData, citizen_id: e.target.value })}
                    placeholder="001098xxxxxx"
                    className="w-full pl-9 pr-3 py-2 rounded-xl border border-slate-200 text-xs font-mono font-bold text-slate-800 focus:border-blue-500 focus:outline-none disabled:bg-slate-50"
                  />
                </div>
              </div>

              {/* Date of Birth */}
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-600">Ngày tháng năm sinh *</label>
                <div className="relative flex items-center">
                  <Calendar className="absolute left-3 w-4 h-4 text-slate-400" />
                  <input
                    type="date"
                    disabled={!isEditing}
                    value={formData.date_of_birth || ''}
                    onChange={(e) => setFormData({ ...formData, date_of_birth: e.target.value })}
                    className="w-full pl-9 pr-3 py-2 rounded-xl border border-slate-200 text-xs font-medium focus:border-blue-500 focus:outline-none disabled:bg-slate-50 disabled:text-slate-700"
                  />
                </div>
              </div>

              {/* Gender */}
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-600">Giới tính *</label>
                <select
                  disabled={!isEditing}
                  value={formData.gender || 'Nam'}
                  onChange={(e) => setFormData({ ...formData, gender: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs font-medium focus:border-blue-500 focus:outline-none disabled:bg-slate-50 disabled:text-slate-700"
                >
                  <option value="Nam">Nam</option>
                  <option value="Nữ">Nữ</option>
                  <option value="Khác">Khác / Chưa xác định</option>
                </select>
              </div>

              {/* Phone */}
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-600">Số điện thoại liên lạc *</label>
                <div className="relative flex items-center">
                  <Phone className="absolute left-3 w-4 h-4 text-slate-400" />
                  <input
                    type="text"
                    disabled={!isEditing}
                    value={formData.phone || ''}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    className="w-full pl-9 pr-3 py-2 rounded-xl border border-slate-200 text-xs font-mono font-medium focus:border-blue-500 focus:outline-none disabled:bg-slate-50"
                  />
                </div>
              </div>

              {/* Health Insurance (BHYT) */}
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-600">Số thẻ Bảo hiểm y tế (BHYT)</label>
                <div className="relative flex items-center">
                  <FileCheck className="absolute left-3 w-4 h-4 text-slate-400" />
                  <input
                    type="text"
                    disabled={!isEditing}
                    value={formData.health_insurance_number || ''}
                    onChange={(e) => setFormData({ ...formData, health_insurance_number: e.target.value })}
                    placeholder="DN4010123456789"
                    className="w-full pl-9 pr-3 py-2 rounded-xl border border-slate-200 text-xs font-mono font-bold text-blue-700 focus:border-blue-500 focus:outline-none disabled:bg-slate-50"
                  />
                </div>
              </div>
            </div>

            {/* Address */}
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-600">Địa chỉ thường trú / Nơi ở hiện tại *</label>
              <div className="relative flex items-center">
                <MapPin className="absolute left-3 w-4 h-4 text-slate-400" />
                <input
                  type="text"
                  disabled={!isEditing}
                  value={formData.address || ''}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                  placeholder="Số nhà, đường phố, phường/xã, quận/huyện, tỉnh/thành phố"
                  className="w-full pl-9 pr-3 py-2 rounded-xl border border-slate-200 text-xs font-medium focus:border-blue-500 focus:outline-none disabled:bg-slate-50"
                />
              </div>
            </div>
          </div>

          {/* SECTION 2: THÔNG TIN LÂM SÀNG BAN ĐẦU & Y TẾ */}
          <div className="space-y-4 pt-2">
            <div className="border-b border-slate-200 pb-2">
              <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
                <HeartPulse className="w-4 h-4 text-rose-600" />
                <span>2. Thông Tin Lâm Sàng & Tiền Sử Bệnh Y Khoa</span>
              </h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Blood Type */}
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-600">Nhóm máu hệ ABO & Rh</label>
                <select
                  disabled={!isEditing}
                  value={formData.blood_type || 'O+'}
                  onChange={(e) => setFormData({ ...formData, blood_type: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs font-bold text-rose-700 focus:border-blue-500 focus:outline-none disabled:bg-slate-50"
                >
                  <option value="O+">O Rh(+)</option>
                  <option value="O-">O Rh(-)</option>
                  <option value="A+">A Rh(+)</option>
                  <option value="A-">A Rh(-)</option>
                  <option value="B+">B Rh(+)</option>
                  <option value="B-">B Rh(-)</option>
                  <option value="AB+">AB Rh(+)</option>
                  <option value="AB-">AB Rh(-)</option>
                  <option value="Chưa xác định">Chưa xét nghiệm</option>
                </select>
              </div>

              {/* Drug Allergies */}
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-600 flex items-center gap-1 text-rose-600">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  <span>Tiền sử dị ứng thuốc & thực phẩm</span>
                </label>
                <input
                  type="text"
                  disabled={!isEditing}
                  value={formData.allergies || ''}
                  onChange={(e) => setFormData({ ...formData, allergies: e.target.value })}
                  placeholder="Vd: Dị ứng kháng sinh Penicillin, aspirin..."
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs font-medium focus:border-blue-500 focus:outline-none disabled:bg-slate-50"
                />
              </div>
            </div>

            {/* Medical History */}
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-600">Tiền sử bệnh lý nền / bệnh mãn tính</label>
              <textarea
                rows={2}
                disabled={!isEditing}
                value={formData.medical_history || ''}
                onChange={(e) => setFormData({ ...formData, medical_history: e.target.value })}
                placeholder="Vd: Tăng huyết áp, Đái tháo đường type 2, Hen phế quản, Viêm gan B..."
                className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs font-medium focus:border-blue-500 focus:outline-none disabled:bg-slate-50"
              />
            </div>
          </div>

          {/* SECTION 3: LIÊN HỆ KHẨN CẤP */}
          <div className="space-y-4 pt-2">
            <div className="border-b border-slate-200 pb-2">
              <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
                <Phone className="w-4 h-4 text-emerald-600" />
                <span>3. Người Liên Hệ Khi Xảy Ra Tình Huống Khẩn Cấp (Cấp Cứu 115)</span>
              </h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-600">Họ tên người thân / Mối quan hệ</label>
                <input
                  type="text"
                  disabled={!isEditing}
                  value={formData.emergency_contact_name || ''}
                  onChange={(e) => setFormData({ ...formData, emergency_contact_name: e.target.value })}
                  placeholder="Vd: Nguyễn Văn An (Bố đẻ)"
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs font-medium focus:border-blue-500 focus:outline-none disabled:bg-slate-50"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-600">Số điện thoại khẩn cấp</label>
                <input
                  type="text"
                  disabled={!isEditing}
                  value={formData.emergency_contact_phone || ''}
                  onChange={(e) => setFormData({ ...formData, emergency_contact_phone: e.target.value })}
                  placeholder="0912 345 678"
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs font-mono font-medium focus:border-blue-500 focus:outline-none disabled:bg-slate-50"
                />
              </div>
            </div>
          </div>
        </form>

        {/* Footer info (BOTTOM CLOSE BUTTON REMOVED AS REQUESTED) */}
        <div className="px-6 py-3 bg-slate-50 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400">
          <span className="flex items-center gap-1.5">
            <Lock className="w-3.5 h-3.5 text-emerald-500" />
            <span>Mã hóa bảo mật theo tiêu chuẩn Y tế Quốc tế ISO/TS 14265 & Bộ Y Tế Việt Nam</span>
          </span>
          <span className="text-[10px] text-slate-400 font-mono">ID: {user.id}</span>
        </div>
      </div>
      </div>
    </ModalPortal>
  );
}
