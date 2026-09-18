from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class ChatMessageRequest(BaseModel):
    session_id: str
    message: str
    message_type: str = "text"  # text, audio, document
    attachments: Optional[List[str]] = []
    chat_history: Optional[List[Dict[str, Any]]] = []

class MedicalRecordRequest(BaseModel):
    session_id: str
    chat_history: List[Dict[str, Any]] = []
    telemetry: Optional[Dict[str, Any]] = {}

class SymptomEntity(BaseModel):
    id: str
    standard_term: str
    matched: bool = True
    original_matched_synonym: Optional[str] = None

class LabIndicator(BaseModel):
    value: float
    raw_extracted: Optional[float] = None
    status: str = "NORMAL"
    message: str = ""
    unit: str = ""

class DiseasePrediction(BaseModel):
    rank: int
    icd_code: str
    disease_name_vi: str
    department: str
    probability: float
    probability_percentage: str
    severity: str
    recommendation: str

class ClarificationQuestion(BaseModel):
    id: str
    question: str
    options: List[str]

class ClarificationPayload(BaseModel):
    needs_clarification: bool = False
    clinical_stage: Optional[str] = "initial_screening"
    confidence_score: float = 0.0
    entropy: float = 0.0
    reason: Optional[str] = None
    questions: List[ClarificationQuestion] = []

class RedFlagDetails(BaseModel):
    is_emergency: bool = False
    latency_seconds: float = 0.0
    triggered_flags: List[Dict[str, Any]] = []
    highest_severity: str = "NORMAL"

class TelemetryPayload(BaseModel):
    is_emergency: bool = False
    red_flag: RedFlagDetails
    symptoms: List[SymptomEntity] = []
    negated_symptoms: Optional[List[SymptomEntity]] = []
    lab_indicators: Dict[str, LabIndicator] = {}
    top_predictions: List[DiseasePrediction] = []
    rag_citations: List[Dict[str, Any]] = []
    clarification: ClarificationPayload
    latency_ms: Optional[int] = 0
    pipeline_breakdown: Optional[Dict[str, Any]] = None

class ChatMessageResponse(BaseModel):
    message_id: str
    session_id: str
    sender: str = "assistant"  # user, assistant, system
    text_content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    latency_ms: Optional[int] = 0
    pipeline_breakdown: Optional[Dict[str, Any]] = None
    telemetry: Optional[TelemetryPayload] = None
