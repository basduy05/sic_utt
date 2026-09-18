import re
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class ConversationalEngine:
    """
    Bộ Sinh Phản Hồi Hội Thoại Lâm Sàng Linh Hoạt (Conversational Response Engine).
    Giải quyết triệt để vấn đề 'câu trả lời cứng nhắc và không trả lời được câu hỏi của người dùng':
    - Nhận diện ý định trực tiếp của người bệnh (Intent Classification).
    - Trả lời thẳng thắn, trực diện vào thắc mắc trước, sau đó mới tổng hợp lâm sàng.
    - Duy trì phong cách bác sĩ ân cần, tôn trọng, không lặp lại câu hỏi đã có câu trả lời.
    """

    def classify_intent(self, user_message: str) -> Dict[str, bool]:
        """Nhận diện các ý định hội thoại trong câu nói của bệnh nhân."""
        msg = user_message.lower().strip()
        return {
            "is_asking_emergency": bool(re.search(
                r'(?:cấp cứu|nhập viện|vào viện|khi nào.*(?:viện|cấp cứu)|dấu hiệu nào.*(?:viện|cấp cứu)|bắt buộc phải.*(?:viện|cấp cứu)|nguy hiểm|dấu hiệu nguy hiểm|có cần đi|có phải đi)',
                msg
            )),
            "is_asking_medication": bool(re.search(
                r'(?:uống thuốc gì|dùng thuốc gì|thuốc gì|uống gì.*hạ sốt|hạ sốt.*như thế nào|hạ sốt.*thế nào|cách hạ sốt|uống thuốc)',
                msg
            )),
            "is_asking_nutrition": bool(re.search(
                r'(?:ăn uống thế nào|ăn gì|chế độ ăn|uống nước gì|kiêng ăn gì|bồi bổ thế nào)',
                msg
            )),
            "is_asking_symptom_meaning": bool(re.search(
                r'(?:thế là.*(?:gì|dấu hiệu gì)|dấu hiệu gì|là bị gì|nghĩa là gì|có phải.*(?:cúm|sốt xuất huyết|bị gì))',
                msg
            )),
            "is_answering_clarification": bool(re.search(
                r'(?:tối qua|hôm qua|ngày nay|có ăn|không ăn|uống chút|uống bia|không sốt|chưa uống)',
                msg
            ))
        }

    def generate_response(
        self,
        patient_message: str,
        clinical_state: Any,
        predicted_diseases: List[Dict[str, Any]],
        symptoms: List[Dict[str, Any]],
        negated_symptoms: List[Dict[str, Any]],
        lab_indicators: Dict[str, Any],
        rag_citations: List[Dict[str, Any]],
        clarifying_questions: Optional[List[Dict[str, Any]]] = None,
        clinical_stage: str = "provisional_assumption",
        is_emergency: bool = False,
        cloud_errors: Optional[List[str]] = None
    ) -> str:
        """Sinh câu phản hồi tự nhiên, chuẩn mực y khoa và trúng đích."""
        intents = self.classify_intent(patient_message)
        lines = []

        # 1. BÁO ĐỘNG ĐỎ CẤP CỨU NẾU CÓ RED FLAG
        if is_emergency:
            lines.append("🚨 **CẢNH BÁO Y TẾ KHẨN CẤP (RED FLAG):**")
            lines.append("👉 **HÃY ĐẾN NGAY PHÒNG CẤP CỨU GẦN NHẤT HOẶC GỌI CẤP CỨU 115 NGAY LẬP TỨC!**\n")

        # 2. LỜI MỞ ĐẦU THÂN THIỆN & GHI NHẬN BỐI CẢNH
        lines.append("Chào bạn, tôi là **Trợ Lý Y Tế AI (MediBot)** tham vấn theo chuẩn Bộ Y Tế Việt Nam.")

        # Liệt kê các triệu chứng đã ghi nhận và các yếu tố nguy cơ tích lũy
        sym_names = [s.get("standard_term") for s in symptoms if s.get("standard_term")]
        if sym_names:
            lines.append(f"🔍 **Dấu hiệu đã ghi nhận:** {', '.join(sym_names)}.")

        # Hiển thị các yếu tố nguy cơ từ Slot Filling
        slots = getattr(clinical_state, "clinical_slots", {}) if clinical_state else {}
        triggers = slots.get("triggers", [])
        if triggers:
            lines.append(f"⚠️ **Yếu tố tiếp xúc / khởi phát:** Đã ghi nhận dùng {', '.join(triggers)}.")
        onset = slots.get("onset", "")
        if onset:
            lines.append(f"⏱️ **Thời gian khởi phát:** {onset}.")

        neg_names = [s.get("standard_term") for s in (negated_symptoms or []) if s.get("standard_term")]
        if neg_names:
            neg_display = [f"Không {n.lower()}" if not n.lower().startswith("không") else n for n in neg_names]
            lines.append(f"❌ **Dấu hiệu đã loại trừ:** {', '.join(neg_display)}.")

        # 3. TRẢ LỜI TRỰC DIỆN VÀO CÂU HỎI CỦA BỆNH NHÂN (TRƯỚC TIÊN)
        msg_lower = patient_message.lower()

        # A. Người bệnh hỏi về Cấp cứu / Nhập viện
        if intents["is_asking_emergency"]:
            lines.append("\n👉 **TRẢ LỜI CÂU HỎI CỦA BẠN: CÓ CẦN ĐI CẤP CỨU KHÔNG?**")
            if any(k in msg_lower for k in ["thở rít", "tê phù", "phù môi", "sưng môi", "khó thở", "nghẹn"]) or any("thở rít" in s.get("standard_term", "").lower() or "phù môi" in s.get("standard_term", "").lower() for s in symptoms):
                lines.append("🔴 **CÓ, BẠN BẮT BUỘC PHẢI ĐẾN PHÒNG CẤP CỨU HOẶC GỌI 115 NGAY LẬP TỨC!**")
                lines.append("Hiện tượng **nổi mảng đỏ/mề đay sau khi ăn hải sản** kết hợp với **môi tê phù** và **thở rít** là dấu hiệu điển hình của **HỘI CHỨNG PHẢN VỆ CẤP (ANAPHYLAXIS) CÓ PHÙ NỀ ĐƯỜNG THỞ (PHÙ QUINCKE)**.")
                lines.append("- Đây là tình trạng **nguy hiểm tính mạng** có thể gây bít tắc khí quản dẫn đến ngạt thở trong vài phút.")
                lines.append("- **Xử trí khẩn cấp:**")
                lines.append("  1. Gọi ngay cấp cứu **115** hoặc nhờ người nhà đưa thẳng vào khoa Cấp cứu gần nhất.")
                lines.append("  2. Ngồi thẳng lưng, thả lỏng cổ áo để dễ thở, tuyệt đối không nằm ngửa.")
                lines.append("  3. Không tự ý uống nước hoặc uống thuốc viên nếu đang nuốt vướng hoặc thở rít.")
                lines.append("  4. Báo ngay cho nhân viên y tế: *'Nghi phản vệ sau ăn hải sản đang bị sưng môi và thở rít'*, bác sĩ sẽ tiêm bắp Adrenaline cấp cứu ngay lập tức!")
            else:
                lines.append("🚨 **CÁC DẤU HIỆU CẢNH BÁO NGUY HIỂM BẮT BUỘC PHẢI VÀO VIỆN CẤP CỨU NGAY (BỘ Y TẾ):**")
                lines.append("Nếu bạn hoặc người bệnh xuất hiện **BẤT KỲ MỘT TRONG CÁC DẤU HIỆU** dưới đây, cần đến ngay cơ sở y tế / phòng cấp cứu gần nhất:")
                lines.append("1. **Khó thở, thở rít, thở ngáp cá hoặc môi sưng phù nhanh chóng.**")
                lines.append("2. **Đau bụng nhiều và liên tục**, đặc biệt đau tức dội vùng hạ sườn phải (vùng gan).")
                lines.append("3. **Nôn mửa nhiều**, nôn liên tục (≥ 3 lần trong 1 giờ hoặc ≥ 4 lần trong 6 giờ).")
                lines.append("4. **Xuất huyết niêm mạc:** Chảy máu chân răng tự nhiên, chảy máu mũi (chảy máu cam), nôn ra máu, đi ngoài phân đen như bã cà phê, tiểu ra máu.")
                lines.append("5. **Dấu hiệu tri giác:** Người lừ đừ, mệt lả, bứt rứt, li bì, vật vã hoặc hôn mê.")
                lines.append("6. **Dấu hiệu sốc & trụy mạch:** Chân tay lạnh ẩm, da nổi vân tím, mạch nhanh nhỏ, huyết áp tụt hoặc huyết áp kẹt.")

        # B. Người bệnh hỏi về Bản chất Triệu chứng
        if intents["is_asking_symptom_meaning"]:
            if any(k in msg_lower for k in ["chấm đỏ", "không mất", "chấm li ti", "nốt đỏ"]):
                lines.append("\n👉 **Giải thích dấu hiệu lâm sàng:**")
                lines.append("Các chấm đỏ li ti trên da ấn vào không mất màu chính là **chấm xuất huyết dưới da (Petechiae)**. Khi nhiễm virus (đặc biệt là virus Dengue), thành mao mạch bị tổn thương tăng tính thấm kết hợp số lượng tiểu cầu trong máu suy giảm khiến hồng cầu thoát mạch. Khác với ban dị ứng (ấn vào sẽ mờ hoặc biến mất tạm thời), chấm xuất huyết ấn vào sẽ không đổi màu. Đây là dấu hiệu then chốt cảnh báo bệnh đang ở **giai đoạn nguy hiểm (ngày thứ 3 - 7 của sốt xuất huyết)**.")
            elif any(k in msg_lower for k in ["hốc mắt", "khớp", "cúm", "sốt xuất huyết"]):
                lines.append("\n👉 **Giải thích dấu hiệu lâm sàng:**")
                lines.append("Đau nhức sâu hai hốc mắt kèm đau mỏi khắp các cơ khớp là hai triệu chứng kinh điển giúp phân biệt sốt virus thông thường với **Sốt xuất huyết Dengue** hoặc **Cúm**. Khi cơn sốt cao liên tục không đáp ứng với thuốc hạ sốt thông thường, đây là dấu hiệu định hướng rất mạnh đến Sốt xuất huyết Dengue.")

        # C. Người bệnh hỏi về Thuốc & Hạ sốt
        if intents["is_asking_medication"]:
            lines.append("\n💊 **HƯỚNG DẪN DÙNG THUỐC HẠ SỐT AN TOÀN THEO BỘ Y TẾ:**")
            lines.append("- **Thuốc hạ sốt an toàn:** Chỉ dùng **Paracetamol** đơn chất với liều 10 - 15 mg/kg thể trọng cho một lần uống (người lớn uống viên 500mg, 1-2 viên/lần tuỳ cân nặng), khoảng cách giữa 2 lần uống tối thiểu từ 4 đến 6 giờ nếu sốt ≥ 38.5°C. Tổng liều không vượt quá 3-4g/ngày.")
            lines.append("- 🚨 **CHỐNG CHỈ ĐỊNH TUYỆT ĐỐI:** CẤM tuyệt đối dùng **Aspirin, Ibuprofen, Diclofenac, Naproxen** hoặc các thuốc chống viêm không steroid (NSAID) khác. Khi đang nghi ngờ sốt xuất huyết, các thuốc này sẽ ức chế kết tập tiểu cầu, có thể gây **xuất huyết tiêu hóa ồ ạt, nôn ra máu, xuất huyết nội tạng đe dọa trực tiếp tính mạng**!")

        # D. Người bệnh hỏi về Chế độ Ăn uống & Dinh dưỡng
        if intents["is_asking_nutrition"] or (intents["is_asking_medication"] and any(k in msg_lower for k in ["ăn", "uống"])):
            lines.append("\n🥗 **CHẾ ĐỘ BÙ DỊCH & DINH DƯỠNG:**")
            lines.append("- Bù nước tích cực bằng dung dịch **Oresol** pha chuẩn theo hướng dẫn trên bao bì (uống 2 - 3 lít/ngày), nước dừa tươi, nước cam/chanh bổ sung vitamin C và khoáng chất.")
            lines.append("- Ăn thức ăn lỏng, mềm, nguội, dễ tiêu hóa như cháo thịt nạc, súp gà. Tránh các thực phẩm có màu đỏ, đen, nâu sẫm để không gây nhầm lẫn nếu có xuất huyết tiêu hóa.")

        # 4. TỔNG HỢP NHẬN ĐỊNH LÂM SÀNG THEO GIAI ĐOẠN
        valid_diseases = [d for d in (predicted_diseases or []) if d.get("probability", 0) >= 0.15]

        # Giai đoạn 1: Chưa đủ căn cứ
        if clinical_stage == "initial_screening" or not valid_diseases:
            if not (intents["is_asking_medication"] or intents["is_asking_emergency"] or intents["is_asking_symptom_meaning"]):
                lines.append("\n🩺 **Nhận định lâm sàng:**")
                lines.append("Dựa trên các dấu hiệu bạn vừa chia sẻ, hiện tại cần làm rõ thêm các chi tiết bệnh cảnh để nhận định chính xác.")
                if clarifying_questions:
                    lines.append("\n👉 *Vui lòng trả lời thêm các câu hỏi sau:*")
                    for q_idx, q in enumerate(clarifying_questions, 1):
                        lines.append(f"**{q_idx}. {q.get('question')}**")
                        if q.get('options'):
                            lines.append(f"   *(Gợi ý: {' / '.join(q.get('options'))})*")

        # Giai đoạn 2: Chẩn đoán giả định lâm sàng
        elif clinical_stage == "provisional_assumption":
            lines.append("\n🩺 **Chẩn đoán Giả định Lâm sàng (Provisional Hypothesis):**")
            lines.append("Dựa trên sự kết hợp các dấu hiệu bạn chia sẻ qua các lượt hội thoại, hệ thống đang **giả định nghi ngờ nhiều nhất** về:")
            for idx, d in enumerate(valid_diseases[:2], 1):
                d_name = d.get("disease_name_vi") or "Bệnh lý"
                prob_str = d.get("probability_percentage", f"{int(d.get('probability', 0)*100)}%")
                role_label = "Bệnh nghi ngờ chính (Tạm thời)" if idx == 1 else "Chẩn đoán phân biệt cần theo dõi"
                lines.append(f"{idx}. **{d_name}** (ICD-10: `{d.get('icd_code', 'N/A')}`) — **{role_label}: {prob_str}**")
                if d.get("department"):
                    lines.append(f"   *Chuyên khoa:* {d.get('department')}")

            if clarifying_questions and not is_emergency and not intents["is_asking_emergency"]:
                lines.append("\n👉 *Để chuyển từ trường hợp giả định sang kết luận sơ bộ chính xác, xin vui lòng làm rõ thêm:*")
                for q_idx, q in enumerate(clarifying_questions, 1):
                    lines.append(f"**{q_idx}. {q.get('question')}**")
                    if q.get('options'):
                        lines.append(f"   *(Gợi ý: {' / '.join(q.get('options'))})*")

            if not intents["is_asking_medication"]:
                lines.append("\n📋 **Hướng dẫn xử trí tạm thời an toàn:**")
                lines.append("- Nghỉ ngơi điều độ, tránh làm việc nặng hoặc ra gió/ánh nắng gắt.")
                lines.append("- Uống đủ nước ấm, theo dõi sát diễn biến triệu chứng.")

        # Giai đoạn 3: Kết luận sơ bộ xác định
        else:
            lines.append("\n🏥 **Kết luận Sơ bộ Sàng lọc (Definitive Screening Diagnosis):**")
            for idx, d in enumerate(valid_diseases[:3], 1):
                d_name = d.get("disease_name_vi") or "Bệnh lý"
                prob_str = d.get("probability_percentage", f"{int(d.get('probability', 0)*100)}%")
                if idx == 1:
                    lines.append(f"1. **Bệnh chính nghĩ nhiều nhất:** **{d_name}** (ICD-10: `{d.get('icd_code', 'N/A')}`) — **Độ tin cậy: {prob_str}**")
                else:
                    lines.append(f"{idx}. **Chẩn đoán phân biệt:** **{d_name}** (ICD-10: `{d.get('icd_code', 'N/A')}`) — {prob_str}")
                if d.get("department"):
                    lines.append(f"   *Chuyên khoa:* {d.get('department')}")

            if rag_citations:
                lines.append("\n📚 **Hướng dẫn phác đồ & Dược lâm sàng (Bộ Y Tế):**")
                for cit in rag_citations[:2]:
                    title = cit.get("title", "")
                    content = cit.get("content", "")
                    if title:
                        lines.append(f"• **{title}:** {content[:250]}...")

        # 5. THÔNG BÁO LỖI CLOUD NẾU CÓ
        if cloud_errors:
            err_summary = " | ".join(cloud_errors)
            lines.append(f"\n\n> ⚠️ **Mã lỗi dịch vụ Cloud AI:** `[{err_summary}]`  \n> *Hệ thống đã tự động chuyển sang Phác đồ Lâm sàng Chuẩn Bộ Y Tế để phục vụ bạn liên tục mà không bị gián đoạn.*")

        return "\n".join(lines)

conversational_engine = ConversationalEngine()
