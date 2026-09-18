import { fetchApi } from './api';
import { TranscribeResult, OCRResult, GlossaryEntry } from '../types/medical';

export const medicalService = {
  async transcribeAudio(audioBlob: Blob, filename: string = 'recording.wav'): Promise<TranscribeResult> {
    const formData = new FormData();
    formData.append('file', audioBlob, filename);
    formData.append('language', 'vi');

    return fetchApi('/medical/transcribe', {
      method: 'POST',
      body: formData,
    });
  },

  async uploadAndAnalyzeLabDocument(files: File | File[]): Promise<OCRResult> {
    const formData = new FormData();
    const fileList = Array.isArray(files) ? files : [files];
    fileList.forEach((f) => {
      formData.append('files', f, f.name);
      formData.append('file', f, f.name); // for backwards compatibility
    });

    return fetchApi('/medical/ocr', {
      method: 'POST',
      body: formData,
    });
  },

  async getGlossary(): Promise<Record<string, GlossaryEntry>> {
    return fetchApi('/admin/glossary');
  },

  async getIcdCodes(): Promise<Record<string, any>> {
    return fetchApi('/admin/icd-codes');
  },

  async getRagKnowledge(): Promise<any[]> {
    return fetchApi('/admin/rag-knowledge');
  },

  async getValidationResults(): Promise<any[]> {
    return fetchApi('/admin/validation-results');
  },

  async saveGlossaryItem(item: { key: string; standard_term: string; icd_mapping?: string; synonyms: string[]; category: string; is_red_flag_potential: boolean }): Promise<any> {
    return fetchApi('/admin/glossary', {
      method: 'POST',
      body: JSON.stringify(item),
    });
  },

  async getFeedbackReports(): Promise<any> {
    return fetchApi('/admin/feedback/reports');
  },

  async submitFeedback(feedback: { session_id: string; message_id: string; doctor_label_correct: boolean; predicted_icd?: string; corrected_icd?: string; comment?: string }): Promise<any> {
    return fetchApi('/admin/feedback', {
      method: 'POST',
      body: JSON.stringify(feedback),
    });
  },

  async getMedicalRecords(userId?: string, includeDrafts: boolean = false): Promise<{ total: number; records: any[] }> {
    const params = new URLSearchParams();
    if (userId) params.append('user_id', userId);
    if (includeDrafts) params.append('include_drafts', 'true');
    const qs = params.toString();
    return fetchApi(`/medical/records${qs ? `?${qs}` : ''}`);
  },

  async createMedicalRecord(recordData: any): Promise<any> {
    return fetchApi('/medical/records', {
      method: 'POST',
      body: JSON.stringify(recordData),
    });
  },

  async deleteMedicalRecord(recordId: string): Promise<any> {
    return fetchApi(`/medical/records/${recordId}`, {
      method: 'DELETE',
    });
  },

  async submitUserFeedback(feedback: { category: string; rating: number; content: string; user_name?: string; user_email?: string }): Promise<any> {
    return fetchApi('/medical/feedback', {
      method: 'POST',
      body: JSON.stringify(feedback),
    });
  },

  // Admin: User Management
  async getUsers(): Promise<{ users: any[]; total: number }> {
    return fetchApi('/admin/users');
  },

  async updateUserRole(userId: string, role: string): Promise<any> {
    return fetchApi(`/admin/users/${userId}/role`, {
      method: 'PUT',
      body: JSON.stringify({ role }),
    });
  },

  async deleteUser(userId: string): Promise<any> {
    return fetchApi(`/admin/users/${userId}`, {
      method: 'DELETE',
    });
  },

  // Admin: AI Model Management
  async getAiModels(): Promise<{ models: any[]; total: number }> {
    return fetchApi('/admin/models');
  },

  // Admin: Datasets & RAG Knowledge
  async getDatasets(): Promise<{ datasets: any[]; total: number }> {
    return fetchApi('/admin/datasets');
  },

  async uploadDataset(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    return fetchApi('/admin/datasets/upload', {
      method: 'POST',
      body: formData,
    });
  },

  async addRagDocument(doc: { title: string; content: string; source?: string; icd_codes?: string[] }): Promise<any> {
    return fetchApi('/admin/rag-knowledge/add', {
      method: 'POST',
      body: JSON.stringify(doc),
    });
  },

  // Admin: Training Center & Google Colab
  async startTraining(jobType: string = 'retrain', datasetFile?: string, config?: any): Promise<any> {
    return fetchApi('/admin/training/start', {
      method: 'POST',
      body: JSON.stringify({
        job_type: jobType,
        dataset_file: datasetFile,
        config: config || {},
      }),
    });
  },

  async getTrainingStatus(): Promise<any> {
    return fetchApi('/admin/training/status');
  },

  async getTrainingJobs(): Promise<{ jobs: any[]; total: number }> {
    return fetchApi('/admin/training/jobs');
  },

  async getTrainingLogs(jobId: string, offset: number = 0): Promise<any> {
    return fetchApi(`/admin/training/logs/${jobId}?offset=${offset}`);
  },

  async downloadFromColab(driveUrl: string, filename?: string): Promise<any> {
    return fetchApi('/admin/colab/download', {
      method: 'POST',
      body: JSON.stringify({ drive_url: driveUrl, filename }),
    });
  },

  // Admin: System Health
  async getSystemHealth(): Promise<any> {
    return fetchApi('/admin/system/health');
  }
};


