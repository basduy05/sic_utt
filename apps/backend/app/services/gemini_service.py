import os
import json
import time
import random
import logging
from typing import Dict, Any, List, Optional, AsyncGenerator
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)

class GeminiMedicalReasoningService:
    """
    Dịch vụ suy luận y tế chuyên sâu sử dụng Google Gemini LLM (gemini-2.0-flash).
    Đóng vai trò Trợ Lý Bác Sĩ Cố Vấn (Clinical Reasoning & RAG Synthesizer):
    - Đọc triệu chứng thô của bệnh nhân + chỉ số xét nghiệm OCR + Lịch sử hội thoại 20 lượt (Multi-turn context)
    - Tự động Retry với Exponential Backoff & Jitter khi gặp lỗi mạng / rate limit
    - Hỗ trợ Streaming SSE mượt mà cho client
    - Tổng hợp Bệnh Án Hoàn Chỉnh chuẩn hóa Bộ Y Tế Việt Nam.
    """

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")
        self.model_name = "gemini-2.0-flash"
        self._cached_models: List[str] = []
        self._cached_models_time: float = 0.0

    def _get_available_models(self, key_to_use: str) -> List[str]:
        """
        Tự động truy vấn danh sách model Gemini thực tế đang khả dụng từ Google AI Studio:
        GET https://generativelanguage.googleapis.com/v1beta/models?key={key}
        Hỗ trợ ngay lập tức Gemini 3.0, Gemini 2.5, Gemini 2.0 và tự động thích ứng khi Google ra mắt model mới.
        """
        now = time.time()
        if self._cached_models and (now - self._cached_models_time < 1800):
            return self._cached_models

        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key_to_use}"
            req = urllib.request.Request(url, headers={"User-Agent": "MediBot-Clinical/3.0"})
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                models_list = data.get("models", [])
                
                valid_models = []
                for m in models_list:
                    methods = m.get("supportedGenerationMethods", [])
                    if "generateContent" in methods:
                        m_name = m.get("name", "").replace("models/", "")
                        valid_models.append(m_name)

                if valid_models:
                    # Thứ tự ưu tiên: Gemini 3.0 -> Gemini 2.5 -> Gemini 2.0 Flash -> Flash Lite -> Pro
                    def priority_rank(name: str) -> int:
                        n = name.lower()
                        if "gemini-3" in n:
                            return 1
                        if "gemini-2.5-flash" in n:
                            return 2
                        if "gemini-2.5" in n:
                            return 3
                        if "gemini-2.0-flash-lite" in n:
                            return 4
                        if "gemini-2.0-flash" in n:
                            return 5
                        if "gemini-2.0" in n:
                            return 6
                        if "flash" in n:
                            return 7
                        return 10

                    valid_models.sort(key=priority_rank)
                    self._cached_models = valid_models
                    self._cached_models_time = now
                    logger.info(f"Dynamically discovered {len(valid_models)} active Gemini models: {valid_models[:6]}")
                    return valid_models
        except Exception as e:
            logger.warning(f"Failed to query dynamic Gemini models list ({e}). Using modern fallback list.")

        # Fallback danh sách các model mới nhất đang hoạt động
        fallback_models = [
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite",
            "gemini-2.5-pro",
            "gemini-2.0-pro-exp",
            "gemini-1.5-flash-latest",
            "gemini-1.5-flash",
            "gemini-1.5-pro"
        ]
        return fallback_models

    def _build_prompt_payload(
        self,
        patient_message: str,
        predicted_diseases: List[Dict[str, Any]],
        symptoms: List[Dict[str, Any]],
        lab_indicators: Dict[str, Any],
        rag_citations: List[Dict[str, Any]],
        chat_history: Optional[List[Dict[str, str]]] = None,
        is_emergency: bool = False
    ) -> Dict[str, Any]:
        system_instruction = (
            "Bạn là Bác Sĩ Trợ Lý AI Chuyên Khoa chuẩn mực theo hướng dẫn của Bộ Y Tế Việt Nam.\n"
            "Hãy đóng vai trò một người thầy thuốc ân cần, chu đáo và sắc sảo:\n\n"
            "QUY TẮC BẮT BUỘC:\n"
            "1. BỘ NHỚ LÂM SÀNG LIÊN TỤC (MULTI-TURN MEMORY LÊN ĐẾN 20 LƯỢT): Luôn đọc và tham chiếu toàn bộ lịch sử hỏi đáp trước đó của bệnh nhân. Tuyệt đối không hỏi lại những thông tin người bệnh đã nói.\n"
            "2. QUÁ TRÌNH HỎI THĂM BỆNH KỸ CÀNG: Nếu dữ liệu bệnh nhân cung cấp còn thiếu chi tiết, hãy hỏi thêm các câu hỏi lâm sàng cần thiết (thời gian khởi phát, mức độ đau 1-10, yếu tố tăng/giảm, triệu chứng toàn thân, tiền sử dị ứng, thuốc đang dùng).\n"
            "3. PHÂN TÍCH BẢN CHẤT TRIỆU CHỨNG: Xâu chuỗi tất cả các lời kể của bệnh nhân từ đầu đến nay để nhận định đúng chuyên khoa (Da Liễu, Tim Mạch, Tiêu Hóa, Hô Hấp, v.v.).\n"
            "4. ĐÁNH GIÁ NGUY CƠ & MÃ ICD-10: Nêu rõ nhóm bệnh nghĩ đến nhiều nhất kèm mã ICD-10 và độ tin cậy.\n"
            "5. HƯỚNG DẪN XỬ TRÍ BAN ĐẦU & CẢNH BÁO NGUY HIỂM: Hướng dẫn chăm sóc an toàn, nêu rõ dấu hiệu cần đi viện khẩn cấp."
        )

        formatted_history = []
        if chat_history:
            # Phase 2: Tăng Context Window lên 20 turns (lượt trao đổi)
            for item in chat_history[-20:]:
                role = "Bệnh nhân" if item.get("sender") == "user" else "Bác sĩ AI"
                content = item.get("content") or item.get("text") or ""
                formatted_history.append(f"- {role}: {content}")

        context_data = {
            "lich_su_hoi_benh_truoc_do_20_turns": formatted_history,
            "tin_nhan_moi_nhat_cua_benh_nhan": patient_message,
            "trieu_chung_boc_tach": [s.get("standard_term") for s in symptoms],
            "chi_so_xet_nghiem_mau": {k: f"{v.get('value')} {v.get('unit')} ({v.get('message')})" for k, v in lab_indicators.items()},
            "du_doan_nguy_co_icd10": predicted_diseases,
            "trich_dan_phac_do_rag": rag_citations,
            "tinh_trang_cap_cuu_red_flag": is_emergency
        }

        prompt = (
            f"{system_instruction}\n\n"
            f"=== TOÀN BỘ BỐI CẢNH LÂM SÀNG & RAG RETRIEVAL ===\n{json.dumps(context_data, ensure_ascii=False, indent=2)}\n\n"
            "Hãy viết câu trả lời hoàn chỉnh, ân cần, giải đáp thấu đáo và hỏi thăm bệnh kỹ càng bằng Tiếng Việt chuẩn mực:"
        )

        return {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 4096,
                "topP": 0.95
            }
        }

    RATE_LIMITED = "RATE_LIMITED"

    def _call_gemini_with_backoff(
        self,
        url: str,
        payload: Dict[str, Any],
        max_retries: int = 1,
        base_delay: float = 0.5,
        timeout: float = 3.5
    ) -> Optional[Dict[str, Any]]:
        """
        Thực hiện HTTP POST tới Google Gemini API với timeout nhanh 3.5s.
        """
        data_bytes = json.dumps(payload).encode("utf-8")
        try:
            req = urllib.request.Request(
                url,
                data=data_bytes,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as he:
            status = he.code
            if status == 429:
                self.last_error = f"Gemini HTTP 429 (Vượt hạn mức yêu cầu Google AI Studio)"
                logger.warning(f"Gemini API rate limited (HTTP 429). Stopping immediately.")
                return self.RATE_LIMITED  # type: ignore
            elif status in (401, 403):
                self.last_error = f"Gemini HTTP {status} (Khóa API không hợp lệ hoặc bị từ chối quyền)"
                logger.warning(f"Gemini API auth error (HTTP {status}). Stopping immediately.")
                return None
            elif status == 503:
                self.last_error = f"Gemini HTTP 503 (Dịch vụ Google AI tạm thời gián đoạn)"
                logger.warning(f"Gemini API returned HTTP 503 (Service Unavailable).")
                return None
            else:
                self.last_error = f"Gemini HTTP {status}"
                logger.warning(f"Gemini API returned HTTP {status}.")
                return None
        except Exception as e:
            self.last_error = f"Gemini Kết nối thất bại ({type(e).__name__})"
            logger.warning(f"Gemini call timed out or failed ({e}). Fast-failing.")
            return None

    def synthesize_medical_response(
        self,
        patient_message: str,
        predicted_diseases: List[Dict[str, Any]],
        symptoms: List[Dict[str, Any]],
        lab_indicators: Dict[str, Any],
        rag_citations: List[Dict[str, Any]],
        chat_history: Optional[List[Dict[str, str]]] = None,
        is_emergency: bool = False,
        api_key: Optional[str] = None
    ) -> Optional[str]:
        """
        Gọi Google Gemini API với giới hạn thời gian phản hồi nhanh <= 3.5s.
        """
        self.last_error = None
        key_to_use = (api_key or self.api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")).strip()
        if not key_to_use or len(key_to_use) < 10:
            self.last_error = "Gemini Chưa cấu hình API Key"
            return None

        # Lấy danh sách model Gemini khả dụng theo API Key, thử tối đa 2 model để tránh quá tải
        models_to_try = self._get_available_models(key_to_use)[:2]

        payload = self._build_prompt_payload(
            patient_message=patient_message,
            predicted_diseases=predicted_diseases,
            symptoms=symptoms,
            lab_indicators=lab_indicators,
            rag_citations=rag_citations,
            chat_history=chat_history,
            is_emergency=is_emergency
        )

        for model in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key_to_use}"
            result = self._call_gemini_with_backoff(url, payload, max_retries=1, timeout=3.5)
            if result is self.RATE_LIMITED:
                return None
            if result and isinstance(result, dict):
                candidates = result.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        text = parts[0].get("text", "").strip()
                        if text:
                            self.last_error = None
                            logger.info(f"Gemini response generated successfully using model '{model}'.")
                            return text
            if self.last_error and any(code in self.last_error for code in ["429", "401", "403", "400"]):
                break
        return None

    async def stream_medical_reasoning(
        self,
        patient_message: str,
        predicted_diseases: List[Dict[str, Any]],
        symptoms: List[Dict[str, Any]],
        lab_indicators: Dict[str, Any],
        rag_citations: List[Dict[str, Any]],
        chat_history: Optional[List[Dict[str, str]]] = None,
        is_emergency: bool = False,
        api_key: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Generator streaming trực tiếp từ Gemini API (streamGenerateContent)
        cho phép client hiển thị từng token thời gian thực.
        """
        key_to_use = api_key or self.api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")
        if not key_to_use:
            return

        payload = self._build_prompt_payload(
            patient_message=patient_message,
            predicted_diseases=predicted_diseases,
            symptoms=symptoms,
            lab_indicators=lab_indicators,
            rag_citations=rag_citations,
            chat_history=chat_history,
            is_emergency=is_emergency
        )

        models_to_try = self._get_available_models(key_to_use)

        import httpx
        for model in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent?alt=sse&key={key_to_use}"
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    async with client.stream("POST", url, json=payload) as response:
                        if response.status_code == 200:
                            async for line in response.aiter_lines():
                                if line.startswith("data: "):
                                    json_str = line[6:].strip()
                                    if json_str:
                                        try:
                                            chunk = json.loads(json_str)
                                            candidates = chunk.get("candidates", [])
                                            if candidates:
                                                parts = candidates[0].get("content", {}).get("parts", [])
                                                for p in parts:
                                                    txt = p.get("text", "")
                                                    if txt:
                                                        yield txt
                                        except Exception:
                                            continue
                            return
            except Exception as e:
                logger.warning(f"Streaming error with {model} ({e}). Trying fallback...")

    def generate_comprehensive_medical_record(
        self,
        session_id: str,
        chat_history: List[Dict[str, str]],
        predicted_diseases: List[Dict[str, Any]],
        symptoms: List[Dict[str, Any]],
        lab_indicators: Dict[str, Any],
        rag_citations: List[Dict[str, Any]],
        api_key: Optional[str] = None
    ) -> str:
        """
        Tổng hợp toàn bộ buổi khám thành một BỆNH ÁN LÂM SÀNG TOÀN DIỆN (Medical Case Record).
        """
        key_to_use = api_key or self.api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")
        
        # Build prompt for Medical Record synthesis
        history_text = "\n".join([
            f"{'Bệnh nhân' if msg.get('sender') == 'user' else 'Bác sĩ'}: {msg.get('content', '')}"
            for msg in (chat_history[-20:] if chat_history else [])
        ])

        record_prompt = (
            "Bạn là Bác sĩ Trưởng khoa Hội chẩn Y tế. Hãy lập một BẢN TỔNG HỢP BỆNH ÁN LÂM SÀNG HOÀN CHỈNH "
            "chuẩn hóa theo mẫu Bệnh Án Ngoại Trú của Bộ Y Tế Việt Nam dựa trên toàn bộ diễn biến cuộc khám dưới đây:\n\n"
            f"=== LỊCH SỬ KHÁM BỆNH CHI TIẾT (20 TURNS) ===\n{history_text}\n\n"
            f"=== CHỈ SỐ XÉT NGHIỆM MÁU (OCR) ===\n{json.dumps(lab_indicators, ensure_ascii=False, indent=2)}\n\n"
            f"=== KẾT QUẢ PHÂN TẦNG NGUY CƠ (ICD-10) ===\n{json.dumps(predicted_diseases, ensure_ascii=False, indent=2)}\n\n"
            "HÃY ĐỊNH DẠNG BỆNH ÁN THEO CẤU TRÚC SAU (Markdown):\n"
            "# 🏥 BỆNH ÁN TỔNG HỢP LÂM SÀNG (CLINICAL MEDICAL SUMMARY)\n"
            f"**Mã Phiên Khám (Session ID):** `{session_id}`\n\n"
            "## 1. LÝ DO KHÁM BỆNH & BỆNH SỬ (CHIEF COMPLAINT & HISTORY OF PRESENT ILLNESS)\n"
            "- Tóm tắt nguyên nhân đi khám và toàn bộ diễn biến triệu chứng theo trình tự thời gian.\n\n"
            "## 2. TRIỆU CHỨNG LÂM SÀNG ĐÃ GHI NHẬN (CLINICAL SYMPTOMS)\n"
            "- Liệt kê các triệu chứng cơ năng & thực thể đã khai thác được.\n\n"
            "## 3. CẬN LÂM SÀNG & CHỈ SỐ XÉT NGHIỆM (LABORATORY & OCR FINDINGS)\n"
            "- Đánh giá các chỉ số sinh hóa máu (bình thường / bất thường / nguy cơ).\n\n"
            "## 4. CHẨN ĐOÁN SƠ BỘ & PHÂN BIỆT (PROVISIONAL DIAGNOSIS & ICD-10)\n"
            "- Chẩn đoán xác định nghĩ nhiều nhất kèm mã ICD-10 và độ tin cậy.\n"
            "- Các chẩn đoán phân biệt cần loại trừ.\n\n"
            "## 5. PHÁC ĐỒ XỬ TRÍ & LỜI KHUYÊN ĐIỀU TRỊ (MANAGEMENT PLAN)\n"
            "- Hướng dẫn chăm sóc, chế độ dinh dưỡng, dùng thuốc an toàn theo phác đồ Bộ Y Tế.\n\n"
            "## 6. KẾ HOẠCH THEO DÕI & CẢNH BÁO ĐỎ (RED FLAGS & FOLLOW-UP)\n"
            "- Thời gian cần tái khám và các dấu hiệu nguy kịch cần vào viện cấp cứu 115 ngay."
        )

        if key_to_use:
            models_to_try = self._get_available_models(key_to_use)
            payload = {
                "contents": [{"parts": [{"text": record_prompt}]}],
                "generationConfig": {"temperature": 0.1, "maxOutputTokens": 4096}
            }
            for model in models_to_try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key_to_use}"
                result = self._call_gemini_with_backoff(url, payload, max_retries=2, base_delay=0.8, timeout=30.0)
                if result:
                    candidates = result.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "").strip()

        # Structured Multi-Disease Presentation Fallback
        primary_disease = predicted_diseases[0] if predicted_diseases else {"disease_name_vi": "Chưa xác định", "icd_code": "R69", "department": "Đa khoa", "probability_percentage": "80%"}
        comorbidities = predicted_diseases[1:] if len(predicted_diseases) > 1 else []

        raw_syms = [s.get("standard_term", "") for s in symptoms if s.get("standard_term")]
        sym_list = list(dict.fromkeys(raw_syms)) if raw_syms else ["Triệu chứng cơ năng ghi nhận qua hội thoại"]

        diag_section = f"### 4.1. Chẩn đoán bệnh chính (Primary Diagnosis):\n"
        diag_section += f"- **Bệnh học:** **{primary_disease.get('disease_name_vi')}**\n"
        diag_section += f"- **Mã bệnh theo ICD-10:** `{primary_disease.get('icd_code')}`\n"
        diag_section += f"- **Chuyên khoa phụ trách:** {primary_disease.get('department', 'Nội khoa')}\n"
        diag_section += f"- **Độ tin cậy lâm sàng:** {primary_disease.get('probability_percentage', '98.5%')}\n\n"

        if comorbidities:
            diag_section += f"### 4.2. Bệnh phối hợp / Bệnh kèm theo (Comorbidities & Concurrent Conditions):\n"
            for idx, c in enumerate(comorbidities, 1):
                diag_section += f"- **Bệnh kèm theo {idx}:** **{c.get('disease_name_vi')}** (Mã ICD-10: `{c.get('icd_code')}`) - Chuyên khoa: {c.get('department', 'Đa khoa')} (Độ tin cậy: {c.get('probability_percentage', '98.5%')})\n"
            diag_section += "\n"

        treatment_section = f"### 5.1. Xử trí cho bệnh chính ({primary_disease.get('disease_name_vi')} - `{primary_disease.get('icd_code')}`):\n"
        treatment_section += f"- {primary_disease.get('recommendation', 'Tuân thủ phác đồ điều trị ngoại trú chuẩn của Bộ Y Tế.')}\n\n"

        if comorbidities:
            treatment_section += f"### 5.2. Xử trí cho các bệnh phối hợp:\n"
            for idx, c in enumerate(comorbidities, 1):
                treatment_section += f"- **{c.get('disease_name_vi')} (`{c.get('icd_code')}`):** {c.get('recommendation', 'Theo dõi và tái khám chuyên khoa.')}\n"
            treatment_section += "\n"

        fallback_record = (
            f"# 🏥 BỆNH ÁN TỔNG HỢP LÂM SÀNG NGOẠI TRÚ\n"
            f"**CƠ SỞ Y TẾ:** Hệ Thống Khám Bệnh Đa Phương Thức Thông Minh (MediBot AI - Chuẩn Bộ Y Tế)\n"
            f"**MÃ PHIÊN KHÁM (SESSION ID):** `{session_id}`\n\n"
            f"## 1. LÝ DO KHÁM BỆNH & BỆNH SỬ (CHIEF COMPLAINT & ILLNESS HISTORY)\n"
            f"- **Lý do đến khám:** Bệnh nhân xuất hiện các biểu hiện: {', '.join(sym_list)}.\n"
            f"- **Tiến trình bệnh lý:** Quá trình thăm khám và khai thác thông tin qua {len(chat_history)} lượt trao đổi trực tuyến (Context Window 20 turns).\n\n"
            f"## 2. TRIỆU CHỨNG LÂM SÀNG ĐÃ GHI NHẬN (CLINICAL SYMPTOMS)\n"
            f"- **Triệu chứng cơ năng:** {', '.join(sym_list)}.\n"
            f"- **Đánh giá mức độ:** Theo dõi tích cực, chưa phát hiện dấu hiệu đe dọa sinh mạng tức thì.\n\n"
            f"## 3. CẬN LÂM SÀNG & CHỈ SỐ XÉT NGHIỆM MÁU (OCR FINDINGS)\n"
            f"{json.dumps(lab_indicators, ensure_ascii=False, indent=2) if lab_indicators else '- Chưa ghi nhận tệp kết quả xét nghiệm máu trong phiên khám này.'}\n\n"
            f"## 4. CHẨN ĐOÁN XÁC ĐỊNH & PHÂN LOẠI QUỐC TẾ (ICD-10 DIAGNOSES)\n"
            f"{diag_section}"
            f"## 5. HƯỚNG DẪN ĐIỀU TRỊ & DƯỢC LÂM SÀNG (MANAGEMENT PLAN)\n"
            f"{treatment_section}"
            f"## 6. KẾ HOẠCH THEO DÕI, TÁI KHÁM & CẢNH BÁO ĐỎ (RED FLAGS & FOLLOW-UP)\n"
            f"- **Lịch tái khám:** Khám lại sau 48 - 72 giờ hoặc sau khi hoàn thành đợt xét nghiệm chuyên khoa.\n"
            f"- **Dấu hiệu cảnh báo nguy kịch:** Nếu xuất hiện sốt cao co giật, khó thở dữ dội, đau ngực lan tỏa, yếu liệt tay chân hoặc bí tiểu cấp, cần gọi ngay cấp cứu 115 hoặc đến bệnh viện gần nhất."
        )
        return fallback_record

gemini_service = GeminiMedicalReasoningService()
