import io
import re
import asyncio
import logging
from typing import Dict, Any, Optional
from .lab_sanity_checker import LabSanityChecker
from .pdf_parser import PDFLabParser

logger = logging.getLogger(__name__)

class ImageLabOCR:
    """
    Trích xuất chữ và bảng chỉ số y tế từ ảnh (PNG, JPG, JPEG, WebP, BMP)
    sử dụng Windows Native OCR (winrt), EasyOCR, Tesseract kèm bộ parser chuẩn hóa sinh học.
    """

    def __init__(self, sanity_checker: Optional[LabSanityChecker] = None):
        self.sanity_checker = sanity_checker or LabSanityChecker()
        self.pdf_parser = PDFLabParser(self.sanity_checker)
        self.easyocr_reader = None
        # Readers are loaded lazily on first image processing call

    def _init_readers(self):
        try:
            import easyocr
            self.easyocr_reader = easyocr.Reader(['vi', 'en'], gpu=False)
            logger.info("EasyOCR loaded.")
        except Exception:
            self.easyocr_reader = None

    def _run_windows_native_ocr(self, image_bytes: bytes) -> str:
        """
        Sử dụng Windows.Media.Ocr Native Engine (cực nhanh, không cần mạng).
        """
        try:
            import winrt.windows.media.ocr as win_ocr
            import winrt.windows.graphics.imaging as imaging
            import winrt.windows.storage.streams as streams

            async def _recognize():
                stream = streams.InMemoryRandomAccessStream()
                writer = streams.DataWriter(stream)
                writer.write_bytes(image_bytes)
                await writer.store_async()
                await writer.flush_async()
                stream.seek(0)

                decoder = await imaging.BitmapDecoder.create_async(stream)
                soft_bmp = await decoder.get_software_bitmap_async()

                engine = win_ocr.OcrEngine.try_create_from_user_profile_languages()
                if not engine:
                    engine = win_ocr.OcrEngine.try_create_from_language_tag("en-US")
                if not engine:
                    return ""

                ocr_res = await engine.recognize_async(soft_bmp)
                lines = [line.text for line in ocr_res.lines]
                return "\n".join(lines)

            # Chạy an toàn kể cả khi đang có event loop
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(lambda: asyncio.run(_recognize()))
                        return future.result(timeout=10)
                else:
                    return loop.run_until_complete(_recognize())
            except Exception:
                return asyncio.run(_recognize())

        except Exception as e:
            logger.warning(f"Windows Native OCR failed: {e}")
            return ""

    def _preprocess_image(self, image_bytes: bytes) -> bytes:
        """
        Tự động xoay ảnh theo chiều chụp (EXIF), chuẩn hóa kênh màu RGB và thu phóng kích thước tối ưu cho OCR.
        """
        try:
            from PIL import Image, ImageOps
            img = Image.open(io.BytesIO(image_bytes))
            img = ImageOps.exif_transpose(img)
            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")
            
            max_dim = 2400
            if max(img.size) > max_dim:
                img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

            buf = io.BytesIO()
            img.save(buf, format="PNG")
            return buf.getvalue()
        except Exception as e:
            logger.warning(f"Image preprocessing warning: {e}")
            return image_bytes

    def process_image(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Bóc tách text từ ảnh và trích xuất bảng chỉ số y tế.
        Ưu tiên sử dụng EasyOCR tiếng Việt với thuật toán gom cụm bounding box theo dòng bảng.
        """
        processed_bytes = self._preprocess_image(image_bytes)
        raw_text = ""

        # 1. Ưu tiên EasyOCR (Deep Learning tiếng Việt + Anh)
        if self.easyocr_reader is None:
            self._init_readers()
        if self.easyocr_reader is not None:
            try:
                import numpy as np
                from PIL import Image
                img = Image.open(io.BytesIO(processed_bytes))
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                img_np = np.array(img)
                results = self.easyocr_reader.readtext(img_np, detail=1, paragraph=False)
                
                # Thuật toán gom cụm bounding boxes thành các dòng bảng hoàn chỉnh
                boxes_with_text = []
                for item in results:
                    bbox = item[0]
                    text = item[1].strip()
                    if not text:
                        continue
                    y_center = (bbox[0][1] + bbox[2][1]) / 2.0
                    x_left = bbox[0][0]
                    h = abs(bbox[2][1] - bbox[0][1])
                    boxes_with_text.append({'y': y_center, 'x': x_left, 'h': h, 'text': text})

                boxes_with_text.sort(key=lambda b: b['y'])

                rows = []
                current_row = []
                current_y = None

                for box in boxes_with_text:
                    if current_y is None:
                        current_y = box['y']
                        current_row.append(box)
                    else:
                        threshold = max(14.0, box['h'] * 0.75)
                        if abs(box['y'] - current_y) <= threshold:
                            current_row.append(box)
                        else:
                            current_row.sort(key=lambda b: b['x'])
                            rows.append(' '.join([b['text'] for b in current_row]))
                            current_row = [box]
                            current_y = box['y']

                if current_row:
                    current_row.sort(key=lambda b: b['x'])
                    rows.append(' '.join([b['text'] for b in current_row]))

                raw_text = '\n'.join(rows)

            except Exception as e:
                logger.error(f"Error during EasyOCR table parsing: {e}")

        # 2. Fallback sang Windows Native OCR nếu EasyOCR chưa ra kết quả
        if not raw_text.strip():
            raw_text = self._run_windows_native_ocr(processed_bytes)

        # 3. Fallback sang pytesseract nếu vẫn trống
        if not raw_text.strip():
            try:
                import pytesseract
                from PIL import Image
                img = Image.open(io.BytesIO(processed_bytes))
                raw_text = pytesseract.image_to_string(img, lang="vie+eng")
            except Exception:
                pass

        # 4. Tiền xử lý sửa lỗi ký tự OCR phổ biến
        cleaned_text = raw_text
        if cleaned_text:
            cleaned_text = re.sub(r'(?i)\bwao\b', 'WBC', cleaned_text)
            cleaned_text = re.sub(r'(?i)\brao\b', 'RBC', cleaned_text)
            cleaned_text = re.sub(r'(?i)\bpl\s*t\b', 'PLT', cleaned_text)
            cleaned_text = re.sub(r'(?i)\bglucc?c?e?\b', 'GLUCOSE', cleaned_text)

        parsed = self.pdf_parser.extract_lab_values_from_text(cleaned_text if cleaned_text.strip() else raw_text)
        parsed["ocr_text"] = raw_text
        return parsed
