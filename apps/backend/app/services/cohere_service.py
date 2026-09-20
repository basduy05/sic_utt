import os
import json
import time
import logging
from typing import Dict, Any, List, Optional
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)

class CohereMedicalReasoningService:
    """
    Dịch vụ suy luận y tế sử dụng Cohere API (command-r-plus).
    Chạy song song với Gemini để race condition, bên nào trả lời trước thì hiển thị trước.
    """

    def __init__(self):
        self.api_key = os.getenv("COHERE_API_KEY", "")
        self.model = "command-r-08-2024"
        self.api_base = "https://api.cohere.com/v1/chat"
        self.last_error: Optional[str] = None

    def _build_medical_prompt(
        self,
        patient_message: str,
        predicted_diseases: List[Dict[str, Any]],
        symptoms: List[Dict[str, Any]],
        lab_indicators: Dict[str, Any],
        rag_citations: List[Dict[str, Any]],
        chat_history: Optional[List[Dict[str, str]]] = None,
        is_emergency: bool = False,
        negated_symptoms: Optional[List[Dict[str, Any]]] = None,
        clarifying_questions: Optional[List[Dict[str, Any]]] = None,
        clinical_stage: str = "provisional_assumption"
    ) -> Dict[str, Any]:
        """Xây dựng payload cho Cohere Chat API."""
        stage_desc = (
            "GIAI ĐOẠN: SÀNG LỌC BAN ĐẦU - Chưa đủ dữ kiện kết luận, chỉ hỏi thăm làm rõ triệu chứng."
            if clinical_stage == "initial_screening"
            else "GIAI ĐOẠN: CHẨN ĐOÁN GIẢ ĐỊNH LÂM SÀNG - Bắt buộc tuyên bố là giả định, hướng dẫn an toàn và hỏi thêm câu hỏi phân biệt để làm rõ bệnh án."
            if clinical_stage == "provisional_assumption"
            else "GIAI ĐOẠN: KẾT LUẬN SƠ BỘ SÀNG LỌC - Đã đủ dữ kiện (độ tin cậy cao >= 75%), đưa ra kết luận chẩn đoán, phác đồ điều trị Bộ Y Tế, và cảnh báo cấp cứu."
        )

        top_pred = predicted_diseases[0] if predicted_diseases else {}
        top_disease_name = top_pred.get("disease_name_vi", "Bệnh lý cần theo dõi")
        top_icd = top_pred.get("icd_code", "ICD-10")
        prob_val = top_pred.get("probability_percentage")
        if not prob_val and top_pred:
            raw_prob = float(top_pred.get("probability", 0.85))
            prob_val = f"{round(raw_prob * 100, 1)}%"
        if not prob_val:
            prob_val = "85.0%"

        system_prompt = (
            "Bạn là Bác Sĩ Chuyên Khoa Hội Chẩn AI Cấp Cao (Senior Second Opinion AI Specialist) theo chuẩn chuyên môn của Bộ Y Tế Việt Nam.\n"
            "Hãy đóng vai trò một chuyên gia hội chẩn y khoa độc lập, sắc sảo, đánh giá đối chiếu phản biện và bảo vệ an toàn tối đa cho người bệnh.\n\n"
            "QUY TẮC BẮT BUỘC CHO HỘI CHẨN:\n"
            "1. KHỐI SUY LUẬN LÂM SÀNG CHUỖI TƯ DUY NÂNG CAO (CLINICAL CHAIN-OF-THOUGHT - BẮT BUỘC):\n"
            "Mở đầu câu trả lời BẮT BUỘC bằng khối suy luận nằm trong cặp thẻ <clinical_thinking>...</clinical_thinking> gồm 5 phần mục chi tiết:\n"
            "<clinical_thinking>\n"
            "- Cơ chế bệnh sinh & Phân tích triệu chứng: Phân tích sâu cơ chế giải phẫu, sinh lý bệnh hoặc biến động huyết học/miễn dịch giải thích các triệu chứng người bệnh gặp phải.\n"
            "- Chẩn đoán phân biệt & Tiêu chí loại trừ: So sánh chi tiết bệnh lý giả định hàng đầu với 2-3 bệnh lý tương đồng (kèm mã ICD-10); chỉ ra triệu chứng then chốt để loại trừ.\n"
            "- Đánh giá cờ đỏ (Red Flags) & Nguy cơ cấp cứu: Rà soát nghiêm ngặt các dấu hiệu nguy hiểm tính mạng theo phác đồ Bộ Y Tế (hô hấp, tuần hoàn, xuất huyết, thần kinh).\n"
            "- Rà soát an toàn dược lâm sàng: Cảnh báo nguy cơ dùng thuốc sai, tương tác thuốc và các thuốc chống chỉ định nguy hiểm (đặc biệt không tự ý dùng kháng sinh, corticoid, aspirin/NSAID khi chưa rõ chẩn đoán).\n"
            "- Định hướng tiếp theo & Khuyến nghị cận lâm sàng: Đề xuất các xét nghiệm định lượng then chốt (Công thức máu CBC, men gan, điện giải, chẩn đoán hình ảnh) và mốc ngày nguy hiểm cần theo dõi.\n"
            "</clinical_thinking>\n\n"
            f"2. BẮT BUỘC NÊU RÕ TỈ LỆ PHẦN TRĂM DỰ ĐOÁN: Trong phần tư vấn cho người bệnh sau thẻ suy luận, bạn BẮT BUỘC phải trích dẫn tên bệnh lý dự đoán: **{top_disease_name}** (Mã ICD-10: `{top_icd}`) kèm theo **Tỉ lệ dự đoán: {prob_val}** (hoặc Độ tin cậy dự đoán: {prob_val}). Tuyệt đối không được bỏ sót con số phần trăm này.\n"
            f"3. GIAI ĐOẠN LÂM SÀNG: {stage_desc}\n"
            "4. LỜI KHUYÊN BỆNH NHÂN: Sau khối </clinical_thinking>, trình bày câu trả lời ân cần, chi tiết, có chiều sâu y khoa và chuẩn mực Tiếng Việt."
        )

        # Build chat history for Cohere format
        chat_history_cohere = []
        if chat_history:
            for item in chat_history[-10:]:
                role = "USER" if item.get("sender") == "user" else "CHATBOT"
                content = item.get("content") or item.get("text", "")
                if content:
                    chat_history_cohere.append({"role": role, "message": content})

        # Build context as user message
        context_data = {
            "giai_doan_lam_sang": clinical_stage,
            "tin_nhan": patient_message,
            "benh_ly_du_doan_chinh": f"{top_disease_name} ({top_icd}) - Tỉ lệ: {prob_val}",
            "trieu_chung": [s.get("standard_term") for s in symptoms if s.get("standard_term")],
            "trieu_chung_loai_tru": [s.get("standard_term") for s in (negated_symptoms or []) if s.get("standard_term")],
            "cau_hoi_lam_ro_de_xuat": clarifying_questions or [],
            "xet_nghiem": {k: f"{v.get('value')} {v.get('unit')} ({v.get('message')})" for k, v in lab_indicators.items()},
            "du_doan_icd10": predicted_diseases[:3],
            "rag_phac_do": [{"title": c.get("title"), "content": str(c.get("content", ""))[:200]} for c in rag_citations[:2]],
            "cap_cuu": is_emergency,
        }

        user_message = (
            f"Dữ liệu lâm sàng:\n{json.dumps(context_data, ensure_ascii=False, indent=2)}\n\n"
            f"LƯU Ý QUAN TRỌNG: Nhớ mở đầu bằng khối <clinical_thinking>...</clinical_thinking> và ghi rõ Tỉ lệ dự đoán ({prob_val}) của {top_disease_name} trong câu trả lời y tế:"
        )

        return {
            "model": self.model,
            "message": user_message,
            "chat_history": chat_history_cohere,
            "preamble": system_prompt,
            "temperature": 0.3,
            "max_tokens": 1500,
        }

    def synthesize_medical_response(
        self,
        patient_message: str,
        predicted_diseases: List[Dict[str, Any]],
        symptoms: List[Dict[str, Any]],
        lab_indicators: Dict[str, Any],
        rag_citations: List[Dict[str, Any]],
        chat_history: Optional[List[Dict[str, str]]] = None,
        is_emergency: bool = False,
        api_key: Optional[str] = None,
        timeout: float = 3.5,
        negated_symptoms: Optional[List[Dict[str, Any]]] = None,
        clarifying_questions: Optional[List[Dict[str, Any]]] = None,
        clinical_stage: str = "provisional_assumption"
    ) -> Optional[str]:
        """
        Gọi Cohere API đồng bộ với timeout 3.5s.
        """
        self.last_error = None
        key = (api_key or self.api_key or os.getenv("COHERE_API_KEY", "")).strip()
        if not key or len(key) < 10:
            self.last_error = "Cohere Chưa cấu hình API Key"
            return None

        payload = self._build_medical_prompt(
            patient_message=patient_message,
            predicted_diseases=predicted_diseases,
            symptoms=symptoms,
            lab_indicators=lab_indicators,
            rag_citations=rag_citations,
            chat_history=chat_history,
            is_emergency=is_emergency,
            negated_symptoms=negated_symptoms,
            clarifying_questions=clarifying_questions,
            clinical_stage=clinical_stage
        )

        try:
            data_bytes = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                self.api_base,
                data=data_bytes,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {key}",
                    "Accept": "application/json",
                },
            )
            with urllib.request.urlopen(req, timeout=timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
                text = result.get("text", "").strip()
                if text:
                    self.last_error = None
                    logger.info(f"Cohere ({self.model}) responded successfully.")

                    # BẢO ĐẢM TỈ LỆ PHẦN TRĂM DỰ ĐOÁN LUÔN CÓ MẶT
                    top_pred = predicted_diseases[0] if predicted_diseases else {}
                    top_disease_name = top_pred.get("disease_name_vi")
                    top_icd = top_pred.get("icd_code")
                    prob_val = top_pred.get("probability_percentage")
                    if not prob_val and top_pred:
                        raw_prob = float(top_pred.get("probability", 0.85))
                        prob_val = f"{round(raw_prob * 100, 1)}%"

                    if prob_val and top_disease_name and ("%" not in text or prob_val not in text):
                        pct_anchor = f"🎯 **Định hướng hội chẩn độc lập:** Bệnh lý nghi ngờ chính: **{top_disease_name}** (Mã ICD-10: `{top_icd}`) — **Tỉ lệ dự đoán: {prob_val}**\n\n"
                        if "</clinical_thinking>" in text:
                            parts = text.split("</clinical_thinking>", 1)
                            text = parts[0] + "</clinical_thinking>\n\n" + pct_anchor + parts[1].strip()
                        else:
                            text = pct_anchor + text

                    return text
        except urllib.error.HTTPError as he:
            err_msg = f"HTTP {he.code}"
            err_body = ""
            try:
                err_body = he.read().decode("utf-8", errors="ignore")
            except Exception:
                pass
            if he.code == 429:
                err_msg += " (Rate limit)"
            elif he.code in (401, 403):
                err_msg += " (Khóa API không hợp lệ)"
            self.last_error = f"Cohere {err_msg}"
            logger.warning(f"Cohere API returned {err_msg}. Detail: {err_body}")
        except Exception as e:
            self.last_error = f"Cohere Kết nối thất bại ({type(e).__name__})"
            logger.warning(f"Cohere call failed ({e}).")

        return None


cohere_service = CohereMedicalReasoningService()
