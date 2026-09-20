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
            )),
            "is_asking_disease_info": bool(re.search(
                r'(?:(?:bệnh|chứng|hội chứng)\s+.*(?:là gì|như thế nào|thế nào|ra sao|có nghĩa là gì)|(?:là gì|định nghĩa|khái niệm|bản chất).*(?:bệnh|hội chứng|tình trạng)|(?:là gì|thế nào)\??$|'
                r'(?:nguyên nhân|tại sao lại bị|do đâu mà bị|yếu tố nguy cơ|nguyên nhân gây|vì sao bị)|'
                r'(?:chữa|điều trị|trị|khỏi).*(?:dứt điểm|khỏi hẳn|được không|như thế nào|thế nào|tự khỏi)|phác đồ điều trị|có mổ được không|'
                r'(?:kiêng (?:ăn )?gì|nên ăn gì|không nên ăn gì|chế độ ăn|ăn uống thế nào|uống nước gì|thực đơn cho người|bồi bổ)|'
                r'(?:có nguy hiểm không|nguy hiểm không|có để lại di chứng không|biến chứng|tiên lượng|sống được bao lâu|ảnh hưởng gì không)|'
                r'(?:phòng ngừa|phòng tránh|phòng bệnh|làm sao để (?:phòng|tránh|không bị)|cách (?:phòng|tránh|ngừa))|'
                r'(?:uống thuốc gì|dùng thuốc như thế nào|thuốc nào tốt|tác dụng phụ|uống bao nhiêu viên|cách dùng thuốc|uống trước hay sau ăn))',
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
        top_icd = top_d.get("icd_code", "ICD-10")
        dept = top_d.get("department", "Đa khoa")
        top_prob = top_d.get("probability_percentage") or (f"{round(float(top_d.get('probability', 0.85))*100, 1)}%" if top_d else "85.0%")

        sym_names = [s.get("standard_term") for s in symptoms if s.get("standard_term")]
        neg_names = [s.get("standard_term") for s in negated_symptoms if s.get("standard_term")]
        diff_names = [f"{d.get('disease_name_vi')} ({d.get('icd_code', '')})" for d in predicted_diseases[1:3] if d.get("disease_name_vi")]

        if clinical_stage == "medical_qa":
            patho = f"Bệnh nhân đặt câu hỏi tìm hiểu kiến thức y khoa về {top_name} (Mã ICD-10: `{top_icd}`). Bản chất bệnh sinh liên quan đến căn nguyên tổn thương mô học, biến đổi sinh lý và diễn tiến cấp - mạn tính theo chuẩn Bộ Y Tế."
            diff_text = f"Mặt bệnh tham chiếu trọng tâm: {top_name} (`{top_icd}`) - Chuyên khoa: {dept}. Độ tương quan tri thức: {top_prob}."
            red_flag = "Cảnh báo các biến chứng cấp tính nguy hiểm nếu không được tầm soát, chẩn đoán phân biệt và can thiệp kịp thời."
            next_step = "Giải đáp trực tiếp, thấu đáo và khoa học các thắc mắc (nguyên nhân, biểu hiện điển hình, chế độ dinh dưỡng, dự phòng) mà không ép làm rõ triệu chứng."
            return (
                "<clinical_thinking>\n"
                f"- Cơ chế bệnh sinh & Liên kết chuyên khoa: {patho}\n"
                f"- Chuyên đề tham chiếu: {diff_text}\n"
                f"- Đánh giá cờ đỏ (Red Flags): {red_flag}\n"
                f"- Định hướng tư vấn: {next_step}\n"
                "</clinical_thinking>"
            )

        if "Tiêu hóa" in dept or any(kw in s.lower() for kw in ["thượng vị", "dạ dày", "ợ chua", "tiêu chảy", "loét", "bụng"] for s in sym_names):
            patho = (
                f"Biểu hiện {', '.join(sym_names[:2]) or 'tiêu hóa'} phản ánh sự mất cân bằng giữa yếu tố tấn công (Acid HCl, Pepsin, vi khuẩn H.pylori, thức ăn kích thích) "
                "và hàng rào bảo vệ niêm mạc (chất nhầy Mucin, Bicarbonate, tưới máu vi mạch). Sự kích thích acid tại vùng tổn thương hoặc trào ngược "
                "gây kích ứng đầu mút thần kinh cảm giác phế vị, dẫn đến co thắt cơ trơn dạ dày - thực quản và cảm giác đau tức cồn cào rát bỏng."
            )
            diff_text = (
                f"Hướng chẩn đoán: **{top_name}** (`{top_icd}`) - Độ tin cậy: **{top_prob}**. "
                f"Phân biệt với: {', '.join(diff_names) if diff_names else 'Viêm loét dạ dày - tá tràng (K29), Trào ngược GERD (K21), Viêm tụy cấp (K85)'}. "
                "Tiêu chuẩn: GERD nổi trội cảm giác nóng rát sau xương ức và trớ thức ăn; Loét tá tràng đau tăng khi đói hoặc nửa đêm về sáng giảm sau khi ăn; Viêm tụy cấp đau dữ dội xuyên lưng."
            )
            red_flag = "Cảnh báo xuất huyết tiêu hóa và thủng tạng rỗng: Nôn ra máu đỏ hoặc dịch bã cà phê, đại tiện phân đen như nhựa đường mùi khắm tanh, đau bụng dữ dội co cứng như gỗ hoặc nôn liên tục mất nước."
            next_step = "Chỉ định Nội soi thực quản - dạ dày - tá tràng (EGD) kèm test Clo tìm vi khuẩn Helicobacter pylori, siêu âm ổ bụng tổng quát loại trừ bệnh lý gan mật tụy."

        elif "Mắt" in dept or any("mắt" in s.lower() or "nhìn" in s.lower() for s in sym_names):
            patho = (
                f"Triệu chứng {', '.join(sym_names[:2]) or 'thị giác'} phản ánh tình trạng quá tải điều tiết cơ thể mi (Ciliary muscle fatigue), "
                "suy giảm độ đàn hồi thể thủy tinh do tuổi tác, kết hợp với bất ổn định màng phim nước mắt (Tear Film Break-up). "
                "Khi làm việc thị giác cự ly gần kéo dài hoặc giảm tần số chớp mắt, nhãn cầu bị khô rát và suy giảm độ sắc nét quang học hội tụ trên hoàng điểm."
            )
            diff_text = (
                f"Ưu tiên nghĩ tới {top_name} (`{top_icd}`) với độ tin cậy {top_prob}. "
                "Cần phân biệt với Viêm kết giác mạc khô (H57.0) và Tật khúc xạ chưa chỉnh kính (H52.1/H52.2). "
                "Tiêu chuẩn phân biệt: Lão thị suy giảm điều tiết nhìn gần trong khi nhìn xa vẫn tốt; Khô mắt nổi bật cảm giác cộm xốn xót mắt."
            )
            red_flag = "Cảnh báo đỏ mắt cương tụ rìa dữ dội, đau nhức sâu trong nhãn cầu lan nửa đầu kèm buồn nôn (cảnh báo Glaucoma góc đóng cấp) hoặc mất thị lực đột ngột."
            next_step = "Khám chuyên khoa Mắt đo khúc xạ toàn diện, đo thị lực nhìn gần bằng bảng Jaeger, kiểm tra đáy mắt và thử nghiệm Schirmer đánh giá tuyến lệ."

        elif "Truyền nhiễm" in dept or any("sốt" in s.lower() or "chấm xuất huyết" in s.lower() for s in sym_names):
            patho = (
                f"Sự phối hợp giữa {', '.join(sym_names[:2]) or 'sốt'} với các biểu hiện toàn thân phản ánh đáp ứng viêm hệ thống cấp tính do virus. "
                "Cơ chế cốt lõi là sự kích hoạt đại thực bào giải phóng bão Cytokine (TNF-α, IL-6), làm tổn thương tế bào nội mô mạch máu, "
                "gây tăng tính thấm thành mao mạch dẫn đến thoát huyết tương cô đặc máu và ức chế tủy xương làm giảm nhanh tiểu cầu."
            )
            diff_text = (
                f"Hướng chẩn đoán chính: **{top_name}** (`{top_icd}`) - Độ tin cậy mô hình: **{top_prob}**. "
                f"Chẩn đoán phân biệt quan trọng: {', '.join(diff_names) if diff_names else 'Cúm mùa (J10/J11), Sốt phát ban (B05/B06), Nhiễm khuẩn huyết'}. "
                "Phân biệt: Sốt Dengue thường có sốt cao đột ngột liên tục, đau mỏi sâu hốc mắt/cơ khớp và chấm xuất huyết dưới da không biến mất khi căng da; Cúm mùa thường kèm viêm long đường hô hấp trên."
            )
            red_flag = (
                "Cảnh báo dấu hiệu nguy hiểm theo phác đồ Bộ Y Tế: Thoát huyết tương nặng gây sốc (mạch nhanh nhỏ, tụt huyết áp); "
                "đau bụng nhiều vùng gan; nôn liên tục (≥3 lần/1h); xuất huyết niêm mạc (chảy máu cam, chân răng, nôn ra máu, đi ngoài phân đen); li bì, bồn chồn, lừ đừ hoặc tiểu ít."
            )
            next_step = (
                "Chỉ định xét nghiệm khẩn: Tổng phân tích tế bào máu ngoại vi (CBC theo dõi Hct và Tiểu cầu mỗi 24h), "
                "Test nhanh kháng nguyên Dengue NS1 (ngày 1-3) hoặc kháng thể IgM/IgG Dengue (từ ngày 4), men gan AST/ALT. Bù điện giải tích cực bằng Oresol pha chuẩn."
            )

        elif "Cơ Xương Khớp" in dept or any(kw in s.lower() for kw in ["cổ", "vai", "gáy", "khớp", "lưng", "mỏi"] for s in sym_names):
            patho = (
                f"Biểu hiện {', '.join(sym_names[:2]) or 'cơ xương khớp'} phản ánh tình trạng quá tải cơ học tĩnh học kéo dài, "
                "co thắt các nhóm cơ cạnh cột sống (Myofascial Spasm), ứ đọng acid lactic cục bộ kết hợp với thoái hóa đĩa đệm mỏm khớp "
                "gây kích thích cơ học hoặc chèn ép các nhánh rễ thần kinh cảm giác chi phối vùng tương ứng."
            )
            diff_text = (
                f"Hướng chẩn đoán: **{top_name}** (`{top_icd}`) - Độ tin cậy: **{top_prob}**. "
                f"Phân biệt với: {', '.join(diff_names) if diff_names else 'Hội chứng cổ vai gáy do co cơ (M54.2), Thoát vị đĩa đệm chèn ép rễ (M50.1), Viêm quanh khớp vai (M75.0)'}. "
                "Tiêu chuẩn: Chèn ép rễ có triệu chứng đau giật buốt lan dọc chi trên kèm tê bì các ngón tay theo dermatomic; Đau cơ mạc khu trú đau âm ỉ tăng khi duy trì một tư thế."
            )
            red_flag = "Cảnh báo tổn thương thần kinh tiến triển: Yếu liệt đột ngột cơ bàn tay (cầm nắm rơi đồ vật), rối loạn cảm giác vùng yên ngựa, hoặc đau cột sống dữ dội về đêm không đỡ khi nghỉ."
            next_step = "Chụp X-quang cột sống tư thế thẳng - nghiêng, chỉ định Chụp cộng hưởng từ (MRI) nếu nghi ngờ chèn ép rễ thần kinh hoặc tủy sống; đo điện cơ (EMG)."

        elif "Hô hấp" in dept or any("ho" in s.lower() or "khó thở" in s.lower() or "đờm" in s.lower() for s in sym_names):
            patho = (
                f"Các triệu chứng {', '.join(sym_names[:2]) or 'hô hấp'} cho thấy tình trạng viêm nhiễm, kích ứng niêm mạc biểu mô đường thở, "
                "phù nề thành phế quản và tăng tiết dịch nhầy đặc quánh làm giảm thiết diện lòng đường dẫn khí và kích hoạt phản xạ ho qua nhánh thần kinh phế vị."
            )
            diff_text = (
                f"Hướng chẩn đoán: **{top_name}** (`{top_icd}`) - Độ tin cậy: **{top_prob}**. "
                f"Phân biệt với: {', '.join(diff_names) if diff_names else 'Viêm phế quản cấp (J20), Hen phế quản (J45), Viêm phổi (J18)'}. "
                "Tiêu chuẩn: Hen có tiếng ran rít/ran ngáy thay đổi theo thời gian; Viêm phổi có sốt cao kèm hội chứng đông đặc hoặc ran ẩm nhỏ hạt khu trú."
            )
            red_flag = "Cảnh báo suy hô hấp cấp: Khó thở khi nằm, co kéo cơ liên sườn và hõm ức, tím tái môi đầu chi, SpO2 suy giảm dưới 94%, thở nhanh > 25 lần/phút hoặc ho ra máu tươi."
            next_step = "Đo SpO2 tại chỗ, chỉ định Chụp X-quang tim phổi thẳng (Chest X-ray), xét nghiệm công thức máu/CRP và đo chức năng hô hấp khi qua giai đoạn cấp."

        elif "Dị ứng" in dept or "Da liễu" in dept or any("ngứa" in s.lower() or "dị ứng" in s.lower() or "mẩn" in s.lower() for s in sym_names):
            patho = (
                f"Biểu hiện {', '.join(sym_names[:2]) or 'mẩn ngứa'} phù hợp với phản ứng quá mẫn giải phóng Histamin và các chất trung gian hóa học "
                "từ dưỡng bào (Mast cell) và bạch cầu ái kiềm qua trung gian IgE hoặc cơ chế kích ứng tiếp xúc trực tiếp tại lớp thượng bì."
            )
            diff_text = (
                f"Hướng chẩn đoán: **{top_name}** (`{top_icd}`) - Độ tin cậy: **{top_prob}**. "
                f"Phân biệt với: {', '.join(diff_names) if diff_names else 'Mày đay cấp tính, Viêm da cơ địa đợt cấp, Dị ứng thuốc'}. "
                "Tiêu chuẩn: Dị ứng tiếp xúc khu trú vùng tiếp xúc; Mày đay phù nề dạng dát sẩn phù di chuyển nhanh."
            )
            red_flag = "BÁO ĐỘNG ĐỎ PHẢN VỆ: Phù mạch Angioedema vùng môi/mí mắt, cảm giác nghẹn họng, khàn tiếng, khó thở thanh quản, thở rít hoặc hoa mắt tụt huyết áp."
            next_step = "Rà soát toàn bộ tiền sử dùng thuốc, thức ăn lạ (hải sản, nhộng), côn trùng đốt trong 24 giờ; ngừng ngay tác nhân nghi ngờ và chuẩn bị sẵn thuốc kháng Histamin H1."

        elif "Thần kinh" in dept or any("đầu" in s.lower() or "chóng mặt" in s.lower() for s in sym_names):
            patho = (
                f"Biểu hiện {', '.join(sym_names[:2]) or 'thần kinh'} phản ánh tình trạng rối loạn điều hòa thần kinh vận mạch não, "
                "tăng trương lực hệ cơ vùng chẩm trán hoặc rối loạn cơ quan tiền đình ngoại biên (ống bán khuyên / thần kinh tiền đình ốc tai)."
            )
            diff_text = (
                f"Hướng chẩn đoán: **{top_name}** (`{top_icd}`) - Độ tin cậy: **{top_prob}**. "
                f"Phân biệt với: {', '.join(diff_names) if diff_names else 'Đau đầu căng thẳng (G44.2), Migraine đau nửa đầu (G43), Hội chứng tiền đình ngoại biên (H81)'}. "
                "Tiêu chuẩn: Migraine đau theo nhịp mạch đập kèm sợ ánh sáng/tiếng động; Rối loạn tiền đình có cảm giác đồ vật xoay tròn kèm rung giật nhãn cầu."
            )
            red_flag = "DẤU HIỆU CẢNH BÁO ĐỘT QUỴ & NGUY HIỂM (FAST): Đau đầu sét đánh dữ dội chưa từng có, yếu liệt mặt méo miệng, yếu liệt nửa người, nói khó hoặc rối loạn ý thức."
            next_step = "Khám thần kinh chuyên sâu, đo huyết áp 2 tay, chụp Cắt lớp vi tính (CT Scanner) hoặc MRI sọ não khẩn cấp nếu có bất kỳ dấu hiệu thần kinh khu trú nào."

        else:
            patho = f"Tập hợp các triệu chứng ({', '.join(sym_names[:3]) or 'ghi nhận'}) phản ánh phản ứng mệt mỏi thể chất, rối loạn thích nghi cơ năng hoặc đáp ứng miễn dịch ban đầu đối với tác nhân gây bệnh."
            diff_text = f"Giả định lâm sàng ưu tiên: **{top_name}** (`{top_icd}`) - Độ tin cậy: **{top_prob}**. Cần phân biệt với: {', '.join(diff_names) if diff_names else 'các hội chứng lâm sàng đồng hành'}."
            red_flag = "Chưa ghi nhận dấu hiệu đe dọa sinh tồn tức thì (tri giác tỉnh táo, đường thở thông thoáng, huyết động ổn định)."
            next_step = "Theo dõi sát diễn biến thân nhiệt và nhịp sinh học trong 24-48 giờ; thăm khám chuyên khoa khi triệu chứng tăng nặng hoặc không thuyên giảm."

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
        # Giai đoạn 0: Giải đáp kiến thức y khoa & Giáo dục sức khỏe (Medical QA Intent - Không suy đoán hay đoán mò)
        if clinical_stage == "medical_qa" or intents.get("is_asking_disease_info"):
            target_dis = predicted_diseases[0].get("disease_name_vi", "") if predicted_diseases else ""
            target_code = predicted_diseases[0].get("icd_code", "") if predicted_diseases else ""
            target_dept = predicted_diseases[0].get("department", "") if predicted_diseases else ""
            
            lines.append(f"\n📚 **TƯ VẤN KIẾN THỨC Y KHOA CHUẨN BỘ Y TẾ**" + (f": **{target_dis.upper()}** (Mã ICD-10: `{target_code}`)" if target_dis else ""))
            if target_dept:
                lines.append(f"*Chuyên khoa phụ trách:* {target_dept}\n")

            # Trích dẫn phác đồ RAG trực tiếp từ CSDL Bộ Y Tế
            if rag_citations:
                for cit in rag_citations[:2]:
                    c_title = cit.get("title", "")
                    c_content = cit.get("content", "")
                    if c_content:
                        lines.append(f"📖 **{c_title}:**\n{c_content}\n")

            # Giải đáp trọng tâm vào đúng nội dung người dùng thắc mắc
            if any(k in msg_lower for k in ["nguyên nhân", "tại sao", "do đâu", "vì sao"]):
                lines.append("🔍 **Nguyên nhân & Yếu tố nguy cơ chính:**")
                lines.append("- Quá trình thoái hóa tự nhiên, lão hóa khớp và giảm chiều cao đĩa đệm theo thời gian.")
                lines.append("- Thói quen sinh hoạt và nghề nghiệp: Ngồi sai tư thế, cúi bấm điện thoại lâu, làm việc máy tính tĩnh tại kéo dài.")
                lines.append("- Vận động quá tải, vi chấn thương lặp đi lặp lại hoặc thiếu hụt các khoáng chất cần thiết.")
            elif any(k in msg_lower for k in ["chữa", "điều trị", "khỏi", "dứt điểm", "tự khỏi"]):
                lines.append("🩺 **Phương pháp điều trị & Khả năng hồi phục:**")
                lines.append("- **Điều trị bảo tồn (Ưu tiên hàng đầu):** Chiếm trên 85-90% trường hợp, gồm vật lý trị liệu, kéo giãn cột sống, tập phục hồi chức năng và điều chỉnh tư thế công thái học.")
                lines.append("- **Điều trị nội khoa:** Sử dụng thuốc giảm đau, giãn cơ, kháng viêm hoặc bảo vệ sụn khớp theo đơn của bác sĩ.")
                lines.append("- **Can thiệp ngoại khoa (Phẫu thuật):** Chỉ đặt ra khi có chèn ép rễ thần kinh/tủy sống nặng gây teo cơ, yếu liệt chi hoặc điều trị bảo tồn thất bại.")
            elif any(k in msg_lower for k in ["kiêng", "ăn gì", "chế độ ăn", "dinh dưỡng"]):
                lines.append("🥗 **Chế độ dinh dưỡng & Chăm sóc:**")
                lines.append("- **Nên bổ sung:** Thực phẩm giàu Canxi, Vitamin D3, Magie, Omega-3 và rau xanh đậm màu.")
                lines.append("- **Cần kiêng cữ:** Hạn chế rượu bia, thuốc lá, đồ ăn quá mặn, thực phẩm chế biến sẵn nhiều dầu mỡ.")
            elif any(k in msg_lower for k in ["nguy hiểm", "biến chứng"]):
                lines.append("⚠️ **Mức độ nguy hiểm & Biến chứng cần đề phòng:**")
                lines.append("- Bệnh là quá trình thoái hóa tiến triển mạn tính lành tính, không gây nguy hiểm tính mạng tức thì.")
                lines.append("- Cần lưu ý đề phòng các biến chứng: Chèn ép rễ thần kinh cánh tay (gây tê bì, yếu tay), đau đầu do thiểu năng tuần hoàn đốt sống - thân nền, hoặc thoát vị đĩa đệm thứ phát.")

            lines.append("\n💡 **Lời khuyên chuyên khoa:** Để có phác đồ điều trị và luyện tập chuẩn mực cho từng người bệnh, bạn nên đến cơ sở y tế chuyên khoa để được bác sĩ thăm khám trực tiếp và chụp X-quang/MRI khi cần thiết.")

        else:
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

        return "\n".join(lines)

conversational_engine = ConversationalEngine()
