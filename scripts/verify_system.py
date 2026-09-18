import os
import sys
import json

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Setup paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "ai_engine")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "backend")))

from src.pipeline import MultimodalTriagePipeline
from src.ocr.lab_sanity_checker import LabSanityChecker
from src.ner.red_flag_detector import RedFlagDetector

def test_system():
    print("=== [TEST 1] Testing Lab Sanity Checker ===")
    checker = LabSanityChecker()
    val, status, msg = checker.validate_and_correct("WBC", 320.0)
    print(f"WBC correction: 320.0 -> {val} ({status}) - {msg}")
    assert val == 3.2, f"Expected 3.2 but got {val}"
    assert status == "LOW"

    val_plt, status_plt, msg_plt = checker.validate_and_correct("PLT", 45.0)
    print(f"PLT check: 45.0 -> {val_plt} ({status_plt}) - {msg_plt}")
    assert status_plt == "CRITICAL_LOW"

    print("\n=== [TEST 2] Testing Red Flag Rapid Filter (<=0.5s) ===")
    detector = RedFlagDetector()
    emergency_text = "Tôi bị đau ngực dữ dội lan ra cánh tay trái, vã mồ hôi ướt đẫm và rất khó thở."
    rf_res = detector.evaluate(emergency_text)
    print(f"Emergency Triggered: {rf_res['is_emergency']} in {rf_res['latency_seconds']}s")
    assert rf_res["is_emergency"] is True
    assert rf_res["latency_seconds"] <= 0.5

    print("\n=== [TEST 3] Testing Multimodal Triage Pipeline (Dengue Scenario) ===")
    pipeline = MultimodalTriagePipeline()
    sample_text = "Tôi bị sốt cao 39 độ, đau đầu và chảy máu chân răng từ 2 ngày nay."
    lab_text = "WBC: 3.2 10^9/L\nPLT: 75 10^9/L\nRBC: 4.2 10^12/L\nHGB: 135 g/L"
    
    triage_res = pipeline.process_multimodal_request(
        text=sample_text,
        document_bytes=lab_text.encode("utf-8"),
        document_filename="blood_test.txt"
    )
    
    print(f"Processed Text: {triage_res['processed_text']}")
    print(f"Extracted Symptoms: {[s['standard_term'] for s in triage_res['extracted_entities']['symptoms']]}")
    print(f"Parsed Lab Indicators: {list(triage_res['lab_indicators'].keys())}")
    print(f"Top 1 Disease: {triage_res['triage_results'][0]['disease_name_vi']} ({triage_res['triage_results'][0]['probability_percentage']})")
    assert triage_res["triage_results"][0]["icd_code"] == "A90"

    print("\n=== [TEST 4] Testing Clarification Decision Loop ===")
    vague_text = "Tôi thấy trong người hơi mệt mỏi khó chịu không rõ nguyên nhân"
    triage_vague = pipeline.process_multimodal_request(text=vague_text)
    clarify = triage_vague["clarification_loop"]
    print(f"Needs Clarification: {clarify['needs_clarification']} (Entropy: {clarify.get('entropy')})")
    print(f"Questions Generated: {len(clarify.get('questions', []))}")
    assert clarify["needs_clarification"] is True
    assert len(clarify["questions"]) > 0

    print("\n✅ TẤT CẢ 4 KỊCH BẢN KIỂM THỬ ĐÃ VƯỢT QUA XUẤT SẮC (ALL TESTS PASSED)!")

if __name__ == "__main__":
    test_system()
