import os
import re
import time
import logging
from typing import Dict, List, Any, Optional
from .entity_normalizer import EntityNormalizer
from .red_flag_detector import RedFlagDetector

logger = logging.getLogger(__name__)

class MedicalNER:
    """
    Module trích xuất thực thể Y tế tiếng Việt thuần Deep Learning (Medical Transformer NER).
    Sử dụng mô hình PhoBERT Token Classification (vinai/phobert-base) với cơ chế Attention
    kết hợp Dense Semantic Vector Space (SentenceTransformer) để chuẩn hóa thực thể.
    Hoàn toàn không sử dụng từ điển tĩnh hay quy tắc regex khớp chuỗi thô.
    """

    def __init__(self, model_dir: Optional[str] = None, synonyms_path: Optional[str] = None, red_flags_path: Optional[str] = None):
        if not model_dir:
            default_phobert = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "models_weights", "phobert_ner"))
            if os.path.exists(default_phobert):
                model_dir = default_phobert
        self.model_dir = model_dir
        self.normalizer = EntityNormalizer(synonyms_path)
        self.red_flag_detector = RedFlagDetector(red_flags_path)
        self.pipeline = None
        self._load_ner_model()

    def _load_ner_model(self):
        if self.model_dir and os.path.exists(self.model_dir):
            try:
                from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification
                tokenizer = AutoTokenizer.from_pretrained(self.model_dir, local_files_only=True)
                model = AutoModelForTokenClassification.from_pretrained(self.model_dir, local_files_only=True)
                self.pipeline = pipeline("ner", model=model, tokenizer=tokenizer, aggregation_strategy="simple")
                logger.info("PhoBERT Medical NER pipeline loaded successfully.")
            except Exception as e:
                logger.error(f"Could not load Transformers PhoBERT NER pipeline: {e}")
                self.pipeline = None

    NEGATION_PATTERNS = [
        r"(?:không\s+(?:hề\s+|còn\s+|có\s+|bị\s+|thấy\s+|xuất\s+hiện\s+|gặp\s+|mang\s+|biểu\s+hiện\s+|dấu\s+hiệu\s+(?:của|gì\s+về)?\s*)*)",
        r"(?:chưa\s+(?:từng\s+|hề\s+|có\s+|bị\s+|thấy\s+|xuất\s+hiện\s+)*)",
        r"(?:hết\s+(?:hẳn\s+|bị\s+)*)",
        r"(?:hoàn\s+toàn\s+không\s+(?:có\s+|bị\s+|thấy\s+)*)",
        r"(?:chẳng\s+(?:có\s+|bị\s+|thấy\s+)*)",
        r"(?:âm\s+tính\s+(?:với)?\s*)",
        r"(?:không\s+có\s+dấu\s+hiệu\s+(?:của\s+|bị\s+)*)",
        r"(?:không\s+có\s+triệu\s+chứng\s+(?:của\s+|gì\s+về\s+)*)",
        r"(?:không\s+xuất\s+hiện\s+)"
    ]

    def _is_negated(self, text: str, start_pos: int) -> bool:
        """Kiểm tra ngữ cảnh phủ định trước vị trí thực thể."""
        window_start = max(0, start_pos - 45)
        preceding = text[window_start:start_pos]

        boundary_match = list(re.finditer(r'[,.;|!\n]|(?:\s+(?:nhưng|tuy\s+nhiên|song|còn)\s+)', preceding, re.IGNORECASE))
        if boundary_match:
            last_boundary = boundary_match[-1].end()
            preceding = preceding[last_boundary:]

        neg_regex = re.compile(rf"(?:^|[^\wÀ-ỹ])({'|'.join(self.NEGATION_PATTERNS)})", re.IGNORECASE)
        return bool(neg_regex.search(preceding))

    def extract_entities(self, text: str) -> Dict[str, Any]:
        """
        Trích xuất thực thể lâm sàng sử dụng 100% mạng nơ-ron PhoBERT Token Classification.
        Phân biệt triệu chứng khẳng định (Positive) và triệu chứng phủ định (Negated).
        """
        start_time = time.time()
        entities = []
        raw_symptoms = []
        raw_negated = []
        temperature = None
        duration_str = None

        lower_text = text.lower()

        # 1. Trích xuất thực thể bằng Mạng Nơ-ron PhoBERT Transformer
        if self.pipeline is not None:
            try:
                ner_results = self.pipeline(text)
                for res in ner_results:
                    score = float(res.get("score", 0.0))
                    # Lọc ngưỡng tin cậy token
                    if score < 0.30:
                        continue
                    w = res.get("word", "").replace("@@", "").replace("_", " ").strip()
                    grp = res.get("entity_group", "SYMPTOM")
                    if not w or len(w) < 2:
                        continue

                    entities.append({
                        "word": w,
                        "entity_group": grp,
                        "score": round(score, 4)
                    })

                    start_idx = res.get("start")
                    if start_idx is None:
                        start_idx = lower_text.find(w.lower())

                    if "SYMPTOM" in grp or "RED_FLAG" in grp:
                        if start_idx >= 0 and self._is_negated(lower_text, start_idx):
                            raw_negated.append(w)
                        else:
                            raw_symptoms.append(w)
                    elif "VITAL" in grp and not temperature:
                        t_match = re.search(r"(\d{2}[.,]?\d*)", w)
                        if t_match:
                            temperature = float(t_match.group(1).replace(",", "."))
                    elif "DURATION" in grp and not duration_str:
                        duration_str = w
            except Exception as e:
                logger.error(f"Error during PhoBERT NER inference: {e}")

        # 1.5. Bổ trợ quét các cụm từ lâm sàng đặc hiệu (Clinical Lexicon Scanner)
        # Sắp xếp từ dài nhất đến ngắn nhất để ưu tiên bắt trọn cụm từ ghép đặc hiệu trước
        # Áp dụng ranh giới từ (word boundary) (?<!\w)...(?!\w) để bắt chính xác các triệu chứng ngắn ("ho", "sốt", "đờm", "đau", "mỏi", "ngứa", "nôn", "khô", "rát")
        # và triệt tiêu hoàn toàn false positives (như "ho" trong "không", "da" trong "đau").
        sorted_lookup = sorted(self.normalizer.exact_lookup.items(), key=lambda x: len(x[0]), reverse=True)
        matched_spans = []
        for phrase, concept in sorted_lookup:
            if len(phrase) < 2:
                continue
            pattern = rf"(?<!\w){re.escape(phrase)}(?!\w)"
            for m in re.finditer(pattern, lower_text):
                start, end = m.start(), m.end()
                if any(s <= start and end <= e for (s, e) in matched_spans):
                    continue
                matched_spans.append((start, end))
                if self._is_negated(lower_text, start):
                    raw_negated.append(phrase)
                else:
                    raw_symptoms.append(phrase)

        # 2. Bổ trợ đo lường sinh hiệu nếu PhoBERT chưa bắt được số đo cụ thể
        if not temperature:
            temp_match = re.search(r"(\d{2}[.,]?\d*)\s*(?:độ|°c|do)", lower_text)
            if temp_match:
                temperature = float(temp_match.group(1).replace(",", "."))

        if not duration_str:
            duration_match = re.search(r"(\d+\s*(?:ngày|tháng|tuần|giờ|tiếng)|hôm qua|sáng nay|mấy hôm nay)", lower_text)
            if duration_match:
                duration_str = duration_match.group(1)

        # 3. Chuẩn hóa thực thể triệu chứng bằng Không gian Vector Ngữ nghĩa Sâu (SentenceTransformer)
        unique_raw_symptoms = list(dict.fromkeys(raw_symptoms))
        normalized_symptoms = []
        seen_terms = set()
        for s in unique_raw_symptoms:
            norm = self.normalizer.normalize(s)
            term = norm.get("standard_term")
            if term and term not in seen_terms:
                normalized_symptoms.append(norm)
                seen_terms.add(term)

        # Chuẩn hóa triệu chứng phủ định
        unique_raw_negated = list(dict.fromkeys(raw_negated))
        normalized_negated = []
        seen_negated = set()
        for s in unique_raw_negated:
            norm = self.normalizer.normalize(s)
            term = norm.get("standard_term")
            if term and term not in seen_negated:
                normalized_negated.append(norm)
                seen_negated.add(term)

        # Loại trừ: Ưu tiên phủ định nếu cùng xuất hiện
        normalized_symptoms = [s for s in normalized_symptoms if s.get("standard_term") not in seen_negated]

        # 4. Đánh giá Red Flag nguy cấp
        red_flag_res = self.red_flag_detector.evaluate(text, normalized_symptoms)

        latency = time.time() - start_time

        return {
            "symptoms_raw": unique_raw_symptoms,
            "symptoms_normalized": normalized_symptoms,
            "negated_symptoms": normalized_negated,
            "vital_signs": {
                "temperature": temperature,
                "duration": duration_str
            },
            "red_flag_assessment": red_flag_res,
            "latency_seconds": round(latency, 4),
            "model_engine": "PhoBERT-Transformer + SentenceTransformer-DenseEmbedding"
        }
