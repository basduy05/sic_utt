import os
import json
import logging
from typing import Dict, Any, List, Optional
import httpx
from ..core.config import settings

logger = logging.getLogger(__name__)

class LocalLLMService:
    """
    Dịch vụ suy luận lâm sàng sử dụng Mô hình Ngôn ngữ Lớn Cục bộ (Local LLM):
    - Hỗ trợ kết nối trực tiếp qua Ollama API (/api/chat, /api/generate)
    - Hỗ trợ OpenAI-compatible API protocol (/v1/chat/completions) cho LM Studio, vLLM, llama.cpp
    - Hoạt động 100% offline, bảo mật dữ liệu y tế của bệnh nhân tại máy chủ nội bộ.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        api_type: Optional[str] = None,
        timeout: Optional[float] = None
    ):
        self.base_url = (base_url or settings.LOCAL_LLM_URL).rstrip("/")
        self.model_name = model_name or settings.LOCAL_LLM_MODEL
        self.api_type = (api_type or settings.LOCAL_LLM_TYPE).lower()
        self.timeout = timeout or settings.LOCAL_LLM_TIMEOUT

    async def is_available(self) -> bool:
        """Kiểm tra nhanh xem Local LLM Server có đang mở port và phản hồi không (0.3s max)."""
        import socket
        try:
            from urllib.parse import urlparse
            parsed = urlparse(self.base_url)
            host = parsed.hostname or "127.0.0.1"
            port = parsed.port or (11434 if self.api_type == "ollama" else 80)
            with socket.create_connection((host, port), timeout=0.3):
                pass
        except (OSError, Exception):
            return False

        try:
            async with httpx.AsyncClient(timeout=1.0) as client:
                if self.api_type == "ollama":
                    resp = await client.get(f"{self.base_url}/api/version")
                    return resp.status_code == 200
                else:
                    resp = await client.get(f"{self.base_url}/v1/models")
                    return resp.status_code == 200
        except Exception:
            return False

    def _build_system_prompt(self) -> str:
        return (
            "Bạn là Bác Sĩ Trợ Lý AI Chuyên Khoa chuẩn mực theo hướng dẫn của Bộ Y Tế Việt Nam.\n"
            "Hãy đóng vai trò một người thầy thuốc ân cần, chu đáo, sắc sảo và tuân thủ các quy tắc y khoa:\n\n"
            "QUY TẮC BẮT BUỘC:\n"
            "1. BỘ NHỚ LÂM SÀNG LIÊN TỤC: Đọc và tham chiếu lịch sử hỏi đáp trước đó. Tuyệt đối không hỏi lại những gì bệnh nhân đã chia sẻ.\n"
            "2. HỎI THĂM BỆNH KỸ CÀNG: Nếu còn thiếu chi tiết, hãy hỏi thêm thời gian khởi phát, mức độ đau (1-10), triệu chứng kèm theo, tiền sử bệnh.\n"
            "3. ĐÁNH GIÁ NGUY CƠ & MÃ ICD-10: Nêu rõ nhóm bệnh nghĩ đến nhiều nhất kèm mã ICD-10 và giải thích ngắn gọn bằng ngôn ngữ dễ hiểu.\n"
            "4. CHỈ SỐ XÉT NGHIỆM: Nếu có kết quả cận lâm sàng (máu, nước tiểu, chẩn đoán hình ảnh), hãy phân tích ý nghĩa các chỉ số bất thường.\n"
            "5. HƯỚNG DẪN XỬ TRÍ BAN ĐẦU & CẢNH BÁO NGUY HIỂM: Hướng dẫn chăm sóc an toàn, nêu rõ dấu hiệu cần đi viện khẩn cấp ngay.\n"
            "LƯU Ý: Tuyệt đối không tự ý kê đơn thuốc kháng sinh hoặc thuốc đặc trị đường uống liều cao. Luôn khuyên bệnh nhân khám trực tiếp tại cơ sở y tế khi cần thiết."
        )

    def _build_context_prompt(
        self,
        patient_message: str,
        predicted_diseases: List[Dict[str, Any]],
        symptoms: List[Dict[str, Any]],
        lab_indicators: Dict[str, Any],
        rag_citations: List[Dict[str, Any]],
        chat_history: Optional[List[Dict[str, str]]] = None,
        is_emergency: bool = False
    ) -> str:
        formatted_history = []
        if chat_history:
            for item in chat_history[-6:]:
                role = "Bệnh nhân" if item.get("sender") == "user" else "Bác sĩ AI"
                content = item.get("content") or item.get("text") or ""
                formatted_history.append(f"- {role}: {content}")

        context_data = {
            "lich_su_hoi_benh_truoc_do": formatted_history,
            "tin_nhan_moi_nhat_cua_benh_nhan": patient_message,
            "trieu_chung_boc_tach": [s.get("standard_term") for s in symptoms if s.get("standard_term")],
            "chi_so_xet_nghiem_mau": {k: f"{v.get('value')} {v.get('unit')} ({v.get('message')})" for k, v in lab_indicators.items()},
            "du_doan_nguy_co_icd10": predicted_diseases,
            "trich_dan_phac_do_rag": rag_citations,
            "tinh_trang_cap_cuu_red_flag": is_emergency
        }

        return (
            f"=== BỐI CẢNH LÂM SÀNG & RAG RETRIEVAL ===\n"
            f"{json.dumps(context_data, ensure_ascii=False, indent=2)}\n\n"
            f"Hãy viết câu trả lời hoàn chỉnh, ân cần, giải đáp thấu đáo và hỏi thăm bệnh kỹ càng bằng Tiếng Việt chuẩn mực:"
        )

    async def generate_response(
        self,
        patient_message: str,
        predicted_diseases: List[Dict[str, Any]],
        symptoms: List[Dict[str, Any]],
        lab_indicators: Dict[str, Any],
        rag_citations: List[Dict[str, Any]],
        chat_history: Optional[List[Dict[str, str]]] = None,
        is_emergency: bool = False
    ) -> Optional[str]:
        if not await self.is_available():
            logger.info("Local LLM (Ollama) is offline. Skipping to next clinical reasoning tier immediately.")
            return None

        system_prompt = self._build_system_prompt()
        user_prompt = self._build_context_prompt(
            patient_message=patient_message,
            predicted_diseases=predicted_diseases,
            symptoms=symptoms,
            lab_indicators=lab_indicators,
            rag_citations=rag_citations,
            chat_history=chat_history,
            is_emergency=is_emergency
        )

        try:
            async with httpx.AsyncClient(timeout=min(self.timeout, 4.0)) as client:
                if self.api_type == "ollama":
                    # Ollama /api/chat endpoint
                    payload = {
                        "model": self.model_name,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "stream": False,
                        "options": {
                            "temperature": 0.3,
                            "top_p": 0.9,
                            "num_predict": 1024
                        }
                    }
                    resp = await client.post(f"{self.base_url}/api/chat", json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        message = data.get("message", {}).get("content", "")
                        if message.strip():
                            logger.info(f"Local LLM (Ollama: {self.model_name}) answered successfully.")
                            return message.strip()
                else:
                    # OpenAI-compatible /v1/chat/completions endpoint
                    payload = {
                        "model": self.model_name,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": 0.3,
                        "max_tokens": 1024
                    }
                    resp = await client.post(f"{self.base_url}/v1/chat/completions", json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        choices = data.get("choices", [])
                        if choices:
                            message = choices[0].get("message", {}).get("content", "")
                            if message.strip():
                                logger.info(f"Local LLM (OpenAI-Compatible: {self.model_name}) answered successfully.")
                                return message.strip()

                logger.warning(f"Local LLM returned status code {resp.status_code}: {resp.text[:200]}")
                return None

        except Exception as e:
            logger.warning(f"Local LLM inference failed: {e}")
            return None
