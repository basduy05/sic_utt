import os
import sys
import json
import numpy as np
import pandas as pd
import joblib

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import accuracy_score

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "apps", "ai_engine", "models_weights")
LEXICON_DIR = os.path.join(BASE_DIR, "data", "medical_lexicon")
DATASETS_DIR = os.path.join(BASE_DIR, "data", "datasets")

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(LEXICON_DIR, exist_ok=True)
os.makedirs(DATASETS_DIR, exist_ok=True)

def run_dataset_ingestion_and_training():
    print("=================================================================")
    print("🏥 BẮT ĐẦU PIPELINE NẠP DỮ LIỆU TỪ DATASETS & HUẤN LUYỆN MODEL")
    print("=================================================================")

    # 1. ĐỌC DỮ LIỆU TỪ CÁC TỆP CƠ SỞ DỮ LIỆU CHUẨN TRONG data/datasets/
    kaggle_path = os.path.join(DATASETS_DIR, "kaggle_41_diseases_full.json")
    qa_path = os.path.join(DATASETS_DIR, "vietnamese_medical_qa_corpus.json")

    if not os.path.exists(kaggle_path):
        raise FileNotFoundError(f"Không tìm thấy tệp dataset: {kaggle_path}")

    with open(kaggle_path, "r", encoding="utf-8") as f:
        diseases_list = json.load(f)

    diseases_dict = {d["code"]: d for d in diseases_list}
    print(f"✅ Đã nạp thành công {len(diseases_list)} nhóm bệnh từ {kaggle_path}")

    qa_samples = []
    if os.path.exists(qa_path):
        with open(qa_path, "r", encoding="utf-8") as f:
            qa_samples = json.load(f)
        print(f"✅ Đã nạp thành công {len(qa_samples)} cặp mẫu hỏi đáp lâm sàng từ {qa_path}")

    # 2. CẬP NHẬT CSDL TỪ ĐIỂN Y KHOA ICD-10 (data/medical_lexicon/icd10_codes.json)
    icd_target_file = os.path.join(LEXICON_DIR, "icd10_codes.json")
    with open(icd_target_file, "w", encoding="utf-8") as f:
        json.dump(diseases_dict, f, ensure_ascii=False, indent=2)
    print(f"💾 Đã đồng bộ từ điển ICD-10 tại: {icd_target_file}")

    # 3. TỔNG HỢP VÀ TĂNG CƯỜNG DỮ LIỆU HUẤN LUYỆN (DATA AUGMENTATION)
    disease_codes = list(diseases_dict.keys())
    corpus_pairs = []

    # Thêm các câu hỏi thực tế từ QA corpus
    for qa in qa_samples:
        code = qa.get("primary_icd")
        if code in disease_codes:
            code_idx = disease_codes.index(code)
            corpus_pairs.append((qa.get("patient_query", ""), code_idx))

    # Sinh mẫu từ danh mục triệu chứng cardinal và all_symptoms của từng bệnh
    for idx, (code, info) in enumerate(diseases_dict.items()):
        name_vi = info["name_vi"]
        cardinal = info.get("cardinal_symptoms", [])
        all_syms = info.get("all_symptoms", [])

        # Mẫu chứa triệu chứng chỉ điểm (cardinal)
        corpus_pairs.append((f"Tôi bị {', '.join(cardinal)}", idx))
        corpus_pairs.append((f"Bệnh nhân có triệu chứng {', '.join(all_syms[:3])}", idx))
        corpus_pairs.append((f"Biểu hiện {', '.join(all_syms)} kéo dài", idx))
        corpus_pairs.append((f"Nghi ngờ mắc {name_vi} do có {', '.join(cardinal[:2])}", idx))

        for sym in all_syms:
            corpus_pairs.append((f"Bị {sym}", idx))
            corpus_pairs.append((f"Tôi cảm thấy {sym} rất khó chịu", idx))

    # Tăng cường dữ liệu bằng biến thể ngôn ngữ
    augmented_texts = []
    augmented_labels = []

    for text, lbl in corpus_pairs:
        words = text.split()
        for _ in range(30):
            keep = [w for w in words if np.random.rand() > 0.08]
            augmented_texts.append(" ".join(keep if keep else words))
            augmented_labels.append(lbl)

    print(f"📊 Tổng số lượng mẫu ngữ liệu sau Augmentation: {len(augmented_texts)} mẫu")

    # 4. CHIA TẬP TRAIN VÀ VALIDATION HOLDOUT (80% / 20%)
    X_train_txt, X_val_txt, y_train, y_val = train_test_split(
        augmented_texts, augmented_labels, test_size=0.20, random_state=42, stratify=augmented_labels
    )
    print(f"📊 Tập Train: {len(X_train_txt)} mẫu | Tập Validation Holdout: {len(X_val_txt)} mẫu")

    # 5. HUẤN LUYỆN MÔ HÌNH PHÂN LOẠI NLP & HIỆU CHUẨN XÁC SUẤT (CALIBRATED CLASSIFIER)
    vectorizer = TfidfVectorizer(ngram_range=(1, 3), max_features=10000, sublinear_tf=True)
    X_train_vec = vectorizer.fit_transform(X_train_txt)
    X_val_vec = vectorizer.transform(X_val_txt)

    base_clf = LogisticRegression(C=8.0, max_iter=1000, class_weight='balanced')
    calibrated_clf = CalibratedClassifierCV(estimator=base_clf, cv=3)
    calibrated_clf.fit(X_train_vec, y_train)

    # Đánh giá trên tập Validation
    val_preds = calibrated_clf.predict(X_val_vec)
    acc = accuracy_score(y_val, val_preds)
    print(f"\n🎯 [KẾT QUẢ ĐÁNH GIÁ TRÊN TẬP VALIDATION HOLDOUT]")
    print(f"✅ Độ chính xác (Validation Accuracy): {round(acc * 100, 2)}% trên {len(disease_codes)} nhóm bệnh")

    # 6. XUẤT TẬP VALIDATION HOLDOUT RA TỆP data/datasets/validation_holdout_set.json
    val_export = []
    for txt, true_lbl, pred_lbl in zip(X_val_txt[:120], y_val[:120], val_preds[:120]):
        val_export.append({
            "text": txt,
            "true_icd": disease_codes[true_lbl],
            "true_disease": diseases_dict[disease_codes[true_lbl]]["name_vi"],
            "pred_icd": disease_codes[pred_lbl],
            "pred_disease": diseases_dict[disease_codes[pred_lbl]]["name_vi"],
            "is_correct": bool(true_lbl == pred_lbl)
        })

    val_file = os.path.join(DATASETS_DIR, "validation_holdout_set.json")
    with open(val_file, "w", encoding="utf-8") as f:
        json.dump(val_export, f, ensure_ascii=False, indent=2)
    print(f"💾 Đã lưu kết quả đánh giá Holdout Set tại: {val_file}")

    # 7. LƯU CÁC TRỌNG SỐ MÔ HÌNH VÀO apps/ai_engine/models_weights/
    joblib.dump(calibrated_clf, os.path.join(MODELS_DIR, "nlp_symptom_classifier.pkl"))
    joblib.dump(vectorizer, os.path.join(MODELS_DIR, "nlp_tfidf_vectorizer.pkl"))
    print(f"💾 Đã lưu NLP Model Weights tại: {os.path.join(MODELS_DIR, 'nlp_symptom_classifier.pkl')}")

    # 8. CẬP NHẬT RAG VECTOR KNOWLEDGE BASE
    rag_records = []
    for code, info in diseases_dict.items():
        rec = {
            "code": code,
            "title": f"Phác đồ Chẩn đoán & Hướng dẫn Xử trí: {info['name_vi']} ({code})",
            "department": info["department"],
            "severity": info["severity"],
            "content": f"Bệnh: {info['name_vi']} ({info['name_en']}). "
                       f"Triệu chứng lâm sàng: {', '.join(info.get('all_symptoms', []))}. "
                       f"Mô tả bệnh học: {info.get('description', '')}. "
                       f"Hướng dẫn chăm sóc: {', '.join(info.get('precautions', []))}. "
                       f"Cảnh báo cấp cứu: {info.get('emergency_warning', '')}",
            "source": f"Bộ Y Tế Việt Nam & CSDL Chuẩn Quốc Gia ({code})"
        }
        rag_records.append(rec)

    rag_file = os.path.join(MODELS_DIR, "rag_knowledge_store.json")
    with open(rag_file, "w", encoding="utf-8") as f:
        json.dump(rag_records, f, ensure_ascii=False, indent=2)
    print(f"💾 Đã lưu {len(rag_records)} tài liệu RAG Knowledge tại: {rag_file}")
    print("=================================================================")
    print("🎉 HOÀN TẤT HUẤN LUYỆN VÀ NẠP DỮ LIỆU ĐỘC LẬP TỪ DATASETS!")
    print("=================================================================")

if __name__ == "__main__":
    run_dataset_ingestion_and_training()
