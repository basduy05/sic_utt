import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

hospital_text = """
1 Hóa sinh
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
Tổng phân tích nước tiểu (Bằng máy tự động)
BIL Âm tính ( Âm tính )
UBG Âm tính ( Âm tính )
KET Âm tính ( Âm tính )
GLU Âm tính ( Âm tính )
PRO Âm tính ( Âm tính )
ERY Âm tính ( Âm tính )
pH 6.5
NIT Âm tính ( Âm tính )
LEU (Nước tiểu) 100 ( Âm tính )
SG 1.008 ( 1.005 - 1.03 )
2 Huyết học
Tổng phân tích tế bào máu ngoại vi (bằng máy đếm laser)
Số lượng hồng cầu (RBC) 4.93 ( 4 - 5.9 )
Huyết sắc tố (Hemoglobin) 158 ( 125 - 175 )
Hematocrit (HCT) 0.49 ( 0.4 - 0.53 )
Thể tích trung bình Hồng cầu (MCV) 98.4 ( 80 - 100 )
Huyết sắc tố trung bình Hồng cầu (MCH) 32 ( 26 - 34 )
Nồng độ huyết sắc tố trung bình Hồng Cầu (MCHC) 327 ( 315 - 363 )
Dải phân bố Hồng cầu- Hệ số biến thiên (RDW-CV) 12.2 ( 11 - 17 )
Số lượng Bạch cầu (WBC) 7.03 ( 4 - 10 )
Tỷ lệ bạch cầu đoạn trung tính (NEUT%) 54.7 ( 45 - 75 )
Tỷ lệ bạch cầu Lympho (LYM%) 34.6 ( 20 - 45 )
Tỷ lệ bạch cầu MONO% 5.00 ( 0 - 8 )
Tỷ lệ bạch cầu đoạn ưa Acid (EOS%) 2.0 ( 0 - 8 )
Tỷ lệ bạch cầu đoạn ưa Baso (BASO%) 0.90 ( 0 - 2 )
Số lượng bạch cầu đoạn trung tính (NEUT) 3.8 ( 1.8 - 7.5 )
Số lượng bạch cầu Lympho (LYMPT) 2.43 ( 0.8 - 4.5 )
Số lượng bạch cầu Mono (MONO) 0.35 ( 0 - 0.8 )
Số lượng bạch cầu đoạn ưa Acid (EOS) 0.14 ( 0 - 0.8 )
Số lượng bạch cầu đoạn ưa Base (BASO) 0.06 ( 0 - 0.1 )
Số lượng Tiểu cầu (PLT) 232 ( 150 - 450 )
Thể tích trung bình Tiểu cầu (MPV) 8.10 ( 5 - 20 )
3 Miễn dịch
Định lượng FT4 (Free Thyroxine) [Máu] 22.80 ( 12 - 22 )
Định lượng TSH (Thyroid Stimulating hormone) [Máu] 1.110 ( 0.27 - 4.2 )
Định lượng IgE 360 ( < 100 )
4 Chẩn đoán hình ảnh
Siêu âm tuyến giáp: Nang hai thùy tuyến giáp (TIRADS 2- Korean 2021).
"""

def parse_hospital_report_accurate(text):
    results = {}
    lines = text.strip().splitlines()
    is_urine_section = False
    
    for line in lines:
        raw_l = line.strip()
        if not raw_l or len(raw_l) < 3:
            continue
        
        # Check section header
        if re.search(r'nước\s*tiểu', raw_l, flags=re.IGNORECASE):
            is_urine_section = True
        elif re.search(r'huyết\s*học|hóa\s*sinh|miễn\s*dịch|chẩn\s*đoán', raw_l, flags=re.IGNORECASE):
            is_urine_section = False
            
        # Pattern 1: Table row with Reference Range in parentheses
        # e.g. "Số lượng Bạch cầu (WBC) 7.03 ( 4 - 10 )"
        # e.g. "Định lượng FT4 (Free Thyroxine) [Máu] 22.80 ( 12 - 22 )"
        # Match test name before the number, result value before ( ... )
        m = re.search(r'^(.*?)\s+([0-9]+[.,]?[0-9]*|âm\s*tính|dương\s*tính)\s*\(\s*([^\)]+)\s*\)', raw_l, flags=re.IGNORECASE)
        if m:
            raw_name = m.group(1).strip(' -:.\t0123456789')
            val_str = m.group(2).strip()
            ref_range = m.group(3).strip()
            
            # Clean name
            clean_name = re.sub(r'^(?:định\s*lượng|đo\s*hoạt\s*độ|số\s*lượng|tỷ\s*lệ)\s*', '', raw_name, flags=re.IGNORECASE)
            clean_name = re.sub(r'\[.*?\]', '', clean_name).strip()
            clean_name = clean_name or raw_name
            
            if is_urine_section:
                clean_name = f"{clean_name} (Nước tiểu)"
            
            status = "NORMAL"
            message = f"Bình thường ({ref_range})"
            try:
                val = float(val_str.replace(',', '.'))
                if '<' in ref_range:
                    cutoffs = re.findall(r'[0-9]+[.,]?[0-9]*', ref_range)
                    if cutoffs and val > float(cutoffs[0]):
                        status = "HIGH"
                        message = f"Cao hơn bình thường ({val} > {cutoffs[0]})"
                elif '>' in ref_range:
                    cutoffs = re.findall(r'[0-9]+[.,]?[0-9]*', ref_range)
                    if cutoffs and val < float(cutoffs[0]):
                        status = "LOW"
                        message = f"Thấp hơn bình thường ({val} < {cutoffs[0]})"
                elif '-' in ref_range:
                    bounds = re.findall(r'[0-9]+[.,]?[0-9]*', ref_range)
                    if len(bounds) >= 2:
                        low_b, high_b = float(bounds[0]), float(bounds[1])
                        if val > high_b:
                            status = "HIGH"
                            message = f"Cao hơn giới hạn ({val} > {high_b})"
                        elif val < low_b:
                            status = "LOW"
                            message = f"Thấp hơn giới hạn ({val} < {low_b})"
            except Exception:
                val = val_str
                if "dương tính" in str(val).lower() or (str(val).isdigit() and float(val) > 0 and "âm tính" in ref_range.lower()):
                    status = "ABNORMAL"
                    message = f"Bất thường (Dương tính / Có hiện diện)"

            results[clean_name] = {
                "name": clean_name,
                "value": val,
                "reference_range": ref_range,
                "status": status,
                "message": message
            }
        else:
            # Pattern 2: Imaging or key-value line
            m2 = re.search(r'^(siêu\s*âm.*?|x-quang.*?|ct.*?|mri.*?|nội\s*soi.*?|kết\s*quả.*?|kết\s*luận.*?)\s*[:\t]\s*(.+)$', raw_l, flags=re.IGNORECASE)
            if m2:
                test_name = m2.group(1).strip()
                val_text = m2.group(2).strip()
                results[test_name] = {
                    "name": test_name,
                    "value": val_text,
                    "reference_range": "-",
                    "status": "INFO",
                    "message": "Chẩn đoán hình ảnh / Kết luận lâm sàng"
                }

    return results

res = parse_hospital_report_accurate(hospital_text)
print(f"=== ACCURATELY PARSED: {len(res)} TESTS ===")
for k, v in res.items():
    print(f"[{v['status']}] {k}: {v['value']} | Ref: {v['reference_range']} -> {v['message']}")
