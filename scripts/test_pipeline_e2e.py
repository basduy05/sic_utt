import os
import sys

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "ai_engine")))
from src.pipeline import MultimodalTriagePipeline

def main():
    print("--- Khởi tạo MultimodalTriagePipeline ---")
    pipeline = MultimodalTriagePipeline()
    
    test_cases = [
        "Tôi bị đau đầu dữ dội và sốt cao 39 độ C",
        "Bệnh nhân đau tức ngực dữ dội, khó thở, vã mồ hôi",
        "Chào bác sĩ, xin tư vấn giúp tôi",
    ]
    
    for text in test_cases:
        print(f"\n[Input]: {text}")
        res = pipeline.process(text=text)
        print(f" -> Latency: {res.get('latency_seconds')}s")
        print(f" -> Cấp cứu (Emergency): {res.get('is_emergency')}")
        symptoms = [s.get('standard_term') for s in res.get('extracted_entities', {}).get('symptoms', [])]
        print(f" -> Triệu chứng: {symptoms}")
        top_triage = res.get('triage_results', [])
        if top_triage:
            print(f" -> Dự đoán bệnh: {top_triage[0].get('disease_name_vi')} ({top_triage[0].get('icd10_code')}) - {top_triage[0].get('confidence')}%")
        else:
            print(" -> Dự đoán bệnh: Không có bệnh khớp (câu hỏi thông thường / xã giao)")

if __name__ == "__main__":
    main()
