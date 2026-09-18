import os
import json
import random
import logging
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_symptoms(icd10_path: str) -> List[str]:
    """Trích xuất danh sách triệu chứng độc nhất từ file icd10.json."""
    logger.info(f"Đọc dữ liệu từ {icd10_path}")
    symptoms = set()
    with open(icd10_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        for disease in data.get('diseases', []):
            for sym in disease.get('symptoms', []):
                name = sym.get('symptom_name', '').strip().lower()
                if name and len(name) > 2:
                    symptoms.add(name)
                # Có thể lấy thêm mô tả nếu ngắn gọn
                desc = sym.get('description', '').strip().lower()
                if desc and 5 < len(desc.split()) < 15: # Lấy mô tả có độ dài vừa phải
                    symptoms.add(desc)
    
    symptoms_list = list(symptoms)
    logger.info(f"Đã trích xuất {len(symptoms_list)} triệu chứng độc nhất.")
    return symptoms_list

def generate_synthetic_data(symptoms: List[str], num_samples: int = 50000) -> List[Dict[str, Any]]:
    """Tạo ngữ liệu huấn luyện BIO bằng templates."""
    
    durations = [
        "từ hôm qua", "3 ngày nay", "khoảng 1 tuần rồi", "mấy hôm nay", "từ sáng", 
        "hơn 2 tháng", "suốt đêm qua", "mới bị lúc nãy", "kéo dài cả tuần", "từ chiều qua"
    ]
    vitals = [
        "sốt 39 độ", "sốt 38.5 độ C", "huyết áp 150/90", "nhịp tim 110", "SpO2 92%", 
        "nhiệt độ 39.5", "huyết áp tụt 90/60", "sốt cao 40 độ"
    ]
    prefixes = ["Bác sĩ ơi, ", "Chào bác sĩ, ", "Em bị ", "Tôi cảm thấy ", "Bệnh nhân có biểu hiện ", "Cháu nó bị ", "Dạ, ", "Tự nhiên tôi bị ", ""]
    
    # Định nghĩa các template sinh dữ liệu
    templates = [
        # Template 1: Chỉ có 1 triệu chứng
        {"text": "{prefix}{S1}", "entities": ["S1"]},
        # Template 2: Triệu chứng + Thời gian
        {"text": "{prefix}{S1} {D}", "entities": ["S1", "D"]},
        # Template 3: 2 triệu chứng
        {"text": "{prefix}{S1} kèm theo {S2}", "entities": ["S1", "S2"]},
        {"text": "{prefix}{S1} và {S2}", "entities": ["S1", "S2"]},
        # Template 4: Triệu chứng + Sinh hiệu
        {"text": "{prefix}{S1}, đo thấy {V}", "entities": ["S1", "V"]},
        # Template 5: 2 triệu chứng + Thời gian
        {"text": "{prefix}{S1} và {S2} {D}", "entities": ["S1", "S2", "D"]},
        # Template 6: Phủ định (Negation)
        {"text": "{prefix}{S1} nhưng không bị {S_NEG}", "entities": ["S1"]}, 
        {"text": "{prefix}{S1}, hoàn toàn không thấy {S_NEG}", "entities": ["S1"]},
    ]
    
    dataset = []
    
    for _ in range(num_samples):
        template = random.choice(templates)
        prefix = random.choice(prefixes)
        
        s1 = random.choice(symptoms)
        s2 = random.choice(symptoms)
        while s2 == s1:
            s2 = random.choice(symptoms)
            
        s_neg = random.choice(symptoms)
        d = random.choice(durations)
        v = random.choice(vitals)
        
        text = template["text"].replace("{prefix}", prefix).replace("{S1}", s1).replace("{S2}", s2).replace("{D}", d).replace("{V}", v).replace("{S_NEG}", s_neg)
        
        # Bắt đầu tìm vị trí các thực thể để gán nhãn
        entities = []
        
        if "S1" in template["entities"]:
            entities.append({"text": s1, "label": "SYMPTOM"})
        if "S2" in template["entities"]:
            entities.append({"text": s2, "label": "SYMPTOM"})
        if "D" in template["entities"]:
            entities.append({"text": d, "label": "DURATION"})
        if "V" in template["entities"]:
            # Phân tách VITAL nếu cần (ở đây gán cứng cả cụm là VITAL để đơn giản)
            entities.append({"text": v, "label": "VITAL"})
            
        # Lọc bỏ nếu text bị rỗng hoặc lỗi
        if text.strip():
            # Xử lý viết hoa chữ cái đầu tiên cho tự nhiên
            text = text[0].upper() + text[1:]
            dataset.append({
                "text": text,
                "entities": entities
            })
            
    logger.info(f"Đã sinh thành công {len(dataset)} mẫu câu huấn luyện.")
    return dataset

def main():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    icd10_path = os.path.join(base_dir, "data", "sic", "icd10.json")
    output_dir = os.path.join(base_dir, "data", "datasets")
    
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "phobert_synthetic_ner.json")
    
    if not os.path.exists(icd10_path):
        logger.error(f"Không tìm thấy file {icd10_path}")
        return
        
    symptoms = load_symptoms(icd10_path)
    
    if not symptoms:
        logger.error("Không tìm thấy triệu chứng nào.")
        return
        
    dataset = generate_synthetic_data(symptoms, num_samples=50000)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
        
    logger.info(f"Đã lưu bộ dữ liệu tại: {output_path}")

if __name__ == "__main__":
    main()
