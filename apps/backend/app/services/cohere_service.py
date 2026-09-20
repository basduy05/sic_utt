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

        system_prompt = (
            "Bạn là Bác Sĩ Chuyên Khoa Hội Chẩn AI (Second Opinion) theo hướng dẫn của Bộ Y Tế Việt Nam. "
            "Hãy đóng vai trò một chuyên gia hội chẩn y khoa ân cần, chu đáo và sắc sảo.\n\n"
            "QUY TẮC BẮT BUỘC:\n"
            "1. KHỐI SUY LUẬN LÂM SÀNG CHUỖI TƯ DUY (CLINICAL CHAIN-OF-THOUGHT - BẮT BUỘC):\n"
            "Trước khi viết câu trả lời cho bệnh nhân, bạn BẮT BUỘC phải mở đầu bằng một khối suy luận nằm trong cặp thẻ <clinical_thinking>...</clinical_thinking> gồm:\n"
            "<clinical_thinking>\n"
            "- Cơ chế bệnh sinh & Phân tích triệu chứng: Cơ chế sinh lý học/giải phẫu đằng sau các triệu chứng.\n"
            "- Chẩn đoán phân biệt: Các bệnh lý tương đồng và tiêu chuẩn loại trừ.\n"
            "- Đánh giá cờ đỏ (Red Flags): Các dấu hiệu cảnh báo nguy hiểm.\n"
            "- Định hướng tiếp theo: Câu hỏi làm rõ hoặc cận lâm sàng cần thiết.\n"
            "</clinical_thinking>\n\n"
            f"2. GIAI ĐOẠN LÂM SÀNG: {stage_desc}\n"
            "3. LỜI KHUYÊN BỆNH NHÂN: Sau khối </clinical_thinking>, hãy trình bày câu trả lời ân cần, súc tích bằng Tiếng Việt chuẩn mực."
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
            "Hãy viết câu trả lời y tế đầy đủ, ân cần và tuân thủ đúng giai đoạn lâm sàng bằng Tiếng Việt:"
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
