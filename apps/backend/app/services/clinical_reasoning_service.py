import os
import re
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

        is_asking_medication = bool(re.search(r'(?:uống thuốc gì|dùng thuốc gì|thuốc gì|uống gì.*hạ sốt|hạ sốt.*như thế nào|hạ sốt.*thế nào|cách hạ sốt|ăn uống thế nào|ăn gì|chế độ ăn|uống thuốc)', patient_message, re.IGNORECASE))
        is_asking_emergency = bool(re.search(r'(?:cấp cứu|nhập viện|vào viện|khi nào.*(?:viện|cấp cứu)|dấu hiệu nào.*(?:viện|cấp cứu)|bắt buộc phải.*(?:viện|cấp cứu)|nguy hiểm|dấu hiệu nguy hiểm)', patient_message, re.IGNORECASE))
        is_asking_symptom_meaning = bool(re.search(r'(?:thế là.*(?:gì|dấu hiệu gì)|dấu hiệu gì|là bị gì|nghĩa là gì|có phải.*(?:cúm|sốt xuất huyết|bị gì))', patient_message, re.IGNORECASE))

        # 0. Giải đáp trực tiếp các thắc mắc lâm sàng cụ thể của người bệnh
        if is_asking_symptom_meaning:
            msg_lower = patient_message.lower()
            if any(k in msg_lower for k in ["chấm đỏ", "không mất", "chấm li ti", "nốt đỏ"]):
                lines.append("\n👉 **Giải thích dấu hiệu lâm sàng:**")
                lines.append("Các chấm đỏ li ti trên da ấn vào không mất màu chính là **chấm xuất huyết dưới da (Petechiae)**. Khi nhiễm virus (đặc biệt là virus Dengue), thành mao mạch bị tổn thương tăng tính thấm kết hợp số lượng tiểu cầu trong máu suy giảm khiến hồng cầu thoát mạch. Khác với ban dị ứng (ấn vào sẽ mờ hoặc biến mất tạm thời), chấm xuất huyết ấn vào sẽ không đổi màu. Đây là dấu hiệu then chốt cảnh báo bệnh đang ở **giai đoạn nguy hiểm (ngày thứ 3 - 7 của sốt xuất huyết)**.")
            elif any(k in msg_lower for k in ["hốc mắt", "khớp", "cúm", "sốt xuất huyết"]):
                lines.append("\n👉 **Giải thích dấu hiệu lâm sàng:**")
                lines.append("Đau nhức sâu hai hốc mắt kèm đau mỏi khắp các cơ khớp là hai triệu chứng kinh điển giúp phân biệt sốt virus thông thường với **Sốt xuất huyết Dengue** hoặc **Cúm**. Khi cơn sốt cao liên tục không đáp ứng với thuốc hạ sốt thông thường, đây là dấu hiệu định hướng rất mạnh đến Sốt xuất huyết Dengue.")

        if is_asking_medication:
            lines.append("\n💊 **HƯỚNG DẪN DÙNG THUỐC HẠ SỐT & DINH DƯỠNG THEO BỘ Y TẾ:**")
            lines.append("- **Thuốc hạ sốt an toàn:** Chỉ dùng **Paracetamol** đơn chất với liều 10 - 15 mg/kg thể trọng cho một lần uống (người lớn uống viên 500mg, 1-2 viên/lần tuỳ cân nặng), khoảng cách giữa 2 lần uống tối thiểu từ 4 đến 6 giờ nếu sốt ≥ 38.5°C. Tổng liều không vượt quá 3-4g/ngày.")
            lines.append("- 🚨 **CHỐNG CHỈ ĐỊNH TUYỆT ĐỐI:** CẤM tuyệt đối dùng **Aspirin, Ibuprofen, Diclofenac, Naproxen** hoặc các thuốc chống viêm không steroid (NSAID) khác. Khi đang nghi ngờ sốt xuất huyết, các thuốc này sẽ ức chế kết tập tiểu cầu, có thể gây **xuất huyết tiêu hóa ồ ạt, nôn ra máu, xuất huyết nội tạng đe dọa trực tiếp tính mạng**!")
            lines.append("- 🥗 **Chế độ bù dịch & dinh dưỡng:**")
            lines.append("  • Bù nước tích cực bằng dung dịch **Oresol** pha chuẩn theo hướng dẫn trên bao bì (uống 2 - 3 lít/ngày), nước dừa tươi, nước cam/chanh bổ sung vitamin C và khoáng chất.")
            lines.append("  • Ăn thức ăn lỏng, mềm, nguội, dễ tiêu hóa như cháo thịt nạc, súp gà. Tránh các thực phẩm có màu đỏ, đen, nâu sẫm để không gây nhầm lẫn nếu có xuất huyết tiêu hóa.")

        if is_asking_emergency:
            lines.append("\n🚨 **CÁC DẤU HIỆU CẢNH BÁO NGUY HIỂM BẮT BUỘC PHẢI VÀO VIỆN CẤP CỨU NGAY (BỘ Y TẾ):**")
            lines.append("Nếu bạn hoặc người bệnh xuất hiện **BẤT KỲ MỘT TRONG CÁC DẤU HIỆU** dưới đây, cần đến ngay cơ sở y tế / phòng cấp cứu gần nhất:")
            lines.append("1. **Đau bụng nhiều và liên tục**, đặc biệt đau tức dội vùng hạ sườn phải (vùng gan).")
            lines.append("2. **Nôn mửa nhiều**, nôn liên tục (≥ 3 lần trong 1 giờ hoặc ≥ 4 lần trong 6 giờ).")
            lines.append("3. **Xuất huyết niêm mạc:** Chảy máu chân răng tự nhiên, chảy máu mũi (chảy máu cam), nôn ra máu, đi ngoài phân đen như bã cà phê, tiểu ra máu.")
            lines.append("4. **Dấu hiệu tri giác:** Người lừ đừ, mệt lả, bứt rứt, li bì, vật vã hoặc hôn mê.")
            lines.append("5. **Dấu hiệu sốc & trụy mạch:** Chân tay lạnh ẩm, da nổi vân tím, mạch nhanh nhỏ, huyết áp tụt hoặc huyết áp kẹt.")
            lines.append("6. **Tiểu ít:** Không đi tiểu trong suốt 6 giờ liên tục.")
            lines.append("👉 *Tuyệt đối không tự ý truyền dịch tại nhà vì có thể gây phù phổi cấp và quá tải dịch nguy hiểm.*")

        # TẦNG 1: Chưa đủ căn cứ lâm sàng
        if (clinical_stage == "initial_screening" or not valid_diseases) and not (is_asking_medication or is_asking_emergency):
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
