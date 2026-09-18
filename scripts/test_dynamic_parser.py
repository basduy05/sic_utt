import re
import unicodedata
import json
import sys
from typing import Dict, Any, List

sys.stdout.reconfigure(encoding='utf-8')

sample_report = """
1. Hóa sinh
Định lượng Glucose [Máu] 5.4 ( 4.11 - 5.89 )
Định lượng HbA1c [Máu] 5.67 ( 4.8 - 5.9 )
Định lượng Urê máu [Máu] 3.7 ( 2.76 - 8.07 )
Định lượng Creatinin (máu) 76 ( 62 - 106 )
Định lượng Acid Uric [Máu] 320 ( 202.3 - 416.5 )
Định lượng Cholesterol toàn phần (máu) 3.99 ( < 5.2 )
Định lượng Triglycerid (máu) [Máu] 0.63 ( < 1.7 )
Định lượng HDL-C (High density lipoprotein Cholesterol) [Máu] 1.65 ( > 0.9 )
Định lượng LDL - C (Low density lipoprotein Cholesterol) [Máu] 2.03 ( < 3.34 )
Đo hoạt độ AST (GOT) [Máu] 17 ( < 40 )
Đo hoạt độ ALT (GPT) [Máu] 30 ( < 41 )
Đo hoạt độ GGT (Gama Glutamyl Transferase) [Máu] 32 ( 8 - 61 )
Định lượng Calci toàn phần [Máu] 2.40 ( 2.15 - 2.5 )
Định lượng sắt huyết thanh 18.2 ( 5.83 - 34.5 )
2. Huyết học
Số lượng hồng cầu (RBC) 4.93 ( 4 - 5.9 )
Huyết sắc tố (Hemoglobin) 158 ( 125 - 175 )
Hematocrit (HCT) 0.49 ( 0.4 - 0.53 )
Số lượng Bạch cầu (WBC) 7.03 ( 4 - 10 )
Số lượng Tiểu cầu (PLT) 232 ( 150 - 450 )
3. Miễn dịch
Định lượng FT4 (Free Thyroxine) [Máu] 22.80 ( 12 - 22 )
Định lượng TSH (Thyroid Stimulating hormone) [Máu] 1.110 ( 0.27 - 4.2 )
Định lượng IgE 360 ( < 100 )
4. Chẩn đoán hình ảnh
Siêu âm tuyến giáp: Nang hai thùy tuyến giáp (TIRADS 2 - Korean 2021)
"""

def extract_dynamic_indicators(text: str) -> Dict[str, Any]:
    """
    Parser động bóc tách TOÀN BỘ các dòng xét nghiệm y tế bất kỳ
    (không giới hạn danh sách cố định), tự động đối chiếu khoảng tham chiếu.
    """
    results = {}
    lines = text.strip().splitlines()
    for line in lines:
        raw_l = line.strip()
        if not raw_l or len(raw_l) < 3:
            continue
        
        # Pattern 1: Tên xét nghiệm + Giá trị + ( Khoảng tham chiếu )
        # VD: "Định lượng Glucose [Máu] 5.4 ( 4.11 - 5.89 )"
        m = re.search(r'^(.*?)\s+([0-9]+[.,]?[0-9]*|âm\s*tính|dương\s*tính)\s*\(\s*([^\)]+)\s*\)', raw_l, flags=re.IGNORECASE)
        if m:
            raw_name = m.group(1).strip(' -:.\t')
            val_str = m.group(2).strip()
            ref_range = m.group(3).strip()
            
            # Làm sạch tên xét nghiệm
            clean_name = re.sub(r'^(?:định\s*lượng|đo\s*hoạt\s*độ|số\s*lượng|tỷ\s*lệ)\s*', '', raw_name, flags=re.IGNORECASE)
            clean_name = re.sub(r'\[.*?\]', '', clean_name).strip()
            clean_name = clean_name or raw_name
            
            # Đánh giá bất thường
            status = "NORMAL"
            message = f"Bình thường ({ref_range})"
            try:
                val = float(val_str.replace(',', '.'))
                # Phân tích ref range: e.g. "4.11 - 5.89", "< 40", "> 0.9", "12 - 22"
                if '<' in ref_range:
                    cutoff = float(re.findall(r'[0-9]+[.,]?[0-9]*', ref_range)[0])
                    if val > cutoff:
                        status = "HIGH"
                        message = f"Cao hơn bình thường ({val} > {cutoff})"
                elif '>' in ref_range:
                    cutoff = float(re.findall(r'[0-9]+[.,]?[0-9]*', ref_range)[0])
                    if val < cutoff:
                        status = "LOW"
                        message = f"Thấp hơn bình thường ({val} < {cutoff})"
                elif '-' in ref_range:
                    bounds = re.findall(r'[0-9]+[.,]?[0-9]*', ref_range)
                    if len(bounds) >= 2:
                        low_b = float(bounds[0])
                        high_b = float(bounds[1])
                        if val > high_b:
                            status = "HIGH"
                            message = f"Cao hơn giới hạn ({val} > {high_b})"
                        elif val < low_b:
                            status = "LOW"
                            message = f"Thấp hơn giới hạn ({val} < {low_b})"
            except Exception:
                val = val_str

            results[clean_name] = {
                "name": clean_name,
                "original_name": raw_name,
                "value": val,
                "reference_range": ref_range,
                "status": status,
                "message": message
            }
        else:
            # Pattern 2: Dòng chẩn đoán hình ảnh hoặc kết quả dạng text
            # VD: "Siêu âm tuyến giáp: Nang hai thùy tuyến giáp (TIRADS 2)"
            m2 = re.search(r'^(.*?)\s*[:\t]\s*(.+)$', raw_l)
            if m2 and len(m2.group(1)) > 3 and not re.match(r'^(?:kết\s*luận|hẹn\s*khám|stt|tên\s*dịch\s*vụ)', m2.group(1), flags=re.IGNORECASE):
                test_name = m2.group(1).strip()
                val_text = m2.group(2).strip()
                results[test_name] = {
                    "name": test_name,
                    "original_name": test_name,
                    "value": val_text,
                    "reference_range": "-",
                    "status": "INFO",
                    "message": "Kết quả chẩn đoán hình ảnh / cận lâm sàng"
                }

    return results

parsed = extract_dynamic_indicators(sample_report)
print(f"=== PARSED {len(parsed)} DYNAMIC CLINICAL TESTS ===")
for k, v in parsed.items():
    print(f"[{v['status']}] {k}: {v['value']} (Tham chiếu: {v['reference_range']}) -> {v['message']}")
