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

    def _build_clinical_thinking(
        self,
        symptoms: List[Dict[str, Any]],
        predicted_diseases: List[Dict[str, Any]],
        negated_symptoms: List[Dict[str, Any]],
        lab_indicators: Dict[str, Any],
        is_emergency: bool,
        clinical_stage: str
    ) -> str:
        top_d = predicted_diseases[0] if predicted_diseases else {}
        top_name = top_d.get("disease_name_vi", "Hội chứng lâm sàng")
        dept = top_d.get("department", "Đa khoa")
        sym_names = [s.get("standard_term") for s in symptoms if s.get("standard_term")]
        neg_names = [s.get("standard_term") for s in negated_symptoms if s.get("standard_term")]
        diff_names = [d.get("disease_name_vi") for d in predicted_diseases[1:3] if d.get("disease_name_vi")]

        if "Mắt" in dept or any("mắt" in s.lower() or "nhìn" in s.lower() for s in sym_names):
            patho = (
                f"Triệu chứng {', '.join(sym_names[:2]) or 'thị giác'} phản ánh tình trạng quá tải điều tiết cơ thể mi "
                "hoặc bất ổn định màng phim nước mắt (Tear Film Break-up). Khi làm việc thị giác cự ly gần kéo dài hoặc "
                "giảm tần số chớp mắt, nhãn cầu bị khô và suy giảm độ sắc nét quang học tạm thời."
            )
            diff_text = f"Ưu tiên nghĩ tới {top_name} (H52.4). Cần phân biệt với Viêm kết giác mạc khô (H57.0) và Tật khúc xạ chưa chỉnh kính (H52.1)."
            red_flag = "Hiện chưa có dấu hiệu đỏ mắt dữ dội, đau nhức sâu kèm buồn nôn (cảnh báo Glaucoma góc đóng cấp) hay mất thị lực đột ngột."
            next_step = "Khai thác thêm thời gian duy trì thị lực gần, tiền sử kính mắt và đáp ứng sau khi nhắm mắt nghỉ ngơi."
        elif "Truyền nhiễm" in dept or any("sốt" in s.lower() or "chấm xuất huyết" in s.lower() for s in sym_names):
            patho = (
                f"Sự phối hợp giữa {', '.join(sym_names[:2]) or 'sốt'} với các biểu hiện toàn thân phản ánh đáp ứng viêm cấp tính do virus. "
                "Cần đặc biệt theo dõi biến động tính thấm thành mao mạch và nguy cơ xuất huyết vi mạch."
            )
            diff_text = f"Hướng chẩn đoán chính: {top_name}. Chẩn đoán phân biệt quan trọng: {', '.join(diff_names) if diff_names else 'Cúm mùa, Sốt phát ban'}."
            red_flag = "Cảnh báo thoát huyết tương, đau bụng vùng gan, nôn ói liên tục hoặc xuất huyết niêm mạc."
            next_step = "Đề nghị kiểm tra tổng phân tích tế bào máu ngoại vi (tiểu cầu, Hct) nếu sốt sang ngày thứ 3."
        elif "Dị ứng" in dept or any("ngứa" in s.lower() or "dị ứng" in s.lower() for s in sym_names):
            patho = (
                f"Biểu hiện {', '.join(sym_names[:2]) or 'mẩn ngứa'} phù hợp với phản ứng phóng thích Histamin từ dưỡng bào "
                "qua trung gian IgE hoặc kích ứng tiếp xúc."
            )
            diff_text = f"Hướng chẩn đoán: {top_name}. Phân biệt với Viêm da cơ địa đợt cấp hoặc dị ứng thuốc."
            red_flag = "Cảnh báo phù mạch Angioedema vùng hầu họng, thở rít hoặc tụt huyết áp (Phản vệ)."
            next_step = "Làm rõ dị nguyên thức ăn, thuốc đã dùng trong 24 giờ qua và tiền sử cơ địa dị ứng."
        elif "Hô hấp" in dept or any("ho" in s.lower() or "khó thở" in s.lower() for s in sym_names):
            patho = (
                f"Các triệu chứng {', '.join(sym_names[:2]) or 'hô hấp'} cho thấy kích ứng niêm mạc đường thở hoặc tăng tính phản ứng phế quản."
            )
            diff_text = f"Hướng chẩn đoán: {top_name}. Phân biệt với {', '.join(diff_names) if diff_names else 'Viêm phế quản cấp, Hen phế quản'}."
            red_flag = "Cảnh báo khó thở khi nằm, thở co kéo cơ hô hấp phụ hoặc SpO2 suy giảm."
            next_step = "Khai thác tính chất đờm, tiếng rít khi thở và thời điểm khởi phát cơn ho."
        elif "Tiêu hóa" in dept or any("bụng" in s.lower() or "nôn" in s.lower() or "tiêu chảy" in s.lower() for s in sym_names):
            patho = (
                f"Biểu hiện {', '.join(sym_names[:2]) or 'tiêu hóa'} phản ánh tình trạng rối loạn nhu động dạ dày - ruột "
                "hoặc kích ứng niêm mạc do acid dịch vị / độc tố thức ăn."
            )
            diff_text = f"Hướng chẩn đoán: {top_name}. Phân biệt với {', '.join(diff_names) if diff_names else 'Viêm dạ dày cấp, Ngộ độc thực phẩm'}."
            red_flag = "Cảnh báo đau bụng quặn dữ dội, nôn ra máu, đi ngoài phân đen hoặc mất nước nặng."
        elif "Cơ Xương Khớp" in dept or any(kw in s.lower() for kw in ["cổ", "vai", "gáy", "khớp", "lưng", "mỏi"] for s in sym_names):
            patho = (
                f"Biểu hiện {', '.join(sym_names[:2]) or 'đau mỏi cơ khớp'} phản ánh tình trạng quá tải cơ học, "
                "co cứng các nhóm cơ cạnh sống (Muscle Spasm) hoặc thoái hóa đốt sống cổ gây kích thích nhánh thần kinh cảm giác. "
                "Tình trạng này rất phổ biến khi ngồi tĩnh tại sai tư thế hoặc làm việc màn hình kéo dài."
            )
            diff_text = f"Hướng chẩn đoán: {top_name}. Phân biệt với Hội chứng đau cơ mạc (Myofascial Pain Syndrome), Thoát vị đĩa đệm cột sống cổ (M50.9) hoặc Căng cơ cổ cấp tính."
            red_flag = "Cảnh báo dấu hiệu tê bì yếu liệt cánh tay, mất khéo léo bàn tay hoặc đau lan dữ dội kèm chóng mặt khi quay cổ."
            next_step = "Khai thác tư thế làm việc, thói quen vận động cổ và mức độ tê bì lan xuống chi trên."
        elif "Thần kinh" in dept or any("đầu" in s.lower() or "chóng mặt" in s.lower() for s in sym_names):
            patho = (
                f"Biểu hiện {', '.join(sym_names[:2]) or 'thần kinh'} phản ánh tình trạng căng thẳng thần kinh vận mạch, "
                "co thắt cơ vùng đầu cổ hoặc rối loạn điều hòa tiền đình ngoại biên."
            )
            diff_text = f"Hướng chẩn đoán: {top_name}. Phân biệt với {', '.join(diff_names) if diff_names else 'Đau đầu căng thẳng, Rối loạn tiền đình'}."
            red_flag = "Cảnh báo đau đầu dữ dội như sét đánh, yếu liệt nửa người hoặc co giật."
            next_step = "Làm rõ tính chất đau nhói hay căng tức, thời gian cơn và yếu tố khởi phát."
        else:
            patho = f"Tập hợp các triệu chứng ({', '.join(sym_names[:3]) or 'ghi nhận'}) phản ánh phản ứng mệt mỏi thể chất hoặc rối loạn cơ năng ban đầu."
            diff_text = f"Giả định lâm sàng: {top_name}. Cần phân biệt với: {', '.join(diff_names) if diff_names else 'các hội chứng tương đương'}."
            red_flag = "Chưa ghi nhận dấu hiệu đe dọa sinh tồn tức thì."
            next_step = "Theo dõi sát đáp ứng ban đầu và thăm khám chuyên khoa khi triệu chứng kéo dài."

        return (
            "<clinical_thinking>\n"
            f"- Cơ chế bệnh sinh & Liên kết triệu chứng: {patho}\n"
            f"- Chẩn đoán phân biệt & Loại trừ: {diff_text}"
            + (f" Dấu hiệu loại trừ đã ghi nhận: {', '.join(neg_names)}." if neg_names else "") + "\n"
            f"- Đánh giá cờ đỏ (Red Flags): {red_flag}\n"
            f"- Định hướng tiếp theo: {next_step}\n"
            "</clinical_thinking>"
        )

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

        # 0. KHỐI SUY LUẬN LÂM SÀNG CHUỖI TƯ DUY (CLINICAL CHAIN-OF-THOUGHT)
        thinking_block = self._build_clinical_thinking(
            symptoms=symptoms,
            predicted_diseases=predicted_diseases,
            negated_symptoms=negated_symptoms,
            lab_indicators=lab_indicators,
            is_emergency=is_emergency,
            clinical_stage=clinical_stage
        )
        lines.append(thinking_block)
        lines.append("")

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
                top_dept = valid_diseases[0].get("department", "") if valid_diseases else ""
                lines.append("\n📋 **Hướng dẫn xử trí tạm thời an toàn:**")
                if "Mắt" in top_dept or any("mắt" in s.get("standard_term", "").lower() for s in symptoms):
                    lines.append("- **Quy tắc 20-20-20:** Cứ sau mỗi 20 phút nhìn sách hoặc màn hình, hãy nhìn xa cự ly 6 mét trong 20 giây để giãn cơ thể mi.")
                    lines.append("- **Làm dịu mắt:** Sử dụng dung dịch nhỏ mắt Natri Hyaluronate hoặc nước muối sinh lý 0.9% để làm ẩm bề mặt nhãn cầu, chườm ấm mắt nhẹ nhàng 5-10 phút.")
                    lines.append("- **Khoảng cách thị giác:** Đảm bảo đủ ánh sáng, cự ly đọc tối thiểu 50-60cm, hạn chế tiếp xúc màn hình trước khi ngủ.")
                elif "Truyền nhiễm" in top_dept or any("sốt" in s.get("standard_term", "").lower() for s in symptoms):
                    lines.append("- Bù đủ nước và điện giải (Oresol pha đúng liều lượng, nước trái cây giàu vitamin C).")
                    lines.append("- Hạ sốt an toàn bằng Paracetamol nếu sốt ≥ 38.5°C; tuyệt đối không dùng Ibuprofen / Aspirin khi chưa loại trừ sốt xuất huyết.")
                    lines.append("- Nghỉ ngơi nơi thoáng khí, theo dõi sát thân nhiệt và các vết xuất huyết dưới da.")
                elif "Tiêu hóa" in top_dept:
                    lines.append("- Chia nhỏ bữa ăn (4-5 bữa/ngày), chọn thức ăn mềm, lỏng, dễ tiêu (cháo, súp).")
                    lines.append("- Không nằm ngay sau ăn, kiêng đồ chua cay, nhiều dầu mỡ, chất kích thích (cà phê, rượu bia).")
                elif "Da liễu" in top_dept:
                    lines.append("- Tạm ngưng các loại mỹ phẩm, kem bôi lạ; rửa nhẹ vùng da bằng nước mát sạch hoặc nước muối sinh lý.")
                    lines.append("- Tránh cào gãi làm xước da, có thể chườm mát nhẹ để giảm cảm giác nóng rát, ngứa ngáy.")
                else:
                    lines.append("- Nghỉ ngơi điều độ, hạn chế làm việc quá sức và tránh căng thẳng thần kinh.")
                    lines.append("- Uống đủ nước ấm (1.5 - 2 lít/ngày), theo dõi sát diễn biến triệu chứng.")

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
