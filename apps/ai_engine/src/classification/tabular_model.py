import os
import json
import logging
from typing import Dict, Any, List, Optional
import numpy as np

# Prevent OpenMP thread contention deadlock on Windows
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

logger = logging.getLogger(__name__)

class TabularClinicalClassifier:
    """
    Phân loại lâm sàng đa bệnh lý (13 nhóm bệnh) từ chỉ số sinh hóa máu (OCR)
    và vector triệu chứng trích xuất từ văn bản/giọng nói.
    """

    FEATURE_NAMES = [
        "WBC", "PLT", "RBC", "HGB", "HCT", "AST", "ALT", "GLUCOSE", "CREATININE",
        "has_sot", "has_dau_dau", "has_dau_nguc", "has_kho_tho", "has_dau_bung",
        "has_non_oi", "has_tieu_chay", "has_chay_mau", "has_meo_mieng", "has_di_ung_da",
        "has_vang_da", "has_tieu_buot", "has_dau_khop", "has_ngua_da"
    ]

    DISEASE_CLASSES = [
        {"code": "A90", "name": "Sốt xuất huyết Dengue", "dept": "Truyền nhiễm"},
        {"code": "I21.9", "name": "Nhồi máu cơ tim cấp", "dept": "Tim mạch"},
        {"code": "I64", "name": "Đột quỵ não", "dept": "Thần kinh"},
        {"code": "J18.9", "name": "Viêm phổi cấp", "dept": "Hô hấp"},
        {"code": "J00", "name": "Viêm mũi họng / Cảm lạnh", "dept": "Tai Mũi Họng"},
        {"code": "K29.7", "name": "Viêm dạ dày tá tràng", "dept": "Tiêu hóa"},
        {"code": "E11.9", "name": "Đái tháo đường týp 2", "dept": "Nội tiết"},
        {"code": "K76.0", "name": "Bệnh lý gan / Men gan cao", "dept": "Gan mật"},
        {"code": "L20.9", "name": "Viêm da dị ứng / Dị ứng da mặt", "dept": "Da liễu"},
        {"code": "J45.9", "name": "Hen phế quản (Hen suyễn)", "dept": "Hô hấp"},
        {"code": "K35.8", "name": "Viêm ruột thừa cấp", "dept": "Ngoại khoa"},
        {"code": "N20.0", "name": "Sỏi thận / Cơn đau quặn thận", "dept": "Thận - Tiết niệu"},
        {"code": "B18.2", "name": "Viêm gan virus mạn tính", "dept": "Truyền nhiễm"}
    ]

    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.DISEASE_CLASSES = []
        self._load_disease_classes()
        target_path = model_path or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "models_weights", "tabular_xgboost.json"))
        if os.path.exists(target_path):
            self._load_xgboost(target_path)

    def _load_disease_classes(self):
        icd_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "data", "medical_lexicon", "icd10_codes.json"))
        idx_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "models_weights", "disease_classes_index.json"))

        icd_map = {}
        if os.path.exists(icd_path):
            try:
                with open(icd_path, "r", encoding="utf-8") as f:
                    icd_map = json.load(f)
            except Exception as e:
                logger.warning(f"Error loading icd10_codes.json: {e}")

        # Ưu tiên thứ tự đồng bộ với model đã huấn luyện (211 classes)
        if os.path.exists(idx_path):
            try:
                with open(idx_path, "r", encoding="utf-8") as f:
                    idx_data = json.load(f)
                    codes = idx_data.get("disease_codes", [])
                    # Model XGBoost & NLP Classifier được train với đúng 211 classes hàng đầu
                    target_codes = codes[:211] if len(codes) >= 211 else codes
                    for code in target_codes:
                        info = icd_map.get(code, {})
                        self.DISEASE_CLASSES.append({
                            "code": code,
                            "name": info.get("name_vi", code),
                            "dept": info.get("department", "Chuyên khoa"),
                            "severity": info.get("severity", "Medium")
                        })
            except Exception as e:
                logger.warning(f"Error loading disease_classes_index.json: {e}")

        if not self.DISEASE_CLASSES and icd_map:
            for code, info in icd_map.items():
                self.DISEASE_CLASSES.append({
                    "code": code,
                    "name": info.get("name_vi", code),
                    "dept": info.get("department", "Chuyên khoa"),
                    "severity": info.get("severity", "Medium")
                })

        if not self.DISEASE_CLASSES:
            self.DISEASE_CLASSES = [
                {"code": "A90", "name": "Sốt xuất huyết Dengue", "dept": "Truyền nhiễm"},
                {"code": "I21.9", "name": "Nhồi máu cơ tim cấp", "dept": "Tim mạch"},
                {"code": "I64", "name": "Đột quỵ não", "dept": "Thần kinh"},
                {"code": "J18.9", "name": "Viêm phổi cấp", "dept": "Hô hấp"},
                {"code": "J00", "name": "Viêm mũi họng / Cảm lạnh", "dept": "Tai Mũi Họng"},
                {"code": "K29.7", "name": "Viêm dạ dày tá tràng", "dept": "Tiêu hóa"},
                {"code": "E11.9", "name": "Đái tháo đường týp 2", "dept": "Nội tiết"},
                {"code": "K76.0", "name": "Bệnh lý gan / Men gan cao", "dept": "Gan mật"},
                {"code": "L20.9", "name": "Viêm da dị ứng / Dị ứng da mặt", "dept": "Da liễu"}
            ]

    def _load_xgboost(self, model_path: str):
        try:
            import xgboost as xgb
            self.model = xgb.Booster()
            self.model.load_model(model_path)
            logger.info("XGBoost Tabular model loaded successfully.")
        except Exception as e:
            logger.warning(f"Could not load XGBoost model from {model_path} ({e}). Using expert clinical decision matrix.")
            self.model = None

    def construct_feature_vector(self, lab_data: Dict[str, Any], symptom_ids: List[str]) -> np.ndarray:
        """
        Xây dựng vector đặc trưng 1D từ dữ liệu lab và triệu chứng.
        """
        vec = []
        defaults = {
            "WBC": 6.5, "PLT": 250.0, "RBC": 4.5, "HGB": 140.0, "HCT": 42.0,
            "AST": 25.0, "ALT": 25.0, "GLUCOSE": 5.2, "CREATININE": 75.0
        }
        for feat in self.FEATURE_NAMES[:9]:
            if feat in lab_data:
                val = lab_data[feat]
                vec.append(float(val.get("value", val) if isinstance(val, dict) else val))
            else:
                vec.append(defaults.get(feat, 0.0))

        sym_set = set([s.lower() for s in symptom_ids])
        vec.append(1.0 if any("sot" in s for s in sym_set) else 0.0)
        vec.append(1.0 if any("dau_dau" in s or "nhuc_dau" in s for s in sym_set) else 0.0)
        vec.append(1.0 if any("nguc" in s for s in sym_set) else 0.0)
        vec.append(1.0 if any("tho" in s for s in sym_set) else 0.0)
        vec.append(1.0 if any("bung" in s or "thuong_vi" in s for s in sym_set) else 0.0)
        vec.append(1.0 if any("non" in s or "oi" in s for s in sym_set) else 0.0)
        vec.append(1.0 if any("chay" in s and "tieu" in s for s in sym_set) else 0.0)
        vec.append(1.0 if any("chay_mau" in s or "xuat_huyet" in s for s in sym_set) else 0.0)
        vec.append(1.0 if any("meo" in s or "liet" in s for s in sym_set) else 0.0)
        # has_di_ung_da (index 18): Viêm da dị ứng / Dị ứng da mặt - bao gồm mọi triệu chứng da liễu liên quan
        vec.append(1.0 if any(
            "di_ung_da" in s or "di_ung" in s or "rat_da" in s or "do_da" in s or "man_do" in s
            or "phat_ban" in s or "sym_da_mat" in s or "viem_da" in s or "da_mat" in s
            or "kem_chong_nang" in s or "man_ngua" in s
            for s in sym_set
        ) else 0.0)
        vec.append(1.0 if any("vang_da" in s or "vang_mat" in s for s in sym_set) else 0.0)
        vec.append(1.0 if any("buot" in s or "tieu_buot" in s or "tieu_rat" in s for s in sym_set) else 0.0)
        vec.append(1.0 if any("khop" in s or "gout" in s or "xuong" in s for s in sym_set) else 0.0)
        # has_ngua_da (index 22): Ngứa da / Mề đay / Mẩn ngứa - bao gồm mọi biểu hiện ngứa da
        vec.append(1.0 if any(
            "ngua" in s or "man" in s or "me_day" in s or "noi_me_day" in s or "phat_ban" in s
            for s in sym_set
        ) else 0.0)

        return np.array(vec, dtype=np.float32).reshape(1, -1)

    def predict_proba(self, lab_data: Dict[str, Any], symptom_ids: List[str]) -> np.ndarray:
        """
        Dự đoán phân bố xác suất của các nhóm bệnh. Trả về mảng 1D float.
        """
        feat_vec = self.construct_feature_vector(lab_data, symptom_ids)

        if self.model is not None:
            try:
                import xgboost as xgb
                dmatrix = xgb.DMatrix(feat_vec, feature_names=self.FEATURE_NAMES)
                return self.model.predict(dmatrix)[0]
            except Exception as e:
                logger.error(f"XGBoost prediction error: {e}")

        # Expert clinical decision logic (Dynamic ICD-10 Rule Matrix)
        num_classes = len(self.DISEASE_CLASSES)
        probs = np.ones(num_classes, dtype=np.float32) * 0.05
        code_to_idx = {c["code"]: i for i, c in enumerate(self.DISEASE_CLASSES)}

        def add_score(code: str, score: float):
            if code in code_to_idx:
                probs[code_to_idx[code]] += score

        # 1. Sốt xuất huyết Dengue (A90)
        if feat_vec[0, 9] and (feat_vec[0, 1] < 100.0 or feat_vec[0, 16] or feat_vec[0, 0] < 4.0):
            add_score("A90", 0.85)
        elif feat_vec[0, 9] and feat_vec[0, 16]:
            add_score("A90", 0.70)

        # 2. Cảm cúm / Nhiễm siêu vi (J10)
        if feat_vec[0, 9] and feat_vec[0, 10] and not feat_vec[0, 11] and not feat_vec[0, 12]:
            add_score("J10", 0.65)

        # 3. Nhồi máu cơ tim cấp (I21.9) & Đau thắt ngực (I20)
        if feat_vec[0, 11]:
            score = 0.85 if feat_vec[0, 12] else 0.55
            add_score("I21.9", score)
            add_score("I20", score * 0.85)

        # 4. Đột quỵ não (I64)
        if feat_vec[0, 17]:
            add_score("I64", 0.90)

        # 5. Viêm phổi cấp (J18.9)
        if (feat_vec[0, 9] or feat_vec[0, 0] > 10.0) and feat_vec[0, 12]:
            add_score("J18.9", 0.70)

        # 6. Viêm mũi họng / Cảm lạnh (J00) & Cảm cúm (J10)
        if feat_vec[0, 10] and not feat_vec[0, 11] and not feat_vec[0, 12] and not feat_vec[0, 13]:
            add_score("J00", 0.75)
            add_score("J10", 0.50)

        # 7. Viêm dạ dày tá tràng (K29.7)
        if feat_vec[0, 13] or feat_vec[0, 14]:
            add_score("K29.7", 0.60)

        # 8. Viêm ruột thừa cấp (K35.8)
        if feat_vec[0, 13] and (feat_vec[0, 9] or feat_vec[0, 14] or feat_vec[0, 0] > 10.0):
            add_score("K35.8", 0.65)

        # 9. Đái tháo đường týp 2 (E11.9)
        if feat_vec[0, 7] >= 7.0:
            add_score("E11.9", 0.85)
        elif feat_vec[0, 7] >= 6.1:
            add_score("E11.9", 0.45)

        # 10. Bệnh lý gan / Men gan cao (K76.0, B18.2)
        if feat_vec[0, 5] > 40.0 or feat_vec[0, 6] > 40.0:
            add_score("K76.0", 0.70)
            add_score("B18.2", 0.55)

        # 11. Viêm da dị ứng / Dị ứng da (L20.9) & Mề đay / Nổi mề đay (L50.9)
        if feat_vec[0, 18]:
            add_score("L20.9", 0.75)  # Tăng từ 0.65 lên 0.75 để ưu tiên Da liễu
        if feat_vec[0, 22]:  # has_ngua_da
            add_score("L50.9", 0.55)  # Mề đay / Nổi mề đay
            add_score("L20.9", 0.40)  # Ngứa da cũng có thể là viêm da dị ứng

        # 12. Hen phế quản (J45.9)
        if feat_vec[0, 12] and not feat_vec[0, 9] and not feat_vec[0, 11]:
            add_score("J45.9", 0.60)

        # 13. Sỏi thận / Cơn đau quặn thận (N20.0)
        if feat_vec[0, 13] and not feat_vec[0, 14]:
            add_score("N20.0", 0.50)

        # Chuẩn hóa Softmax
        exp_p = np.exp(probs - np.max(probs))
        return exp_p / np.sum(exp_p)
