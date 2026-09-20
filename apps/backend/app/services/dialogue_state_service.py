import json
import logging
import time
import re
from typing import Dict, Any, List, Optional, Set

from ..core.redis import redis_manager
from ..core.config import settings

logger = logging.getLogger(__name__)

SLOT_TOPIC_MAP: Dict[str, str] = {
    "q_skin_trigger": "allergen_trigger",
    "q_derma_triggers": "allergen_trigger",
    "q_fever_temp": "fever_pattern",
    "q_fever_pattern": "fever_pattern",
    "q_fever_days": "onset",
    "q_dengue_day": "onset",
    "q_resp_duration": "onset",
    "q_migraine_duration": "onset",
    "q_chest_duration": "onset",
    "q_dynamic_duration_stage2": "onset",
    "q_dynamic_medication_response": "medication_response",
    "q_migraine_aggravating": "medication_response",
    "q_cardio_pain_type": "chest_nature",
    "q_chest_spread": "chest_nature",
    "q_resp_cough_nature": "respiratory_nature",
    "q_cough_sputum": "respiratory_nature",
    "q_derma_sensation": "skin_sensation",
    "q_skin_itch": "skin_sensation",
    "q_bleeding": "bleeding_signs",
    "q_stomach_timing": "gi_symptoms",
    "q_heartburn": "gi_symptoms",
    "q_stool_nature": "gi_symptoms",
    "q_gerd_throat": "gi_symptoms",
    "q_kidney_urinate": "urinary_symptoms",
    "q_flank_pain": "urinary_symptoms",
    "q_eye_symptoms": "eye_symptoms",
    "q_eye_vision_impact": "eye_vision",
    "q_eye_habits": "eye_habits",
    "q_presbyopia_read": "eye_vision",
    "q_presbyopia_age": "eye_vision",
    "q_dry_eye_sensation": "eye_symptoms",
    "q_eye_triggers": "eye_habits",
    "q_myopia_signs": "eye_vision",
    "q_conjunctivitis_signs": "eye_symptoms",
    # Mở rộng cho Cúm mùa, Sốt và Cơ Xương Khớp
    "q_flu_respiratory_signs": "respiratory_nature",
    "q_flu_systemic_myalgia": "fever_associated",
    "q_flu_dengue_differential": "bleeding_signs",
    "q_fever_associated_signs": "fever_associated",
    "q_fever_danger_dengue": "bleeding_signs",
    "q_liver_digestive": "gi_symptoms",
    "q_liver_risk_habits": "liver_habits",
    "q_cervical_spine_character": "cervical_spine",
    "q_cervical_spine_aggravation": "cervical_spine",
    "q_lumbar_spine_character": "lumbar_spine",
    "q_bp_measurement": "cardio_bp",
    "q_bp_associated_signs": "cardio_bp",
    "q_diarrhea_frequency": "gi_symptoms",
    "q_diarrhea_associated": "gi_symptoms",
    "q_chickenpox_rash": "skin_sensation",
    "q_asthma_nature": "respiratory_nature",
    "q_appendicitis_pain_shift": "gi_symptoms",
}

def resolve_question_topic(question: Optional[Dict[str, Any]]) -> str:
    """Xác định topic chuẩn của câu hỏi làm rõ từ ID hoặc nội dung."""
    if not question:
        return "general"
    qid = question.get("id", "")
    if qid in SLOT_TOPIC_MAP:
        return SLOT_TOPIC_MAP[qid]
    
    q_text = question.get("question", "").lower()
    if any(k in q_text for k in ["dị ứng", "tiếp xúc", "thức ăn", "hải sản", "mỹ phẩm", "dị nguyên"]):
        return "allergen_trigger"
    if any(k in q_text for k in ["nhiệt độ", "sốt cao", "thân nhiệt", "cơn sốt"]):
        return "fever_pattern"
    if any(k in q_text for k in ["mấy ngày", "bao lâu", "thời gian", "khởi phát"]):
        return "onset"
    if any(k in q_text for k in ["uống thuốc", "xử trí", "đỡ không", "giảm đau", "hạ sốt"]):
        return "medication_response"
    if any(k in q_text for k in ["ngực", "bóp nghẹt", "nhịp tim"]):
        return "chest_nature"
    if any(k in q_text for k in ["mắt", "thị giác", "nhìn mờ", "thị lực", "mỏi mắt", "khô mắt", "nhức mắt"]):
        return "eye_symptoms"
    if any(k in q_text for k in ["ho", "đờm", "khó thở", "khò khè"]):
        return "respiratory_nature"
    if any(k in q_text for k in ["vùng da", "ngứa", "nổi mẩn", "mề đay", "dị ứng da", "mụn nước"]):
        return "skin_sensation"
    return "general"

class ClinicalSessionState:
    """
    Trạng thái lâm sàng động của phiên khám (Dynamic Clinical Session State).
    Lưu trữ toàn diện các slot y khoa và bối cảnh hỏi đáp xuyên suốt nhiều lượt.
    """
    def __init__(self, session_id: str):
        self.session_id: str = session_id
        self.turn_count: int = 0
        self.chief_complaint: str = ""
        self.confirmed_symptoms: Dict[str, Dict[str, Any]] = {}
        self.negated_symptoms: Dict[str, Dict[str, Any]] = {}
        self.clinical_slots: Dict[str, Any] = {
            "triggers": [],              # Dị nguyên, thức ăn, bia rượu, yếu tố khởi phát
            "allergen_trigger": "",      # Chi tiết dị nguyên xác định (hải sản, phấn hoa, thuốc)
            "onset": "",                 # Thời gian bắt đầu (tối qua, 3 ngày trước)
            "duration": "",              # Kéo dài bao lâu
            "progression": "",           # Diễn biến (tăng dần, liên tục)
            "fever_pattern": "",         # Kiểu sốt (39 độ, liên tục)
            "medication_response": "",   # Đáp ứng hạ sốt / thuốc (uống không đỡ)
            "anatomical_locations": [],  # Vị trí (đùi, lưng, hốc mắt, khớp, môi)
        }
        self.active_hypotheses: List[Dict[str, Any]] = []
        self.pending_question: Optional[Dict[str, Any]] = None  # Câu hỏi bác sĩ vừa đặt ở lượt trước
        self.is_emergency: bool = False
        self.emergency_reason: str = ""
        self.created_at: float = time.time()
        self.updated_at: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "turn_count": self.turn_count,
            "chief_complaint": self.chief_complaint,
            "confirmed_symptoms": self.confirmed_symptoms,
            "negated_symptoms": self.negated_symptoms,
            "clinical_slots": self.clinical_slots,
            "active_hypotheses": self.active_hypotheses,
            "pending_question": self.pending_question,
            "is_emergency": self.is_emergency,
            "emergency_reason": self.emergency_reason,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ClinicalSessionState":
        state = cls(session_id=data.get("session_id", "default_session"))
        state.turn_count = data.get("turn_count", 0)
        state.chief_complaint = data.get("chief_complaint", "")
        state.confirmed_symptoms = data.get("confirmed_symptoms", {})
        state.negated_symptoms = data.get("negated_symptoms", {})
        state.clinical_slots = data.get("clinical_slots", state.clinical_slots)
        state.active_hypotheses = data.get("active_hypotheses", [])
        state.pending_question = data.get("pending_question")
        state.is_emergency = data.get("is_emergency", False)
        state.emergency_reason = data.get("emergency_reason", "")
        state.created_at = data.get("created_at", time.time())
        state.updated_at = data.get("updated_at", time.time())
        return state

class DialogueStateService:
    """
    Dịch vụ quản lý Trạng thái Hội thoại Lâm sàng (Dialogue State Tracking - DST).
    Chịu trách nhiệm:
    - Lưu & Phục hồi bệnh án động qua Redis (hoặc In-Memory fallback).
    - Tự động điền slot (Slot Filling) đối chiếu với câu hỏi làm rõ ở lượt trước.
    - Xâu chuỗi triệu chứng lũy kế và loại trừ dấu hiệu phủ định.
    """
    def __init__(self):
        self._memory_store: Dict[str, Dict[str, Any]] = {}

    async def get_state(self, session_id: str) -> ClinicalSessionState:
        """Lấy trạng thái phiên khám từ Redis hoặc Memory."""
        cache_key = f"dst_state:{session_id}"
        cached = await redis_manager.get_json(cache_key)
        if cached:
            return ClinicalSessionState.from_dict(cached)
        
        if session_id in self._memory_store:
            return ClinicalSessionState.from_dict(self._memory_store[session_id])

        new_state = ClinicalSessionState(session_id=session_id)
        return new_state

    async def save_state(self, state: ClinicalSessionState) -> None:
        """Lưu trạng thái phiên khám vào Redis và Memory."""
        state.updated_at = time.time()
        state_dict = state.to_dict()
        self._memory_store[state.session_id] = state_dict
        cache_key = f"dst_state:{state.session_id}"
        await redis_manager.set_json(cache_key, state_dict, ex=86400)  # TTL 24h

    def fill_slots_from_utterance(
        self,
        state: ClinicalSessionState,
        user_message: str,
        extracted_symptoms: List[Dict[str, Any]],
        negated_symptoms: List[Dict[str, Any]]
    ) -> ClinicalSessionState:
        """
        Bóc tách và điền slot lâm sàng thông minh (Slot Filling):
        1. Đối chiếu với pending_question từ lượt trước.
        2. Quét các thực thể yếu tố nguy cơ (dị nguyên thức ăn, hải sản, bia rượu, thời gian).
        3. Cập nhật triệu chứng khẳng định và phủ định.
        """
        msg_lower = user_message.lower().strip()
        state.turn_count += 1

        if not state.chief_complaint and user_message:
            state.chief_complaint = user_message.strip()

        # 1. Quét Dị nguyên / Thức ăn / Chất kích thích (Triggers)
        trigger_patterns = [
            (r'(?:ăn|dùng|uống)?\s*(?:hải sản|tôm|cua|cá|mực|ghẹ|sò|ốc|đồ tanh|đậu phộng|nhộng)', 'hải sản'),
            (r'(?:uống|dùng)\s*(?:chút\s*)?(?:bia|rượu|cồn)', 'bia / rượu'),
            (r'(?:dùng|bôi|xức)\s*(?:mỹ phẩm|kem|sữa rửa mặt|thuốc bôi)', 'mỹ phẩm / hóa chất bôi ngoài'),
            (r'(?:tiếp xúc|đi vào|nguồn)\s*(?:nước lạ|ánh nắng|khói bụi)', 'môi trường lạ / ánh nắng'),
            (r'(?:uống|dùng)\s*(?:thuốc|kháng sinh|giảm đau)', 'thuốc mới uống'),
        ]
        for pat, tag in trigger_patterns:
            if re.search(pat, msg_lower) and tag not in state.clinical_slots["triggers"]:
                state.clinical_slots["triggers"].append(tag)
                if tag == "hải sản" and not state.clinical_slots.get("allergen_trigger"):
                    state.clinical_slots["allergen_trigger"] = "hải sản / đồ tanh"

        # 2. Quét Thời gian / Khởi phát (Timeline)
        if re.search(r'(?:tối qua|đêm qua)', msg_lower):
            state.clinical_slots["onset"] = "Tối qua (~12-24 giờ)"
        elif re.search(r'(?:hôm qua|ngày qua)', msg_lower):
            state.clinical_slots["onset"] = "Hôm qua (~24 giờ)"
        elif re.search(r'(?:ngày thứ 3|sang ngày thứ 3|3 ngày nay|3 ngày)', msg_lower):
            state.clinical_slots["onset"] = "Ngày thứ 3 của bệnh"
        elif re.search(r'(?:vừa mới|đột ngột|tự nhiên|mới bị)', msg_lower):
            state.clinical_slots["onset"] = "Mới khởi phát đột ngột"

        # 3. Quét Diễn biến & Đáp ứng thuốc (Medication Response)
        if re.search(r'(?:không\s*(?:thấy\s*)?đỡ|không hạ|vẫn sốt|vẫn ngứa|tăng nặng)', msg_lower):
            state.clinical_slots["medication_response"] = "Không đỡ sau khi dùng thuốc / Tự xử trí"
        elif re.search(r'(?:có đỡ|đỡ một phần|giảm nhẹ)', msg_lower):
            state.clinical_slots["medication_response"] = "Có đỡ một phần khi nghỉ ngơi"

        # 4. Quét Nhiệt độ sốt
        temp_match = re.search(r'(?:sốt\s*)?(\d{2}(?:\.\d)?)\s*(?:độ|°c)', msg_lower)
        if temp_match:
            state.clinical_slots["fever_pattern"] = f"Sốt cao {temp_match.group(1)}°C"

        # 5. Quét Vị trí giải phẫu
        body_parts = ["đùi", "lưng", "mặt", "môi", "hốc mắt", "khớp", "tay", "chân", "cổ họng", "ngực", "bụng"]
        for bp in body_parts:
            if bp in msg_lower and bp not in state.clinical_slots["anatomical_locations"]:
                state.clinical_slots["anatomical_locations"].append(bp)

        # 6. Cập nhật Triệu chứng Khẳng định
        for s in extracted_symptoms:
            term = s.get("standard_term")
            if term:
                state.confirmed_symptoms[term] = s

        # 7. Cập nhật Triệu chứng Phủ định & Gạt bỏ khỏi confirmed
        for neg in negated_symptoms:
            term = neg.get("standard_term")
            if term:
                state.negated_symptoms[term] = neg
                if term in state.confirmed_symptoms:
                    del state.confirmed_symptoms[term]

        # 8. Giải quyết Pending Question nếu lượt trước AI đã hỏi
        if state.pending_question:
            q_topic = state.pending_question.get("topic") or resolve_question_topic(state.pending_question)
            state.clinical_slots[f"answered_{q_topic}"] = user_message

            if q_topic == "allergen_trigger":
                if any(kw in msg_lower for kw in ["hải sản", "tôm", "cua", "mực", "cá", "đồ tanh", "đậu phộng", "nhộng"]):
                    state.clinical_slots["allergen_trigger"] = "hải sản / thức ăn lạ"
                elif any(kw in msg_lower for kw in ["mỹ phẩm", "sữa rửa mặt", "kem", "thuốc bôi"]):
                    state.clinical_slots["allergen_trigger"] = "mỹ phẩm / hóa chất bôi"
                elif any(kw in msg_lower for kw in ["nắng", "ánh nắng", "nước lạ"]):
                    state.clinical_slots["allergen_trigger"] = "ánh nắng / nguồn nước lạ"
                elif any(kw in msg_lower for kw in ["không", "tự nhiên", "chưa rõ", "không rõ"]):
                    state.clinical_slots["allergen_trigger"] = "không rõ dị nguyên tiếp xúc"
                else:
                    state.clinical_slots["allergen_trigger"] = user_message.strip()

                # Tăng xác suất giả thuyết dị ứng khi đã xác nhận dị nguyên
                if state.clinical_slots.get("allergen_trigger") not in ["", "không rõ dị nguyên tiếp xúc"]:
                    for hyp in state.active_hypotheses:
                        code = str(hyp.get("icd_code", ""))
                        if any(code.startswith(pfx) for pfx in ["L20", "L50", "T78", "Z91"]):
                            cur = hyp.get("probability", 0.0)
                            hyp["probability"] = min(0.95, round(cur + 0.15, 3))

            state.pending_question = None

        return state

dialogue_state_service = DialogueStateService()
