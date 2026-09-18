import os
import sys
import json
import logging
from typing import Dict, Any, List

# Add apps paths
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(base_dir, "apps", "ai_engine"))
sys.path.insert(0, os.path.join(base_dir, "apps", "backend"))

# Configure UTF-8 encoding for standard output on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("TestE2E")

def run_benchmark():
    from src.pipeline import MultimodalTriagePipeline

    test_file = os.path.join(base_dir, "data", "datasets", "test_cases_50.json")
    if not os.path.exists(test_file):
        logger.error(f"Test cases file not found at: {test_file}")
        return False

    with open(test_file, "r", encoding="utf-8") as f:
        cases = json.load(f)

    logger.info(f"Loaded {len(cases)} benchmark medical test cases.")

    pipeline = MultimodalTriagePipeline()
    
    top1_correct = 0
    top3_correct = 0
    red_flag_correct = 0
    total_red_flags = 0
    total = len(cases)

    print("\n" + "="*80)
    print(" BẮT ĐẦU CHẠY KIỂM THỬ TỰ ĐỘNG BỘ CA BỆNH LÂM SÀNG (BENCHMARK TEST SUITE)")
    print("="*80 + "\n")

    for i, case in enumerate(cases, 1):
        case_id = case.get("case_id", f"CASE_{i}")
        title = case.get("title", "")
        text = case.get("user_input_text", "")
        expected_icd = case.get("expected_icd", "")
        is_rf_expected = case.get("is_red_flag", False)
        lab_data = case.get("lab_data", {})

        # Chuyển đổi định dạng lab_data nếu có
        formatted_labs = {}
        for k, v in lab_data.items():
            formatted_labs[k] = {"value": float(v), "unit": "", "status": "normal", "message": ""}

        # Phân tích qua Pipeline
        res = pipeline.process_multimodal_request(text=text)
        
        # Nếu ca test có lab data, chạy lại predict với lab_indicators
        if formatted_labs:
            entities = res.get("extracted_entities", {}).get("symptoms", [])
            triage_res = pipeline.predictor.predict(text, entities, formatted_labs)
            preds = triage_res.get("top_predictions", [])
        else:
            preds = res.get("triage_results", [])

        is_emergency = res.get("is_emergency", False)
        clarification = res.get("clarification_loop", {})
        requires_clarification = case.get("requires_clarification", False)

        top1_code = preds[0].get("icd_code") if preds else "NONE"
        top3_codes = [p.get("icd_code") for p in preds[:3]]

        # Đánh giá độ chính xác chẩn đoán
        is_top1 = (expected_icd in top1_code or top1_code in expected_icd)
        is_top3 = any(expected_icd in c or c in expected_icd for c in top3_codes)

        # Nếu ca bệnh yêu cầu kích hoạt Clarification Loop
        clarification_passed = True
        if requires_clarification:
            clarification_passed = clarification.get("needs_clarification", False)
            if clarification_passed:
                is_top1 = True  # Đã hoàn thành đúng mục tiêu kích hoạt câu hỏi làm rõ
                is_top3 = True

        if is_top1:
            top1_correct += 1
        if is_top3:
            top3_correct += 1

        # Đánh giá cảnh báo khẩn cấp (Red Flag)
        if is_rf_expected:
            total_red_flags += 1
            if is_emergency:
                red_flag_correct += 1

        status_icon = "✅" if is_top1 else ("⚠️" if is_top3 else "❌")
        rf_icon = "🚨" if is_emergency else ("❓" if requires_clarification else "  ")
        print(f"[{i:02d}/{total:02d}] {status_icon} {rf_icon} {case_id}: {title}")
        if requires_clarification:
            print(f"       Clarification Loop Kích hoạt: {'ĐẠT' if clarification_passed else 'CHƯA ĐẠT'} (Entropy/Confidence threshold)")
        else:
            print(f"       Kỳ vọng: {expected_icd} | Dự đoán: {top1_code} (Top 3: {', '.join(top3_codes)})")

    print("\n" + "="*80)
    print(" KẾT QUẢ ĐÁNH GIÁ TỔNG THỂ (BENCHMARK SUMMARY):")
    print(f"- Tổng số ca bệnh kiểm thử: {total}")
    print(f"- Độ chính xác Top-1 Accuracy: {top1_correct}/{total} ({top1_correct/total*100:.1f}%)")
    print(f"- Độ chính xác Top-3 Accuracy: {top3_correct}/{total} ({top3_correct/total*100:.1f}%)")
    if total_red_flags > 0:
        print(f"- Tỷ lệ phát hiện Báo động đỏ Red Flag: {red_flag_correct}/{total_red_flags} ({red_flag_correct/total_red_flags*100:.1f}%)")
    print("="*80 + "\n")

    return top3_correct >= (total * 0.7)

if __name__ == "__main__":
    success = run_benchmark()
    sys.exit(0 if success else 1)
