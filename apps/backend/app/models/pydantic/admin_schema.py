from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class GlossaryItem(BaseModel):
    key: str
    standard_term: str
    icd_mapping: Optional[str] = None
    synonyms: List[str]
    category: str = "Chung"
    is_red_flag_potential: bool = False

class FeedbackCreate(BaseModel):
    session_id: str
    message_id: str
    predicted_icd: Optional[str] = None
    doctor_label_correct: bool
    corrected_icd: Optional[str] = None
    comment: Optional[str] = None

class UserRoleUpdate(BaseModel):
    role: str  # "admin" | "user" | "doctor" | "guest"

class ColabConnectRequest(BaseModel):
    drive_url: str
    filename: Optional[str] = None

class TrainingStartRequest(BaseModel):
    job_type: str = "retrain"  # "retrain" | "finetune"
    dataset_file: Optional[str] = None
    config: Optional[Dict[str, Any]] = None

class RagDocumentAdd(BaseModel):
    title: str
    content: str
    source: Optional[str] = None
    icd_codes: Optional[List[str]] = None
