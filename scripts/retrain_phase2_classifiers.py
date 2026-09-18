"""
Script Retrain Mô Hình AI Lâm Sàng Phase 2 (211+ Bệnh Lý Chuẩn Bộ Y Tế):
1. Huấn luyện lại Tabular XGBoost (chỉ số sinh hóa máu + cờ triệu chứng) cho 211+ bệnh.
2. Huấn luyện lại NLP Semantic Classifier cho 211+ bệnh.
3. Xuất model weights vào apps/ai_engine/models_weights/.
"""
import os
import sys
import json
import logging
import numpy as np
import joblib

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("RetrainPhase2")

import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import accuracy_score

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "apps", "ai_engine", "models_weights")
LEXICON_DIR = os.path.join(BASE_DIR, "data", "medical_lexicon")
ICD_PATH = os.path.join(LEXICON_DIR, "icd10_codes.json")

os.makedirs(MODELS_DIR, exist_ok=True)

# 1. Đọc toàn bộ CSDL 211+ bệnh từ icd10_codes.json
with open(ICD_PATH, "r", encoding="utf-8") as f:
    icd_data = json.load(f)

disease_codes = list(icd_data.keys())
num_diseases = len(disease_codes)
logger.info(f"Loaded {num_diseases} diseases from {ICD_PATH}")

code_to_idx = {code: i for i, code in enumerate(disease_codes)}
idx_to_code = {i: code for i, code in enumerate(disease_codes)}

# Lưu lại mapping index để inference tra cứu tức thì
mapping_path = os.path.join(MODELS_DIR, "disease_classes_index.json")
with open(mapping_path, "w", encoding="utf-8") as f:
    json.dump({
        "disease_codes": disease_codes,
        "code_to_idx": code_to_idx,
        "total_classes": num_diseases
    }, f, ensure_ascii=False, indent=2)
logger.info(f"Saved disease index mapping to {mapping_path}")

# ==============================================================================
# 2. HUẤN LUYỆN NLP SYMPTOM CLASSIFIER TRÊN 211+ BỆNH
# ==============================================================================
logger.info("--- [1/2] BẮT ĐẦU HUẤN LUYỆN NLP SYMPTOM CLASSIFIER (211+ BỆNH) ---")

nlp_texts = []
nlp_labels = []

# Xây dựng ngữ liệu huấn luyện từ mô tả và triệu chứng của từng bệnh
for code, info in icd_data.items():
    idx = code_to_idx[code]
    name_vi = info.get("name_vi", "")
    cardinal = info.get("cardinal_symptoms", [])
    all_syms = info.get("all_symptoms", [])
    desc = info.get("description", "")

    # Mẫu 1: Tên bệnh + triệu chứng chính
    nlp_texts.append(f"Tôi bị {name_vi}, có biểu hiện {', '.join(cardinal)}")
    nlp_labels.append(idx)

    # Mẫu 2: Triệu chứng toàn bộ
    nlp_texts.append(f"Bệnh nhân có triệu chứng: {', '.join(all_syms)}. {desc}")
    nlp_labels.append(idx)

    # Mẫu 3: Lời kể bệnh nhân tự nhiên
    for s in cardinal:
        nlp_texts.append(f"Mấy hôm nay tôi thấy bị {s}, người rất mệt mỏi khó chịu")
        nlp_labels.append(idx)

    if len(cardinal) >= 2:
        nlp_texts.append(f"Em bị {cardinal[0]} và {cardinal[1]}, lo lắng không biết có sao không")
        nlp_labels.append(idx)

# Data Augmentation: Nhân rộng dữ liệu với nhiễu nhẹ
aug_texts = []
aug_labels = []
for text, lbl in zip(nlp_texts, nlp_labels):
    words = text.split()
    for _ in range(12):
        keep = [w for w in words if np.random.rand() > 0.08]
        if keep:
            aug_texts.append(" ".join(keep))
            aug_labels.append(lbl)

logger.info(f"Total NLP training samples generated: {len(aug_texts)}")

vectorizer = TfidfVectorizer(
    ngram_range=(1, 3),
    max_features=12000,
    sublinear_tf=True
)
X_tfidf = vectorizer.fit_transform(aug_texts)
y_nlp = np.array(aug_labels)

X_train, X_val, y_train, y_val = train_test_split(X_tfidf, y_nlp, test_size=0.15, random_state=42, stratify=y_nlp)

base_lr = LogisticRegression(C=5.0, max_iter=800, class_weight='balanced')
calibrated_clf = CalibratedClassifierCV(estimator=base_lr, cv=3)
calibrated_clf.fit(X_train, y_train)

val_acc = accuracy_score(y_val, calibrated_clf.predict(X_val))
logger.info(f"✅ NLP Classifier Validation Accuracy across {num_diseases} classes: {val_acc * 100:.2f}%")

# Lưu mô hình NLP
joblib.dump(calibrated_clf, os.path.join(MODELS_DIR, "nlp_symptom_classifier.pkl"))
joblib.dump(vectorizer, os.path.join(MODELS_DIR, "nlp_tfidf_vectorizer.pkl"))
logger.info("Saved nlp_symptom_classifier.pkl and nlp_tfidf_vectorizer.pkl successfully.")

# ==============================================================================
# 3. HUẤN LUYỆN TABULAR XGBOOST TRÊN 211+ BỆNH
# ==============================================================================
logger.info("--- [2/2] BẮT ĐẦU HUẤN LUYỆN TABULAR XGBOOST (211+ BỆNH) ---")

FEATURE_COLS = [
    'WBC', 'PLT', 'RBC', 'HGB', 'HCT', 'AST', 'ALT', 'GLUCOSE', 'CREATININE',
    'has_sot', 'has_dau_dau', 'has_dau_nguc', 'has_kho_tho', 'has_dau_bung',
    'has_non_oi', 'has_tieu_chay', 'has_chay_mau', 'has_meo_mieng', 'has_di_ung_da',
    'has_vang_da', 'has_tieu_buot', 'has_dau_khop', 'has_ngua_da'
]

np.random.seed(42)
N_SAMPLES = 8500
X_tab = np.zeros((N_SAMPLES, len(FEATURE_COLS)), dtype=np.float32)
y_tab = np.zeros(N_SAMPLES, dtype=np.int32)

for i in range(N_SAMPLES):
    d_idx = np.random.randint(0, num_diseases)
    code = idx_to_code[d_idx]
    info = icd_data[code]
    all_sym_text = " ".join(info.get("cardinal_symptoms", []) + info.get("all_symptoms", [])).lower()

    # Sinh chỉ số lab sinh lý bình thường
    wbc = np.random.uniform(4.5, 9.5)
    plt = np.random.uniform(180, 350)
    rbc = np.random.uniform(4.0, 5.2)
    hgb = np.random.uniform(130, 155)
    hct = np.random.uniform(38, 46)
    ast = np.random.uniform(15, 35)
    alt = np.random.uniform(15, 35)
    glu = np.random.uniform(4.2, 5.8)
    cre = np.random.uniform(60, 95)

    # Điều chỉnh chỉ số lab đặc thù theo bệnh
    if "dengue" in all_sym_text or code == "A90":
        plt = np.random.uniform(25, 95)   # Giảm tiểu cầu sâu
        wbc = np.random.uniform(1.8, 3.8) # Giảm bạch cầu
        hct = np.random.uniform(46, 54)   # Cô đặc máu
    elif "gan" in all_sym_text or "hepatitis" in code.lower() or "k70" in code.lower() or "b18" in code.lower():
        ast = np.random.uniform(120, 850)
        alt = np.random.uniform(150, 950)
    elif "thận" in all_sym_text or "n18" in code.lower() or "n10" in code.lower():
        cre = np.random.uniform(140, 500)
    elif "đái tháo đường" in all_sym_text or "e10" in code.lower() or "e11" in code.lower():
        glu = np.random.uniform(8.5, 18.0)
    elif "nhiễm khuẩn" in all_sym_text or "viêm phổi" in all_sym_text or "viêm ruột thừa" in all_sym_text:
        wbc = np.random.uniform(13.0, 22.0)
    elif "thiếu máu" in all_sym_text or "d50" in code.lower() or "d64" in code.lower():
        hgb = np.random.uniform(65, 95)
        rbc = np.random.uniform(2.2, 3.4)

    # Gán cờ triệu chứng
    has_sot = 1 if ("sốt" in all_sym_text or "nhiệt" in all_sym_text) and np.random.rand() > 0.15 else 0
    has_dau_dau = 1 if "đau đầu" in all_sym_text and np.random.rand() > 0.15 else 0
    has_dau_nguc = 1 if ("đau ngực" in all_sym_text or "tức ngực" in all_sym_text) and np.random.rand() > 0.15 else 0
    has_kho_tho = 1 if "khó thở" in all_sym_text and np.random.rand() > 0.15 else 0
    has_dau_bung = 1 if "đau bụng" in all_sym_text and np.random.rand() > 0.15 else 0
    has_non_oi = 1 if ("nôn" in all_sym_text or "buồn nôn" in all_sym_text) and np.random.rand() > 0.2 else 0
    has_tieu_chay = 1 if "tiêu chảy" in all_sym_text and np.random.rand() > 0.15 else 0
    has_chay_mau = 1 if ("chảy máu" in all_sym_text or "xuất huyết" in all_sym_text) and np.random.rand() > 0.15 else 0
    has_meo_mieng = 1 if ("méo miệng" in all_sym_text or "liệt" in all_sym_text) and np.random.rand() > 0.1 else 0
    has_di_ung_da = 1 if ("dị ứng" in all_sym_text or "mày đay" in all_sym_text or "phát ban" in all_sym_text) and np.random.rand() > 0.15 else 0
    has_vang_da = 1 if "vàng da" in all_sym_text and np.random.rand() > 0.1 else 0
    has_tieu_buot = 1 if ("tiểu buốt" in all_sym_text or "tiểu rắt" in all_sym_text) and np.random.rand() > 0.1 else 0
    has_dau_khop = 1 if ("đau khớp" in all_sym_text or "sưng khớp" in all_sym_text or "gout" in all_sym_text) and np.random.rand() > 0.1 else 0
    has_ngua_da = 1 if "ngứa" in all_sym_text and np.random.rand() > 0.15 else 0

    X_tab[i] = [
        wbc, plt, rbc, hgb, hct, ast, alt, glu, cre,
        has_sot, has_dau_dau, has_dau_nguc, has_kho_tho, has_dau_bung,
        has_non_oi, has_tieu_chay, has_chay_mau, has_meo_mieng, has_di_ung_da,
        has_vang_da, has_tieu_buot, has_dau_khop, has_ngua_da
    ]
    y_tab[i] = d_idx

X_train_t, X_val_t, y_train_t, y_val_t = train_test_split(X_tab, y_tab, test_size=0.15, random_state=42)

xgb_model = xgb.XGBClassifier(
    n_estimators=180,
    max_depth=6,
    learning_rate=0.08,
    subsample=0.85,
    colsample_bytree=0.85,
    objective="multi:softprob",
    num_class=num_diseases,
    random_state=42,
    n_jobs=2
)
xgb_model.fit(X_train_t, y_train_t)

xgb_val_acc = accuracy_score(y_val_t, xgb_model.predict(X_val_t))
logger.info(f"✅ XGBoost Tabular Classifier Validation Accuracy ({num_diseases} classes): {xgb_val_acc * 100:.2f}%")

# Lưu mô hình XGBoost
xgb_path = os.path.join(MODELS_DIR, "tabular_xgboost.json")
xgb_model.save_model(xgb_path)
logger.info(f"Saved tabular_xgboost.json to {xgb_path}")

print(f"🎉 TẤT CẢ MODEL PHASE 2 ĐÃ ĐƯỢC HUẤN LUYỆN VÀ XUẤT THÀNH CÔNG CHO {num_diseases} BỆNH LÝ!")
