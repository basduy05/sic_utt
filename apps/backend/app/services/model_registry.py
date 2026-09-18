"""
Model Registry Service
Quản lý thông tin các model AI đang được sử dụng trong hệ thống.
"""
import os
import json
import pickle
import time
from typing import Dict, Any, List

# Đường dẫn đến thư mục chứa model weights
def get_models_dir() -> str:
    candidates = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "ai_engine", "models_weights")),
        os.path.abspath(os.path.join(os.getcwd(), "..", "ai_engine", "models_weights")),
        os.path.abspath(os.path.join(os.getcwd(), "apps", "ai_engine", "models_weights")),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return r"c:\Users\basduy05\Downloads\ai_utt_sic\apps\ai_engine\models_weights"

MODELS_DIR = get_models_dir()

# Registry mô tả các model được sử dụng
MODEL_REGISTRY_METADATA = {
    "nlp_symptom_classifier.pkl": {
        "name": "NLP Symptom Classifier",
        "name_vi": "Mô Hình Phân Loại Triệu Chứng NLP",
        "type": "sklearn",
        "role": "Phân loại văn bản triệu chứng thô → mã ICD-10",
        "function": "chat_triage",
        "framework": "scikit-learn (LinearSVC / Multi-class)",
        "input": "Raw symptom text (TF-IDF features)",
        "output": "ICD-10 code prediction & probability",
        "stage": "Phân loại bệnh lý NLP (Bước 5)",
    },
    "nlp_tfidf_vectorizer.pkl": {
        "name": "TF-IDF Vectorizer",
        "name_vi": "Bộ Vector Hóa Triệu Chứng TF-IDF",
        "type": "sklearn",
        "role": "Chuyển đổi văn bản thành vector đặc trưng cho NLP Classifier",
        "function": "feature_extraction",
        "framework": "scikit-learn TfidfVectorizer (50k n-grams)",
        "input": "Raw text",
        "output": "TF-IDF sparse matrix",
        "stage": "Trích xuất đặc trưng (Bước 4)",
    },
    "tabular_xgboost.json": {
        "name": "XGBoost Tabular Classifier",
        "name_vi": "Mô Hình XGBoost Phân Tầng Lâm Sàng",
        "type": "xgboost",
        "role": "Phân loại dựa trên đặc trưng lâm sàng có cấu trúc (tuổi, giới, vital signs)",
        "function": "clinical_triage",
        "framework": "XGBoost Gradient Boosted Trees",
        "input": "Structured clinical features (vital signs, age, negatives)",
        "output": "Disease risk & ESI triage tier",
        "stage": "Phân tầng nguy cơ lâm sàng (Bước 6)",
    },
    "rag_knowledge_store.json": {
        "name": "RAG Knowledge Store",
        "name_vi": "Kho Tri Thức RAG (Bộ Y Tế Grounding)",
        "type": "vector_store",
        "role": "Truy xuất phác đồ y khoa Bộ Y Tế bổ sung ngữ cảnh cho Gemini LLM",
        "function": "rag_retrieval",
        "framework": "Semantic Vector Store (BYT Protocols)",
        "input": "Symptom query embedding & ICD-10 code",
        "output": "Relevant clinical guidelines & treatment protocols",
        "stage": "Truy xuất tri thức y khoa RAG (Bước 7)",
    },
    "label_encoder.pkl": {
        "name": "Label Encoder",
        "name_vi": "Bộ Mã Hóa Nhãn ICD-10",
        "type": "sklearn",
        "role": "Chuyển đổi qua lại giữa mã ICD-10 dạng chuỗi và chỉ số số nguyên",
        "function": "label_encoding",
        "framework": "scikit-learn LabelEncoder (32+ classes)",
        "input": "ICD-10 string code",
        "output": "Integer class index",
        "stage": "Ánh xạ nhãn bệnh (Bước 5)",
    },
    "gemini_medical_llm": {
        "name": "Gemini 1.5 Medical Synthesizer",
        "name_vi": "Mô Hình Suy Luận & Sinh Phản Hồi Lâm Sàng (LLM)",
        "type": "llm",
        "role": "Suy luận chẩn đoán sâu, cá nhân hóa phản hồi và đối chiếu phác đồ BYT",
        "function": "clinical_reasoning",
        "framework": "Google Gemini API + Local Rule Engine Fallback",
        "input": "Patient dialog + Extracted NER + Lab values + RAG guidelines",
        "output": "Structured medical advice & empathetic consultation",
        "stage": "Suy luận lâm sàng & sinh câu trả lời (Bước 8)",
    },
    "multimodal_ocr_stt": {
        "name": "Multimodal Input Processing (OCR & STT)",
        "name_vi": "Bộ Tiền Xử Lý Đa Phương Thức (Hình Ảnh & Giọng Nói)",
        "type": "multimodal",
        "role": "Trích xuất đơn thuốc, xét nghiệm (EasyOCR) và nhận dạng giọng nói (Whisper)",
        "function": "multimodal_perception",
        "framework": "EasyOCR / Tesseract + Whisper STT",
        "input": "Audio WAV/MP3, Image PNG/JPG/PDF",
        "output": "Transcribed clinical text & parsed lab values",
        "stage": "Thu nhận đầu vào đa phương thức (Bước 1)",
    },
}


def get_file_info(filepath: str) -> Dict[str, Any]:
    """Lấy thông tin file (size, last modified)."""
    if not os.path.exists(filepath):
        return {"exists": False, "size_mb": 0, "last_updated": None}
    stat = os.stat(filepath)
    return {
        "exists": True,
        "size_mb": round(stat.st_size / 1024 / 1024, 2),
        "last_updated": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime)),
    }


def get_rag_doc_count() -> int:
    """Đếm số tài liệu trong RAG knowledge store."""
    rag_path = os.path.join(MODELS_DIR, "rag_knowledge_store.json")
    if not os.path.exists(rag_path):
        return 0
    try:
        with open(rag_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return len(data)
            if isinstance(data, dict):
                return len(data.get("documents", data.get("entries", [])))
    except Exception:
        pass
    return 0


def list_models() -> List[Dict[str, Any]]:
    """Lấy thông tin tất cả model trong registry."""
    models = []
    for filename, meta in MODEL_REGISTRY_METADATA.items():
        if filename == "gemini_medical_llm":
            has_key = bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))
            models.append({
                "filename": filename,
                "status": "active",
                "exists": True,
                "size_mb": 0.0,
                "last_updated": "Google Cloud API v1.5",
                "mode": "Gemini 1.5 Flash (Online)" if has_key else "Local Rule Engine (Fallback)",
                **meta,
            })
            continue

        if filename == "multimodal_ocr_stt":
            models.append({
                "filename": filename,
                "status": "active",
                "exists": True,
                "size_mb": 142.5,
                "last_updated": "EasyOCR / Whisper Ready",
                "mode": "EasyOCR & Whisper Speech",
                **meta,
            })
            continue

        filepath = os.path.join(MODELS_DIR, filename)
        file_info = get_file_info(filepath)

        extra = {}
        if filename == "rag_knowledge_store.json":
            extra["doc_count"] = get_rag_doc_count()

        models.append({
            "filename": filename,
            "status": "active" if file_info["exists"] else "missing",
            **meta,
            **file_info,
            **extra,
        })
    return models


def get_model_detail(filename: str) -> Dict[str, Any]:
    """Lấy chi tiết một model cụ thể."""
    if filename not in MODEL_REGISTRY_METADATA:
        return {"error": "Model not found in registry"}
    
    meta = MODEL_REGISTRY_METADATA[filename]
    if filename == "gemini_medical_llm":
        has_key = bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))
        return {
            "filename": filename,
            "status": "active",
            "exists": True,
            "size_mb": 0.0,
            "last_updated": "Google Cloud API v1.5",
            "mode": "Gemini 1.5 Flash (Online)" if has_key else "Local Rule Engine (Fallback)",
            **meta,
        }
    if filename == "multimodal_ocr_stt":
        return {
            "filename": filename,
            "status": "active",
            "exists": True,
            "size_mb": 142.5,
            "last_updated": "EasyOCR / Whisper Ready",
            "mode": "EasyOCR & Whisper Speech",
            **meta,
        }

    filepath = os.path.join(MODELS_DIR, filename)
    file_info = get_file_info(filepath)
    
    return {
        "filename": filename,
        "status": "active" if file_info["exists"] else "missing",
        **meta,
        **file_info,
    }


def get_dataset_list() -> List[Dict[str, Any]]:
    """Lấy danh sách dataset đã upload."""
    datasets_dir_candidates = [
        os.path.abspath(os.path.join(MODELS_DIR, "..", "..", "..", "data", "datasets")),
        r"c:\Users\basduy05\Downloads\ai_utt_sic\data\datasets",
    ]
    datasets_dir = None
    for d in datasets_dir_candidates:
        if os.path.exists(d):
            datasets_dir = d
            break
    
    if not datasets_dir:
        return []
    
    result = []
    for f in os.listdir(datasets_dir):
        if f.endswith((".csv", ".json", ".jsonl")):
            fp = os.path.join(datasets_dir, f)
            stat = os.stat(fp)
            result.append({
                "filename": f,
                "size_mb": round(stat.st_size / 1024 / 1024, 3),
                "last_modified": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime)),
                "type": f.split(".")[-1].upper(),
            })
    return result
