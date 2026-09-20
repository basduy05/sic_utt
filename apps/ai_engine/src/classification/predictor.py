import os
import re
import json
import logging
import numpy as np
from typing import Dict, List, Any, Optional

from .text_encoder import SymptomTextEncoder
from .tabular_model import TabularClinicalClassifier
from .fusion_layer import HybridLateFusionLayer
from .clarification_engine import ClarificationEngine

logger = logging.getLogger(__name__)


OVERLAP_STOPWORDS = {
    "người", "chứng", "tình", "triệu", "bị", "thấy", "khi", "lúc", "vùng", "khu",
    "vực", "ở", "tại", "có", "do", "nhẹ", "vừa", "nhiều", "ít", "đang", "cảm",
    "thể", "chất", "mức", "độ", "gây", "ra", "lại", "qua", "lần"
}

def _token_overlap(a: str, b: str) -> bool:
    """Kiểm tra xem hai chuỗi có chia sẻ ít nhất 1 từ y khoa có nghĩa không (trừ stopword)."""
    tokens_a = {w for w in a.split() if w not in OVERLAP_STOPWORDS and len(w) >= 2}
    tokens_b = {w for w in b.split() if w not in OVERLAP_STOPWORDS and len(w) >= 2}
    return bool(tokens_a & tokens_b)



class HybridClinicalPredictor:
    """
    Interface cấp cao dự đoán nhóm bệnh, trả về Top 3-5 nguy cơ kèm mã ICD-10,
    phân tích mức độ tin cậy và kích hoạt Clarification Loop nếu cần.
    """

    def __init__(self, icd_path: Optional[str] = None):
        self.tabular_model = TabularClinicalClassifier()
        self.text_encoder = SymptomTextEncoder()
        self.fusion_layer = HybridLateFusionLayer()
        self.clarification_engine = ClarificationEngine()

        target_icd = icd_path or os.path.abspath(os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "..", "data", "medical_lexicon", "icd10_codes.json"
        ))
        self.icd_db = {}
        if target_icd and os.path.exists(target_icd):
            with open(target_icd, "r", encoding="utf-8") as f:
                self.icd_db = json.load(f)

        # Đồng bộ chính xác thứ tự 211 classes đã huấn luyện của mô hình AI
        self.disease_classes = list(self.tabular_model.DISEASE_CLASSES)

        # Preload NLP Symptom Classifier (tránh joblib.load 60MB mỗi lần gọi predict)
        self.nlp_clf = None
        self.nlp_vectorizer = None
        nlp_model_path = os.path.join(os.path.dirname(__file__), "..", "..", "models_weights", "nlp_symptom_classifier.pkl")
        vectorizer_path = os.path.join(os.path.dirname(__file__), "..", "..", "models_weights", "nlp_tfidf_vectorizer.pkl")
        if os.path.exists(nlp_model_path) and os.path.exists(vectorizer_path):
            try:
                import joblib
                self.nlp_clf = joblib.load(nlp_model_path)
                self.nlp_vectorizer = joblib.load(vectorizer_path)
                logger.info("NLP Symptom Classifier preloaded successfully.")
            except Exception as e:
                logger.warning(f"Could not preload NLP classifier: {e}")

        # Pre-compute disease text embeddings cho semantic fallback
        self._disease_texts: List[str] = []
        self._doc_vecs = None
        self._precompute_disease_embeddings()

    def _precompute_disease_embeddings(self):
        """Precompute disease text embedding vectors for semantic fallback."""
        try:
            self._disease_texts = []
            for d in self.disease_classes:
                code = d.get("code")
                info = self.icd_db.get(code, {})
                cardinal = " ".join(info.get("cardinal_symptoms", []))
                all_sym = " ".join(info.get("all_symptoms", []))
                desc = info.get("description", "")
                self._disease_texts.append(f"{d.get('name', '')} {cardinal} {all_sym} {desc}")
            if self._disease_texts:
                self._doc_vecs = self.text_encoder.encode(self._disease_texts)
                logger.info(f"Precomputed embeddings for {len(self._disease_texts)} diseases.")
        except Exception as e:
            logger.warning(f"Could not precompute disease embeddings: {e}")
            self._doc_vecs = None

    def predict(
        self,
        user_text: str,
        normalized_symptoms: List[Dict[str, Any]],
        lab_indicators: Dict[str, Any],
        negated_symptoms: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Nhận vào text, thực thể triệu chứng đã bóc tách, chỉ số lab, và danh sách triệu chứng đã loại trừ (negated)
        -> Trả về kết quả phân tầng bệnh theo chuẩn y khoa Bộ Y Tế.
        """
        num_classes = len(self.disease_classes)
        symptom_ids = [s.get("id", "") for s in normalized_symptoms]
        symptom_names = [s.get("standard_term", "") for s in normalized_symptoms]
        negated_symptoms = negated_symptoms or []

        # Nếu không có text và không có triệu chứng
        if not user_text.strip() and not normalized_symptoms and not lab_indicators:
            return {
                "top_predictions": [],
                "fusion_metadata": {"alpha_tabular_weight": 0.0, "has_lab_indicators": False, "total_indicators_used": 0},
                "clarification": {
                    "needs_clarification": True,
                    "confidence_score": 0.0,
                    "entropy": 0.0,
                    "reason": "Chưa có thông tin triệu chứng",
                    "questions": []
                }
            }

        # 1. Nhánh NLP Symptom Classifier hoặc Semantic Text Matching
        prob_text = np.ones(num_classes, dtype=np.float32) / num_classes

        nlp_loaded = False
        # Sử dụng preloaded classifier nếu có sẵn (tránh load lại 60MB)
        if self.nlp_clf is not None and self.nlp_vectorizer is not None:
            try:
                X_vec = self.nlp_vectorizer.transform([user_text])
                inferred_probs = self.nlp_clf.predict_proba(X_vec)[0]
                if len(inferred_probs) == num_classes:
                    prob_text = inferred_probs
                    nlp_loaded = True
                    logger.debug(f"NLP classifier predicted {num_classes} classes successfully.")
            except Exception as e:
                logger.warning(f"Failed to infer with preloaded NLP classifier: {e}")

        if not nlp_loaded and (user_text.strip() or symptom_names):
            # Semantic Text Embedding matching qua cached doc_vecs
            try:
                query_str = f"{user_text} {' '.join(symptom_names)}"
                query_vec = self.text_encoder.encode([query_str])[0]

                # Dùng precomputed embeddings nếu có, ngược lại tính lại
                if self._doc_vecs is not None and len(self._doc_vecs) == num_classes:
                    doc_vecs = self._doc_vecs
                else:
                    disease_texts = []
                    for d in self.disease_classes:
                        code = d.get("code")
                        info = self.icd_db.get(code, {})
                        cardinal = " ".join(info.get("cardinal_symptoms", []))
                        all_sym = " ".join(info.get("all_symptoms", []))
                        desc = info.get("description", "")
                        disease_texts.append(f"{d.get('name', '')} {cardinal} {all_sym} {desc}")
                    doc_vecs = self.text_encoder.encode(disease_texts)

                sims = np.dot(doc_vecs, query_vec)
                exp_sims = np.exp((sims - np.max(sims)) * 2.5)
                prob_text = exp_sims / np.sum(exp_sims)
            except Exception as e:
                logger.warning(f"Error in semantic text embedding inference: {e}")

        # 2. Nhánh Tabular Classifier (P_tabular) & Multimodal Fusion
        prob_tabular = self.tabular_model.predict_proba(lab_indicators, symptom_ids)
        has_lab = len(lab_indicators) > 0
        if len(prob_tabular) == num_classes:
            p_final, alpha_used = self.fusion_layer.fuse(prob_tabular, prob_text, has_lab_data=has_lab)
        else:
            p_final = prob_text.copy()
            alpha_used = 0.0

        # 3. Áp dụng quy tắc Loại trừ Lâm sàng & Dấu hiệu Phủ định (Pertinent Negatives Rule)
        if negated_symptoms:
            neg_terms = [s.get("standard_term", "").lower() for s in negated_symptoms]
            neg_ids = [s.get("id", "").lower() for s in negated_symptoms]
            has_neg_fever = any("sốt" in t or "sot" in i for t, i in zip(neg_terms, neg_ids))
            has_neg_bleeding = any("xuất huyết" in t or "chảy máu" in t or "huyet" in i for t, i in zip(neg_terms, neg_ids))
            has_neg_chest_pain = any("ngực" in t for t in neg_terms)

            for idx, d in enumerate(self.disease_classes):
                code = d.get("code")
                info = self.icd_db.get(code, {})
                cardinal = " ".join(info.get("cardinal_symptoms", [])).lower()

                # Bệnh nhiễm trùng cấp tính bắt buộc phải sốt (Sốt xuất huyết, Sốt rét, Cúm) -> Phạt nặng khi không sốt
                if has_neg_fever and ("sốt" in cardinal or "nhiệt độ" in cardinal):
                    p_final[idx] *= 0.01

                # Bệnh có xuất huyết (Sốt xuất huyết Dengue) -> Phạt khi không xuất huyết
                if has_neg_bleeding and ("chảy máu" in cardinal or "xuất huyết" in cardinal):
                    p_final[idx] *= 0.1

                # Bệnh tim mạch cấp -> Phạt khi không đau ngực
                if has_neg_chest_pain and "ngực" in cardinal:
                    p_final[idx] *= 0.05

                # Tăng tỷ trọng cho các bệnh lý phù hợp với đau đầu không sốt (Migraine, Tăng huyết áp, Đau vai gáy)
                if has_neg_fever and any("dau_dau" in s for s in symptom_ids):
                    if code in ["G43.9", "I10", "H81.1", "M47.9"]:
                        p_final[idx] *= 4.5

            if np.sum(p_final) > 0:
                p_final = p_final / np.sum(p_final)

        # 3.5. PATHOGNOMONIC CLINICAL SYNDROMES BOOSTING (TĂNG TỶ TRỌNG HỘI CHỨNG KINH ĐIỂN)
        user_text_lower = user_text.lower()
        all_syms_str = " ".join(symptom_names + symptom_ids).lower() + " " + user_text_lower
        has_fever = any(kw in all_syms_str for kw in ["sốt", "sot", "39 độ", "38 độ", "40 độ", "nhiệt độ"])
        has_petechiae = any(kw in all_syms_str for kw in ["chấm đỏ", "chấm xuất huyết", "xuat_huyet", "không mất", "ban xuất huyết", "nốt xuất huyết"])
        has_retro_orbital = any(kw in all_syms_str for kw in ["hốc mắt", "hoc_mat", "mắt"])
        has_arthralgia = any(kw in all_syms_str for kw in ["khớp", "khop", "đau nhức khắp", "đau mỏi"])
        has_respiratory = any(kw in all_syms_str for kw in ["ho", "đờm", "sổ mũi", "ngạt mũi", "nghẹt mũi", "chảy nước mũi", "rát họng", "đau họng", "viêm họng", "hắt hơi", "khó thở", "thở khò khè"])
        has_neck_shoulder = any(kw in all_syms_str for kw in ["mỏi cổ", "đau cổ", "cổ vai gáy", "đau mỏi cổ", "mỏi vai", "đau vai", "cổ gáy", "mỏi gáy", "cứng cổ", "thoái hóa cổ", "mỏi bả vai", "vai gáy"])
        has_back_spine = any(kw in all_syms_str for kw in ["đau lưng", "mỏi lưng", "thắt lưng", "cột sống", "thoát vị", "đĩa đệm"])
        has_eye_symptoms = any(kw in all_syms_str for kw in ["mỏi mắt", "đau mắt", "đỏ mắt", "cộm mắt", "khô mắt", "chảy nước mắt", "nhìn mờ", "thị lực"])

        for idx, d in enumerate(self.disease_classes):
            code = d.get("code")
            # 1. Hội chứng Sốt Dengue (A90): Sốt cao + (Chấm xuất huyết / Đau hốc mắt / Đau khớp)
            if code == "A90":
                if has_fever and has_petechiae:
                    p_final[idx] *= 8.0  # Chấm xuất huyết khi sốt là dấu hiệu chỉ điểm kinh điển
                elif has_fever and (has_retro_orbital or has_arthralgia):
                    p_final[idx] *= 4.5
                elif has_fever:
                    p_final[idx] *= 1.8

            # 2. Hội chứng Cúm (J10): Sốt cao + Đau mỏi người nhưng KHÔNG xuất huyết
            if code in ["J10", "J11"]:
                if has_fever and not has_petechiae and (has_arthralgia or "ho" in all_syms_str):
                    p_final[idx] *= 3.0
                elif has_petechiae:
                    p_final[idx] *= 0.1  # Cúm rất hiếm khi nổi chấm xuất huyết ấn không mất

            # 3. Phạt nặng các bệnh hô hấp (URI / Cảm / Viêm mũi họng) nếu hoàn toàn KHÔNG CÓ triệu chứng hô hấp và KHÔNG sốt
            if code.startswith("J0") or code.startswith("J1") or code.startswith("J2"):
                if not has_respiratory and not has_fever:
                    p_final[idx] *= 0.05

            # 4. Hội chứng Thoái hóa cột sống cổ / Hội chứng đau mỏi vai gáy (M47.9) & Thoát vị cổ (M50.9)
            if code == "M47.9":
                if has_neck_shoulder:
                    p_final[idx] *= 6.5
                elif has_back_spine:
                    p_final[idx] *= 3.0
            elif code == "M50.9":
                if has_neck_shoulder:
                    p_final[idx] *= 4.5

            # 5. Bệnh lý Mắt (H10.9, H52.4, H57.0)
            if code.startswith("H10") or code.startswith("H52") or code.startswith("H57"):
                if has_eye_symptoms:
                    p_final[idx] *= 5.0
                elif not has_eye_symptoms:
                    p_final[idx] *= 0.05

        if np.sum(p_final) > 0:
            p_final = p_final / np.sum(p_final)

        # 4. CLINICAL GATEKEEPER & SYMPTOM OVERLAP GUARD (CHỐNG ĐOÁN MÒ)
        # Xây dựng tập từ khóa bệnh nhân: symptom names, symptom IDs, n-gram từ user_text
        user_text_lower = user_text.lower()

        # Tích hợp tokens từ cả symptom names, symptom IDs và n-gram từ user text
        patient_tokens_raw = (
            [s.lower() for s in symptom_names if s]
            + [s.lower() for s in symptom_ids if s]
        )

        CONVERSATIONAL_STOPWORDS = {
            "chào", "bạn", "tôi", "đang", "hơi", "rất", "quá", "lắm", "thấy", "bị", "cảm",
            "giúp", "bác", "sĩ", "cho", "hỏi", "với", "này", "kia", "người", "ngày", "nào",
            "gì", "được", "không", "nhé", "dạ", "ạ", "ơi", "alo", "thưa"
        }

        # Sinh unigram (trừ stopwords), bigram và trigram từ user_text
        words = re.sub(r'[^\w\s]', ' ', user_text_lower).split()
        ngrams: set = {w for w in words if w not in CONVERSATIONAL_STOPWORDS and len(w) >= 2}
        for i in range(len(words) - 1):
            if words[i] not in CONVERSATIONAL_STOPWORDS or words[i+1] not in CONVERSATIONAL_STOPWORDS:
                ngrams.add(f"{words[i]} {words[i+1]}")  # bigrams
        for i in range(len(words) - 2):
            ngrams.add(f"{words[i]} {words[i+1]} {words[i+2]}")  # trigrams
        patient_tokens_raw += list(ngrams)

        # Bổ sung từ khóa giải phẫu học rút gọn từ symptom IDs (e.g. "di_ung_da" -> ["di", "ung", "da"])
        for sid in symptom_ids:
            parts = [p for p in sid.replace("_", " ").split() if p not in CONVERSATIONAL_STOPWORDS]
            patient_tokens_raw += parts

        patient_tokens = set(t.strip() for t in patient_tokens_raw if t and len(t.strip()) >= 2)

        overlap_mask = np.zeros(num_classes, dtype=bool)
        for idx, d in enumerate(self.disease_classes):
            code = d.get("code")
            info = self.icd_db.get(code, {})
            cardinal = [cs.lower() for cs in info.get("cardinal_symptoms", [])]
            all_syms = [s.lower() for s in info.get("all_symptoms", [])]
            name_vi = d.get("name", "").lower()

            # Kiểm tra overlap: mỗi token bệnh nhân có chứa trong hoặc chia sẻ chuỗi con với triệu chứng bệnh này
            has_symptom_match = False

            # Thử khớp token bệnh nhân với cardinal symptoms (full string OR substring OR word-token overlap)
            for pt in patient_tokens:
                for cs in cardinal:
                    if len(cs) >= 3 and (pt in cs or cs in pt or _token_overlap(pt, cs)):
                        has_symptom_match = True
                        break
                if has_symptom_match:
                    break

            # Thử khớp với all_symptoms
            if not has_symptom_match:
                for pt in patient_tokens:
                    for asym in all_syms:
                        if len(asym) >= 3 and (pt in asym or asym in pt or _token_overlap(pt, asym)):
                            has_symptom_match = True
                            break
                    if has_symptom_match:
                        break

            # Tên bệnh có trùng khớp token không
            if not has_symptom_match:
                for pt in patient_tokens:
                    if len(pt) >= 3 and (pt in name_vi or name_vi in pt):
                        has_symptom_match = True
                        break

            # Kiểm tra văn bản bệnh nhân có chứa cardinal symptom của bệnh này không (full text scan)
            if not has_symptom_match:
                for cs in cardinal:
                    if len(cs) >= 3 and cs in user_text_lower:
                        has_symptom_match = True
                        break

            # Nếu có kết quả xét nghiệm bất thường thì cho qua (lab anomaly override)
            if not has_symptom_match and has_lab:
                has_symptom_match = True

            if has_symptom_match:
                overlap_mask[idx] = True

        # Triệt tiêu xác suất của các bệnh hoàn toàn không có triệu chứng khớp (Zero Overlap)
        # Loại bỏ triệt để các bệnh đoán mò (Chắp lẹo mắt, Loét giác mạc, Alzheimer...)
        p_final[~overlap_mask] = 0.0

        if np.sum(p_final) > 0:
            p_final = p_final / np.sum(p_final)
        else:
            p_final = np.zeros(num_classes, dtype=np.float32)

        # 5. Sắp xếp và lọc bệnh theo ngưỡng tin cậy lâm sàng nghiêm ngặt
        sorted_indices = np.argsort(p_final)[::-1]
        top_predictions = []

        # Chỉ nhận những bệnh có xác suất >= 8% (0.08) VÀ có overlap
        for idx in sorted_indices:
            prob = float(p_final[idx])
            if prob < 0.08:  # Ngưỡng sàn tin cậy - loại bỏ các bệnh dưới 8%
                break
            if not overlap_mask[idx]:
                continue

            disease = self.disease_classes[idx]
            code = disease.get("code")
            icd_info = self.icd_db.get(code, {})

            top_predictions.append({
                "rank": len(top_predictions) + 1,
                "icd_code": code,
                "disease_name_vi": disease.get("name"),
                "department": disease.get("dept"),
                "probability": round(prob, 4),
                "probability_percentage": f"{round(prob * 100, 1)}%",
                "severity": icd_info.get("severity", "Medium"),
                "recommendation": icd_info.get("emergency_warning", "Theo dõi và thăm khám chuyên khoa khi có bất thường.")
            })
            if len(top_predictions) >= 3:
                break

        # Nếu chưa đủ bệnh do ngưỡng nhưng có bệnh overlap rõ ràng, nhận tối đa 2 bệnh cao nhất
        if not top_predictions:
            for idx in sorted_indices:
                prob = float(p_final[idx])
                if prob <= 0.02 or not overlap_mask[idx]:
                    continue
                disease = self.disease_classes[idx]
                code = disease.get("code")
                icd_info = self.icd_db.get(code, {})
                top_predictions.append({
                    "rank": len(top_predictions) + 1,
                    "icd_code": code,
                    "disease_name_vi": disease.get("name"),
                    "department": disease.get("dept"),
                    "probability": round(prob, 4),
                    "probability_percentage": f"{round(prob * 100, 1)}%",
                    "severity": icd_info.get("severity", "Medium"),
                    "recommendation": icd_info.get("emergency_warning", "Theo dõi và thăm khám chuyên khoa khi có bất thường.")
                })
                if len(top_predictions) >= 2:
                    break

        # 6. Clarification Assessment với 3 tầng phân định lâm sàng
        top_prob = float(top_predictions[0]["probability"]) if top_predictions else (float(p_final[sorted_indices[0]]) if len(sorted_indices) > 0 else 0.0)
        clarification_res = self.clarification_engine.generate_clarification_questions(
            p_final,
            self.disease_classes,
            symptom_names,
            user_text=user_text
        )
        stage = self.clarification_engine.determine_clinical_stage(
            top_probability=top_prob,
            symptom_count=len(symptom_names),
            clarification_turns_count=0
        )
        clarification_res["clinical_stage"] = stage
        clarification_res["needs_clarification"] = (stage != "definitive_conclusion")

        return {
            "top_predictions": top_predictions,
            "fusion_metadata": {
                "alpha_tabular_weight": round(alpha_used, 2),
                "has_lab_indicators": has_lab,
                "total_indicators_used": len(lab_indicators)
            },
            "clarification": clarification_res
        }
