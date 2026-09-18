import re
import unicodedata
from typing import Dict, Any, List

def remove_diacritics(text: str) -> str:
    text = unicodedata.normalize('NFD', text)
    text = re.sub(r'[\u0300-\u036f]', '', text)
    return text.replace('đ', 'd').replace('Đ', 'D')

sample_ocr_texts = """
BỆNH VIỆN ĐA KHOA QUỐC TẾ
PHIẾU KẾT QUẢ XÉT NGHIỆM HUYẾT HỌC & SINH HÓA
1. Số lượng Bạch cầu (WBC): 12.5 G/L    (BT: 4.0 - 10.0)
2. Số lượng Tiểu cầu (PLT): 85 10^9/L   (BT: 150 - 450)
3. Số lượng Hồng cầu (RBC) 4.35 T/L     (BT: 3.8 - 5.5)
4. Huyết sắc tố (HGB): 132 g/L          (BT: 120 - 165)
5. Dung tích hồng cầu (HCT): 38.5 %     (BT: 35 - 48)
6. Định lượng Glucose (Đường huyết đói): 7.8 mmol/L  (BT: 3.9 - 6.4)
7. Men gan AST (SGOT): 45.2 U/L         (BT: < 40)
8. Men gan ALT (SGPT): 38.0 U/L         (BT: < 40)
9. Định lượng Creatinine máu: 88.5 umol/L (BT: 53 - 106)
10. Định lượng Ure máu: 5.2 mmol/L       (BT: 2.5 - 7.5)
11. Acid Uric máu: 340 umol/L            (BT: 180 - 420)
12. Bilirubin toàn phần: 14.5 umol/L     (BT: 5 - 21)
"""

PATTERNS = {
    'WBC': [r'\b(?:wbc|bach\s*cau|leu|leucocyte|white\s*blood)\b'],
    'PLT': [r'\b(?:plt|tieu\s*cau|platelet)\b'],
    'RBC': [r'\b(?:rbc|hong\s*cau|ery|erythrocyte|red\s*blood)\b'],
    'HGB': [r'\b(?:hgb|hb|hemoglobin|huyet\s*sac\s*to)\b'],
    'HCT': [r'\b(?:hct|hematocrit|dung\s*tich\s*hong\s*cau)\b'],
    'AST': [r'\b(?:ast|sgot|got)\b'],
    'ALT': [r'\b(?:alt|sgpt|gpt)\b'],
    'GLUCOSE': [r'\b(?:glucose|glu|duong\s*huyet|duong\s*mau)\b'],
    'CREATININE': [r'\b(?:creatinine|creatinin|crea)\b'],
    'UREA': [r'\b(?:urea|ure|uree|bun)\b'],
    'BILIRUBIN': [r'\b(?:bilirubin|tbil|bili)\b'],
    'URIC_ACID': [r'\b(?:acid\s*uric|axit\s*uric|uric)\b']
}

def parse_medical_lines(raw_text: str) -> Dict[str, float]:
    results = {}
    lines = raw_text.splitlines()
    for line in lines:
        cleaned = line.strip()
        if not cleaned:
            continue
        norm_line = remove_diacritics(cleaned.lower())
        
        for key, regex_list in PATTERNS.items():
            if key in results:
                continue
            matched = False
            for reg in regex_list:
                m = re.search(reg, norm_line)
                if m:
                    matched = True
                    # Look for number after the match position or in the line
                    after_match = norm_line[m.end():]
                    # Find numbers with optional decimal point/comma
                    nums = re.findall(r'[:\s=\-\|]+([0-9]+[.,]?[0-9]*)', after_match)
                    if not nums:
                        nums = re.findall(r'([0-9]+[.,]?[0-9]*)', after_match)
                    if not nums:
                        # Find anywhere in the line
                        nums = re.findall(r'([0-9]+[.,]?[0-9]*)', norm_line)
                    
                    if nums:
                        val_str = nums[0].replace(',', '.')
                        try:
                            val = float(val_str)
                            results[key] = val
                        except ValueError:
                            pass
                    break
    return results

parsed = parse_medical_lines(sample_ocr_texts)
print("=== PARSED INDICATORS FROM HOSPITAL REPORT ===")
for k, v in parsed.items():
    print(f"  {k}: {v}")
