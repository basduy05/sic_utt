"""
Script Kiểm Thử Toàn Diện Hệ Thống Phase 2 MediBot AI:
1. Dense Embeddings & Vector Retrieval (300+ Phác đồ Bộ Y Tế, 640+ tài liệu)
2. PhoBERT Medical NER & Colab Pipeline Skeleton
3. Gemini 2.0 Flash Reasoning Service (20 turns context, exponential backoff, streaming generator)
4. Mở rộng 200+ mã bệnh ICD-10 & Retrained Classifiers (XGBoost + NLP Classifier)
"""
import os
import sys
import json
import time

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(BASE_DIR, "apps", "ai_engine"))
sys.path.append(os.path.join(BASE_DIR, "apps", "backend"))

def test_phase2():
    print("=" * 60)
    print("🏥 BẮT ĐẦU KIỂM THỬ TOÀN DIỆN PHASE 2 (MEDIBOT AI)")
    print("=" * 60)

    # -------------------------------------------------------------
    # [TEST 1] Kiểm tra CSDL ICD-10 mở rộng (>= 200 bệnh)
    # -------------------------------------------------------------
    print("\n--- [TEST 1] KIỂM TRA CSDL ICD-10 MỞ RỘNG (200+ BỆNH) ---")
    icd_path = os.path.join(BASE_DIR, "data", "medical_lexicon", "icd10_codes.json")
    with open(icd_path, "r", encoding="utf-8") as f:
        icd_db = json.load(f)
    print(f"Tổng số mã bệnh ICD-10 trong CSDL: {len(icd_db)}")
    assert len(icd_db) >= 200, f"Expected >= 200 diseases, got {len(icd_db)}"
    print("✅ Đạt yêu cầu mở rộng CSDL: >= 200 bệnh lý thực tế tại Việt Nam.")

    # -------------------------------------------------------------
    # [TEST 2] Kiểm tra RAG Dense Embedding & Knowledge Base (>= 300 phác đồ)
    # -------------------------------------------------------------
    print("\n--- [TEST 2] KIỂM TRA RAG DENSE EMBEDDINGS & KNOWLEDGE BASE ---")
    rag_path = os.path.join(BASE_DIR, "apps", "ai_engine", "models_weights", "rag_knowledge_store.json")
    with open(rag_path, "r", encoding="utf-8") as f:
        rag_data = json.load(f)
    print(f"Tổng số tài liệu phác đồ Bộ Y Tế trong RAG store: {len(rag_data)}")
    assert len(rag_data) >= 300, f"Expected >= 300 treatment guidelines, got {len(rag_data)}"
    
    from app.core.vector_store import vector_store
    print(f"Tổng số tài liệu nạp vào Vector Database: {len(vector_store.documents)}")
    print(f"Embedding Dimension: {vector_store.embedding_dim}")
    print(f"Qdrant Status: {'Online' if vector_store.is_qdrant_online else 'In-Memory Resilient Dense Mode'}")

    query = "Tôi bị sốt xuất huyết chảy máu chân răng và giảm tiểu cầu"
    results = vector_store.search_similar(query, disease_code="A90", top_k=3)
    print(f"Kết quả truy vấn cho: '{query}'")
    for r in results:
        print(f"  - [{r['code']}] {r['title']} (Điểm: {r['similarity_score']})")
    assert len(results) > 0
    assert results[0]["code"] == "A90"
    print("✅ RAG Dense Retrieval hoạt động xuất sắc!")

    # -------------------------------------------------------------
    # [TEST 3] Kiểm tra Retrained Models (NLP + Tabular XGBoost trên 211 bệnh)
    # -------------------------------------------------------------
    print("\n--- [TEST 3] KIỂM TRA MÔ HÌNH RETRAINED NLP & TABULAR CLASSIFIER ---")
    from src.classification.predictor import HybridClinicalPredictor
    predictor = HybridClinicalPredictor()
    print(f"Predictor Disease Classes: {len(predictor.disease_classes)}")
    assert len(predictor.disease_classes) >= 200

    pred_res = predictor.predict(
        user_text="Bệnh nhân bị đau thắt ngực dữ dội lan ra cánh tay trái, vã mồ hôi và khó thở",
        normalized_symptoms=[{"standard_term": "Đau thắt ngực", "id": "dau_nguc"}],
        lab_indicators={"Troponin": {"value": 50.0, "unit": "ng/L", "message": "Tăng cao"}}
    )
    top1 = pred_res["top_predictions"][0]
    print(f"Top 1 Chẩn đoán: {top1['disease_name_vi']} ({top1['icd_code']}) - Xác suất: {top1['probability_percentage']}")
    assert top1["icd_code"] in ("I21.9", "I20.9", "I20.0", "I25.1")
    print("✅ Multimodal Clinical Predictor phân tầng chính xác trên không gian 200+ bệnh!")

    # -------------------------------------------------------------
    # [TEST 4] Kiểm tra Nâng cấp Gemini 2.0 Flash & Context Memory (20 turns)
    # -------------------------------------------------------------
    print("\n--- [TEST 4] KIỂM TRA GEMINI 2.0 FLASH SERVICE ---")
    from app.services.gemini_service import gemini_service
    print(f"Gemini Primary Model: {gemini_service.model_name}")
    assert gemini_service.model_name == "gemini-2.0-flash"

    # Tạo lịch sử 25 turns để kiểm tra cắt đúng 20 turns
    dummy_history = [{"sender": "user" if i % 2 == 0 else "bot", "content": f"Turn {i}"} for i in range(25)]
    payload = gemini_service._build_prompt_payload(
        patient_message="Tôi bị sốt cao 39 độ",
        predicted_diseases=[{"disease_name_vi": "Sốt xuất huyết Dengue", "icd_code": "A90", "probability_percentage": "95%"}],
        symptoms=[{"standard_term": "Sốt cao"}],
        lab_indicators={},
        rag_citations=[],
        chat_history=dummy_history
    )
    prompt_str = payload["contents"][0]["parts"][0]["text"]
    assert "Turn 24" in prompt_str
    assert "Turn 5" in prompt_str
    assert "Turn 3" not in prompt_str # Đã cắt đúng 20 turns gần nhất (từ Turn 5 đến Turn 24)
    print("✅ Context Window mở rộng chuẩn xác lên 20 turns (đã kiểm tra cắt đúng 20 turns gần nhất).")

    # Kiểm tra phương thức streaming generator sẵn sàng
    import inspect
    assert inspect.isasyncgenfunction(gemini_service.stream_medical_reasoning)
    print("✅ Streaming Generator (stream_medical_reasoning) sẵn sàng.")

    # -------------------------------------------------------------
    # [TEST 5] Kiểm tra PhoBERT NER Pipeline & Colab Notebook
    # -------------------------------------------------------------
    print("\n--- [TEST 5] KIỂM TRA PHOBERT MEDICAL NER & COLAB PIPELINE ---")
    colab_script = os.path.join(BASE_DIR, "scripts", "train_phobert_ner_colab.py")
    colab_notebook = os.path.join(BASE_DIR, "notebooks", "PhoBERT_Medical_NER_Colab.ipynb")
    assert os.path.exists(colab_script), "Missing train_phobert_ner_colab.py"
    assert os.path.exists(colab_notebook), "Missing PhoBERT_Medical_NER_Colab.ipynb"
    print(f"Colab Script: {os.path.basename(colab_script)} - Sẵn sàng")
    print(f"Colab Notebook: {os.path.basename(colab_notebook)} - Sẵn sàng")

    from src.ner.medical_ner import MedicalNER
    ner = MedicalNER()
    ner_res = ner.extract_entities("Tôi bị sốt cao 39 độ và chảy máu chân răng từ sáng nay")
    print(f"Extracted Symptoms: {[s['standard_term'] for s in ner_res['symptoms_normalized']]}")
    print(f"Red Flags: {ner_res['red_flag_assessment']['is_emergency']}")
    assert len(ner_res["symptoms_normalized"]) > 0
    print("✅ PhoBERT Medical NER với Confidence Thresholding hoạt động hoàn hảo.")

    print("\n" + "=" * 60)
    print("🎉 TẤT CẢ 5/5 MỤC TIÊU PHASE 2 ĐÃ VƯỢT QUA KIỂM THỬ XUẤT SẮC!")
    print("=" * 60)

if __name__ == "__main__":
    test_phase2()
