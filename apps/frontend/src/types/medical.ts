export interface TranscribeResult {
  text: string;
  language: string;
  duration_seconds: number;
  latency_seconds: number;
  status: string;
}

export interface OCRResult {
  parsed_indicators: Record<string, any>;
  critical_flags: string[];
  total_indicators_found: number;
  raw_text?: string;
}

export interface GlossaryEntry {
  standard_term: string;
  icd_mapping?: string;
  synonyms: string[];
  category: string;
  is_red_flag_potential: boolean;
}

export interface MedicalRecord {
  id: string;
  record_code: string;
  user_id: string;
  patient_name: string;
  age: number;
  gender: string;
  phone?: string;
  admission_date: string;
  primary_symptoms: string[];
  icd_code: string;
  diagnosis: string;
  department: string;
  severity: 'Critical' | 'High' | 'Medium' | 'Low';
  treatment_plan: string;
  notes?: string;
  created_at: string;
  is_draft: boolean;
  source?: 'manual_entry' | 'chat_session';
}

export interface AuthUser {
  id: string;
  email: string;
  full_name: string;
  role: 'admin' | 'user';
  phone?: string;
  avatar?: string;
  date_of_birth?: string; // Ngày sinh YYYY-MM-DD
  gender?: 'Nam' | 'Nữ' | 'Khác' | string; // Giới tính
  citizen_id?: string; // Số Căn cước công dân (12 số)
  address?: string; // Địa chỉ thường trú
  health_insurance_number?: string; // Số thẻ BHYT
  blood_type?: 'A+' | 'A-' | 'B+' | 'B-' | 'AB+' | 'AB-' | 'O+' | 'O-' | 'Chưa xác định' | string; // Nhóm máu
  allergies?: string; // Tiền sử dị ứng thuốc/thực phẩm
  medical_history?: string; // Tiền sử bệnh nền
  emergency_contact_name?: string; // Người liên hệ khẩn cấp
  emergency_contact_phone?: string; // SĐT người liên hệ khẩn cấp
}

export interface FeedbackData {
  category: string;
  rating: number;
  content: string;
  user_name?: string;
  user_email?: string;
}

