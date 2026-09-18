import os
import time
import logging
from typing import Dict, Any, Optional

from .stt.whisper_model import FasterWhisperSTT
from .ocr.pdf_parser import PDFLabParser
from .ocr.image_ocr import ImageLabOCR
from .ner.medical_ner import MedicalNER
from .classification.predictor import HybridClinicalPredictor

logger = logging.getLogger(__name__)

class MultimodalTriagePipeline:
    """
    Orchestrator trung tâm của AI Engine.
    Điều phối toàn bộ luồng đa phương thức: Audio -> STT -> OCR -> NER -> Red Flag -> Fusion Triage.
    """

    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = data_dir or os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "medical_lexicon")
        
        # Đường dẫn CSDL tri thức
        icd_path = os.path.join(self.data_dir, "icd10_codes.json")
        synonyms_path = os.path.join(self.data_dir, "symptom_synonyms.json")
        red_flags_path = os.path.join(self.data_dir, "red_flags.json")
        lab_ref_path = os.path.join(self.data_dir, "lab_reference_ranges.json")

        # Đường dẫn thư mục trọng số mô hình cục bộ
        models_weights_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models_weights"))
        phobert_dir = os.path.join(models_weights_dir, "phobert_ner")

        # Khởi tạo các sub-modules
        self.stt_engine = FasterWhisperSTT()
        self.pdf_parser = PDFLabParser()
        self.image_ocr = ImageLabOCR()
        self.ner_engine = MedicalNER(
            model_dir=phobert_dir if os.path.exists(phobert_dir) else None,
            synonyms_path=synonyms_path if os.path.exists(synonyms_path) else None,
            red_flags_path=red_flags_path if os.path.exists(red_flags_path) else None
        )
        self.predictor = HybridClinicalPredictor(
            icd_path=icd_path if os.path.exists(icd_path) else None
        )

    def process(self, *args, **kwargs) -> Dict[str, Any]:
        """Alias for process_multimodal_request."""
        return self.process_multimodal_request(*args, **kwargs)

    def process_multimodal_request(
        self,
        text: Optional[str] = None,
        audio_bytes: Optional[bytes] = None,
        audio_filename: str = "",
        document_bytes: Optional[bytes] = None,
        document_filename: str = ""
    ) -> Dict[str, Any]:
        """
        Xử lý toàn diện một yêu cầu khám/tư vấn y tế đa phương thức.
        """
        pipeline_start = time.time()
        final_text = (text or "").strip()
        stt_metadata = None
        ocr_metadata = None
        lab_indicators = {}

        # 1. Xử lý Voice Audio nếu có
        if audio_bytes and len(audio_bytes) > 0:
            stt_res = self.stt_engine.transcribe(audio_bytes, audio_filename)
            stt_metadata = stt_res
            transcribed_text = stt_res.get("text", "")
            if transcribed_text:
                final_text = f"{final_text} {transcribed_text}".strip()

        # 2. Xử lý Tài liệu xét nghiệm nếu có
        if document_bytes and len(document_bytes) > 0:
            doc_ext = document_filename.lower().split(".")[-1] if document_filename else ""
            if doc_ext == "pdf":
                ocr_res = self.pdf_parser.parse_pdf(document_bytes)
            else:
                ocr_res = self.image_ocr.process_image(document_bytes)
            ocr_metadata = ocr_res
            lab_indicators = ocr_res.get("parsed_indicators", {})
        elif final_text:
            # Tự động trích xuất chỉ số sinh hóa nếu người dùng nhắc đến trong tin nhắn
            text_labs = self.pdf_parser.extract_lab_values_from_text(final_text).get("parsed_indicators", {})
            if text_labs:
                lab_indicators = text_labs

        # 3. Trích xuất Thực thể Y tế (NER) & Kiểm tra Red Flag
        ner_res = self.ner_engine.extract_entities(final_text)
        normalized_symptoms = ner_res.get("symptoms_normalized", [])
        negated_symptoms = ner_res.get("negated_symptoms", [])
        red_flag_res = ner_res.get("red_flag_assessment", {})

        # Tích hợp thêm lab criticals vào red flag nếu có
        if lab_indicators and not red_flag_res.get("is_emergency"):
            red_flag_res = self.ner_engine.red_flag_detector.evaluate(final_text, normalized_symptoms, lab_indicators)

        # 4. Dự đoán phân tầng bệnh (Hybrid Fusion Triage)
        triage_res = self.predictor.predict(
            user_text=final_text,
            normalized_symptoms=normalized_symptoms,
            lab_indicators=lab_indicators,
            negated_symptoms=negated_symptoms
        )

        pipeline_latency = time.time() - pipeline_start

        return {
            "processed_text": final_text,
            "latency_seconds": round(pipeline_latency, 3),
            "is_emergency": red_flag_res.get("is_emergency", False),
            "red_flag_details": red_flag_res,
            "extracted_entities": {
                "symptoms": normalized_symptoms,
                "negated_symptoms": negated_symptoms,
                "vital_signs": ner_res.get("vital_signs", {})
            },
            "negated_symptoms": negated_symptoms,
            "lab_indicators": lab_indicators,
            "triage_results": triage_res.get("top_predictions", []),
            "fusion_metadata": triage_res.get("fusion_metadata", {}),
            "clarification_loop": triage_res.get("clarification", {}),
            "stt_telemetry": stt_metadata,
            "ocr_telemetry": ocr_metadata
        }
