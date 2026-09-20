import numpy as np
import logging
import re
import os
import json
from typing import Dict, List, Any, Optional, Set

logger = logging.getLogger(__name__)

class ClarificationEngine:
    """
    Thuật toán phân tích Entropy, Cây quyết định lâm sàng và Ngữ cảnh động (Context-Aware Clarification).
    Hỗ trợ mô hình 3 tầng phân định lâm sàng:
    1. INITIAL_SCREENING (Chưa đủ dữ liệu, < 40%): Thu thập triệu chứng cơ bản, KHÔNG đoán bệnh.
    2. PROVISIONAL_ASSUMPTION (Giả định lâm sàng, 40% - 75%): Tạm thời giả định, BẮT BUỘC hỏi thêm câu hỏi phân biệt.
    3. DEFINITIVE_CONCLUSION (Kết luận sơ bộ xác định, >= 75% & >= 3 triệu chứng/lượt hỏi): Đưa ra chẩn đoán xác định, phác đồ điều trị.
    """

    CONFIDENCE_THRESHOLD_DEFINITIVE = 0.75
    CONFIDENCE_THRESHOLD_PROVISIONAL = 0.40
    MIN_SYMPTOMS_FOR_DEFINITIVE = 3

    # Ngân hàng câu hỏi phân biệt đa tầng (Stage 1 cơ bản, Stage 2 phân biệt chuyên sâu, Stage 3 tiền sử/đáp ứng)
    DISCRIMINATING_QUESTIONS = {
        "A90": [
            {"id": "q_fever_temp", "question": "Thân nhiệt và tính chất cơn sốt của bạn như thế nào?", "options": ["Sốt cao liên tục trên 38.5°C", "Sốt theo cơn có rét run", "Sốt nhẹ âm ỉ", "Không sốt"]},
            {"id": "q_bleeding", "question": "Bạn có xuất hiện dấu hiệu xuất huyết hoặc đau nhức nào đi kèm không?", "options": ["Đau nhức hốc mắt & đau mỏi cơ", "Có chấm đỏ xuất huyết dưới da", "Chảy máu chân răng / chảy máu cam", "Không có dấu hiệu xuất huyết"]},
            {"id": "q_dengue_day", "question": "Hôm nay là ngày thứ mấy kể từ khi bạn bắt đầu có biểu hiện sốt?", "options": ["Ngày 1 - 2 (Giai đoạn sốt cao)", "Ngày 3 - 5 (Giai đoạn nguy hiểm, cần theo dõi tiểu cầu)", "Ngày 6 trở đi (Giai đoạn hồi phục)", "Sốt ngắt quãng không nhớ ngày"]},
            {"id": "q_dengue_warning", "question": "Bạn có xuất hiện các dấu hiệu cảnh báo nặng dưới đây không?", "options": ["Đau tức vùng hạ sườn phải (vùng gan)", "Nôn mửa nhiều liên tục trên 3 lần/ngày", "Người lừ đừ, mệt lả hoặc li bì", "Không có dấu hiệu cảnh báo trên"]}
        ],
        "G43.9": [
            {"id": "q_migraine_side", "question": "Tính chất cơn đau đầu của bạn diễn ra như thế nào?", "options": ["Đau giật nhói theo nhịp mạch ở nửa bên đầu", "Đau căng tức cả hai bên thái dương và trán", "Đau cứng ê ẩm sau gáy lan lên đầu", "Cảm giác choáng váng hoa mắt bồng bềnh"]},
            {"id": "q_migraine_trigger", "question": "Bạn có các dấu hiệu thần kinh giác quan nào đi kèm không?", "options": ["Sợ ánh sáng chói và tiếng ồn lớn", "Kèm buồn nôn hoặc nôn mửa", "Thấy chớp sáng / đốm mờ trước mắt", "Không có dấu hiệu kèm theo"]},
            {"id": "q_migraine_duration", "question": "Thời gian mỗi cơn đau đầu thường kéo dài trong bao lâu?", "options": ["Kéo dài từ 4 đến 72 giờ liên tục", "Đau ê ẩm cả ngày, tăng dần khi căng thẳng/stress", "Cơn đau nhói thoáng qua vài giây đến vài phút", "Đau liên tục nhiều ngày không dứt"]},
            {"id": "q_migraine_aggravating", "question": "Yếu tố nào làm cơn đau đầu của bạn tăng lên hoặc thuyên giảm?", "options": ["Đau tăng khi đi lại, vận động hoặc cúi người", "Đỡ đau rõ rệt khi nằm nghỉ trong phòng tối yên tĩnh", "Đau tăng khi nhìn màn hình điện thoại / thiếu ngủ", "Đã uống thuốc giảm đau nhưng không đỡ"]}
        ],
        "I21.9": [
            {"id": "q_chest_spread", "question": "Cơn đau ngực có đặc điểm và hướng lan như thế nào?", "options": ["Đau thắt bóp nghẹt sau xương ức", "Đau lan lên cổ, hàm hoặc xuống tay trái", "Đau nhói thoáng qua khi ấn vào sườn", "Cảm giác tim đập nhanh, hồi hộp"]},
            {"id": "q_sweat_cold", "question": "Bạn có kèm theo các dấu hiệu tuần hoàn cấp tính nào không?", "options": ["Vã mồ hôi lạnh toàn thân", "Khó thở, thở dốc ngột ngạt", "Chóng mặt, cảm giác muốn ngất xỉu", "Không vã mồ hôi"]},
            {"id": "q_chest_duration", "question": "Cơn đau tức ngực kéo dài liên tục trong bao lâu?", "options": ["Đau dữ dội kéo dài trên 20 phút không giảm", "Đau tức từng cơn 2-5 phút khi gắng sức rồi đỡ", "Đau nhói vài giây khi thay đổi tư thế", "Đau tức âm ỉ cả ngày"]},
            {"id": "q_cardio_history", "question": "Bạn có tiền sử bệnh lý nền tim mạch chuyển hóa nào dưới đây không?", "options": ["Tăng huyết áp hoặc bệnh mạch vành", "Đái tháo đường (tiểu đường)", "Rối loạn mỡ máu hoặc hút thuốc lá lâu năm", "Chưa từng mắc bệnh tim mạch"]}
        ],
        "J00": [
            {"id": "q_runny_nose", "question": "Đường hô hấp trên của bạn có biểu hiện nào dưới đây?", "options": ["Ngạt mũi, chảy dịch mũi trong", "Chảy nước mũi vàng đục", "Hắt xì hơi liên tục", "Mũi khô rát khó thở"]},
            {"id": "q_throat_pain", "question": "Cảm giác tại vùng họng của bạn diễn biến ra sao?", "options": ["Đau rát họng tăng khi nuốt", "Khô ngứa họng gây ho từng cơn", "Khàn tiếng, mất giọng", "Họng bình thường"]},
            {"id": "q_cold_cough", "question": "Tình trạng ho và thân nhiệt hiện tại thế nào?", "options": ["Ho khan từng cơn, không có đờm", "Ho khạc đờm trắng loãng", "Sốt nhẹ 37.5 - 38°C kèm đau mỏi người", "Không sốt, chỉ mệt mỏi nhẹ"]}
        ],
        "J18.9": [
            {"id": "q_cough_sputum", "question": "Cơn ho của bạn có tính chất và đờm dịch như thế nào?", "options": ["Ho khạc đờm đặc màu vàng / xanh", "Ho khạc đờm rỉ sét / có vệt máu", "Ho đờm trắng trong loãng", "Ho khan từng cơn không đờm"]},
            {"id": "q_chest_pain_breathe", "question": "Khi hít thở sâu hoặc ho, ngực của bạn có biểu hiện gì?", "options": ["Đau nhói ngực tăng lên rõ rệt", "Cảm giác hụt hơi, thở rít khò khè", "Tức nặng vùng giữa ngực", "Không đau tức khi hít thở"]},
            {"id": "q_pneumonia_fever", "question": "Tình trạng sốt và khó thở của bạn ra sao?", "options": ["Sốt cao liên tục kèm rét run dữ dội", "Thở nhanh nông, cánh mũi phập phồng", "Cảm giác đuối sức khi làm việc nhẹ", "Sốt nhẹ từng cơn"]}
        ],
        "K29.7": [
            {"id": "q_stomach_timing", "question": "Cơn đau bụng của bạn khu trú ở đâu và xuất hiện vào lúc nào?", "options": ["Đau quặn / cồn cào vùng thượng vị (trên rốn)", "Đau nhiều lúc đói hoặc ban đêm", "Đau tức cồn cào ngay sau khi ăn no", "Đau âm ỉ bất kỳ thời điểm nào"]},
            {"id": "q_heartburn", "question": "Bạn có gặp các triệu chứng trào ngược tiêu hóa đi kèm không?", "options": ["Ợ chua, ợ hơi nóng rát lên cổ", "Buồn nôn hoặc nôn mửa thức ăn", "Chướng bụng, đầy hơi khó tiêu", "Cảm giác đắng miệng, chua miệng"]},
            {"id": "q_stool_nature", "question": "Tính chất phân và đại tiện của bạn có bất thường gì không?", "options": ["Phân đen sệt như bã cà phê (dấu hiệu xuất huyết tiêu hóa)", "Đi ngoài phân sống hoặc lỏng sau ăn", "Táo bón, nhiều ngày không đại tiện", "Đại tiện phân vàng bình thường"]}
        ],
        "K21.9": [
            {"id": "q_gerd_throat", "question": "Cảm giác nóng rát trào ngược và cổ họng của bạn như thế nào?", "options": ["Nóng rát sau xương ức lan lên họng", "Ợ chua, đắng miệng vào buổi sáng", "Ho khan kéo dài nhiều về đêm", "Vướng nghẹn ở cổ họng khi nuốt"]},
            {"id": "q_gerd_triggers", "question": "Triệu chứng trào ngược thường nặng lên trong hoàn cảnh nào?", "options": ["Khi nằm ngửa hoặc cúi gập người sau ăn", "Sau khi uống cà phê, rượu bia hoặc ăn đồ chua cay", "Khi bụng quá no hoặc ăn khuya trước ngủ", "Xuất hiện bất kỳ lúc nào"]}
        ],
        "L20.9": [
            {"id": "q_skin_trigger", "question": "Tình trạng kích ứng hoặc rát đỏ da xuất hiện sau yếu tố nào?", "options": ["Đi ngoài trời nắng gắt", "Dùng mỹ phẩm / sữa rửa mặt mới", "Ăn hải sản / thức ăn lạ", "Tự nhiên bùng phát"]},
            {"id": "q_skin_itch", "question": "Cảm giác tại vùng da bị tổn thương diễn ra như thế nào?", "options": ["Ngứa râm ran, châm chích khó chịu", "Căng rát đỏ ửng bề mặt da", "Có nổi mẩn đỏ hoặc mụn nước li ti", "Da khô ráp, bong tróc vảy"]},
            {"id": "q_skin_history", "question": "Bạn có tiền sử dị ứng hoặc viêm da cơ địa trước đây không?", "options": ["Từng bị viêm da cơ địa / chàm mạn tính", "Có cơ địa dị ứng thời tiết / phấn hoa", "Bị hen suyễn hoặc viêm mũi dị ứng", "Lần đầu tiên bị dị ứng da"]}
        ],
        "N20.0": [
            {"id": "q_kidney_urinate", "question": "Tình trạng đi tiểu và màu sắc nước tiểu của bạn thế nào?", "options": ["Cảm giác tiểu buốt, tiểu rắt buốt dọc niệu đạo", "Nước tiểu có màu đỏ hồng hoặc nâu sẫm", "Nước tiểu đục, có cặn lắng", "Đi tiểu bình thường"]},
            {"id": "q_flank_pain", "question": "Bạn có bị đau vùng hông lưng thắt lưng không?", "options": ["Đau quặn từng cơn dữ dội một bên hông lưng", "Đau lan xuống vùng bẹn và đùi trong", "Đau âm ỉ mỏi vùng thắt lưng", "Không đau thắt lưng"]}
        ],
        "H52.4": [
            {
                "id": "q_presbyopia_read",
                "question": "Khả năng nhìn gần và đọc sách của bạn có biểu hiện nào dưới đây?",
                "options": [
                    "Nhìn gần mờ, phải đưa sách hoặc điện thoại ra xa mới đọc được",
                    "Mỏi mắt, nhức đầu vùng trán khi cố gắng đọc chữ nhỏ lâu",
                    "Cần ánh sáng rất mạnh mới nhìn rõ chữ ở cự ly gần",
                    "Khó chuyển đổi tiêu cự từ nhìn xa sang nhìn gần"
                ]
            },
            {
                "id": "q_presbyopia_age",
                "question": "Độ tuổi và tiền sử điều tiết mắt của bạn như thế nào?",
                "options": [
                    "Độ tuổi trên 40 tuổi, trước đây nhìn bình thường nay nhìn gần mờ",
                    "Đã từng đeo kính cận thị hoặc viễn thị từ trước",
                    "Dưới 40 tuổi nhưng thường xuyên mỏi mắt khi làm việc máy tính lâu",
                    "Mới xuất hiện tình trạng mỏi mắt và nhìn mờ gần đây"
                ]
            }
        ],
        "H57": [
            {
                "id": "q_dry_eye_sensation",
                "question": "Cảm giác bề mặt nhãn cầu và phản xạ mắt của bạn ra sao?",
                "options": [
                    "Khô rát, cộm xốn như có hạt cát hoặc dị vật trong mắt",
                    "Chảy nước mắt sống phản xạ khi mắt bị khô cay kích thích",
                    "Mỏi mắt, mệt mỏi căng thẳng thị giác sau nhiều giờ nhìn màn hình",
                    "Chớp mắt vài cái thì sáng rõ sau đó lại mờ nhòe"
                ]
            },
            {
                "id": "q_eye_triggers",
                "question": "Tình trạng mỏi mắt và khô mắt xuất hiện nhiều nhất khi nào?",
                "options": [
                    "Sau nhiều giờ làm việc liên tục với máy tính, điện thoại",
                    "Đi ngoài trời nhiều gió bụi, ánh nắng gắt hoặc phòng máy lạnh",
                    "Vào buổi chiều tối hoặc sau một ngày làm việc căng thẳng",
                    "Xuất hiện liên tục cả ngày dù đã nghỉ ngơi nhắm mắt"
                ]
            }
        ],
        "H52.1": [
            {
                "id": "q_myopia_signs",
                "question": "Tầm nhìn xa và khả năng quan sát của bạn có đặc điểm nào dưới đây?",
                "options": [
                    "Nhìn xa bị mờ nhòe, phải nheo mắt mới nhìn rõ",
                    "Mỏi mắt, nhức đầu vùng thái dương khi học tập / làm việc",
                    "Nhìn gần (sách, điện thoại) vẫn rõ bình thường",
                    "Thị lực nhìn xa suy giảm dần trong vài tháng qua"
                ]
            }
        ],
        "H10": [
            {
                "id": "q_conjunctivitis_signs",
                "question": "Mắt của bạn có tiết dịch, ghèn rỉ mắt hoặc sưng đỏ không?",
                "options": [
                    "Mắt đỏ rực, nhiều ghèn rỉ mắt dính mi khó mở mắt buổi sáng",
                    "Chảy nước mắt trong, ngứa mắt nhiều (nghi do dị ứng)",
                    "Sưng nề mi mắt, cộm rát khó chịu",
                    "Không có ghèn rỉ mắt, chỉ đỏ nhẹ"
                ]
            }
        ],
        "J10": [
            {
                "id": "q_flu_respiratory_signs",
                "question": "Đường hô hấp trên và vùng mắt/họng của bạn có biểu hiện nào dưới đây không?",
                "options": [
                    "Ho khan rát họng, nghẹt mũi hoặc chảy nước mũi trong",
                    "Đau nhức sâu sau hai hốc mắt (tăng lên khi cử động liếc mắt)",
                    "Đau rát bỏng sau xương ức khi ho hoặc hít thở sâu",
                    "Không có triệu chứng hô hấp, đường thở thông thoáng bình thường"
                ]
            },
            {
                "id": "q_flu_systemic_myalgia",
                "question": "Tính chất cơn sốt và mức độ đau nhức cơ thể của bạn diễn biến ra sao?",
                "options": [
                    "Đau nhức cơ bắp toàn thân ê ẩm như bị đánh, mệt lả kiệt sức",
                    "Sốt cao đột ngột kèm ớn lạnh rét run từng cơn bần bật",
                    "Sốt kèm mệt mỏi nhưng không đau nhức cơ khớp nhiều",
                    "Thân nhiệt bình thường hoặc chỉ ấm đầu nhẹ"
                ]
            },
            {
                "id": "q_flu_dengue_differential",
                "question": "Để phân biệt Cúm với Sốt xuất huyết và theo dõi an toàn, bạn có dấu hiệu nào sau đây không?",
                "options": [
                    "Không có nốt xuất huyết dưới da, không chảy máu chân răng/cam",
                    "Có chấm đỏ li ti xuất huyết dưới da hoặc chảy máu niêm mạc",
                    "Đau quặn tức vùng hạ sườn phải (vùng gan) hoặc nôn ói liên tục",
                    "Khó thở, thở nhanh nông, đau tức ngực dữ dội (cần loại trừ viêm phổi)"
                ]
            }
        ],
        "J11": [
            {
                "id": "q_flu_respiratory_signs",
                "question": "Đường hô hấp trên và vùng mắt/họng của bạn có biểu hiện nào dưới đây không?",
                "options": [
                    "Ho khan rát họng, nghẹt mũi hoặc chảy nước mũi trong",
                    "Đau nhức sâu sau hai hốc mắt (tăng lên khi cử động liếc mắt)",
                    "Đau rát bỏng sau xương ức khi ho hoặc hít thở sâu",
                    "Không có triệu chứng hô hấp, đường thở thông thoáng bình thường"
                ]
            },
            {
                "id": "q_flu_systemic_myalgia",
                "question": "Tính chất cơn sốt và mức độ đau nhức cơ thể của bạn diễn biến ra sao?",
                "options": [
                    "Đau nhức cơ bắp toàn thân ê ẩm như bị đánh, mệt lả kiệt sức",
                    "Sốt cao đột ngột kèm ớn lạnh rét run từng cơn bần bật",
                    "Sốt kèm mệt mỏi nhưng không đau nhức cơ khớp nhiều",
                    "Thân nhiệt bình thường hoặc chỉ ấm đầu nhẹ"
                ]
            },
            {
                "id": "q_flu_dengue_differential",
                "question": "Để phân biệt Cúm với Sốt xuất huyết và theo dõi an toàn, bạn có dấu hiệu nào sau đây không?",
                "options": [
                    "Không có nốt xuất huyết dưới da, không chảy máu chân răng/cam",
                    "Có chấm đỏ li ti xuất huyết dưới da hoặc chảy máu niêm mạc",
                    "Đau quặn tức vùng hạ sườn phải (vùng gan) hoặc nôn ói liên tục",
                    "Khó thở, thở nhanh nông, đau tức ngực dữ dội (cần loại trừ viêm phổi)"
                ]
            }
        ],
        "K76.0": [
            {
                "id": "q_liver_digestive",
                "question": "Vùng hạ sườn phải và hệ tiêu hóa của bạn có biểu hiện nào dưới đây không?",
                "options": [
                    "Tức nặng, đau tức âm ỉ vùng hạ sườn phải (vùng gan)",
                    "Đầy bụng khó tiêu, chướng hơi đặc biệt sau ăn nhiều dầu mỡ",
                    "Nước tiểu sẫm màu như nước vối, vàng da hoặc vàng mắt",
                    "Không đau tức vùng gan, tiêu hóa bình thường"
                ]
            },
            {
                "id": "q_liver_risk_habits",
                "question": "Bạn có tiền sử hoặc thói quen nào liên quan đến chuyển hóa / chức năng gan không?",
                "options": [
                    "Thường xuyên uống rượu bia hoặc ăn đồ nhiều dầu mỡ, thừa cân",
                    "Từng xét nghiệm thấy men gan cao (AST/ALT) hoặc gan nhiễm mỡ",
                    "Đang dùng thuốc kéo dài hoặc có tiền sử viêm gan B, C",
                    "Chưa từng mắc bệnh gan mật, không uống rượu bia"
                ]
            }
        ],
        "M47.9": [
            {
                "id": "q_cervical_spine_character",
                "question": "Vị trí và tính chất cảm giác đau mỏi ở vùng cổ gáy của bạn như thế nào?",
                "options": [
                    "Đau mỏi căng cứng vùng cổ vai gáy, khó xoay hoặc cúi ngửa đầu",
                    "Đau mỏi cổ kèm tê rần, tê bì lan xuống vai hoặc cánh tay/ngón tay",
                    "Mỏi ê ẩm bả vai gáy sau khi ngồi làm việc máy tính lâu một tư thế",
                    "Cổ vận động bình thường, không đau căng cứng"
                ]
            },
            {
                "id": "q_cervical_spine_aggravation",
                "question": "Triệu chứng đau mỏi cổ vai gáy thay đổi như thế nào khi nghỉ ngơi hoặc vận động?",
                "options": [
                    "Tăng nặng khi ngồi làm việc máy tính, cúi bấm điện thoại lâu",
                    "Đỡ hẳn khi được nằm nghỉ ngơi, xoa bóp hoặc chườm ấm",
                    "Xuất hiện liên tục cả ngày, ê ẩm vùng vai gáy và thắt lưng",
                    "Đã uống thuốc giảm đau nhưng chỉ đỡ tạm thời rồi đau lại"
                ]
            }
        ],
        "M54.5": [
            {
                "id": "q_lumbar_spine_character",
                "question": "Vị trí và đặc điểm cơn đau vùng lưng của bạn diễn biến như thế nào?",
                "options": [
                    "Đau mỏi âm ỉ vùng thắt lưng, tăng khi ngồi lâu hoặc cúi người",
                    "Đau quặn thắt lưng lan xuống mông hoặc dọc cẳng chân (nghi thần kinh tọa)",
                    "Đau nhói thắt lưng xuất hiện đột ngột sau khi mang vác vật nặng",
                    "Vùng lưng bình thường, không đau mỏi"
                ]
            }
        ],
        "I10": [
            {
                "id": "q_bp_measurement",
                "question": "Chỉ số huyết áp gần đây của bạn đo được là bao nhiêu?",
                "options": [
                    "Huyết áp tâm thu trên 140 mmHg (hoặc tâm trương trên 90 mmHg)",
                    "Huyết áp bình thường quanh mức 120/80 mmHg",
                    "Chưa đo huyết áp gần đây",
                    "Có tiền sử đang uống thuốc hạ huyết áp hằng ngày"
                ]
            },
            {
                "id": "q_bp_associated_signs",
                "question": "Bạn có các biểu hiện tuần hoàn sọ não nào dưới đây đi kèm không?",
                "options": [
                    "Đau tức nặng sau gáy, bốc hỏa nóng bừng mặt",
                    "Chóng mặt, choáng váng hoa mắt hoặc mất thăng bằng",
                    "Hồi hộp, tim đập nhanh hoặc tức nặng nhẹ vùng ngực",
                    "Không có các dấu hiệu choáng váng hay đau gáy kể trên"
                ]
            }
        ],
        "G44.2": [
            {
                "id": "q_tension_headache_character",
                "question": "Tính chất và vị trí cơn đau đầu của bạn có đặc điểm nào dưới đây?",
                "options": [
                    "Đau căng tức bó chặt như có dải băng thắt quanh đầu cả hai bên",
                    "Đau âm ỉ cả ngày, tăng dần vào chiều tối khi căng thẳng/stress",
                    "Không kèm buồn nôn, không sợ ánh sáng/tiếng động",
                    "Đau nhói giật theo nhịp mạch ở nửa bên đầu"
                ]
            }
        ],
        "A09": [
            {
                "id": "q_diarrhea_frequency",
                "question": "Tình trạng đi ngoài phân lỏng của bạn diễn biến như thế nào trong ngày?",
                "options": [
                    "Đi ngoài phân lỏng nước nhiều trên 3 - 5 lần/ngày",
                    "Phân có nhầy máu hoặc mùi tanh nồng bất thường",
                    "Chỉ đi phân lỏng 1 - 2 lần sau khi ăn đồ ăn lạ",
                    "Không đi ngoài phân lỏng, đại tiện bình thường"
                ]
            },
            {
                "id": "q_diarrhea_associated",
                "question": "Bạn có triệu chứng sốt hoặc đau quặn bụng đi kèm không?",
                "options": [
                    "Đau quặn bụng từng cơn quanh rốn kèm buồn nôn, nôn mửa",
                    "Sốt nhẹ hoặc sốt cao kèm cảm giác khát nước nhiều",
                    "Xuất hiện sau khi ăn thức ăn ôi thiu / thực phẩm để lâu",
                    "Bụng chỉ đầy hơi khó tiêu nhẹ, không sốt"
                ]
            }
        ],
        "B01.9": [
            {
                "id": "q_chickenpox_rash",
                "question": "Tình trạng tổn thương trên bề mặt da của bạn có biểu hiện nào dưới đây?",
                "options": [
                    "Nổi nốt phỏng nước trong li ti khắp người, có viền đỏ xung quanh",
                    "Các nốt mụn nước có vết lõm ở giữa, ngứa ngáy dữ dội",
                    "Mụn nước bắt đầu trợt loét đóng vảy màu nâu",
                    "Không có nốt phỏng nước, chỉ là mẩn đỏ phẳng"
                ]
            }
        ],
        "J45.9": [
            {
                "id": "q_asthma_nature",
                "question": "Cơn khó thở của bạn có đặc điểm nào dưới đây không?",
                "options": [
                    "Khó thở thành cơn, thở rít khò khè nhiều ở thì thở ra",
                    "Cơn khó thở xuất hiện nhiều về đêm, gần sáng hoặc khi gặp lạnh",
                    "Đỡ khó thở nhanh chóng sau khi dùng thuốc xịt giãn phế quản",
                    "Khó thở liên tục cả ngày khi vận động gắng sức"
                ]
            }
        ],
        "K35.8": [
            {
                "id": "q_appendicitis_pain_shift",
                "question": "Cơn đau bụng của bạn có hướng di chuyển và vị trí thế nào?",
                "options": [
                    "Đau âm ỉ từ quanh rốn / thượng vị rồi chuyển khu trú xuống bụng dưới bên phải",
                    "Đau nhói tăng lên rõ rệt khi đi lại, ho hoặc khi ấn vào hố chậu phải rồi buông nhanh",
                    "Kèm sốt nhẹ 37.5 - 38.5°C, chán ăn, buồn nôn hoặc nôn nhẹ",
                    "Đau khắp cả bụng, không tập trung ở hố chậu phải"
                ]
            }
        ]
    }

    def __init__(self, confidence_threshold: float = 0.75, entropy_threshold: float = 1.2):
        self.confidence_threshold = confidence_threshold
        self.entropy_threshold = entropy_threshold
        icd_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "..", "data", "medical_lexicon", "icd10_codes.json"
        ))
        self.icd_db = {}
        if os.path.exists(icd_path):
            try:
                with open(icd_path, "r", encoding="utf-8") as f:
                    self.icd_db = json.load(f)
            except Exception as e:
                logger.warning(f"Error loading icd10_codes in ClarificationEngine: {e}")

    def calculate_entropy(self, probabilities: np.ndarray) -> float:
        """Tính Shannon Entropy H(P) = - sum(p * log2(p))."""
        probs = probabilities[probabilities > 1e-6]
        return float(-np.sum(probs * np.log2(probs)))

    def determine_clinical_stage(
        self,
        top_probability: float,
        symptom_count: int,
        clarification_turns_count: int,
        is_emergency: bool = False
    ) -> str:
        """
        Xác định phân tầng nhận định lâm sàng:
        - 'emergency': Cấp cứu nguy kịch (Red Flag)
        - 'initial_screening': Chưa đủ căn cứ, triệu chứng đơn độc (< 0.40 hoặc <= 1 triệu chứng)
        - 'provisional_assumption': Chẩn đoán Giả định lâm sàng (0.40 <= prob < 0.75 hoặc chưa qua hỏi phân biệt)
        - 'definitive_conclusion': Kết luận sơ bộ xác định (prob >= 0.75 và đã thu thập đủ 3+ triệu chứng hoặc qua lượt hỏi)
        """
        if is_emergency:
            return "emergency"

        # Nếu đạt ngưỡng cao >= 0.75 và đã có đủ triệu chứng hoặc đã hỏi qua làm rõ
        if top_probability >= self.CONFIDENCE_THRESHOLD_DEFINITIVE and (symptom_count >= self.MIN_SYMPTOMS_FOR_DEFINITIVE or clarification_turns_count >= 1):
            return "definitive_conclusion"

        # Tầng 1: Chỉ sàng lọc ban đầu khi dữ liệu còn quá ít (<= 2 triệu chứng) VÀ xác suất thấp
        if top_probability < self.CONFIDENCE_THRESHOLD_PROVISIONAL and symptom_count <= 2:
            return "initial_screening"

        # Mặc định nằm ở tầng Giả định lâm sàng (Provisional Assumption)
        return "provisional_assumption"

    def _synthesize_hypothesis_question(self, code: str) -> Optional[Dict[str, Any]]:
        """Tự động sinh câu hỏi định hướng theo giả định lâm sàng (Hypothesis-Driven Question) từ ICD-10."""
        info = self.icd_db.get(code, {})
        if not info:
            return None
        name_vi = info.get("name_vi", code)
        cardinal = info.get("cardinal_symptoms", [])
        all_syms = info.get("all_symptoms", [])

        key_signs = [s for s in cardinal if s][:2] or [s for s in all_syms if s][:2]
        other_signs = [s for s in all_syms if s and s not in key_signs][:2]

        options = []
        if key_signs:
            options.append(f"Có biểu hiện đặc trưng: {', '.join(key_signs)}")
        if other_signs:
            options.append(f"Có kèm theo: {', '.join(other_signs)}")
        options.append("Các triệu chứng nhẹ hơn hoặc chỉ thoáng qua")
        options.append("Không có các dấu hiệu đặc thù kể trên")

        return {
            "id": f"q_hypothesis_{code.lower().replace('.', '_')}",
            "question": f"Để làm rõ thêm định hướng về {name_vi}, bạn có xuất hiện các biểu hiện nào dưới đây không?",
            "options": options
        }

    def generate_context_aware_questions(
        self,
        user_text: str,
        detected_symptoms: Optional[List[str]] = None,
        top_disease_codes: Optional[List[str]] = None,
        already_asked_ids: Optional[Set[str]] = None,
        already_asked_texts: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Sinh câu hỏi làm rõ bám sát ngữ cảnh và KHÔNG TRÙNG LẶP với các câu đã hỏi hoặc đã trả lời.
        """
        already_ids: Set[str] = set(already_asked_ids or [])
        asked_texts_lower = [t.lower() for t in (already_asked_texts or [])]
        user_text_lower = (user_text or "").lower()

        text_lower = (user_text or "").lower()
        symptom_str = " ".join([str(s).lower() for s in (detected_symptoms or [])])
        combined = f"{text_lower} {symptom_str}"

        questions: List[Dict[str, Any]] = []

        def is_question_usable(q: Dict[str, Any]) -> bool:
            qid = q.get("id", "")
            if qid in already_ids:
                return False
            qtext = q.get("question", "").lower()
            # Tránh lặp câu hỏi đã từng hỏi trong hội thoại
            for asked in asked_texts_lower:
                if len(asked) > 10 and (asked in qtext or qtext in asked):
                    return False
            # Tránh câu hỏi mà người dùng đã nêu rõ các options trong lời nói
            opts = q.get("options", [])
            answered_opts = sum(1 for opt in opts if len(opt) > 6 and opt.lower() in user_text_lower)
            if answered_opts >= 2:
                return False
            return True

        # 1. Ưu tiên lấy từ ngân hàng câu hỏi chuyên biệt theo mã ICD-10 của bệnh đang dự đoán
        if top_disease_codes:
            for code in top_disease_codes:
                if code in self.DISCRIMINATING_QUESTIONS:
                    for q in self.DISCRIMINATING_QUESTIONS[code]:
                        if is_question_usable(q) and q not in questions and len(questions) < 2:
                            questions.append(q)
                elif code in self.icd_db and len(questions) < 2:
                    dyn_q = self._synthesize_hypothesis_question(code)
                    if dyn_q and is_question_usable(dyn_q) and dyn_q not in questions:
                        questions.append(dyn_q)

        def _match_keywords(text: str, keywords: List[str]) -> bool:
            text_lower = text.lower()
            for kw in keywords:
                kw_clean = kw.strip().lower()
                if not kw_clean:
                    continue
                # Nếu là từ đơn ngắn (<= 5 ký tự), BẮT BUỘC dùng regex \b để tránh khớp nhầm chuỗi con
                # Ví dụ: "ho" KHÔNG ĐƯỢC khớp "hoặc", "khoa học", "kế hoạch"
                # "da" KHÔNG ĐƯỢC khớp "dạ dày", "đang"
                # "tim" KHÔNG ĐƯỢC khớp "tiêm", "tiềm"
                if len(kw_clean.split()) == 1 and len(kw_clean) <= 5:
                    escaped = re.escape(kw_clean)
                    pattern = rf'(?:\b|^){escaped}(?:\b|$)'
                    if re.search(pattern, text_lower):
                        return True
                else:
                    if kw_clean in text_lower:
                        return True
            return False

        # 2. Phân tích theo nhóm cơ quan chức năng
        # A. Tiêu hóa (Dạ dày, ruột, bụng, nôn, ợ chua, tiêu chảy, táo bón)
        if len(questions) < 2 and _match_keywords(combined, ["bụng", "dạ dày", "bao tử", "thượng vị", "ợ chua", "ợ hơi", "buồn nôn", "nôn ói", "tiêu chảy", "đi ngoài", "đầy bụng", "trĩ"]):
            candidates = [
                {
                    "id": "q_stomach_pos",
                    "question": "Cơn đau bụng của bạn tập trung rõ nhất ở khu vực nào?",
                    "options": ["Vùng thượng vị (trên rốn, dưới xương ức)", "Quanh rốn, đau quặn từng cơn", "Bụng dưới bên phải (hố chậu phải)", "Đau âm ỉ khắp toàn bộ ổ bụng"]
                },
                {
                    "id": "q_digestive_associated",
                    "question": "Bạn có gặp các biểu hiện rối loạn tiêu hóa đi kèm dưới đây không?",
                    "options": ["Ợ chua, ợ nóng rát cổ họng", "Buồn nôn hoặc nôn mửa", "Đầy hơi, chướng bụng khó tiêu sau ăn", "Đi ngoài phân lỏng nhiều lần / phân đen"]
                },
                {
                    "id": "q_stomach_meal_relation",
                    "question": "Cơn đau bụng có mối liên hệ như thế nào với bữa ăn?",
                    "options": ["Đau tăng lên khi bụng đói hoặc về đêm", "Đau tức dữ dội sau khi ăn no", "Đau sau khi ăn đồ cay nóng, chua hoặc uống rượu bia", "Đau không phụ thuộc vào bữa ăn"]
                }
            ]
            for c in candidates:
                if is_question_usable(c) and c not in questions and len(questions) < 2:
                    questions.append(c)

        # B. Hô hấp & Tai mũi họng (Ho, đờm, khó thở, thở rít, rát họng, ngạt mũi, viêm phổi)
        if len(questions) < 2 and _match_keywords(combined, ["ho", "đờm", "khó thở", "thở dốc", "khò khè", "rát họng", "đau họng", "ngạt mũi", "sổ mũi", "phổi", "viêm họng", "viêm phế quản"]):
            candidates = [
                {
                    "id": "q_resp_cough_nature",
                    "question": "Cơn ho và đường thở của bạn có đặc điểm nào dưới đây?",
                    "options": ["Ho khan từng cơn gây rát cổ họng", "Ho khạc đờm đặc màu vàng hoặc xanh", "Khó thở, thở dốc khi hít thở sâu hoặc đi lại", "Khò khè, rít đường thở nhiều về đêm / sáng sớm"]
                },
                {
                    "id": "q_resp_ent_signs",
                    "question": "Bạn có xuất hiện các triệu chứng tai mũi họng & toàn thân đi kèm không?",
                    "options": ["Cổ họng sưng đỏ, nuốt đau buốt", "Ngạt mũi, chảy nước mũi trong hoặc đục", "Đau tức thành ngực khi ho hoặc hít sâu", "Sốt nhẹ hoặc ớn lạnh gai người"]
                },
                {
                    "id": "q_resp_duration",
                    "question": "Tình trạng ho và khó thở đã kéo dài bao nhiêu ngày?",
                    "options": ["Mới xuất hiện 1 - 3 ngày nay", "Kéo dài 1 - 2 tuần", "Kéo dài trên 3 tuần dai dẳng", "Tái phát từng đợt theo mùa / thời tiết"]
                }
            ]
            for c in candidates:
                if is_question_usable(c) and c not in questions and len(questions) < 2:
                    questions.append(c)

        # C. Thần kinh & Sọ não (Đau đầu, nhức đầu, chóng mặt, mất ngủ, choáng váng)
        # TUYỆT ĐỐI KHÔNG để "tê bì" ở đây để tránh nhầm tê bì tay chân/rễ thần kinh với đau đầu sọ não
        if len(questions) < 2 and _match_keywords(combined, ["nhức đầu", "đau đầu", "chóng mặt", "hoa mắt", "choáng", "mất ngủ", "buồn ngủ", "đau nửa đầu"]):
            candidates = [
                {
                    "id": "q_neuro_headache_type",
                    "question": "Cơn đau đầu hoặc choáng váng của bạn diễn biến như thế nào?",
                    "options": ["Đau giật nhói theo nhịp mạch ở nửa bên đầu", "Đau căng tức cả hai bên thái dương và trán", "Đau cứng ê ẩm vùng sau gáy lan lên đỉnh đầu", "Cảm giác chao đảo, bồng bềnh, đồ vật xoay tròn"]
                },
                {
                    "id": "q_neuro_alert_signs",
                    "question": "Bạn có các dấu hiệu thần kinh giác quan nào đi kèm dưới đây không?",
                    "options": ["Sợ ánh sáng chói hoặc tiếng động lớn", "Kèm buồn nôn hoặc nôn mửa đột ngột", "Tê bì, châm chích vùng tay chân hoặc mặt", "Nhìn mờ, thấy đốm sáng hoặc bóng đen"]
                },
                {
                    "id": "q_neuro_duration_triggers",
                    "question": "Thời gian mỗi cơn đau đầu kéo dài bao lâu và xuất hiện sau yếu tố nào?",
                    "options": ["Kéo dài từ 4 đến 72 giờ, tăng khi vận động", "Đau âm ỉ cả ngày, tăng khi căng thẳng hoặc thiếu ngủ", "Đau nhói thoáng qua vài phút rồi hết", "Đau liên tục tăng dần không giảm khi uống thuốc"]
                },
                {
                    "id": "q_neuro_history",
                    "question": "Bạn hoặc người thân trong gia đình có tiền sử bệnh lý nào dưới đây không?",
                    "options": ["Bản thân từng nhiều lần bị đau nửa đầu tương tự", "Có người thân (bố mẹ/anh chị em) bị Migraine", "Có tiền sử tăng huyết áp hoặc xoang", "Đây là lần đầu tiên bị cơn đau dữ dội như vậy"]
                }
            ]
            for c in candidates:
                if is_question_usable(c) and c not in questions and len(questions) < 2:
                    questions.append(c)

        # C2. Thần kinh ngoại biên & Chèn ép rễ thần kinh (Tê bì, tê rần, chèn ép rễ cổ/thắt lưng)
        if len(questions) < 2 and _match_keywords(combined, ["tê bì", "tê rần", "tê tay", "tê chân", "châm chích", "mất cảm giác", "yếu cơ"]):
            candidates = [
                {
                    "id": "q_radiculopathy_distribution",
                    "question": "Cảm giác tê bì hoặc châm chích của bạn lan như thế nào và có ảnh hưởng đến vận động không?",
                    "options": [
                        "Tê bì lan từ cổ xuống vai, dọc mặt ngoài cánh tay và các ngón tay",
                        "Tê râm ran các đầu ngón tay, ngón chân như kiến bò",
                        "Tê bì kèm yếu sức cơ, cảm giác vụng về hoặc dễ đánh rơi đồ vật",
                        "Chỉ tê mỏi thoáng qua khi ngồi tì đè lâu một chỗ"
                    ]
                }
            ]
            for c in candidates:
                if is_question_usable(c) and c not in questions and len(questions) < 2:
                    questions.append(c)

        # D. Mắt & Thị giác (Chuyên khoa Mắt, Khúc xạ, Khô mắt, Mỏi mắt)
        if len(questions) < 2 and _match_keywords(combined, ["mắt", "thị giác", "nhìn mờ", "thị lực", "mỏi mắt", "khô mắt", "cộm mắt", "nhức mắt", "đau mắt", "đỏ mắt", "điều tiết", "cận thị", "lão thị"]):
            candidates = [
                {
                    "id": "q_eye_symptoms",
                    "question": "Cảm giác khó chịu và biểu hiện tại mắt của bạn diễn ra như thế nào?",
                    "options": [
                        "Mỏi mắt, căng tức vùng mắt khi nhìn màn hình/đọc sách lâu",
                        "Khô rát, cộm xốn như có hạt cát hoặc dị vật trong mắt",
                        "Mắt nhìn mờ nhòe, dao động lúc rõ lúc mờ",
                        "Đau nhức mắt, sợ ánh sáng hoặc đỏ mắt chảy nước mắt"
                    ]
                },
                {
                    "id": "q_eye_vision_impact",
                    "question": "Tầm nhìn và thị lực của bạn có đặc điểm nào dưới đây?",
                    "options": [
                        "Nhìn gần mờ, phải đưa sách hoặc điện thoại ra xa mới đọc được",
                        "Nhìn xa bị nhòe mờ, phải nheo mắt mới nhìn rõ",
                        "Thị lực bình thường, chỉ mỏi mệt khi làm việc điều tiết nhiều",
                        "Mắt bị hoa mắt, nhìn đôi hoặc thấy quầng sáng"
                    ]
                },
                {
                    "id": "q_eye_habits",
                    "question": "Tình trạng mỏi và khó chịu ở mắt xuất hiện nhiều nhất trong hoàn cảnh nào?",
                    "options": [
                        "Sau nhiều giờ làm việc liên tục với máy tính, điện thoại",
                        "Đi ngoài trời gió bụi, nắng gắt hoặc ngồi phòng điều hòa máy lạnh",
                        "Vào buổi chiều tối sau một ngày làm việc căng thẳng",
                        "Xuất hiện liên tục cả ngày dù đã nghỉ ngơi nhắm mắt"
                    ]
                }
            ]
            for c in candidates:
                if is_question_usable(c) and c not in questions and len(questions) < 2:
                    questions.append(c)

        # E. Da liễu & Dị ứng
        derma_keywords = ["ngứa", "nổi mẩn", "rát da", "đỏ da", "phát ban", "mề đay", "dị ứng da", "mụn nước", "sẩn ngứa", "mẩn đỏ", "da"]
        if len(questions) < 2 and _match_keywords(combined, derma_keywords):
            candidates = [
                {
                    "id": "q_derma_sensation",
                    "question": "Cảm giác và hình thái tổn thương trên bề mặt da của bạn thế nào?",
                    "options": ["Ngứa ngáy dữ dội, cào gãi không đỡ", "Căng rát, đỏ ửng bề mặt da", "Nổi sẩn cộm phù nề hoặc mảng mề đay", "Có mụn nước li ti, trợt loét chảy dịch"]
                },
                {
                    "id": "q_derma_triggers",
                    "question": "Tổn thương da xuất hiện sau khi tiếp xúc với yếu tố nào dưới đây?",
                    "options": ["Dùng mỹ phẩm, sữa rửa mặt hoặc thuốc bôi mới", "Ăn hải sản, đồ tanh hoặc thức ăn lạ", "Tiếp xúc trực tiếp ánh nắng gắt / nguồn nước lạ", "Tự nhiên bùng phát, không rõ nguyên nhân tiếp xúc"]
                }
            ]
            for c in candidates:
                if is_question_usable(c) and c not in questions and len(questions) < 2:
                    questions.append(c)

        # E. Tim mạch & Lồng ngực
        if len(questions) < 2 and _match_keywords(combined, ["ngực", "tức ngực", "đau ngực", "tim", "hồi hộp", "đánh trống ngực", "nhịp tim"]):
            candidates = [
                {
                    "id": "q_cardio_pain_type",
                    "question": "Tính chất cơn đau tức ngực và hướng lan của bạn như thế nào?",
                    "options": ["Đau thắt bóp nghẹt sau xương ức", "Đau lan lên cổ, cằm hoặc cánh tay trái", "Đau nhói thoáng qua khi ấn vào thành ngực", "Cảm giác tim đập nhanh hồi hộp, thình thịch"]
                },
                {
                    "id": "q_cardio_warning_signs",
                    "question": "Bạn có gặp các dấu hiệu tuần hoàn đi kèm nào sau đây không?",
                    "options": ["Vã mồ hôi lạnh, bồn chồn lo lắng", "Khó thở hụt hơi khi đi lại hoặc leo cầu thang", "Cảm giác choáng váng, xây xẩm muốn ngất", "Không kèm vã mồ hôi hay khó thở"]
                }
            ]
            for c in candidates:
                if is_question_usable(c) and c not in questions and len(questions) < 2:
                    questions.append(c)

        # F. Sốt & Toàn thân (Bao gồm câu hỏi giai đoạn 1, 2 và phân tầng loại trừ cờ đỏ)
        if len(questions) < 2 and _match_keywords(combined, ["sốt", "nóng", "ớn lạnh", "rét", "uể oải", "mệt mỏi"]):
            candidates = [
                {
                    "id": "q_fever_pattern",
                    "question": "Thân nhiệt và tính chất cơn sốt của bạn như thế nào?",
                    "options": ["Sốt cao liên tục trên 38.5°C, khó hạ sốt", "Sốt theo cơn có kèm cảm giác rét run", "Sốt nhẹ âm ỉ về chiều và tối", "Người mệt mỏi rã rời, đau nhức mình mẩy"]
                },
                {
                    "id": "q_fever_days",
                    "question": "Bạn đã bị sốt được bao nhiêu ngày và có dùng thuốc hạ sốt chưa?",
                    "options": ["Mới sốt trong 24 giờ qua", "Đã sốt 2 - 3 ngày liên tục", "Uống Paracetamol có hạ nhưng sau đó sốt lại", "Chưa dùng bất kỳ loại thuốc nào"]
                },
                {
                    "id": "q_fever_associated_signs",
                    "question": "Bên cạnh sốt và mệt mỏi, bạn có xuất hiện các triệu chứng toàn thân nào dưới đây không?",
                    "options": [
                        "Đau nhức cơ bắp ê ẩm toàn thân, đau sâu sau hai hốc mắt",
                        "Ho khan rát họng, ngạt mũi hoặc chảy nước mũi trong",
                        "Đau tức vùng bụng, buồn nôn hoặc chán ăn rõ rệt",
                        "Không có triệu chứng nào khác, chỉ sốt và mệt rã rời"
                    ]
                },
                {
                    "id": "q_fever_danger_dengue",
                    "question": "Để theo dõi an toàn và phân biệt Sốt xuất huyết / Cúm, bạn có dấu hiệu nào sau đây?",
                    "options": [
                        "Không có nốt xuất huyết dưới da, không chảy máu cam / chân răng",
                        "Có chấm đỏ li ti xuất huyết dưới da hoặc chảy máu niêm mạc",
                        "Đau tức dữ dội vùng hạ sườn phải, nôn nhiều liên tục",
                        "Người li bì, lừ đừ, chân tay lạnh ẩm hoặc khó thở"
                    ]
                }
            ]
            for c in candidates:
                if is_question_usable(c) and c not in questions and len(questions) < 2:
                    questions.append(c)

        # G. Cơ Xương Khớp, Cột sống & Vai gáy (CHỈ KÍCH HOẠT KHI CÓ TRIỆU CHỨNG GIẢI PHẪU RÕ RÀNG)
        # TUYỆT ĐỐI KHÔNG dùng từ đơn "mỏi" hoặc "ê ẩm" vì "mệt mỏi / ê ẩm mình mẩy" là triệu chứng toàn thân do sốt/nhiễm trùng
        ortho_keywords = [
            "cổ vai gáy", "đau cổ", "mỏi cổ", "vai gáy", "đau vai", "cột sống", "đau lưng", "mỏi lưng",
            "thắt lưng", "thoái hóa cổ", "thoát vị", "cứng cổ", "đau khớp", "sưng khớp", "gút", "viêm khớp"
        ]
        if len(questions) < 2 and _match_keywords(combined, ortho_keywords):
            candidates = self.DISCRIMINATING_QUESTIONS.get("M47.9", [])
            for c in candidates:
                if is_question_usable(c) and c not in questions and len(questions) < 2:
                    questions.append(c)

        # H. Dynamic Follow-up: Nếu các câu hỏi chuyên biệt đã hết
        if not questions:
            clean_symptoms = [str(s).strip() for s in (detected_symptoms or []) if str(s).strip()]
            if clean_symptoms:
                snippet_label = f'"{", ".join(clean_symptoms[:2])}"'
            else:
                snippet_label = "triệu chứng khó chịu bạn vừa chia sẻ"

            fallback_candidates = [
                {
                    "id": "q_dynamic_duration_stage2",
                    "question": f"Về biểu hiện {snippet_label}, tình trạng này kéo dài bao lâu và diễn biến theo xu hướng nào?",
                    "options": ["Mới xuất hiện đột ngột trong 24 giờ qua", "Kéo dài từ 2 đến 3 ngày nay", "Kéo dài trên 1 tuần và tái phát nhiều lần", "Triệu chứng đang có chiều hướng tăng nặng dần"]
                },
                {
                    "id": "q_dynamic_medication_response",
                    "question": "Bạn đã sử dụng biện pháp hoặc thuốc nào để xử trí và có đỡ không?",
                    "options": ["Đã uống thuốc giảm đau / hạ sốt thông thường nhưng không đỡ", "Có đỡ một phần khi nghỉ ngơi tĩnh dưỡng", "Chưa dùng bất kỳ loại thuốc hay biện pháp nào", "Triệu chứng tăng lên khi tiếp tục làm việc"]
                }
            ]
            for fc in fallback_candidates:
                if is_question_usable(fc) and len(questions) < 2:
                    questions.append(fc)

        return questions[:2]

    def generate_clarification_questions(
        self,
        probabilities: np.ndarray,
        disease_classes: List[Dict[str, Any]],
        known_symptoms: List[str],
        user_text: str = "",
        already_asked_ids: Optional[Set[str]] = None,
        already_asked_texts: Optional[List[str]] = None,
        clarification_turns_count: int = 0
    ) -> Dict[str, Any]:
        """
        Đánh giá độ tin cậy và sinh câu hỏi làm rõ lâm sàng bám sát ngữ cảnh người dùng.
        """
        max_prob = float(np.max(probabilities)) if len(probabilities) > 0 else 0.0
        entropy = self.calculate_entropy(probabilities) if len(probabilities) > 0 else 0.0

        stage = self.determine_clinical_stage(
            top_probability=max_prob,
            symptom_count=len(known_symptoms),
            clarification_turns_count=clarification_turns_count
        )

        needs_clarification = (stage != "definitive_conclusion")

        # Lấy top các bệnh đang cạnh tranh xác suất
        top_indices = np.argsort(probabilities)[::-1][:2] if len(probabilities) > 0 else []
        top_codes = []
        for idx in top_indices:
            if idx < len(disease_classes) and float(probabilities[idx]) > 0.0:
                code = disease_classes[idx].get("code")
                if code:
                    top_codes.append(code)

        questions = []
        if needs_clarification:
            questions = self.generate_context_aware_questions(
                user_text=user_text,
                detected_symptoms=known_symptoms,
                top_disease_codes=top_codes,
                already_asked_ids=already_asked_ids,
                already_asked_texts=already_asked_texts
            )

        return {
            "needs_clarification": needs_clarification,
            "clinical_stage": stage,
            "confidence_score": round(max_prob, 3),
            "entropy": round(entropy, 3),
            "reason": (
                "Chưa đủ dữ liệu đặc hiệu để chẩn đoán sơ bộ." if stage == "initial_screening"
                else "Đang ở mức Giả định lâm sàng (Provisional Hypothesis). Cần đặt thêm câu hỏi phân biệt để làm rõ bệnh án." if stage == "provisional_assumption"
                else "Đã thu thập đủ căn cứ lâm sàng để đưa ra Kết luận sơ bộ xác định."
            ),
            "questions": questions
        }

clarification_engine = ClarificationEngine()
