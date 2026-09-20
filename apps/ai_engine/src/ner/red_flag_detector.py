import json
import os
import time
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class RedFlagDetector:
    """
    Module phát hiện dấu hiệu cấp cứu y khoa khẩn cấp (Red Flag Escalation Service).
    Thời gian phản hồi cam kết <= 0.5s.
    """

    def __init__(self, rules_path: Optional[str] = None):
        self.rules = []
        if not rules_path:
            possible_dirs = [
                os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "data", "medical_lexicon")),
                os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "medical_lexicon")),
                os.path.abspath(os.path.join(os.getcwd(), "data", "medical_lexicon")),
            ]
            base_dir = next((d for d in possible_dirs if os.path.exists(d)), possible_dirs[0])
            rules_path = os.path.join(base_dir, "red_flags.json")

        if rules_path and os.path.exists(rules_path):
            try:
                with open(rules_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.rules = data.get("red_flag_rules", [])
            except Exception as e:
                logger.error(f"Error loading red flag rules: {e}")

        if not self.rules:
            # Fallback rules
            self.rules = [
                {
                    "id": "RF_CARDIAC_INFARCTION",
                    "disease_group": "Hội chứng vành cấp / Nhồi máu cơ tim",
                    "severity": "CRITICAL_EMERGENCY",
                    "triggers_all": ["đau ngực"],
                    "triggers_any": ["vã mồ hôi", "vai trái", "cánh tay trái", "hàm", "bóp nghẹt", "đè nặng", "khó thở"],
                    "action_vi": "BÁO ĐỘNG ĐỎ: Nghi ngờ Nhồi máu cơ tim cấp. Gọi 115 ngay lập tức. Để người bệnh ngồi yên tĩnh, nới lỏng trang phục."
                },
                {
                    "id": "RF_STROKE_FAST",
                    "disease_group": "Tai biến mạch máu não / Đột quỵ",
                    "severity": "CRITICAL_EMERGENCY",
                    "triggers_all": [],
                    "triggers_any": ["méo miệng", "lệch mặt", "yếu nửa người", "liệt tay chân", "nói ngọng đột ngột", "nói đớ"],
                    "action_vi": "BÁO ĐỘNG ĐỎ: Dấu hiệu Đột quỵ não (FAST). Gọi 115 đưa ngay đến bệnh viện có đơn vị Đột quỵ trong giờ vàng."
                },
                {
                    "id": "RF_RESPIRATORY_FAILURE",
                    "disease_group": "Suy hô hấp cấp tính",
                    "severity": "CRITICAL_EMERGENCY",
                    "triggers_all": ["khó thở"],
                    "triggers_any": ["tím tái", "ngáp cá", "co kéo", "thở rít", "nghẹn thở"],
                    "action_vi": "BÁO ĐỘNG ĐỎ: Suy hô hấp cấp. Cho người bệnh ngồi thẳng, hít thở oxy và gọi 115 khẩn cấp."
                }
            ]

    def _evaluate_anaphylaxis_rule(self, all_terms_str: str) -> Optional[Dict[str, Any]]:
        """
        Quy tắc lâm sàng phản vệ (WAO / Bộ Y Tế):
        Tổn thương da/niêm mạc (mề đay, phù môi/mắt...) KÈM THEO
        ít nhất một trong các biểu hiện:
        1. Hô hấp (thở rít, khó thở, tức ngực, khàn tiếng...) HOẶC
        2. Tuần hoàn/Toàn thân (choáng, ngất, tụt huyết áp...)
        """
        skin_terms = [
            "mày đay", "mề đay", "ngứa", "phù môi", "ban đỏ", "sưng môi",
            "sưng phù môi", "nổi mảng", "mẩn ngứa", "tê phù", "nổi cục đỏ",
            "phù mạch", "phù quincke", "nổi mề đay", "sưng mắt", "phù mắt"
        ]
        resp_terms = [
            "thở rít", "khó thở", "tức ngực", "khàn tiếng", "nghẹt cổ họng",
            "nghẹt họng", "thở dốc", "tiếng rít", "rít thanh quản", "nghẹn thở",
            "co thắt họng", "thở rít nhẹ"
        ]
        circ_terms = [
            "choáng", "xây xẩm", "ngất", "tụt huyết áp", "hạ huyết áp",
            "chóng mặt dữ dội", "mạch nhanh nhỏ", "vã mồ hôi lạnh", "ngất xỉu"
        ]

        has_skin = any(term in all_terms_str for term in skin_terms)
        has_resp = any(term in all_terms_str for term in resp_terms)
        has_circ = any(term in all_terms_str for term in circ_terms)

        if has_skin and (has_resp or has_circ):
            return {
                "rule_id": "RF_ANAPHYLAXIS",
                "disease_group": "Sốc phản vệ / Phù mạch cấp tính",
                "severity": "CRITICAL_EMERGENCY",
                "action_vi": "🚨 BÁO ĐỘNG ĐỎ: Dấu hiệu Phản vệ / Phù mạch thanh quản (Anaphylaxis / Quincke). Tình trạng co thắt đường thở hoặc phù nề niêm mạc sau tiếp xúc dị nguyên có thể đe dọa tính mạng. BẠN CẦN GỌI CẤP CỨU 115 HOẶC VÀO NGAY KHOA CẤP CỨU GẦN NHẤT ĐỂ TIÊM ADRENALINE!",
                "emergency_phone": "115"
            }
        return None

    def evaluate(self, text: str, normalized_symptoms: Optional[List[Dict[str, Any]]] = None, lab_indicators: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Quét nhanh dấu hiệu nguy cấp trong text, thực thể triệu chứng và chỉ số máu.
        Thời gian thực thi trung bình < 10ms.
        """
        start_time = time.time()
        lower_text = text.lower()
        symptom_terms = [s.get("standard_term", "").lower() for s in (normalized_symptoms or [])]
        symptom_ids = [s.get("id", "").lower() for s in (normalized_symptoms or [])]
        all_terms_str = " ".join(symptom_terms + symptom_ids) + " " + lower_text

        triggered_flags = []

        # 1. Đánh giá chuyên biệt Phản vệ / Phù mạch (Độ ưu tiên cao nhất, luật kết hợp đa hệ cơ quan)
        anaphylaxis_flag = self._evaluate_anaphylaxis_rule(all_terms_str)
        if anaphylaxis_flag:
            triggered_flags.append(anaphylaxis_flag)

        for rule in self.rules:
            # Tránh trùng lặp nếu RF_ANAPHYLAXIS đã được kích hoạt bởi luật kết hợp
            if rule.get("id") == "RF_ANAPHYLAXIS" and any(f.get("rule_id") == "RF_ANAPHYLAXIS" for f in triggered_flags):
                continue

            # Kiểm tra triggers_all
            all_satisfied = True
            for req in rule.get("triggers_all", []):
                req_lower = req.lower()
                if req_lower not in all_terms_str:
                    all_satisfied = False
                    break

            if not all_satisfied:
                continue

            # Kiểm tra triggers_any
            any_satisfied = False
            triggers_any = rule.get("triggers_any", [])
            if not triggers_any:
                any_satisfied = True
            else:
                for trig in triggers_any:
                    if trig.lower() in all_terms_str:
                        any_satisfied = True
                        break

            if any_satisfied:
                triggered_flags.append({
                    "rule_id": rule.get("id"),
                    "disease_group": rule.get("disease_group"),
                    "severity": rule.get("severity"),
                    "action_vi": rule.get("action_vi"),
                    "emergency_phone": "115"
                })

        # Kiểm tra Lab Critical Flags (Ví dụ PLT < 50 hoặc WBC > 30)
        if lab_indicators:
            plt_info = lab_indicators.get("PLT")
            if plt_info and isinstance(plt_info, dict) and plt_info.get("value", 999) < 50.0:
                triggered_flags.append({
                    "rule_id": "RF_LAB_CRITICAL_THROMBOCYTOPENIA",
                    "disease_group": "Giảm tiểu cầu nặng (Xuất huyết nguy cơ cao)",
                    "severity": "CRITICAL_EMERGENCY",
                    "action_vi": f"CẢNH BÁO NGUY CẤP: Tiểu cầu xuống rất thấp ({plt_info.get('value')} 10^9/L). Nguy cơ xuất huyết nội tạng hoặc sốc Dengue. Cần nhập viện ngay!",
                    "emergency_phone": "115"
                })

        latency = time.time() - start_time
        is_emergency = len(triggered_flags) > 0

        return {
            "is_emergency": is_emergency,
            "latency_seconds": round(latency, 4),
            "triggered_flags": triggered_flags,
            "highest_severity": "CRITICAL_EMERGENCY" if is_emergency else "NORMAL"
        }
