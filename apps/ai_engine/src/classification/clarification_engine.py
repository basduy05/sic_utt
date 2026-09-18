import numpy as np
import logging
import re
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class ClarificationEngine:
    """
    Thuật toán phân tích Entropy, Cây quyết định lâm sàng và Ngữ cảnh động (Context-Aware Clarification).
    Đảm bảo câu hỏi làm rõ bám sát triệu chứng và nội dung câu hỏi thực tế của người bệnh.
    """

    # Ngân hàng câu hỏi phân biệt theo mã ICD-10 chuyên khoa
    DISCRIMINATING_QUESTIONS = {
        "A90": [
            {"id": "q_fever_temp", "question": "Thân nhiệt và tính chất cơn sốt của bạn như thế nào?", "options": ["Sốt cao liên tục trên 38.5°C", "Sốt theo cơn có rét run", "Sốt nhẹ âm ỉ", "Không sốt"]},
            {"id": "q_bleeding", "question": "Bạn có xuất hiện dấu hiệu xuất huyết hoặc đau nhức nào đi kèm không?", "options": ["Đau nhức hốc mắt & đau mỏi cơ", "Có chấm đỏ xuất huyết dưới da", "Chảy máu chân răng / chảy máu cam", "Không có dấu hiệu xuất huyết"]}
        ],
        "L20.9": [
            {"id": "q_skin_trigger", "question": "Tình trạng kích ứng hoặc rát đỏ da xuất hiện sau yếu tố nào?", "options": ["Đi ngoài trời nắng gắt", "Dùng mỹ phẩm / sữa rửa mặt mới", "Ăn hải sản / thức ăn lạ", "Tự nhiên bùng phát"]},
            {"id": "q_skin_itch", "question": "Cảm giác tại vùng da bị tổn thương diễn ra như thế nào?", "options": ["Ngứa râm ran, châm chích khó chịu", "Căng rát đỏ ửng bề mặt da", "Có nổi mẩn đỏ hoặc mụn nước li ti", "Da khô ráp, bong tróc vảy"]}
        ],
        "I21.9": [
            {"id": "q_chest_spread", "question": "Cơn đau ngực có đặc điểm và hướng lan như thế nào?", "options": ["Đau thắt bóp nghẹt sau xương ức", "Đau lan lên cổ, hàm hoặc xuống tay trái", "Đau nhói thoáng qua khi ấn vào sườn", "Cảm giác tim đập nhanh, hồi hộp"]},
            {"id": "q_sweat_cold", "question": "Bạn có kèm theo các dấu hiệu tuần hoàn cấp tính nào không?", "options": ["Vã mồ hôi lạnh toàn thân", "Khó thở, thở dốc ngột ngạt", "Chóng mặt, cảm giác muốn ngất xỉu", "Không vã mồ hôi"]}
        ],
        "J18.9": [
            {"id": "q_cough_sputum", "question": "Cơn ho của bạn có tính chất và đờm dịch như thế nào?", "options": ["Ho khạc đờm đặc màu vàng / xanh", "Ho khạc đờm rỉ sét / có vệt máu", "Ho đờm trắng trong loãng", "Ho khan từng cơn không đờm"]},
            {"id": "q_chest_pain_breathe", "question": "Khi hít thở sâu hoặc ho, ngực của bạn có biểu hiện gì?", "options": ["Đau nhói ngực tăng lên rõ rệt", "Cảm giác hụt hơi, thở rít khò khè", "Tức nặng vùng giữa ngực", "Không đau tức khi hít thở"]}
        ],
        "K29.7": [
            {"id": "q_stomach_timing", "question": "Cơn đau bụng của bạn khu trú ở đâu và xuất hiện vào lúc nào?", "options": ["Đau quặn / cồn cào vùng thượng vị (trên rốn)", "Đau nhiều lúc đói hoặc ban đêm", "Đau tức cồn cào ngay sau khi ăn no", "Đau âm ỉ bất kỳ thời điểm nào"]},
            {"id": "q_heartburn", "question": "Bạn có gặp các triệu chứng trào ngược tiêu hóa đi kèm không?", "options": ["Ợ chua, ợ hơi nóng rát lên cổ", "Buồn nôn hoặc nôn mửa thức ăn", "Chướng bụng, đầy hơi khó tiêu", "Cảm giác đắng miệng, chua miệng"]}
        ],
        "K21.9": [
            {"id": "q_gerd_throat", "question": "Cảm giác nóng rát trào ngược và cổ họng của bạn như thế nào?", "options": ["Nóng rát sau xương ức lan lên họng", "Ợ chua, đắng miệng vào buổi sáng", "Ho khan kéo dài nhiều về đêm", "Vướng nghẹn ở cổ họng khi nuốt"]}
        ],
        "J00": [
            {"id": "q_runny_nose", "question": "Đường hô hấp trên của bạn có biểu hiện nào dưới đây?", "options": ["Ngạt mũi, chảy dịch mũi trong", "Chảy nước mũi vàng đục", "Hắt xì hơi liên tục", "Mũi khô rát khó thở"]},
            {"id": "q_throat_pain", "question": "Cảm giác tại vùng họng của bạn diễn biến ra sao?", "options": ["Đau rát họng tăng khi nuốt", "Khô ngứa họng gây ho từng cơn", "Khàn tiếng, mất giọng", "Họng bình thường"]}
        ],
        "J45.9": [
            {"id": "q_asthma_night", "question": "Cơn khó thở và tiếng rít của bạn thường xuất hiện khi nào?", "options": ["Khó thở khò khè nhiều về đêm / gần sáng", "Khó thở khi tiếp xúc khói bụi / phấn hoa / trời lạnh", "Khó thở tăng khi gắng sức", "Không rõ thời điểm"]}
        ],
        "K35.8": [
            {"id": "q_appendicitis_pos", "question": "Vị trí và tính chất cơn đau bụng chuyển biến như thế nào?", "options": ["Đau nhói khu trú vùng bụng dưới bên phải (hố chậu phải)", "Ban đầu đau quanh rốn rồi lan dần xuống bụng dưới phải", "Đau tăng khi ho hoặc cử động mạnh", "Kèm sốt nhẹ và buồn nôn"]}
        ],
        "N20.0": [
            {"id": "q_kidney_urinate", "question": "Tình trạng đi tiểu và màu sắc nước tiểu của bạn thế nào?", "options": ["Cảm giác tiểu buốt, tiểu rắt buốt dọc niệu đạo", "Nước tiểu có màu đỏ hồng hoặc nâu sẫm", "Nước tiểu đục, có cặn lắng", "Đi tiểu bình thường"]},
            {"id": "q_flank_pain", "question": "Bạn có bị đau vùng hông lưng thắt lưng không?", "options": ["Đau quặn từng cơn dữ dội một bên hông lưng", "Đau lan xuống vùng bẹn và đùi trong", "Đau âm ỉ mỏi vùng thắt lưng", "Không đau thắt lưng"]}
        ],
        "G43.9": [
            {"id": "q_migraine_side", "question": "Tính chất cơn đau đầu của bạn diễn ra như thế nào?", "options": ["Đau giật nhói theo nhịp mạch ở nửa bên đầu", "Đau căng tức cả hai bên thái dương", "Đau cứng ê ẩm sau gáy lan lên đầu", "Cảm giác choáng váng hoa mắt bồng bềnh"]},
            {"id": "q_migraine_trigger", "question": "Bạn có các dấu hiệu thần kinh giác quan nào đi kèm không?", "options": ["Sợ ánh sáng chói và tiếng ồn lớn", "Kèm buồn nôn hoặc nôn mửa", "Thấy chớp sáng / đốm mờ trước mắt", "Không có dấu hiệu kèm theo"]}
        ],
        "M54.5": [
            {"id": "q_back_pain_nature", "question": "Cơn đau lưng của bạn có đặc điểm nào dưới đây?", "options": ["Đau nhức ê ẩm dọc cột sống thắt lưng", "Đau nhói lan xuống mông và cẳng chân (đau thần kinh tọa)", "Đau tăng khi cúi gập người hoặc nâng vật nặng", "Cứng khớp lưng vào buổi sáng khó xoay người"]}
        ],
        "M05.9": [
            {"id": "q_joint_swelling", "question": "Tình trạng các khớp xương của bạn diễn biến ra sao?", "options": ["Khớp sưng nề, nóng đỏ và đau nhức", "Cứng khớp vào buổi sáng kéo dài trên 30 phút", "Đau đối xứng hai bên (cổ tay, ngón tay, khớp gối)", "Đau tăng nhiều khi thời tiết thay đổi"]}
        ],
        "K02.9": [
            {"id": "q_dental_pain", "question": "Tình trạng răng miệng của bạn có biểu hiện nào dưới đây?", "options": ["Đau buốt nhức răng dữ dội khi ăn đồ nóng / lạnh", "Nướu răng sưng đỏ, phù nề hoặc chảy máu", "Sưng má hoặc góc hàm bên phía răng đau", "Có ổ sâu răng hoặc lỗ hổng trên mặt răng"]}
        ]
    }

    def __init__(self, confidence_threshold: float = 0.70, entropy_threshold: float = 1.2):
        self.confidence_threshold = confidence_threshold
        self.entropy_threshold = entropy_threshold

    def calculate_entropy(self, probabilities: np.ndarray) -> float:
        """Tính Shannon Entropy H(P) = - sum(p * log2(p))."""
        probs = probabilities[probabilities > 1e-6]
        return float(-np.sum(probs * np.log2(probs)))

    def generate_context_aware_questions(
        self,
        user_text: str,
        detected_symptoms: Optional[List[str]] = None,
        top_disease_codes: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Sinh các câu hỏi làm rõ bám sát ngữ cảnh thực tế từ câu hỏi và triệu chứng người dùng mô tả.
        Hỗ trợ phân tích chuyên sâu đa cơ quan: Tiêu hóa, Hô hấp, Thần kinh, Da liễu, Tim mạch, Cơ xương khớp, v.v.
        """
        text_lower = (user_text or "").lower()
        symptom_str = " ".join([str(s).lower() for s in (detected_symptoms or [])])
        combined = f"{text_lower} {symptom_str}"

        questions: List[Dict[str, Any]] = []

        # 1. Nếu có top ICD codes trong ngân hàng chuyên biệt
        if top_disease_codes:
            for code in top_disease_codes:
                if code in self.DISCRIMINATING_QUESTIONS:
                    for q in self.DISCRIMINATING_QUESTIONS[code]:
                        if q not in questions and len(questions) < 3:
                            questions.append(q)

        # 2. Phân tích ngữ cảnh từ khóa chuyên sâu
        # A. Tiêu hóa (Dạ dày, ruột, bụng, nôn, ợ chua, tiêu chảy, táo bón)
        if any(kw in combined for kw in ["bụng", "dạ dày", "bao tử", "thượng vị", "ợ chua", "ợ hơi", "buồn nôn", "nôn ói", "tiêu chảy", "đi ngoài", "đầy bụng", "trĩ"]):
            if not any(q["id"].startswith("q_stomach") or q["id"].startswith("q_appendicitis") for q in questions):
                questions.append({
                    "id": "q_stomach_pos",
                    "question": "Cơn đau bụng của bạn tập trung rõ nhất ở khu vực nào?",
                    "options": [
                        "Vùng thượng vị (trên rốn, dưới xương ức)",
                        "Quanh rốn, đau quặn từng cơn",
                        "Bụng dưới bên phải (hố chậu phải)",
                        "Đau âm ỉ khắp toàn bộ ổ bụng"
                    ]
                })
                questions.append({
                    "id": "q_digestive_associated",
                    "question": "Bạn có gặp các biểu hiện rối loạn tiêu hóa đi kèm dưới đây không?",
                    "options": [
                        "Ợ chua, ợ nóng rát cổ họng",
                        "Buồn nôn hoặc nôn mửa",
                        "Đầy hơi, chướng bụng khó tiêu sau ăn",
                        "Đi ngoài phân lỏng nhiều lần / phân đen"
                    ]
                })

        # B. Hô hấp & Tai mũi họng (Ho, đờm, khó thở, thở rít, rát họng, ngạt mũi, viêm phổi)
        elif any(kw in combined for kw in ["ho", "đờm", "khó thở", "thở dốc", "khò khè", "rát họng", "đau họng", "ngạt mũi", "sổ mũi", "phổi"]):
            if not any(q["id"].startswith("q_cough") or q["id"].startswith("q_throat") for q in questions):
                questions.append({
                    "id": "q_resp_cough_nature",
                    "question": "Cơn ho và đường thở của bạn có đặc điểm nào dưới đây?",
                    "options": [
                        "Ho khan từng cơn gây rát cổ họng",
                        "Ho khạc đờm đặc màu vàng hoặc xanh",
                        "Khó thở, thở dốc khi hít thở sâu hoặc đi lại",
                        "Khò khè, rít đường thở nhiều về đêm / sáng sớm"
                    ]
                })
                questions.append({
                    "id": "q_resp_ent_signs",
                    "question": "Bạn có xuất hiện các triệu chứng tai mũi họng & toàn thân đi kèm không?",
                    "options": [
                        "Cổ họng sưng đỏ, nuốt đau buốt",
                        "Ngạt mũi, chảy nước mũi trong hoặc đục",
                        "Đau tức thành ngực khi ho hoặc hít sâu",
                        "Sốt nhẹ hoặc ớn lạnh gai người"
                    ]
                })

        # C. Thần kinh & Sọ não (Đau đầu, nhức đầu, chóng mặt, mất ngủ, choáng váng, tê bì, giật)
        elif any(kw in combined for kw in ["đầu", "nhức đầu", "đau đầu", "chóng mặt", "hoa mắt", "choáng", "mất ngủ", "tê bì", "buồn ngủ"]):
            if not any(q["id"].startswith("q_migraine") for q in questions):
                questions.append({
                    "id": "q_neuro_headache_type",
                    "question": "Cơn đau đầu hoặc choáng váng của bạn diễn biến như thế nào?",
                    "options": [
                        "Đau giật nhói theo nhịp mạch ở nửa bên đầu",
                        "Đau căng tức cả hai bên thái dương và trán",
                        "Đau cứng ê ẩm vùng sau gáy lan lên đỉnh đầu",
                        "Cảm giác chao đảo, bồng bềnh, đồ vật xoay tròn"
                    ]
                })
                questions.append({
                    "id": "q_neuro_alert_signs",
                    "question": "Bạn có các dấu hiệu thần kinh giác quan nào đi kèm dưới đây không?",
                    "options": [
                        "Sợ ánh sáng chói hoặc tiếng động lớn",
                        "Kèm buồn nôn hoặc nôn mửa đột ngột",
                        "Tê bì, châm chích vùng tay chân hoặc mặt",
                        "Nhìn mờ, thấy đốm sáng hoặc bóng đen"
                    ]
                })

        # D. Da liễu & Dị ứng (Ngứa, phát ban, nổi mẩn, rát đỏ, mề đay, mụn nước, dị ứng da)
        elif any(kw in combined for kw in ["da", "ngứa", "nổi mẩn", "rát", "đỏ", "phát ban", "mề đay", "dị ứng", "mụn nước"]):
            if not any(q["id"].startswith("q_skin") for q in questions):
                questions.append({
                    "id": "q_derma_sensation",
                    "question": "Cảm giác và hình thái tổn thương trên bề mặt da của bạn thế nào?",
                    "options": [
                        "Ngứa ngáy dữ dội, cào gãi không đỡ",
                        "Căng rát, đỏ ửng bề mặt da",
                        "Nổi sẩn cộm phù nề hoặc mảng mề đay",
                        "Có mụn nước li ti, trợt loét chảy dịch"
                    ]
                })
                questions.append({
                    "id": "q_derma_triggers",
                    "question": "Tổn thương da xuất hiện sau khi tiếp xúc với yếu tố nào dưới đây?",
                    "options": [
                        "Dùng mỹ phẩm, sữa rửa mặt hoặc thuốc bôi mới",
                        "Ăn hải sản, đồ tanh hoặc thức ăn lạ",
                        "Tiếp xúc trực tiếp ánh nắng gắt / nguồn nước lạ",
                        "Tự nhiên bùng phát, không rõ nguyên nhân tiếp xúc"
                    ]
                })

        # E. Tim mạch & Lồng ngực (Đau ngực, tức ngực, tim đập nhanh, hồi hộp, khó thở khi gắng sức)
        elif any(kw in combined for kw in ["ngực", "tức ngực", "đau ngực", "tim", "hồi hộp", "đánh trống ngực", "nhịp tim"]):
            if not any(q["id"].startswith("q_chest") for q in questions):
                questions.append({
                    "id": "q_cardio_pain_type",
                    "question": "Tính chất cơn đau tức ngực và hướng lan của bạn như thế nào?",
                    "options": [
                        "Đau thắt bóp nghẹt sau xương ức",
                        "Đau lan lên cổ, cằm hoặc cánh tay trái",
                        "Đau nhói thoáng qua khi ấn vào thành ngực",
                        "Cảm giác tim đập nhanh hồi hộp, thình thịch"
                    ]
                })
                questions.append({
                    "id": "q_cardio_warning_signs",
                    "question": "Bạn có gặp các dấu hiệu tuần hoàn đi kèm nào sau đây không?",
                    "options": [
                        "Vã mồ hôi lạnh, bồn chồn lo lắng",
                        "Khó thở hụt hơi khi đi lại hoặc leo cầu thang",
                        "Cảm giác choáng váng, xây xẩm muốn ngất",
                        "Không kèm vã mồ hôi hay khó thở"
                    ]
                })

        # F. Cơ xương khớp (Đau lưng, đau khớp, khớp gối, vai gáy, cứng khớp, sưng đau khớp)
        elif any(kw in combined for kw in ["lưng", "khớp", "gối", "vai gáy", "cột sống", "xương", "cơ", "thoát vị", "cứng khớp"]):
            if not any(q["id"].startswith("q_back") or q["id"].startswith("q_joint") for q in questions):
                questions.append({
                    "id": "q_ortho_movement",
                    "question": "Cơn đau cơ khớp ảnh hưởng đến vận động của bạn như thế nào?",
                    "options": [
                        "Đau tăng rõ rệt khi đi lại, vận động hoặc chịu lực",
                        "Cứng khớp khó cử động vào buổi sáng (> 30 phút)",
                        "Khớp sưng nề, sờ thấy nóng đỏ rõ rệt",
                        "Đau nhức ê ẩm dọc vùng cột sống thắt lưng"
                    ]
                })
                questions.append({
                    "id": "q_ortho_radiation",
                    "question": "Cơn đau có lan truyền hay xuất hiện sau yếu tố nào?",
                    "options": [
                        "Đau lan xuống mông và cẳng chân (hướng dây thần kinh)",
                        "Đau lan lên vai gáy và cánh tay",
                        "Đau đột ngột xuất hiện sau khi khuân vác nặng / sai tư thế",
                        "Đau âm ỉ tái phát kéo dài nhiều tuần"
                    ]
                })

        # G. Răng hàm mặt & Nha khoa (Đau răng, sưng nướu, chảy máu chân răng, lợi, nhiệt miệng)
        elif any(kw in combined for kw in ["răng", "nướu", "lợi", "hàm", "nhiệt miệng", "chảy máu răng"]):
            if not any(q["id"].startswith("q_dental") for q in questions):
                questions.append({
                    "id": "q_dental_specific",
                    "question": "Tình trạng răng miệng của bạn có đặc điểm nào dưới đây?",
                    "options": [
                        "Đau buốt nhức răng dữ dội khi ăn đồ nóng / lạnh",
                        "Nướu lợi sưng đỏ, phù nề hoặc có mủ",
                        "Chảy máu chân răng khi đánh răng hoặc chạm nhẹ",
                        "Có các vết loét nhiệt miệng màu trắng đau rát"
                    ]
                })
                questions.append({
                    "id": "q_dental_jaw_swelling",
                    "question": "Vùng hàm mặt có dấu hiệu lan rộng nào đi kèm không?",
                    "options": [
                        "Sưng to một bên má hoặc vùng dưới hàm",
                        "Khó há miệng hoặc khó nhai nuốt",
                        "Kèm sốt nhẹ hoặc nổi hạch cổ",
                        "Chỉ đau khu trú tại răng, không sưng mặt"
                    ]
                })

        # H. Tiết niệu & Thận (Tiểu buốt, tiểu rắt, tiểu máu, đau hông lưng, tiểu nhiều)
        elif any(kw in combined for kw in ["tiểu", "đái", "nước tiểu", "buốt", "rắt", "thận", "hông lưng"]):
            if not any(q["id"].startswith("q_kidney") for q in questions):
                questions.append({
                    "id": "q_uro_symptoms",
                    "question": "Bạn gặp bất thường nào khi đi tiểu tiện?",
                    "options": [
                        "Cảm giác nóng rát, buốt buốt dọc đường tiểu",
                        "Đi tiểu lắt nhắt nhiều lần, cảm giác không hết bãi",
                        "Nước tiểu có màu đỏ hồng, nâu sẫm hoặc có cặn",
                        "Nước tiểu đục, có mùi hôi nồng nặc"
                    ]
                })
                questions.append({
                    "id": "q_uro_flank_pain",
                    "question": "Bạn có kèm theo cơn đau thắt lưng hoặc sốt không?",
                    "options": [
                        "Đau quặn từng cơn dữ dội một bên hông lưng",
                        "Đau tức âm ỉ vùng bụng dưới (hạ vị)",
                        "Kèm theo sốt cao, ớn lạnh rét run",
                        "Không đau lưng, chỉ khó chịu khi tiểu"
                    ]
                })

        # I. Sốt & Nhiễm khuẩn toàn thân (Sốt, mệt mỏi, ớn lạnh, đau mỏi toàn thân)
        elif any(kw in combined for kw in ["sốt", "mệt", "ớn lạnh", "rét", "nhiễm khuẩn", "uể oải"]):
            if not any(q["id"].startswith("q_fever") for q in questions):
                questions.append({
                    "id": "q_fever_pattern",
                    "question": "Thân nhiệt và tính chất cơn sốt của bạn như thế nào?",
                    "options": [
                        "Sốt cao liên tục trên 38.5°C, khó hạ sốt",
                        "Sốt theo cơn có kèm cảm giác rét run",
                        "Sốt nhẹ âm ỉ về chiều và tối",
                        "Người mệt mỏi rã rời, đau nhức mình mẩy"
                    ]
                })
                questions.append({
                    "id": "q_infection_signs",
                    "question": "Bạn có nhận thấy dấu hiệu bất thường nào đi kèm dưới đây không?",
                    "options": [
                        "Đau nhức hốc mắt và đau mỏi cơ bắp toàn thân",
                        "Xuất hiện chấm đỏ li ti xuất huyết dưới da",
                        "Chảy máu chân răng hoặc chảy máu cam",
                        "Cổ họng đau rát hoặc có ho đờm"
                    ]
                })

        # J. Fallback thông minh: Tạo câu hỏi khai thác bám sát câu hỏi người dùng
        if not questions:
            # Tóm tắt lại câu người dùng để câu hỏi mang tính cá nhân hóa cao
            clean_snippet = user_text.strip()
            if len(clean_snippet) > 40:
                clean_snippet = clean_snippet[:40] + "..."
            snippet_label = f'"{clean_snippet}"' if clean_snippet else "triệu chứng của bạn"

            questions.append({
                "id": "q_dynamic_main_location",
                "question": f"Về tình trạng {snippet_label}, cảm giác khó chịu nhất hiện tại của bạn thuộc nhóm nào dưới đây?",
                "options": [
                    "Đau nhức / Khó chịu tại một vị trí cụ thể",
                    "Sốt cao / Mệt mỏi / Ớn lạnh toàn thân",
                    "Rối loạn tiêu hóa (đau bụng, buồn nôn, đi ngoài)",
                    "Vấn đề đường thở (ho, khó thở, rát họng, ngạt mũi)"
                ]
            })
            questions.append({
                "id": "q_dynamic_onset_duration",
                "question": "Tình trạng này đã diễn ra bao lâu và xu hướng diễn biến thế nào?",
                "options": [
                    "Mới xuất hiện đột ngột trong 24 giờ qua",
                    "Đã kéo dài từ 2 đến 3 ngày nay",
                    "Kéo dài trên 1 tuần và tái phát nhiều lần",
                    "Triệu chứng đang có chiều hướng tăng nặng dần"
                ]
            })

        return questions[:2]

    def generate_clarification_questions(
        self,
        probabilities: np.ndarray,
        disease_classes: List[Dict[str, Any]],
        known_symptoms: List[str],
        user_text: str = ""
    ) -> Dict[str, Any]:
        """
        Đánh giá độ tin cậy và sinh câu hỏi làm rõ lâm sàng bám sát ngữ cảnh người dùng.
        """
        max_prob = float(np.max(probabilities)) if len(probabilities) > 0 else 0.0
        entropy = self.calculate_entropy(probabilities) if len(probabilities) > 0 else 0.0

        # Kích hoạt clarification khi xác suất chưa vượt trội hoặc entropy cao hoặc triệu chứng ít
        # Nếu đã có bệnh xác suất cao >= 0.65 thì không cần ép hỏi làm rõ
        needs_clarification = (max_prob < 0.65) and ((max_prob < self.confidence_threshold) or (entropy > self.entropy_threshold) or len(known_symptoms) <= 1)

        if not needs_clarification:
            return {
                "needs_clarification": False,
                "confidence_score": round(max_prob, 3),
                "entropy": round(entropy, 3),
                "questions": []
            }

        # Lấy top các bệnh đang cạnh tranh xác suất
        top_indices = np.argsort(probabilities)[::-1][:2] if len(probabilities) > 0 else []
        top_codes = []
        for idx in top_indices:
            if idx < len(disease_classes) and float(probabilities[idx]) > 0.0:
                code = disease_classes[idx].get("code")
                if code:
                    top_codes.append(code)

        # Sinh câu hỏi bám chặt ngữ cảnh người dùng
        questions = self.generate_context_aware_questions(
            user_text=user_text,
            detected_symptoms=known_symptoms,
            top_disease_codes=top_codes
        )

        # Loại bỏ các câu hỏi mà người dùng đã trả lời trong câu hội thoại trước
        user_text_lower = (user_text or "").lower()
        filtered_questions = []
        for q in questions:
            opts = q.get("options", [])
            already_answered = any(len(opt) > 6 and opt.lower() in user_text_lower for opt in opts)
            if not already_answered:
                filtered_questions.append(q)

        questions = filtered_questions
        if not questions:
            needs_clarification = False

        return {
            "needs_clarification": needs_clarification,
            "confidence_score": round(max_prob, 3),
            "entropy": round(entropy, 3),
            "reason": f"Độ tin cậy sơ bộ ({round(max_prob * 100, 1)}%) chưa đủ cao để khẳng định. Cần thêm thông tin làm rõ." if needs_clarification else "Đã thu thập đủ căn cứ lâm sàng sơ bộ.",
            "questions": questions
        }
