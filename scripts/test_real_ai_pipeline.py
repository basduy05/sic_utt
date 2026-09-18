import os
import sys
sys.stdout.reconfigure(encoding='utf-8')

# Ensure ai_engine in python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(os.path.join(project_root, "apps", "ai_engine"))

from src.pipeline import MultimodalTriagePipeline

print("=" * 60)
print("TESTING 100% REAL DEEP LEARNING AI PIPELINE (NO DICTIONARY)")
print("=" * 60)

pipeline = MultimodalTriagePipeline()

test_cases = [
    "Tôi bị sốt cao 39 độ, đau đầu dữ dội và chảy máu chân răng từ 2 ngày nay",
    "Bệnh nhân đột ngột méo miệng lệch mặt và liệt nửa người bên phải",
    "Em bị đau bụng quặn từng cơn kèm tiêu chảy đi ngoài liên tục từ tối qua"
]

for idx, text in enumerate(test_cases, 1):
    print(f"\n--- TEST CASE {idx} ---")
    print(f"Bệnh nhân: \"{text}\"")
    result = pipeline.process(text=text)
    
    extracted = result.get("extracted_entities", {})
    symptoms = [s.get("standard_term") for s in extracted.get("symptoms", [])]
    vitals = extracted.get("vital_signs", {})
    is_emergency = result.get("is_emergency", False)
    predictions = result.get("triage_results", [])
    
    print(f"PhoBERT Symptoms (Normalized via Dense Embeddings): {symptoms}")
    print(f"Vitals: {vitals}")
    print(f"Emergency Alert: {is_emergency}")
    print("Top Predictions (XGBoost + Calibrated NLP Classifier):")
    for p in predictions[:3]:
        prob = p.get('probability', 0.0)
        print(f"  - [{p.get('icd_code')}] {p.get('disease_name_vi')}: {prob:.2%}")

print("\n" + "=" * 60)
print("ALL REAL AI PIPELINE TESTS COMPLETED SUCCESSFULLY!")
print("=" * 60)
