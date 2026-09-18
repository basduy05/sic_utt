"""
Calibrated Sigmoidal Evidence Model Engine
Chuẩn hóa theo thuật toán và tham số WHO ICD-10 & Syndromic Calibrated Weights:
Formula: P(D) = P_max * (1 / (1 + exp(-k * (R - R0))))
Parameters:
  P_max = 0.88
  R0 = 0.3
  k = 10.0
  lambda_penalty = 1.5
"""
import os
import re
import json
import logging
import unicodedata
from typing import Dict, List, Any, Optional, Tuple, Set
import numpy as np

logger = logging.getLogger(__name__)

def _normalize_text(text: str) -> str:
    """Loại bỏ dấu thanh và đưa về chữ thường để so khớp chuỗi bền vững."""
    if not text:
        return ""
    text = text.lower().strip()
    text = unicodedata.normalize('NFD', text)
    text = "".join(c for c in text if unicodedata.category(c) != 'Mn')
    text = re.sub(r'[^\w\s]', ' ', text)
    return " ".join(text.split())

class CalibratedSigmoidalEvidenceModel:
    """
    Động cơ tính toán xác suất bằng chứng lâm sàng hiệu chuẩn (Calibrated Sigmoidal Evidence Model)
    cho 1.218 nhóm bệnh lý ICD-10 và 8.489 triệu chứng.
    """

    def __init__(self, icd_json_path: Optional[str] = None):
        self.P_max = 0.88
        self.R0 = 0.3
        self.k = 10.0
        self.lambda_penalty = 1.5

        # Danh sách bệnh và bộ nhớ tra cứu
        self.diseases: List[Dict[str, Any]] = []
        self.disease_id_to_idx: Dict[str, int] = {}
        self.symptom_inverted_index: Dict[str, List[Tuple[int, float, bool, str]]] = {} # norm_term -> [(disease_idx, omega, is_exclusion, sym_id)]
        self.symptom_id_to_matches: Dict[str, List[Tuple[int, float, bool]]] = {} # sym_id -> [(disease_idx, omega, is_exclusion)]
        self.max_evidence_scores: np.ndarray = np.array([], dtype=np.float32)

        default_paths = [
            icd_json_path,
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "data", "sic", "icd10.json")),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "data", "sic", "icd10_knowledge_base.json")),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "data", "medical_lexicon", "icd10_codes.json")),
        ]

        target_path = next((p for p in default_paths if p and os.path.exists(p)), None)
        if target_path:
            self._load_knowledge_base(target_path)
        else:
            logger.warning("Không tìm thấy tệp CSDL ICD-10 cho Calibrated Sigmoidal Evidence Model.")

    def _load_knowledge_base(self, path: str):
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)

            if "metadata" in raw_data and "usage" in raw_data["metadata"]:
                params = raw_data["metadata"]["usage"].get("parameters", {})
                self.P_max = float(params.get("P_max", self.P_max))
                self.R0 = float(params.get("R0", self.R0))
                self.k = float(params.get("k", self.k))
                self.lambda_penalty = float(params.get("lambda_penalty", self.lambda_penalty))

            if "diseases" in raw_data and isinstance(raw_data["diseases"], list):
                self.diseases = raw_data["diseases"]
            elif isinstance(raw_data, dict):
                # Format icd10_codes.json
                self.diseases = list(raw_data.values())

            num_diseases = len(self.diseases)
            self.max_evidence_scores = np.zeros(num_diseases, dtype=np.float32)
            self.disease_id_to_idx = {}
            self.symptom_inverted_index = {}
            self.symptom_id_to_matches = {}

            for idx, d in enumerate(self.diseases):
                did = d.get("disease_id") or d.get("code")
                self.disease_id_to_idx[did] = idx

                max_ev = float(d.get("max_evidence_score", 0.0))
                symptoms = d.get("symptoms", [])

                calc_max = 0.0
                for sym in symptoms:
                    omega = float(sym.get("omega", 0.0))
                    calc_max += omega
                    is_excl = bool(sym.get("is_exclusion_criterion", False))
                    sym_id = sym.get("symptom_id", "")
                    sym_name = sym.get("symptom_name", "")

                    if sym_id:
                        if sym_id not in self.symptom_id_to_matches:
                            self.symptom_id_to_matches[sym_id] = []
                        self.symptom_id_to_matches[sym_id].append((idx, omega, is_excl))

                    if sym_name:
                        norm_name = _normalize_text(sym_name)
                        if norm_name not in self.symptom_inverted_index:
                            self.symptom_inverted_index[norm_name] = []
                        self.symptom_inverted_index[norm_name].append((idx, omega, is_excl, sym_id))

                        # Bổ sung n-grams chính của triệu chứng để bắt khớp từ ngữ
                        parts = norm_name.split()
                        if len(parts) >= 3:
                            for wlen in [2, 3]:
                                for i in range(len(parts) - wlen + 1):
                                    sub_phrase = " ".join(parts[i:i+wlen])
                                    if len(sub_phrase) >= 5:
                                        if sub_phrase not in self.symptom_inverted_index:
                                            self.symptom_inverted_index[sub_phrase] = []
                                        self.symptom_inverted_index[sub_phrase].append((idx, omega * 0.75, is_excl, sym_id))

                self.max_evidence_scores[idx] = max_ev if max_ev > 0 else (calc_max if calc_max > 0 else 1.0)

            logger.info(f"Đã nạp {num_diseases} bệnh lý và {len(self.symptom_inverted_index)} cụm triệu chứng vào Sigmoidal Evidence Engine.")
        except Exception as e:
            logger.error(f"Lỗi khi nạp cơ sở tri thức Sigmoidal Evidence Model: {e}")

    def evaluate(
        self,
        user_text: str,
        normalized_symptoms: Optional[List[Dict[str, Any]]] = None,
        negated_symptoms: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
        """
        Tính toán phân bố xác suất bằng chứng P(D) trên toàn bộ 1.218 nhóm bệnh:
        P(D) = P_max * (1 / (1 + exp(-k * (R - R0))))
        """
        num_diseases = len(self.diseases)
        if num_diseases == 0:
            return np.array([], dtype=np.float32), []

        evidence_sums = np.zeros(num_diseases, dtype=np.float32)
        exclusion_triggered = np.zeros(num_diseases, dtype=bool)
        matched_symptoms_per_disease: Dict[int, List[Dict[str, Any]]] = {i: [] for i in range(num_diseases)}

        normalized_symptoms = normalized_symptoms or []
        negated_symptoms = negated_symptoms or []

        # Chuẩn hóa văn bản bệnh nhân và trích xuất n-grams
        norm_user_text = _normalize_text(user_text)
        words = norm_user_text.split()
        user_ngrams = set()
        for n in range(1, 5):
            for i in range(len(words) - n + 1):
                user_ngrams.add(" ".join(words[i:i+n]))

        # Tập ID và Standard Term từ thực thể NER
        detected_sym_ids = set(s.get("id", "").strip() for s in normalized_symptoms if s.get("id"))
        detected_terms = set(_normalize_text(s.get("standard_term", "")) for s in normalized_symptoms if s.get("standard_term"))
        negated_terms = set(_normalize_text(s.get("standard_term", "")) for s in negated_symptoms if s.get("standard_term"))

        # 1. Khớp qua Symptom ID
        for sym_id in detected_sym_ids:
            if sym_id in self.symptom_id_to_matches:
                for d_idx, omega, is_excl in self.symptom_id_to_matches[sym_id]:
                    if is_excl:
                        exclusion_triggered[d_idx] = True
                    else:
                        evidence_sums[d_idx] += omega
                        matched_symptoms_per_disease[d_idx].append({
                            "symptom_id": sym_id,
                            "omega": omega,
                            "matched_by": "id"
                        })

        # 2. Khớp qua Từ điển Inverted Index (user_ngrams + detected_terms)
        evaluated_candidates = user_ngrams.union(detected_terms)
        seen_pairs: Set[Tuple[int, str]] = set()

        for term in evaluated_candidates:
            if term in self.symptom_inverted_index:
                for d_idx, omega, is_excl, sym_id in self.symptom_inverted_index[term]:
                    pair_key = (d_idx, sym_id if sym_id else term)
                    if pair_key in seen_pairs:
                        continue
                    seen_pairs.add(pair_key)

                    # Kiểm tra xem triệu chứng này có bị phủ định (negated) không
                    if term in negated_terms:
                        if is_excl:
                            # Không có triệu chứng loại trừ -> Tốt cho chẩn đoán
                            pass
                        else:
                            # Phủ định triệu chứng bệnh -> Phạt
                            evidence_sums[d_idx] = max(0.0, evidence_sums[d_idx] - (omega * 0.5))
                        continue

                    if is_excl:
                        exclusion_triggered[d_idx] = True
                    else:
                        evidence_sums[d_idx] += omega
                        matched_symptoms_per_disease[d_idx].append({
                            "symptom_name": term,
                            "symptom_id": sym_id,
                            "omega": omega,
                            "matched_by": "phrase"
                        })

        # 3. Tính tỷ lệ bằng chứng R và áp dụng Sigmoidal Function
        # R = E / max_evidence_score
        # Nếu gặp exclusion criterion -> R = R / lambda_penalty
        ratios = np.zeros(num_diseases, dtype=np.float32)
        nonzero_mask = evidence_sums > 0

        safe_max_scores = np.maximum(self.max_evidence_scores, 0.1)
        ratios[nonzero_mask] = evidence_sums[nonzero_mask] / safe_max_scores[nonzero_mask]

        # Phạt các bệnh có tiêu chuẩn loại trừ bị vi phạm
        ratios[exclusion_triggered] /= self.lambda_penalty

        # Công thức: P(D) = P_max * (1 / (1 + exp(-k * (R - R0))))
        probs = np.zeros(num_diseases, dtype=np.float32)
        if np.any(nonzero_mask):
            exponent = -self.k * (ratios[nonzero_mask] - self.R0)
            # Clip exponent để chống tràn số
            exponent = np.clip(exponent, -30.0, 30.0)
            probs[nonzero_mask] = self.P_max * (1.0 / (1.0 + np.exp(exponent)))

        # Lọc danh sách bệnh có bằng chứng tích lũy
        top_candidates = []
        scored_indices = np.where(probs > 0.01)[0]
        sorted_indices = scored_indices[np.argsort(probs[scored_indices])[::-1]]

        for rank_idx, idx in enumerate(sorted_indices[:15]):
            d = self.diseases[idx]
            did = d.get("disease_id") or d.get("code")
            dname = d.get("disease_name") or d.get("name_vi") or d.get("name")
            p_val = float(probs[idx])

            top_candidates.append({
                "rank": rank_idx + 1,
                "disease_id": did,
                "disease_name": dname,
                "chapter_id": d.get("chapter_id", ""),
                "chapter_title": d.get("chapter_title", ""),
                "chapter_specialty": d.get("chapter_specialty", ""),
                "evidence_score": round(float(evidence_sums[idx]), 4),
                "evidence_ratio_R": round(float(ratios[idx]), 4),
                "max_score": round(float(self.max_evidence_scores[idx]), 4),
                "probability": round(p_val, 4),
                "probability_percentage": f"{round(p_val * 100, 1)}%",
                "exclusion_triggered": bool(exclusion_triggered[idx]),
                "matched_symptoms_count": len(matched_symptoms_per_disease[idx]),
                "matched_symptoms": matched_symptoms_per_disease[idx][:5]
            })

        return probs, top_candidates
