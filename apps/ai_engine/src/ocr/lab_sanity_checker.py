import json
import os
import logging
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class LabSanityChecker:
    """
    Module kiểm tra tính hợp lý sinh học (Biological Plausibility & Sanity Check)
    của các chỉ số xét nghiệm sau khi OCR bóc tách.
    Tự động hiệu chỉnh lỗi đọc nhầm dấu chấm phẩy, số 0 thừa, hoặc đơn vị khác chuẩn.
    """

    def __init__(self, reference_path: Optional[str] = None):
        self.references = {}
        target_path = reference_path or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "data", "medical_lexicon", "lab_reference_ranges.json"))
        if os.path.exists(target_path):
            try:
                with open(target_path, "r", encoding="utf-8") as f:
                    self.references = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load lab_reference_ranges from {target_path}: {e}")

        if not self.references:
            # Default reference values
            self.references = {
                "WBC": {"min_normal": 4.0, "max_normal": 10.0, "critical_low": 2.0, "critical_high": 30.0, "plausible_min": 0.1, "plausible_max": 200.0, "unit": "10^9/L"},
                "PLT": {"min_normal": 150.0, "max_normal": 450.0, "critical_low": 50.0, "critical_high": 1000.0, "plausible_min": 5.0, "plausible_max": 3000.0, "unit": "10^9/L"},
                "RBC": {"min_normal": 3.8, "max_normal": 5.8, "critical_low": 2.0, "critical_high": 7.5, "plausible_min": 0.5, "plausible_max": 12.0, "unit": "10^12/L"},
                "HGB": {"min_normal": 120.0, "max_normal": 165.0, "critical_low": 70.0, "critical_high": 200.0, "plausible_min": 20.0, "plausible_max": 250.0, "unit": "g/L"},
                "HCT": {"min_normal": 35.0, "max_normal": 50.0, "critical_low": 20.0, "critical_high": 60.0, "plausible_min": 10.0, "plausible_max": 80.0, "unit": "%"},
                "AST": {"min_normal": 0.0, "max_normal": 40.0, "critical_low": None, "critical_high": 500.0, "plausible_min": 1.0, "plausible_max": 5000.0, "unit": "U/L"},
                "ALT": {"min_normal": 0.0, "max_normal": 40.0, "critical_low": None, "critical_high": 500.0, "plausible_min": 1.0, "plausible_max": 5000.0, "unit": "U/L"},
                "GLUCOSE": {"min_normal": 3.9, "max_normal": 6.4, "critical_low": 2.8, "critical_high": 20.0, "plausible_min": 0.5, "plausible_max": 60.0, "unit": "mmol/L"},
                "CREATININE": {"min_normal": 53.0, "max_normal": 106.0, "critical_low": None, "critical_high": 300.0, "plausible_min": 10.0, "plausible_max": 2000.0, "unit": "umol/L"}
            }

    def validate_and_correct(self, test_name: str, raw_value: float) -> Tuple[float, str, str]:
        """
        Kiểm tra và hiệu chỉnh chỉ số:
        Trả về: (giá trị đã hiệu chỉnh, trạng thái [NORMAL/LOW/HIGH/CRITICAL_LOW/CRITICAL_HIGH], thông báo cảnh báo)
        """
        test_key = test_name.upper().strip()
        if test_key not in self.references:
            return raw_value, "UNKNOWN", "Chỉ số không có trong danh mục tham chiếu"

        ref = self.references[test_key]
        p_min = ref.get("plausible_min", 0.0)
        p_max = ref.get("plausible_max", 99999.0)
        n_min = ref.get("min_normal", 0.0)
        n_max = ref.get("max_normal", 99999.0)

        corrected_value = raw_value

        # Heuristic fix 1: Quên dấu chấm động cho WBC (ví dụ 32 -> 3.2 hoặc 320 -> 3.2)
        if test_key == "WBC" and raw_value > 30.0:
            if raw_value >= 100.0:
                corrected_value = raw_value / 100.0
            else:
                corrected_value = raw_value / 10.0
            logger.warning(f"Auto-corrected WBC value from {raw_value} to {corrected_value}")

        # Heuristic fix 2: Đơn vị HGB g/dL sang g/L (ví dụ 13.5 g/dL -> 135 g/L)
        if test_key == "HGB" and raw_value < 25.0:
            corrected_value = raw_value * 10.0
            logger.warning(f"Auto-corrected HGB value from {raw_value} g/dL to {corrected_value} g/L")

        # Heuristic fix 3: Đơn vị Glucose mg/dL sang mmol/L (ví dụ 180 mg/dL -> 10.0 mmol/L)
        if test_key == "GLUCOSE" and raw_value > 60.0:
            corrected_value = round(raw_value / 18.0, 2)
            logger.warning(f"Auto-corrected Glucose from {raw_value} mg/dL to {corrected_value} mmol/L")

        # Đánh giá trạng thái theo khoảng chuẩn
        status = "NORMAL"
        message = f"Bình thường ({n_min} - {n_max} {ref.get('unit', '')})"

        if corrected_value < n_min:
            crit_low = ref.get("critical_low")
            if crit_low is not None and corrected_value <= crit_low:
                status = "CRITICAL_LOW"
                message = f"NGUY HIỂM: Giảm rất sâu dưới mức nguy cấp ({corrected_value} < {crit_low})"
            else:
                status = "LOW"
                message = f"Thấp hơn bình thường ({corrected_value} < {n_min})"
        elif corrected_value > n_max:
            crit_high = ref.get("critical_high")
            if crit_high is not None and corrected_value >= crit_high:
                status = "CRITICAL_HIGH"
                message = f"NGUY HIỂM: Tăng rất cao vượt ngưỡng nguy cấp ({corrected_value} > {crit_high})"
            else:
                status = "HIGH"
                message = f"Cao hơn bình thường ({corrected_value} > {n_max})"

        return round(corrected_value, 2), status, message
