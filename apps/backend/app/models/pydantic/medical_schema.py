from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class TranscribeResponse(BaseModel):
    text: str
    language: str = "vi"
    duration_seconds: float
    latency_seconds: float
    status: str

class OCRAnalysisResponse(BaseModel):
    parsed_indicators: Dict[str, Any]
    critical_flags: List[str] = []
    total_indicators_found: int
    raw_text: Optional[str] = None

class TriageAnalysisRequest(BaseModel):
    user_text: str
    lab_indicators: Optional[Dict[str, Any]] = {}

class TriageAnalysisResponse(BaseModel):
    processed_text: str
    is_emergency: bool
    red_flag_details: Dict[str, Any]
    extracted_entities: Dict[str, Any]
    lab_indicators: Dict[str, Any]
    triage_results: List[Dict[str, Any]]
    fusion_metadata: Dict[str, Any]
    clarification_loop: Dict[str, Any]
    latency_seconds: float
