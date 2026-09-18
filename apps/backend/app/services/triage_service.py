import os
import sys
import logging
from typing import Dict, Any, Optional

# Add ai_engine to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "ai_engine")))

from src.pipeline import MultimodalTriagePipeline

logger = logging.getLogger(__name__)

class TriageService:
    def __init__(self):
        self._pipeline = None

    @property
    def pipeline(self):
        if self._pipeline is None:
            data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "data", "medical_lexicon"))
            self._pipeline = MultimodalTriagePipeline(data_dir=data_dir)
        return self._pipeline

    def analyze(
        self,
        text: Optional[str] = None,
        audio_bytes: Optional[bytes] = None,
        audio_filename: str = "",
        document_bytes: Optional[bytes] = None,
        document_filename: str = ""
    ) -> Dict[str, Any]:
        return self.pipeline.process_multimodal_request(
            text=text,
            audio_bytes=audio_bytes,
            audio_filename=audio_filename,
            document_bytes=document_bytes,
            document_filename=document_filename
        )

triage_service = TriageService()
