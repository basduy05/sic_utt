import io
import re
import unicodedata
import logging
from typing import Dict, Any, List, Optional
from .lab_sanity_checker import LabSanityChecker

logger = logging.getLogger(__name__)

def remove_diacritics(text: str) -> str:
    """Loại bỏ dấu tiếng Việt để tăng khả năng so khớp OCR chính xác."""
    if not text:
        return ""
    norm = unicodedata.normalize('NFD', text)
    res = re.sub(r'[\u0300-\u036f]', '', norm)
    return res.replace('đ', 'd').replace('Đ', 'D')

class PDFLabParser:
    """
    Trích xuất bảng chỉ số xét nghiệm từ file PDF y tế và text OCR.
    Hỗ trợ đọc đa trang và bóc tách đầy đủ các chỉ số Huyết học, Sinh hóa, Chức năng gan thận.
    """

    def __init__(self, sanity_checker: Optional[LabSanityChecker] = None):
        self.sanity_checker = sanity_checker or LabSanityChecker()
        
        # Danh mục từ khóa nhận diện cho từng chỉ số (đã chuẩn hóa không dấu)
        self.indicator_keywords = {
            "WBC": [r'\b(?:wbc|bach\s*cau|leu|leucocyte|white\s*blood)\b'],
            "PLT": [r'\b(?:plt|tieu\s*cau|platelet)\b'],
            "RBC": [r'\b(?:rbc|hong\s*cau|ery|erythrocyte|red\s*blood)\b'],
            "HGB": [r'\b(?:hgb|hb|hemoglobin|huyet\s*sac\s*to)\b'],
            "HCT": [r'\b(?:hct|hematocrit|dung\s*tich\s*hong\s*cau)\b'],
            "AST": [r'\b(?:ast|sgot|got|men\s*gan\s*ast)\b'],
            "ALT": [r'\b(?:alt|sgpt|gpt|men\s*gan\s*alt)\b'],
            "GLUCOSE": [r'\b(?:glucose|glu|duong\s*huyet|duong\s*mau)\b'],
            "CREATININE": [r'\b(?:creatinine|creatinin|crea)\b'],
            "UREA": [r'\b(?:urea|ure|uree|bun)\b'],
            "BILIRUBIN": [r'\b(?:bilirubin|tbil|bili|sac\s*to\s*mat)\b'],
            "URIC_ACID": [r'\b(?:acid\s*uric|axit\s*uric|uric)\b'],
            "CHOLESTEROL": [r'\b(?:cholesterol|choles|tc)\b'],
            "TRIGLYCERIDE": [r'\b(?:triglyceride|triglycerid|trig|tg)\b']
        }

    def parse_pdf(self, pdf_bytes: bytes) -> Dict[str, Any]:
        """
        Bóc tách text và bảng số liệu từ toàn bộ các trang trong file PDF.
        """
        extracted_text = ""
        
        # 1. Thử pypdf
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    extracted_text += t + "\n"
        except Exception as e:
            logger.warning(f"pypdf extraction failed: {e}")

        # 2. Thử fitz (PyMuPDF) nếu chưa có text
        if not extracted_text.strip():
            try:
                import fitz
                doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                for page in doc:
                    extracted_text += page.get_text() + "\n"
            except Exception as e:
                logger.warning(f"PyMuPDF extraction failed: {e}")

        # 3. Fallback text decoding nếu định dạng text stream
        if not extracted_text.strip():
            try:
                extracted_text = pdf_bytes.decode("utf-8", errors="ignore")
            except Exception:
                extracted_text = ""

        res = self.extract_lab_values_from_text(extracted_text)
        res["ocr_text"] = extracted_text
        return res

    def extract_lab_values_from_text(self, text: str) -> Dict[str, Any]:
        """
        Bóc tách và chuẩn hóa sinh học các chỉ số xét nghiệm từ văn bản OCR / PDF.
        """
        results = {}
        flags = []
        if not text:
            return {
                "parsed_indicators": {},
                "raw_text_length": 0,
                "critical_flags": [],
                "total_indicators_found": 0,
                "ocr_text": ""
            }

        lines = text.splitlines()
        is_urine_section = False

        # Bóc tách từng dòng bảng tổng quát theo cấu trúc bệnh viện
        for line in lines:
            raw_l = line.strip()
            if not raw_l or len(raw_l) < 3:
                continue

            # Phân tách khu vực xét nghiệm
            if re.search(r'nước\s*tiểu', raw_l, flags=re.IGNORECASE):
                is_urine_section = True
            elif re.search(r'huyết\s*học|hóa\s*sinh|miễn\s*dịch|chẩn\s*đoán|máu', raw_l, flags=re.IGNORECASE):
                is_urine_section = False

            # Pattern A: Dòng bảng có Khoảng Tham Chiếu trong ngoặc đơn
            # VD: "Số lượng Bạch cầu (WBC) 7.03 ( 4 - 10 )"
            # VD: "Định lượng FT4 (Free Thyroxine) [Máu] 22.80 ( 12 - 22 )"
            m = re.search(r'^(.*?)\s+([0-9]+[.,]?[0-9]*|âm\s*tính|dương\s*tính)\s*\(\s*([^\)]+)\s*\)', raw_l, flags=re.IGNORECASE)
            if m:
                raw_name = m.group(1).strip(' -:.\t0123456789')
                val_str = m.group(2).strip()
                ref_range = m.group(3).strip()

                clean_name = re.sub(r'^(?:định\s*lượng|đo\s*hoạt\s*độ|số\s*lượng|tỷ\s*lệ)\s*', '', raw_name, flags=re.IGNORECASE)
                clean_name = re.sub(r'\[.*?\]', '', clean_name).strip()
                clean_name = clean_name or raw_name

                if is_urine_section and "nước tiểu" not in clean_name.lower():
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
                    "message": message,
                    "unit": ""
                }
                if status in ("HIGH", "LOW", "ABNORMAL", "CRITICAL_HIGH", "CRITICAL_LOW"):
                    flags.append(f"{clean_name}: {val} ({status})")
            else:
                # Pattern B: Chẩn đoán hình ảnh / Kết luận có dấu hai chấm
                m2 = re.search(r'^(siêu\s*âm.*?|x-quang.*?|ct.*?|mri.*?|nội\s*soi.*?|kết\s*quả.*?|kết\s*luận.*?)\s*[:\t]\s*(.+)$', raw_l, flags=re.IGNORECASE)
                if m2:
                    test_name = m2.group(1).strip()
                    val_text = m2.group(2).strip()
                    if test_name not in results:
                        results[test_name] = {
                            "name": test_name,
                            "value": val_text,
                            "reference_range": "-",
                            "status": "INFO",
                            "message": "Chẩn đoán hình ảnh / Kết luận lâm sàng",
                            "unit": ""
                        }

        return {
            "parsed_indicators": results,
            "raw_text_length": len(text),
            "critical_flags": flags,
            "total_indicators_found": len(results),
            "ocr_text": text
        }
