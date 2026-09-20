export interface SymptomEntity {
  id: string;
  standard_term: string;
  matched: boolean;
  original_matched_synonym?: string;
}

export interface LabIndicator {
  value: number;
  raw_extracted?: number;
  status: 'NORMAL' | 'LOW' | 'HIGH' | 'CRITICAL_LOW' | 'CRITICAL_HIGH';
  message: string;
  unit: string;
}

export interface DiseasePrediction {
  rank: number;
  icd_code: string;
  disease_name_vi: string;
  department: string;
  probability: number;
  probability_percentage: string;
  severity: string;
  recommendation: string;
}

export interface ClarificationQuestion {
  id: string;
  question: string;
  options: string[];
}

export interface ClarificationPayload {
  needs_clarification: boolean;
  clinical_stage?: 'initial_screening' | 'provisional_assumption' | 'definitive_conclusion';
  confidence_score: number;
  entropy: number;
  reason?: string;
  questions: ClarificationQuestion[];
}

export interface RedFlagAlert {
  rule_id?: string;
  disease_group?: string;
  severity?: string;
  action_vi?: string;
  emergency_phone?: string;
}

export interface TelemetryData {
  is_emergency: boolean;
  red_flag?: {
    is_emergency: boolean;
    latency_seconds: number;
    triggered_flags: RedFlagAlert[];
    highest_severity: string;
  };
  symptoms: SymptomEntity[];
  negated_symptoms?: SymptomEntity[];
  lab_indicators: Record<string, LabIndicator>;
  top_predictions: DiseasePrediction[];
  clarification: ClarificationPayload;
  rag_citations?: any[];
  latency_ms?: number;
  provider?: string;
  pipeline_breakdown?: {
    ner_ms?: number;
    rag_ms?: number;
    llm_ms?: number;
    total_ms?: number;
  };
  cloud_error?: string;
}

/** Một câu trả lời từ một provider (Gemini, Cohere, deterministic...) */
export interface AlternativeAnswer {
  text: string;
  provider: string;
}

/** Feedback người dùng về một câu trả lời */
export interface MessageFeedback {
  rating: 'like' | 'dislike';
  reason?: string;
  answer_index: number;
}

export interface ChatMessage {
  id: string;
  sessionId: string;
  sender: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  telemetry?: TelemetryData;
  isStreaming?: boolean;
  latency_ms?: number;
  pipeline_breakdown?: {
    ner_ms?: number;
    rag_ms?: number;
    llm_ms?: number;
    total_ms?: number;
  };
  /** Danh sách câu trả lời thay thế (nếu Gemini + Cohere cùng trả lời) */
  alternative_answers?: AlternativeAnswer[];
  /** Index câu trả lời đang hiển thị (0 = primary, 1 = alternative) */
  active_answer_index?: number;
  /** Feedback của người dùng về câu trả lời này */
  feedback?: MessageFeedback;
  /** provider chính đã trả lời */
  provider?: string;
}
