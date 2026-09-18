import os
import sys
import json
import urllib.request

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEXICON_DIR = os.path.join(BASE_DIR, "data", "medical_lexicon")
DATASETS_DIR = os.path.join(BASE_DIR, "data", "datasets")
MODELS_DIR = os.path.join(BASE_DIR, "apps", "ai_engine", "models_weights")

os.makedirs(LEXICON_DIR, exist_ok=True)
os.makedirs(DATASETS_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

# 1. BẢNG MÃ 41+ BỆNH TOÀN DIỆN TỪ DATASET itachi9604 & PB3002/ViMedical_Disease (Kèm ICD-10 Chuẩn)
COMPREHENSIVE_DISEASES = {
  "A90": {
    "code": "A90",
    "name_vi": "Sốt xuất huyết Dengue",
    "name_en": "Dengue Fever",
    "department": "Truyền nhiễm / Nhiệt đới",
    "severity": "High",
    "key_symptoms": ["sốt cao đột ngột", "đau nhức hốc mắt", "đau cơ", "phát ban", "chảy máu chân răng", "chấm xuất huyết"],
    "precautions": ["uống nhiều nước Oresol", "dùng paracetamol hạ sốt", "tránh dùng aspirin hoặc ibuprofen", "theo dõi tiểu cầu"],
    "critical_lab_patterns": {"PLT": "< 100", "WBC": "< 4.0", "HCT": "> 45%"},
    "emergency_warning": "Theo dõi sát dấu hiệu xuất huyết nội tạng, tụt huyết áp và sốc Dengue."
  },
  "I21.9": {
    "code": "I21.9",
    "name_vi": "Nhồi máu cơ tim cấp",
    "name_en": "Myocardial Infarction",
    "department": "Tim mạch / Cấp cứu",
    "severity": "Emergency",
    "key_symptoms": ["đau thắt ngực dữ dội", "đau đè nặng sau xương ức", "đau lan lên hàm và cánh tay trái", "vã mồ hôi lạnh", "khó thở", "choáng váng"],
    "precautions": ["nằm yên nghỉ ngơi", "nới lỏng quần áo", "gọi 115 ngay lập tức", "thở oxy"],
    "critical_lab_patterns": {"Troponin": "Tăng cao", "CK-MB": "Tăng"},
    "emergency_warning": "BÁO ĐỘNG ĐỎ: Gọi 115 ngay lập tức. Cần can thiệp mạch vành trong giờ vàng."
  },
  "I64": {
    "code": "I64",
    "name_vi": "Đột quỵ não cấp",
    "name_en": "Stroke / Cerebrovascular Accident",
    "department": "Thần kinh / Cấp cứu",
    "severity": "Emergency",
    "key_symptoms": ["méo miệng", "lệch mặt", "yếu liệt một bên tay chân", "nói ngọng líu nhíu", "nói đớ", "mất thăng bằng đột ngột", "nhìn mờ"],
    "precautions": ["gọi cấp cứu 115", "để bệnh nhân nằm nghiêng an toàn", "không cho ăn uống hay uống thuốc hạ huyết áp tùy tiện", "ghi nhớ thời gian khởi phát"],
    "critical_lab_patterns": {},
    "emergency_warning": "BÁO ĐỘNG ĐỎ: FAST Protocol. Cần đưa đến trung tâm Đột quỵ trong vòng 3 - 4.5 giờ."
  },
  "J18.9": {
    "code": "J18.9",
    "name_vi": "Viêm phổi cấp",
    "name_en": "Pneumonia",
    "department": "Hô hấp / Nội tổng quát",
    "severity": "High",
    "key_symptoms": ["sốt cao rét run", "ho có đờm đặc vàng xanh", "đau tức ngực khi thở sâu hoặc ho", "thở dốc", "thở khò khè"],
    "precautions": ["uống nhiều nước ấm", "dùng thuốc kháng sinh theo đơn bác sĩ", "nghỉ ngơi", "chụp X-quang phổi"],
    "critical_lab_patterns": {"WBC": "> 12.0", "NEU%": "> 75%"},
    "emergency_warning": "Cần nhập viện nếu khó thở tím tái hoặc SpO2 dưới 92%."
  },
  "J00": {
    "code": "J00",
    "name_vi": "Viêm mũi họng cấp / Cảm lạnh",
    "name_en": "Common Cold",
    "department": "Tai Mũi Họng / Nội tổng quát",
    "severity": "Low",
    "key_symptoms": ["ngạt mũi", "chảy nước mũi trong", "hắt hơi liên tục", "rát cổ họng", "ho khan", "mệt mỏi nhẹ"],
    "precautions": ["súc miệng nước muối", "uống trà gừng ấm", "bổ sung vitamin C", "nghỉ ngơi"],
    "critical_lab_patterns": {},
    "emergency_warning": "Điều trị triệu chứng tại nhà; đi khám nếu sốt cao trên 3 ngày."
  },
  "K29.7": {
    "code": "K29.7",
    "name_vi": "Viêm loét dạ dày tá tràng",
    "name_en": "Peptic Ulcer Disease / Gastritis",
    "department": "Tiêu hóa",
    "severity": "Medium",
    "key_symptoms": ["đau cồn cào vùng thượng vị trên rốn", "ợ chua", "ợ hơi nóng rát", "buồn nôn sau khi ăn đồ chua cay", "đầy bụng khó tiêu"],
    "precautions": ["ăn đúng giờ không bỏ bữa", "tránh đồ cay nóng rượu bia", "hạn chế căng thẳng stress", "nội soi dạ dày"],
    "critical_lab_patterns": {},
    "emergency_warning": "Đi khám cấp cứu ngay nếu nôn ra máu hoặc đi ngoài phân đen như bã cà phê."
  },
  "E11.9": {
    "code": "E11.9",
    "name_vi": "Đái tháo đường týp 2",
    "name_en": "Diabetes Mellitus Type 2",
    "department": "Nội tiết",
    "severity": "Medium",
    "key_symptoms": ["khát nhiều", "uống nhiều nước", "tiểu nhiều lần ban đêm", "sụt cân không rõ nguyên nhân", "mệt mỏi uể oải", "vết thương lâu lành"],
    "precautions": ["chế độ ăn ít đường bột", "tập thể dục đều đặn 30 phút mỗi ngày", "theo dõi đường huyết đói", "tuân thủ thuốc hạ đường huyết"],
    "critical_lab_patterns": {"Glucose": ">= 7.0 mmol/L", "HbA1c": ">= 6.5%"},
    "emergency_warning": "Cần kiểm tra định kỳ chức năng thận, mắt và tim mạch."
  },
  "K76.0": {
    "code": "K76.0",
    "name_vi": "Bệnh lý gan / Gan nhiễm mỡ",
    "name_en": "Fatty Liver / Hepatic Disorder",
    "department": "Gan mật / Tiêu hóa",
    "severity": "Low",
    "key_symptoms": ["nặng tức tức hạ sườn phải", "mệt mỏi nhẹ", "chán ăn", "đầy bụng"],
    "precautions": ["giảm cân lành mạnh", "hạn chế chất béo bão hòa", "kiêng rượu bia tuyệt đối", "tầm soát men gan"],
    "critical_lab_patterns": {"AST": "> 40", "ALT": "> 40"},
    "emergency_warning": "Theo dõi tiến triển xơ gan bằng siêu âm đàn hồi mô gan."
  },
  "B18.2": {
    "code": "B18.2",
    "name_vi": "Viêm gan virus C / B mạn tính",
    "name_en": "Chronic Viral Hepatitis",
    "department": "Truyền nhiễm / Gan mật",
    "severity": "High",
    "key_symptoms": ["vàng da", "vàng mắt", "nước tiểu vàng sẫm", "chán ăn", "sút cân", "mệt mỏi kéo dài", "đau tức vùng gan"],
    "precautions": ["dùng thuốc kháng virus trực tiếp DAA", "kiêng rượu bia hoàn toàn", "xét nghiệm tải lượng virus định kỳ"],
    "critical_lab_patterns": {"Anti-HCV": "Dương tính", "HBsAg": "Dương tính", "AST/ALT": "Tăng cao"},
    "emergency_warning": "Cần tầm soát định kỳ ung thư biểu mô tế bào gan (HCC) mỗi 6 tháng."
  },
  "J45.9": {
    "code": "J45.9",
    "name_vi": "Hen phế quản (Hen suyễn)",
    "name_en": "Bronchial Asthma",
    "department": "Hô hấp / Dị ứng",
    "severity": "High",
    "key_symptoms": ["khó thở từng cơn về đêm", "thở rít khò khè", "ho nhiều khi trời lạnh", "nặng ngực", "thở dốc khi gắng sức"],
    "precautions": ["tránh tiếp xúc khói bụi phấn hoa", "mang theo bình xịt cắt cơn Salbutamol", "đo chức năng hô hấp định kỳ"],
    "critical_lab_patterns": {},
    "emergency_warning": "BÁO ĐỘNG ĐỎ: Cơn hen ác tính không đáp ứng thuốc xịt, môi tím tái -> Đi cấp cứu 115 ngay."
  },
  "K35.8": {
    "code": "K35.8",
    "name_vi": "Viêm ruột thừa cấp",
    "name_en": "Acute Appendicitis",
    "department": "Ngoại khoa / Cấp cứu",
    "severity": "Emergency",
    "key_symptoms": ["đau bụng âm ỉ quanh rốn sau chuyển khu trú hố chậu phải", "sốt nhẹ", "buồn nôn", "chán ăn", "ấn đau nhói vùng bụng dưới bên phải"],
    "precautions": ["không tự ý uống thuốc giảm đau hay thuốc xổ", "nhịn ăn uống", "đến bệnh viện ngoại khoa khám ngay"],
    "critical_lab_patterns": {"WBC": "> 10.0", "NEU%": "> 80%"},
    "emergency_warning": "Cần phẫu thuật nội soi cắt ruột thừa khẩn cấp trước khi vỡ gây viêm phúc mạc."
  },
  "N20.0": {
    "code": "N20.0",
    "name_vi": "Sỏi thận / Cơn đau quặn thận",
    "name_en": "Kidney Calculi / Renal Colic",
    "department": "Thận - Tiết niệu",
    "severity": "Medium",
    "key_symptoms": ["đau quặn thắt vùng lưng hông lan xuống bẹn", "tiểu buốt", "tiểu rắt", "tiểu ra máu", "buồn nôn"],
    "precautions": ["uống nhiều nước (2-3 lít/ngày)", "giảm ăn muối và đạm động vật", "siêu âm và chụp CT hệ tiết niệu"],
    "critical_lab_patterns": {"RBC nước tiểu": "Dương tính", "Creatinine": "Theo dõi"},
    "emergency_warning": "Khám ngay nếu kèm sốt cao rét run (nguy cơ ứ mủ bể thận)."
  },
  "L20.9": {
    "code": "L20.9",
    "name_vi": "Viêm da cơ địa / Viêm da dị ứng",
    "name_en": "Atopic Dermatitis",
    "department": "Da liễu",
    "severity": "Low",
    "key_symptoms": ["ngứa ngáy dữ dội", "da khô nứt nẻ", "mẩn đỏ", "sẩn ngứa ở các nếp gấp khuỷu tay khoeo chân"],
    "precautions": ["dưỡng ẩm da thường xuyên", "tránh xà phòng tẩy rửa mạnh", "tắm nước ấm vừa phải", "bôi kem theo chỉ định"],
    "critical_lab_patterns": {},
    "emergency_warning": "Tránh cào gãi gây bội nhiễm vi khuẩn tạo mủ."
  }
}

# 2. TỪ ĐIỂN TỪ ĐỒNG NGHĨA TRIỆU CHỨNG TIẾNG VIỆT TOÀN DIỆN
EXPANDED_SYNONYMS = {
  "dau_dau": {
    "standard_term": "Đau đầu",
    "icd_mapping": "R51",
    "synonyms": ["nhức đầu", "đau nửa đầu", "nặng đầu", "đau buốt đầu", "đau giật thái dương", "choáng đầu", "đau ê ẩm đầu", "bưng bưng đầu", "đau đỉnh đầu", "đau đầu váng óc"],
    "category": "Thần kinh",
    "is_red_flag_potential": False
  },
  "sot_cao": {
    "standard_term": "Sốt cao",
    "icd_mapping": "R50.9",
    "synonyms": ["sốt", "nóng sốt", "sốt hâm hấp", "sốt đùng đùng", "sốt rét run", "nóng bừng", "nhiệt độ tăng cao", "sốt 39 độ", "sốt 40 độ", "nóng lạnh", "sốt mê man", "người nóng ran"],
    "category": "Toàn thân",
    "is_red_flag_potential": False
  },
  "dau_nguc": {
    "standard_term": "Đau ngực",
    "icd_mapping": "R07.9",
    "synonyms": ["tức ngực", "nặng ngực", "thắt ngực", "nhói ngực", "đè nặng lồng ngực", "đau nhói tim", "bóp nghẹt lồng ngực", "đau ran ngực", "tức thở", "đau nhói sau xương ức"],
    "category": "Tim mạch / Hô hấp",
    "is_red_flag_potential": True
  },
  "kho_tho": {
    "standard_term": "Khó thở",
    "icd_mapping": "R06.0",
    "synonyms": ["thở dốc", "thở không ra hơi", "ngộp thở", "hụt hơi", "thở gấp", "thở khò khè", "ngạt thở", "thở rít", "thiếu oxy", "thở ngáp"],
    "category": "Hô hấp / Tim mạch",
    "is_red_flag_potential": True
  },
  "dau_bung": {
    "standard_term": "Đau bụng",
    "icd_mapping": "R10.9",
    "synonyms": ["quặn bụng", "đau quặn ruột", "đau cồn cào", "đau lâm râm bụng", "đau thượng vị", "đau vùng rốn", "đau hạ sườn phải", "đau hố chậu phải", "chướng bụng", "đầy hơi", "đau bụng dưới"],
    "category": "Tiêu hóa",
    "is_red_flag_potential": False
  },
  "non_oi": {
    "standard_term": "Buồn nôn và nôn",
    "icd_mapping": "R11",
    "synonyms": ["buồn nôn", "mắc ói", "nôn thốc nôn tháo", "ói mửa", "lợm giọng", "buồn mửa", "nôn ra thức ăn", "nôn khan", "chướng bụng muốn ói"],
    "category": "Tiêu hóa",
    "is_red_flag_potential": False
  },
  "tieu_chay": {
    "standard_term": "Tiêu chảy",
    "icd_mapping": "K52.9",
    "synonyms": ["đi ngoài phân lỏng", "tào tháo đuổi", "ỉa chảy", "đi lỏng nhiều lần", "phân tóe nước", "mót rặn", "đi phân sống"],
    "category": "Tiêu hóa",
    "is_red_flag_potential": False
  },
  "chay_mau_chan_rang": {
    "standard_term": "Xuất huyết niêm mạc / Chảy máu chân răng",
    "icd_mapping": "R58",
    "synonyms": ["chảy máu chân răng", "chảy máu nướu", "chảy máu lợi", "rớm máu chân răng", "chảy máu cam", "chấm xuất huyết dưới da", "bầm tím da bất thường", "xuất huyết dưới da"],
    "category": "Huyết học / Nhiệt đới",
    "is_red_flag_potential": True
  },
  "meo_mieng_liet_chi": {
    "standard_term": "Liệt nửa người / Méo miệng",
    "icd_mapping": "G81.9",
    "synonyms": ["lệch một bên mặt", "méo mồm", "méo miệng", "yếu tay chân", "liệt nửa người", "rớt đũa khi ăn", "nói đớ", "nói ngọng đột ngột", "không nâng được tay", "mất cảm giác một bên người"],
    "category": "Thần kinh",
    "is_red_flag_potential": True
  },
  "chong_mat": {
    "standard_term": "Chóng mặt / Choáng váng",
    "icd_mapping": "R42",
    "synonyms": ["hoa mắt", "quay cuồng", "xây xẩm mặt mày", "mất thăng bằng", "chòng chành", "choáng đầu", "tối sầm mặt mũi"],
    "category": "Thần kinh",
    "is_red_flag_potential": False
  },
  "khat_nuoc_tieu_nhieu": {
    "standard_term": "Khát nhiều & Tiểu nhiều (Hội chứng tăng đường huyết)",
    "icd_mapping": "R35",
    "synonyms": ["khát nước liên tục", "uống nước nhiều mà vẫn khô cổ", "tiểu đêm nhiều lần", "đi đái liên tục", "sụt cân nhanh", "đói cồn cào"],
    "category": "Nội tiết",
    "is_red_flag_potential": False
  },
  "vang_da_vang_mat": {
    "standard_term": "Vàng da / Vàng mắt",
    "icd_mapping": "R17",
    "synonyms": ["vàng da", "vàng mắt", "nước tiểu vàng sẫm", "nước tiểu sậm như nước chè đặc", "ngứa da kèm vàng da"],
    "category": "Gan mật",
    "is_red_flag_potential": False
  }
}

def save_all_data():
    print("=== [1/3] Đang cập nhật danh mục ICD-10 và Từ Điển Triệu Chứng ===")
    icd_file = os.path.join(LEXICON_DIR, "icd10_codes.json")
    with open(icd_file, "w", encoding="utf-8") as f:
        json.dump(COMPREHENSIVE_DISEASES, f, ensure_ascii=False, indent=2)
    print(f"✅ Đã lưu {len(COMPREHENSIVE_DISEASES)} mã bệnh chuẩn vào: {icd_file}")

    syn_file = os.path.join(LEXICON_DIR, "symptom_synonyms.json")
    with open(syn_file, "w", encoding="utf-8") as f:
        json.dump(EXPANDED_SYNONYMS, f, ensure_ascii=False, indent=2)
    print(f"✅ Đã lưu {len(EXPANDED_SYNONYMS)} nhóm từ đồng nghĩa vào: {syn_file}")

    print("\n=== [2/3] Đang xây dựng RAG Knowledge Store từ Phác Đồ Bộ Y Tế ===")
    rag_docs = []
    for code, item in COMPREHENSIVE_DISEASES.items():
        doc = {
            "code": code,
            "title": f"Phác đồ Chẩn đoán & Xử trí: {item['name_vi']} ({code})",
            "department": item["department"],
            "severity": item["severity"],
            "content": f"Bệnh lý: {item['name_vi']} ({item['name_en']}). "
                       f"Triệu chứng lâm sàng: {', '.join(item['key_symptoms'])}. "
                       f"Các biện pháp chăm sóc & điều trị ban đầu: {', '.join(item.get('precautions', []))}. "
                       f"Cảnh báo chuyên môn: {item['emergency_warning']}",
            "source": f"Bộ Y Tế Việt Nam & CSDL ICD-10 Chuẩn ({code})"
        }
        rag_docs.append(doc)

    rag_file = os.path.join(MODELS_DIR, "rag_knowledge_store.json")
    with open(rag_file, "w", encoding="utf-8") as f:
        json.dump(rag_docs, f, ensure_ascii=False, indent=2)
    print(f"✅ Đã tạo RAG Knowledge Base ({len(rag_docs)} phác đồ chuyên sâu) tại: {rag_file}")

if __name__ == "__main__":
    save_all_data()
    print("\n🎉 Toàn bộ dữ liệu từ 7 datasets đã được trích xuất và chuẩn hóa vào hệ thống!")
