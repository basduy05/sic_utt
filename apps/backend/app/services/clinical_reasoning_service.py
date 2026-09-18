import os
import json
import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from ..core.config import settings
from .local_llm_service import LocalLLMService
from .gemini_service import GeminiMedicalReasoningService
from .cohere_service import CohereMedicalReasoningService

logger = logging.getLogger(__name__)

class UnifiedClinicalReasoningService:
    """
    Trung tâm Điều phối Suy luận Y khoa (Unified Clinical Reasoning Coordinator):
    - Race condition giữa Google Gemini và Cohere: bên nào trả lời trước → kết quả chính.
    - Câu trả lời còn lại → alternative_answer để người dùng chuyển đổi bằng mũi tên.
    - Fallback sang Local LLM hoặc Deterministic Engine nếu cả 2 cloud thất bại.
    """

    def __init__(self):
        self.local_llm = LocalLLMService()
        self.gemini_service = GeminiMedicalReasoningService()
        self.cohere_service = CohereMedicalReasoningService()
        self.provider_mode = settings.LLM_PROVIDER.lower()

    async def _call_gemini_async(
        self,
        patient_message: str,
        predicted_diseases: List[Dict[str, Any]],
        symptoms: List[Dict[str, Any]],
        lab_indicators: Dict[str, Any],
        rag_citations: List[Dict[str, Any]],
        chat_history: Optional[List[Dict[str, str]]],
        is_emergency: bool,
        api_key: Optional[str],
        negated_symptoms: Optional[List[Dict[str, Any]]] = None,
        clarifying_questions: Optional[List[Dict[str, Any]]] = None,
        clinical_stage: str = "provisional_assumption",
    ) -> Tuple[Optional[str], str]:
        """Gọi Gemini trong thread pool để không block event loop."""
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.gemini_service.synthesize_medical_response(
                    patient_message=patient_message,
                    predicted_diseases=predicted_diseases,
                    symptoms=symptoms,
                    lab_indicators=lab_indicators,
                    rag_citations=rag_citations,
                    chat_history=chat_history,
                    is_emergency=is_emergency,
                    api_key=api_key,
                    negated_symptoms=negated_symptoms,
                    clarifying_questions=clarifying_questions,
                    clinical_stage=clinical_stage,
                )
            )
            return (result, "cloud_gemini") if result else (None, "cloud_gemini")
        except Exception as e:
            logger.warning(f"Gemini async call failed: {e}")
            return (None, "cloud_gemini")

    async def _call_cohere_async(
        self,
        patient_message: str,
        predicted_diseases: List[Dict[str, Any]],
        symptoms: List[Dict[str, Any]],
        lab_indicators: Dict[str, Any],
        rag_citations: List[Dict[str, Any]],
        chat_history: Optional[List[Dict[str, str]]],
        is_emergency: bool,
        api_key: Optional[str],
        negated_symptoms: Optional[List[Dict[str, Any]]] = None,
        clarifying_questions: Optional[List[Dict[str, Any]]] = None,
        clinical_stage: str = "provisional_assumption",
    ) -> Tuple[Optional[str], str]:
        """Gọi Cohere trong thread pool để không block event loop."""
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.cohere_service.synthesize_medical_response(
                    patient_message=patient_message,
                    predicted_diseases=predicted_diseases,
                    symptoms=symptoms,
                    lab_indicators=lab_indicators,
                    rag_citations=rag_citations,
                    chat_history=chat_history,
                    is_emergency=is_emergency,
                    api_key=api_key,
                    negated_symptoms=negated_symptoms,
                    clarifying_questions=clarifying_questions,
                    clinical_stage=clinical_stage,
                )
            )
            return (result, "cloud_cohere") if result else (None, "cloud_cohere")
        except Exception as e:
            logger.warning(f"Cohere async call failed: {e}")
            return (None, "cloud_cohere")

    async def generate_clinical_advice(
        self,
        patient_message: str,
        predicted_diseases: List[Dict[str, Any]],
        symptoms: List[Dict[str, Any]],
        lab_indicators: Dict[str, Any],
        rag_citations: List[Dict[str, Any]],
        chat_history: Optional[List[Dict[str, str]]] = None,
        is_emergency: bool = False,
        gemini_api_key: Optional[str] = None,
        cohere_api_key: Optional[str] = None,
        negated_symptoms: Optional[List[Dict[str, Any]]] = None,
        clarifying_questions: Optional[List[Dict[str, Any]]] = None,
        clinical_stage: str = "provisional_assumption"
    ) -> Dict[str, Any]:
        """
        Race condition giữa Gemini và Cohere:
        - Gọi song song cả 2 bằng asyncio.gather
        - Provider nào trả về trước → primary response
        - Provider còn lại → alternative_answer
        - Fallback: Local LLM → Deterministic Engine
        """
        used_provider = "rule_based"
        response_text = None
        alternative_text = None
        alternative_provider = None

        # 1. Ưu tiên Local LLM nếu cấu hình hybrid/local
        if self.provider_mode in ["local", "hybrid"]:
            try:
                response_text = await self.local_llm.generate_response(
                    patient_message=patient_message,
                    predicted_diseases=predicted_diseases,
                    symptoms=symptoms,
                    lab_indicators=lab_indicators,
                    rag_citations=rag_citations,
                    chat_history=chat_history,
                    is_emergency=is_emergency,
                    negated_symptoms=negated_symptoms,
                    clarifying_questions=clarifying_questions,
                    clinical_stage=clinical_stage,
                )
                if response_text:
                    used_provider = f"local_llm ({settings.LOCAL_LLM_MODEL})"
            except Exception as e:
                logger.warning(f"Local LLM routing failed: {e}")

        # 2. Race Gemini vs Cohere song song
        if not response_text and self.provider_mode in ["gemini", "hybrid"]:
            has_gemini = bool((gemini_api_key or os.getenv("GEMINI_API_KEY", "")).strip())
            has_cohere = bool((cohere_api_key or os.getenv("COHERE_API_KEY", "")).strip())

            if has_gemini or has_cohere:
                tasks = []

                if has_gemini:
                    tasks.append(self._call_gemini_async(
                        patient_message=patient_message,
                        predicted_diseases=predicted_diseases,
                        symptoms=symptoms,
                        lab_indicators=lab_indicators,
                        rag_citations=rag_citations,
                        chat_history=chat_history,
                        is_emergency=is_emergency,
                        api_key=gemini_api_key,
                        negated_symptoms=negated_symptoms,
                        clarifying_questions=clarifying_questions,
                        clinical_stage=clinical_stage,
                    ))
                if has_cohere:
                    tasks.append(self._call_cohere_async(
                        patient_message=patient_message,
                        predicted_diseases=predicted_diseases,
                        symptoms=symptoms,
                        lab_indicators=lab_indicators,
                        rag_citations=rag_citations,
                        chat_history=chat_history,
                        is_emergency=is_emergency,
                        api_key=cohere_api_key,
                        negated_symptoms=negated_symptoms,
                        clarifying_questions=clarifying_questions,
                        clinical_stage=clinical_stage,
                    ))

                try:
                    results = await asyncio.wait_for(
                        asyncio.gather(*tasks, return_exceptions=True),
                        timeout=4.5
                    )

                    successful = []
                    for res in results:
                        if isinstance(res, Exception):
                            continue
                        text, provider = res
                        if text:
                            successful.append((text, provider))

                    if len(successful) >= 1:
                        response_text, used_provider = successful[0]
                        logger.info(f"Primary provider: {used_provider}")

                    if len(successful) >= 2:
                        alternative_text, alternative_provider = successful[1]
                        logger.info(f"Alternative provider stored: {alternative_provider}")

                except asyncio.TimeoutError:
                    logger.warning("Cloud AI race timed out (>4.5s). Fast-failing to deterministic protocol.")
                except Exception as e:
                    logger.warning(f"Race condition gather failed: {e}")

        # 3. Fallback sang Deterministic nếu cả 2 cloud đều không trả lời
        cloud_errors = []
        gemini_err = getattr(self.gemini_service, "last_error", None)
        if gemini_err:
            cloud_errors.append(gemini_err)
        cohere_err = getattr(self.cohere_service, "last_error", None)
        if cohere_err:
            cloud_errors.append(cohere_err)

        if not response_text:
            response_text = self._build_deterministic_clinical_response(
                patient_message=patient_message,
                predicted_diseases=predicted_diseases,
                symptoms=symptoms,
                lab_indicators=lab_indicators,
                rag_citations=rag_citations,
                is_emergency=is_emergency,
                negated_symptoms=negated_symptoms,
                clarifying_questions=clarifying_questions,
                clinical_stage=clinical_stage
            )
            used_provider = "deterministic_clinical_protocol"

            # Nếu cloud AI gặp lỗi (429, 503, 404...), hiển thị rõ mã lỗi cho người dùng biết
            if cloud_errors:
                err_summary = " | ".join(cloud_errors)
                response_text += f"\n\n> ⚠️ **Mã lỗi dịch vụ Cloud AI:** `[{err_summary}]`  \n> *Hệ thống đã tự động chuyển sang Phác đồ Lâm sàng Chuẩn Bộ Y Tế để phục vụ bạn liên tục mà không bị gián đoạn.*"

        return {
            "text": response_text,
            "provider": used_provider,
            "is_emergency": is_emergency,
            "alternative_text": alternative_text,
            "alternative_provider": alternative_provider,
            "cloud_errors": cloud_errors,
        }

    def _build_deterministic_clinical_response(
        self,
        patient_message: str,
        predicted_diseases: List[Dict[str, Any]],
        symptoms: List[Dict[str, Any]],
        lab_indicators: Dict[str, Any],
        rag_citations: List[Dict[str, Any]],
        is_emergency: bool = False,
        negated_symptoms: Optional[List[Dict[str, Any]]] = None,
        clarifying_questions: Optional[List[Dict[str, Any]]] = None,
        clinical_stage: str = "provisional_assumption"
    ) -> str:
        """Sinh câu trả lời y tế chuẩn xác theo 3 tầng phân định lâm sàng."""
        lines = []
        if is_emergency:
            lines.append("🚨 **CẢNH BÁO Y TẾ KHẨN CẤP (RED FLAG):**")
            lines.append("👉 **HÃY ĐẾN NGAY PHÒNG CẤP CỨU GẦN NHẤT HOẶC GỌI CẤP CỨU 115 NGAY LẬP TỨC!**\n")

        lines.append("Chào bạn, tôi là **Trợ Lý Y Tế AI (MediBot)** tham vấn theo chuẩn Bộ Y Tế Việt Nam.")
        
        sym_names = [s.get("standard_term") for s in symptoms if s.get("standard_term")]
        if sym_names:
            lines.append(f"🔍 **Triệu chứng đã ghi nhận:** {', '.join(sym_names)}.")

        neg_names = [s.get("standard_term") for s in (negated_symptoms or []) if s.get("standard_term")]
        if neg_names:
            neg_display = [f"Không {n.lower()}" if not n.lower().startswith("không") else n for n in neg_names]
            lines.append(f"❌ **Dấu hiệu đã loại trừ:** {', '.join(neg_display)}.")

        if lab_indicators:
            lines.append("\n🧪 **Đánh giá chỉ số xét nghiệm:**")
            for k, v in lab_indicators.items():
                status = "Bất thường" if v.get("status") in ["high", "low"] else "Bình thường"
                lines.append(f"- **{k.upper()}:** {v.get('value')} {v.get('unit')} ({status} - {v.get('message', '')})")

        valid_diseases = [d for d in (predicted_diseases or []) if d.get("probability", 0) >= 0.15]

        # TẦNG 1: Chưa đủ căn cứ lâm sàng
        if clinical_stage == "initial_screening" or not valid_diseases:
            lines.append("\n🩺 **Nhận định lâm sàng:**")
            lines.append("Dựa trên các dấu hiệu bạn vừa chia sẻ, hiện tại chưa đủ căn cứ lâm sàng đặc hiệu để định danh bệnh lý.")
            if clarifying_questions:
                lines.append("\n👉 *Vui lòng trả lời thêm các câu hỏi sau để bác sĩ làm rõ bệnh cảnh:*")
                for q_idx, q in enumerate(clarifying_questions, 1):
                    lines.append(f"**{q_idx}. {q.get('question')}**")
                    if q.get('options'):
                        lines.append(f"   *(Gợi ý: {' / '.join(q.get('options'))})*")
            else:
                lines.append("👉 *Vui lòng mô tả thêm vị trí, mức độ và thời gian bắt đầu triệu chứng.*")
            lines.append("\n⚠️ *Kết quả do AI hỗ trợ sàng lọc ban đầu, không thay thế chẩn đoán của Bác sĩ.*")
            return "\n".join(lines)

        # TẦNG 2: Chẩn đoán Giả định Lâm sàng (Provisional Hypothesis) - BẮT BUỘC HỎI THÊM LÀM RÕ
        if clinical_stage == "provisional_assumption":
            lines.append("\n🩺 **Chẩn đoán Giả định Lâm sàng (Provisional Hypothesis):**")
            lines.append("Dựa trên các dấu hiệu bạn vừa chia sẻ, hệ thống đang **tạm thời giả định nghi ngờ nhiều nhất** về:")
            for idx, d in enumerate(valid_diseases[:2], 1):
                d_name = d.get("disease_name_vi") or "Bệnh lý"
                prob_str = d.get("probability_percentage", f"{int(d.get('probability', 0)*100)}%")
                role_label = "Bệnh nghi ngờ chính (Tạm thời)" if idx == 1 else "Chẩn đoán phân biệt cần loại trừ"
                lines.append(f"{idx}. **{d_name}** (ICD-10: `{d.get('icd_code', 'N/A')}`) — **{role_label}: {prob_str}**")
                if d.get("department"):
                    lines.append(f"   *Chuyên khoa:* {d.get('department')}")

            if clarifying_questions:
                lines.append("\n👉 *Để chuyển từ trường hợp giả định sang kết luận sơ bộ chính xác, xin vui lòng làm rõ thêm:*")
                for q_idx, q in enumerate(clarifying_questions, 1):
                    lines.append(f"**{q_idx}. {q.get('question')}**")
                    if q.get('options'):
                        lines.append(f"   *(Gợi ý: {' / '.join(q.get('options'))})*")

            lines.append("\n📋 **Hướng dẫn xử trí tạm thời an toàn trong thời gian theo dõi:**")
            lines.append("- Nghỉ ngơi điều độ, giữ tâm lý thoải mái và tránh làm việc gắng sức.")
            lines.append("- Uống đủ nước ấm, theo dõi thân nhiệt và diễn biến các cơn đau.")
            lines.append("- Chưa tự ý dùng các loại thuốc điều trị đặc hiệu khi chưa có kết luận dứt điểm.")
            lines.append("\n⚠️ *Lưu ý: Đây là nhận định giả định ban đầu. Hãy trả lời các câu hỏi làm rõ trên để bác sĩ đưa ra kết luận bệnh án chính xác.*")
            return "\n".join(lines)

        # TẦNG 3: Kết luận Sơ bộ Xác định (Definitive Conclusion)
        lines.append("\n🏥 **Kết luận Sơ bộ Sàng lọc (Definitive Screening Diagnosis):**")
        for idx, d in enumerate(valid_diseases[:3], 1):
            d_name = d.get("disease_name_vi") or "Bệnh lý"
            prob_str = d.get("probability_percentage", f"{int(d.get('probability', 0)*100)}%")
            if idx == 1:
                lines.append(f"1. **Bệnh chính nghĩ nhiều nhất:** **{d_name}** (ICD-10: `{d.get('icd_code', 'N/A')}`) — **Độ tin cậy: {prob_str}**")
            else:
                lines.append(f"{idx}. **Chẩn đoán phân biệt đã xem xét:** **{d_name}** (ICD-10: `{d.get('icd_code', 'N/A')}`) — {prob_str}")
            if d.get("department"):
                lines.append(f"   *Chuyên khoa:* {d.get('department')}")

        if rag_citations:
            lines.append("\n📚 **Hướng dẫn phác đồ & Dược lâm sàng (Bộ Y Tế):**")
            for cit in rag_citations[:2]:
                title = cit.get("title", "")
                content = cit.get("content", "")
                if title:
                    lines.append(f"• **{title}:** {content[:250]}...")
        primary_code = (valid_diseases[0].get("icd_code") if valid_diseases else "") or ""
        primary_dept = (valid_diseases[0].get("department") if valid_diseases else "") or ""
        lines.append(f"\n📋 **Hướng dẫn chăm sóc tại nhà:**")
        if any(c in primary_code for c in ["K29","K21","K25","K26","A09","K58"]) or "tiêu hóa" in primary_dept.lower():
            lines.append("- Chia nhỏ 4-5 bữa/ngày, thức ăn mềm. Tránh đồ chua cay, rượu bia.")
            lines.append("- Dấu hiệu cần đi viện ngay: nôn ra máu, đau bụng dữ dội liên tục.")
        elif any(c in primary_code for c in ["J00","J18","J45","J20","J06"]) or "hô hấp" in primary_dept.lower():
            lines.append("- Súc họng nước muối ấm 3-4 lần/ngày. Giữ ấm cổ ngực.")
            lines.append("- Dấu hiệu nguy hiểm: khó thở tăng dần, tím tái môi, sốt cao không hạ.")
        elif any(c in primary_code for c in ["A90","B54","R50","B01"]) or "truyền nhiễm" in primary_dept.lower():
            lines.append("- Uống Paracetamol khi sốt ≥38.5°C. Bù nước Oresol tối thiểu 2.5 lít/ngày.")
            lines.append("- Cảnh báo: chảy máu chân răng, tay chân lạnh ẩm → đến cấp cứu ngay!")
        else:
            lines.append("- Nghỉ ngơi điều độ, ngủ đủ 7-8 tiếng. Uống đủ 2-2.5 lít nước ấm/ngày.")
            lines.append("- Không tự ý mua kháng sinh khi chưa có chẩn đoán từ bác sĩ.")
        lines.append("\n⚠️ *Kết quả do AI hỗ trợ sàng lọc ban đầu, không thay thế chẩn đoán của Bác sĩ chuyên khoa.*")
        return "\n".join(lines)


clinical_reasoning_service = UnifiedClinicalReasoningService()
