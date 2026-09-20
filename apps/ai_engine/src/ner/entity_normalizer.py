import json
import os
import re
import logging
import numpy as np
from typing import Dict, List, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

class EntityNormalizer:
    """
    Chuẩn hóa thực thể y tế tiếng Việt sử dụng Không gian Vector Ngữ nghĩa Sâu (Dense Semantic Vector Space).
    Sử dụng mô hình Transformer Sentence-Transformers (paraphrase-multilingual-MiniLM-L12-v2)
    để tính toán Cosine Similarity trong không gian vector 384 chiều với danh mục 211 bệnh học &
    triệu chứng chuẩn ICD-10 của Bộ Y Tế.
    Loại bỏ hoàn toàn tra từ điển tĩnh / regex chuỗi ký tự cứng.
    """

    def __init__(self, synonyms_path: Optional[str] = None):
        self.embedder = None
        self.concepts: List[Dict[str, str]] = []
        self.exact_lookup: Dict[str, Dict[str, str]] = {}
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.concept_embeddings = None
        self.synonyms_map = {}  # Backward-compatible view

        self._init_concepts(synonyms_path)
        self._init_dense_embedder()

    def _init_concepts(self, synonyms_path: Optional[str] = None):
        """Khởi tạo danh mục khái niệm lâm sàng chuẩn từ symptom_synonyms.json, ICD-10 và tri thức y tế."""
        possible_dirs = [
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "data", "medical_lexicon")),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "medical_lexicon")),
            os.path.abspath(os.path.join(os.getcwd(), "data", "medical_lexicon")),
        ]
        base_dir = next((d for d in possible_dirs if os.path.exists(d)), possible_dirs[0])
        syn_path = synonyms_path or os.path.join(base_dir, "symptom_synonyms.json")
        icd_path = os.path.join(base_dir, "icd10_codes.json")

        seen_terms = set()

        # 1. Nạp từ CSDL Từ đồng nghĩa Triệu chứng Toàn diện (symptom_synonyms.json)
        if os.path.exists(syn_path):
            try:
                with open(syn_path, "r", encoding="utf-8") as f:
                    syn_data = json.load(f)
                for sym_id, details in syn_data.items():
                    standard = details.get("standard_term", sym_id)
                    syns = details.get("synonyms", [])
                    category = details.get("category", "Chung")

                    entry = {"id": sym_id, "standard_term": standard, "category": category}
                    if standard.lower() not in seen_terms:
                        self.concepts.append(entry)
                        seen_terms.add(standard.lower())

                    # Tra cứu trực tiếp O(1)
                    self.exact_lookup[standard.lower()] = entry
                    for s in syns:
                        s_clean = s.strip().lower()
                        if s_clean:
                            self.exact_lookup[s_clean] = entry
                            if s_clean not in seen_terms:
                                self.concepts.append({"id": sym_id, "standard_term": s.capitalize(), "category": category})
                                seen_terms.add(s_clean)
                logger.info(f"Loaded {len(self.concepts)} concepts and {len(self.exact_lookup)} synonym mappings from {syn_path}")
            except Exception as e:
                logger.warning(f"Could not load symptom synonyms from {syn_path}: {e}")

        # 2. Nạp từ ICD-10 nếu có
        if os.path.exists(icd_path):
            try:
                with open(icd_path, "r", encoding="utf-8") as f:
                    icd_data = json.load(f)
                admin_blacklist = ("chua_xac_dinh", "kham_chua_ra", "chua_phan_loai", "khong_dac_hieu", "benh_chua_ro")
                for code, details in icd_data.items():
                    name_vi = details.get("name_vi", "")
                    if name_vi and name_vi.lower() not in seen_terms:
                        if not any(b in name_vi.lower() or b in code.lower() for b in admin_blacklist):
                            self.concepts.append({"id": code, "standard_term": name_vi, "category": details.get("department", "Chuyên khoa")})
                            seen_terms.add(name_vi.lower())
                    for sym in details.get("cardinal_symptoms", []) + details.get("all_symptoms", []):
                        s_clean = sym.strip().lower()
                        if s_clean and s_clean not in seen_terms:
                            if any(b in s_clean for b in admin_blacklist):
                                continue
                            clean_id = f"sym_{re.sub(r'[^a-zA-Z0-9_]', '_', s_clean)}"
                            self.concepts.append({"id": clean_id, "standard_term": sym.capitalize(), "category": details.get("department", "Chuyên khoa")})
                            seen_terms.add(s_clean)
            except Exception as e:
                logger.warning(f"Could not load ICD-10 concepts: {e}")

        # 3. Bổ sung các khái niệm lâm sàng cơ bản dự phòng
        default_clinical_concepts = [
            ("sot_cao", "Sốt cao", "Toàn thân"),
            ("dau_dau", "Đau đầu", "Thần kinh"),
            ("dau_nguc", "Đau ngực", "Tim mạch"),
            ("kho_tho", "Khó thở", "Hô hấp"),
            ("dau_bung", "Đau bụng", "Tiêu hóa"),
            ("non_oi", "Buồn nôn và nôn", "Tiêu hóa"),
            ("tieu_chay", "Tiêu chảy", "Tiêu hóa"),
            ("chay_mau_chan_rang", "Xuất huyết niêm mạc", "Huyết học"),
            ("chong_mat", "Chóng mặt", "Thần kinh"),
            ("ho_khan", "Ho khan", "Hô hấp"),
            ("ho_co_dom", "Ho có đờm", "Hô hấp"),
            ("meo_mieng", "Méo miệng lệch mặt", "Thần kinh"),
            ("yeu_liet_nua_nguoi", "Yếu liệt nửa người", "Thần kinh"),
            ("co_giat", "Co giật", "Thần kinh"),
            ("phat_ban", "Phát ban mẩn đỏ", "Da liễu"),
            ("di_ung_da", "Viêm da dị ứng / Dị ứng da mặt", "Da liễu"),
            ("dau_khop", "Đau nhức khớp", "Cơ xương khớp"),
            ("sym_cham_xuat_huyet", "Chấm xuất huyết dưới da", "Truyền nhiễm"),
            ("sym_dau_nhuc_hoc_mat", "Đau nhức hốc mắt", "Truyền nhiễm"),
            ("sym_moi_mat", "Mỏi mắt điều tiết (Asthenopia)", "Mắt"),
            ("sym_dau_nhuc_mat", "Đau nhức mắt", "Mắt"),
            ("sym_kho_mat", "Khô mắt (Dry eye)", "Mắt"),
            ("sym_nhin_mo", "Nhìn mờ / Giảm thị lực", "Mắt"),
            ("sym_do_mat", "Đỏ mắt / Viêm kết mạc", "Mắt"),
        ]
        for cid, cterm, cat in default_clinical_concepts:
            if cterm.lower() not in seen_terms:
                self.concepts.append({"id": cid, "standard_term": cterm, "category": cat})

        # Bổ sung các cụm từ triệu chứng cơ xương khớp / công thái học phổ biến
        common_ergonomic_phrases = {
            "mỏi ê ẩm": {"id": "sym_mỏi_người", "standard_term": "Mỏi người", "category": "Cơ xương khớp"},
            "mỏi ê ẩm toàn thân": {"id": "sym_mỏi_người", "standard_term": "Mỏi người", "category": "Cơ xương khớp"},
            "mỏi toàn thân": {"id": "sym_mỏi_người", "standard_term": "Mỏi người", "category": "Cơ xương khớp"},
            "ê ẩm toàn thân": {"id": "sym_mỏi_người", "standard_term": "Mỏi người", "category": "Cơ xương khớp"},
            "đau mỏi toàn thân": {"id": "sym_mỏi_người", "standard_term": "Mỏi người", "category": "Cơ xương khớp"},
            "mỏi cổ": {"id": "sym_mỏi_cổ", "standard_term": "Mỏi cổ", "category": "Cơ xương khớp"},
            "đau mỏi cổ": {"id": "sym_mỏi_cổ", "standard_term": "Mỏi cổ", "category": "Cơ xương khớp"},
            "đau mỏi vai gáy": {"id": "dau_moi_vai_gay", "standard_term": "Đau mỏi cổ vai gáy / Đau vai", "category": "Cơ xương khớp"},
            "mỏi vai gáy": {"id": "dau_moi_vai_gay", "standard_term": "Đau mỏi cổ vai gáy / Đau vai", "category": "Cơ xương khớp"},
            "mỏi bả vai": {"id": "dau_moi_vai_gay", "standard_term": "Đau mỏi cổ vai gáy / Đau vai", "category": "Cơ xương khớp"},
        }
        for k, v in common_ergonomic_phrases.items():
            self.exact_lookup[k] = v
            if k not in seen_terms:
                self.concepts.append(v)
                seen_terms.add(k)
                seen_terms.add(cterm.lower())
            if cterm.lower() not in self.exact_lookup:
                self.exact_lookup[cterm.lower()] = {"id": cid, "standard_term": cterm, "category": cat}

        # Bổ sung các cụm từ đặc hiệu lâm sàng sốt xuất huyết & truyền nhiễm & chuyên khoa mắt vào exact lookup
        specific_synonyms = {
            "mỏi mắt": {"id": "sym_moi_mat", "standard_term": "Mỏi mắt điều tiết (Asthenopia)", "category": "Mắt"},
            "bị mỏi mắt": {"id": "sym_moi_mat", "standard_term": "Mỏi mắt điều tiết (Asthenopia)", "category": "Mắt"},
            "mắt mỏi": {"id": "sym_moi_mat", "standard_term": "Mỏi mắt điều tiết (Asthenopia)", "category": "Mắt"},
            "mắt mệt mỏi": {"id": "sym_moi_mat", "standard_term": "Mỏi mắt điều tiết (Asthenopia)", "category": "Mắt"},
            "nhức mỏi mắt": {"id": "sym_moi_mat", "standard_term": "Mỏi mắt điều tiết (Asthenopia)", "category": "Mắt"},
            "mỏi mắt khi đọc sách": {"id": "sym_moi_mat", "standard_term": "Mỏi mắt điều tiết (Asthenopia)", "category": "Mắt"},
            "mỏi mắt nhìn máy tính": {"id": "sym_moi_mat", "standard_term": "Mỏi mắt điều tiết (Asthenopia)", "category": "Mắt"},
            "mỏi mắt khi làm việc": {"id": "sym_moi_mat", "standard_term": "Mỏi mắt điều tiết (Asthenopia)", "category": "Mắt"},
            "mắt căng thẳng": {"id": "sym_moi_mat", "standard_term": "Mỏi mắt điều tiết (Asthenopia)", "category": "Mắt"},
            "đau mắt": {"id": "sym_dau_nhuc_mat", "standard_term": "Đau nhức mắt", "category": "Mắt"},
            "nhức mắt": {"id": "sym_dau_nhuc_mat", "standard_term": "Đau nhức mắt", "category": "Mắt"},
            "đau nhức mắt": {"id": "sym_dau_nhuc_mat", "standard_term": "Đau nhức mắt", "category": "Mắt"},
            "nhức nhối mắt": {"id": "sym_dau_nhuc_mat", "standard_term": "Đau nhức mắt", "category": "Mắt"},
            "thốn mắt": {"id": "sym_dau_nhuc_mat", "standard_term": "Đau nhức mắt", "category": "Mắt"},
            "xót mắt": {"id": "sym_dau_nhuc_mat", "standard_term": "Đau nhức mắt", "category": "Mắt"},
            "khô mắt": {"id": "sym_kho_mat", "standard_term": "Khô mắt (Dry eye)", "category": "Mắt"},
            "cộm mắt": {"id": "sym_kho_mat", "standard_term": "Khô mắt (Dry eye)", "category": "Mắt"},
            "cộm rát mắt": {"id": "sym_kho_mat", "standard_term": "Khô mắt (Dry eye)", "category": "Mắt"},
            "xốn mắt": {"id": "sym_kho_mat", "standard_term": "Khô mắt (Dry eye)", "category": "Mắt"},
            "cay xè mắt": {"id": "sym_kho_mat", "standard_term": "Khô mắt (Dry eye)", "category": "Mắt"},
            "như có cát trong mắt": {"id": "sym_kho_mat", "standard_term": "Khô mắt (Dry eye)", "category": "Mắt"},
            "nhìn mờ": {"id": "sym_nhin_mo", "standard_term": "Nhìn mờ / Mắt mờ", "category": "Mắt"},
            "mờ mắt": {"id": "sym_nhin_mo", "standard_term": "Nhìn mờ / Mắt mờ", "category": "Mắt"},
            "mắt nhìn mờ": {"id": "sym_nhin_mo", "standard_term": "Nhìn mờ / Mắt mờ", "category": "Mắt"},
            "mắt mờ nhòe": {"id": "sym_nhin_mo", "standard_term": "Nhìn mờ / Mắt mờ", "category": "Mắt"},
            "nhìn gần mờ": {"id": "sym_nhin_mo", "standard_term": "Nhìn mờ / Mắt mờ", "category": "Mắt"},
            "nhìn xa mờ": {"id": "sym_nhin_mo", "standard_term": "Nhìn mờ / Mắt mờ", "category": "Mắt"},
            "nheo mắt": {"id": "sym_nhin_mo", "standard_term": "Nhìn mờ / Mắt mờ", "category": "Mắt"},
            "đỏ mắt": {"id": "sym_do_mat", "standard_term": "Đỏ mắt / Viêm kết mạc", "category": "Mắt"},
            "mắt đỏ": {"id": "sym_do_mat", "standard_term": "Đỏ mắt / Viêm kết mạc", "category": "Mắt"},
            "đau mắt đỏ": {"id": "sym_do_mat", "standard_term": "Đỏ mắt / Viêm kết mạc", "category": "Mắt"},
            "chảy nước mắt": {"id": "sym_chay_nuoc_mat", "standard_term": "Chảy nước mắt", "category": "Mắt"},
            "chấm đỏ li ti": {"id": "sym_cham_xuat_huyet", "standard_term": "Chấm xuất huyết dưới da", "category": "Truyền nhiễm"},
            "chấm đỏ": {"id": "sym_cham_xuat_huyet", "standard_term": "Chấm xuất huyết dưới da", "category": "Truyền nhiễm"},
            "chấm đỏ li ti ở tay": {"id": "sym_cham_xuat_huyet", "standard_term": "Chấm xuất huyết dưới da", "category": "Truyền nhiễm"},
            "ấn vào không mất": {"id": "sym_cham_xuat_huyet", "standard_term": "Chấm xuất huyết dưới da", "category": "Truyền nhiễm"},
            "nổi mấy chấm đỏ": {"id": "sym_cham_xuat_huyet", "standard_term": "Chấm xuất huyết dưới da", "category": "Truyền nhiễm"},
            "chấm xuất huyết": {"id": "sym_cham_xuat_huyet", "standard_term": "Chấm xuất huyết dưới da", "category": "Truyền nhiễm"},
            "ban xuất huyết": {"id": "sym_cham_xuat_huyet", "standard_term": "Chấm xuất huyết dưới da", "category": "Truyền nhiễm"},
            "xuất huyết dưới da": {"id": "sym_cham_xuat_huyet", "standard_term": "Chấm xuất huyết dưới da", "category": "Truyền nhiễm"},
            "ê buốt hai hốc mắt": {"id": "sym_dau_nhuc_hoc_mat", "standard_term": "Đau nhức hốc mắt", "category": "Truyền nhiễm"},
            "buốt hai hốc mắt": {"id": "sym_dau_nhuc_hoc_mat", "standard_term": "Đau nhức hốc mắt", "category": "Truyền nhiễm"},
            "đau hốc mắt": {"id": "sym_dau_nhuc_hoc_mat", "standard_term": "Đau nhức hốc mắt", "category": "Truyền nhiễm"},
            "nhức hốc mắt": {"id": "sym_dau_nhuc_hoc_mat", "standard_term": "Đau nhức hốc mắt", "category": "Truyền nhiễm"},
            "đau nhức hốc mắt": {"id": "sym_dau_nhuc_hoc_mat", "standard_term": "Đau nhức hốc mắt", "category": "Truyền nhiễm"},
            "đau nhức khắp các khớp": {"id": "dau_khop", "standard_term": "Đau nhức khớp", "category": "Cơ xương khớp"},
            "đau nhức các khớp": {"id": "dau_khop", "standard_term": "Đau nhức khớp", "category": "Cơ xương khớp"},
            "đau khắp các khớp": {"id": "dau_khop", "standard_term": "Đau nhức khớp", "category": "Cơ xương khớp"},
            "tê phù môi": {"id": "sym_phu_moi", "standard_term": "Phù môi / Phù mạch Angioedema", "category": "Dị ứng - Miễn dịch"},
            "hơi tê phù": {"id": "sym_phu_moi", "standard_term": "Phù môi / Phù mạch Angioedema", "category": "Dị ứng - Miễn dịch"},
            "phù môi": {"id": "sym_phu_moi", "standard_term": "Phù môi / Phù mạch Angioedema", "category": "Dị ứng - Miễn dịch"},
            "sưng môi": {"id": "sym_phu_moi", "standard_term": "Phù môi / Phù mạch Angioedema", "category": "Dị ứng - Miễn dịch"},
            "thở rít": {"id": "sym_tho_rit", "standard_term": "Thở rít / Co thắt thanh quản", "category": "Hô hấp"},
            "thở rít nhẹ": {"id": "sym_tho_rit", "standard_term": "Thở rít / Co thắt thanh quản", "category": "Hô hấp"},
            "cảm giác thở rít": {"id": "sym_tho_rit", "standard_term": "Thở rít / Co thắt thanh quản", "category": "Hô hấp"},
            "cảm giác thở rít nhẹ": {"id": "sym_tho_rit", "standard_term": "Thở rít / Co thắt thanh quản", "category": "Hô hấp"},
            "ăn hải sản": {"id": "sym_tiep_xuc_di_nguyen", "standard_term": "Tiếp xúc dị nguyên thức ăn", "category": "Dị ứng"},
            "uống chút bia": {"id": "sym_tiep_xuc_di_nguyen", "standard_term": "Tiếp xúc dị nguyên thức ăn", "category": "Dị ứng"},
            "nổi từng mảng": {"id": "sym_may_day", "standard_term": "Mày đay sẩn ngứa cấp tính", "category": "Dị ứng - Da liễu"},
            "mảng sưng đỏ": {"id": "sym_may_day", "standard_term": "Mày đay sẩn ngứa cấp tính", "category": "Dị ứng - Da liễu"},
            "sưng đỏ như muỗi đốt": {"id": "sym_may_day", "standard_term": "Mày đay sẩn ngứa cấp tính", "category": "Dị ứng - Da liễu"},
            "ngứa dữ dội": {"id": "sym_ngua_du_doi", "standard_term": "Ngứa dữ dội da niêm mạc", "category": "Dị ứng - Da liễu"},
            # Triệu chứng ngắn & Khẩu ngữ tiếng Việt đời thường
            "ho": {"id": "ho_khan", "standard_term": "Ho khan", "category": "Hô hấp"},
            "sốt": {"id": "sot_cao", "standard_term": "Sốt cao", "category": "Toàn thân"},
            "sốt nhẹ": {"id": "sot_cao", "standard_term": "Sốt cao", "category": "Toàn thân"},
            "hâm hấp": {"id": "sot_cao", "standard_term": "Sốt cao", "category": "Toàn thân"},
            "hâm hấp sốt": {"id": "sot_cao", "standard_term": "Sốt cao", "category": "Toàn thân"},
            "đờm": {"id": "ho_co_dom", "standard_term": "Ho có đờm", "category": "Hô hấp"},
            "ngứa": {"id": "sym_ngua_du_doi", "standard_term": "Ngứa dữ dội da niêm mạc", "category": "Da liễu"},
            "rát da": {"id": "di_ung_da", "standard_term": "Viêm da dị ứng / Dị ứng da mặt", "category": "Da liễu"},
            "bỏng rát da": {"id": "di_ung_da", "standard_term": "Viêm da dị ứng / Dị ứng da mặt", "category": "Da liễu"},
            "căng rát da": {"id": "di_ung_da", "standard_term": "Viêm da dị ứng / Dị ứng da mặt", "category": "Da liễu"},
            "rát họng": {"id": "ho_khan", "standard_term": "Ho khan / Đau rát họng", "category": "Hô hấp"},
            "đau họng": {"id": "ho_khan", "standard_term": "Ho khan / Đau rát họng", "category": "Hô hấp"},
            "nôn": {"id": "non_oi", "standard_term": "Buồn nôn và nôn", "category": "Tiêu hóa"},
            "ói": {"id": "non_oi", "standard_term": "Buồn nôn và nôn", "category": "Tiêu hóa"},
            "buồn nôn": {"id": "non_oi", "standard_term": "Buồn nôn và nôn", "category": "Tiêu hóa"},
            "nôn nao": {"id": "non_oi", "standard_term": "Buồn nôn và nôn", "category": "Tiêu hóa"},
            "mắc ói": {"id": "non_oi", "standard_term": "Buồn nôn và nôn", "category": "Tiêu hóa"},
            "ậm ạch": {"id": "dau_bung", "standard_term": "Đầy bụng / Khó tiêu ậm ạch", "category": "Tiêu hóa"},
            "cồn cào": {"id": "dau_bung", "standard_term": "Đau bụng / Cồn cào dạ dày", "category": "Tiêu hóa"},
            "tức tức": {"id": "dau_nguc", "standard_term": "Đau ngực / Tức ngực", "category": "Tim mạch"},
            "tức tức ngực": {"id": "dau_nguc", "standard_term": "Đau ngực / Tức ngực", "category": "Tim mạch"},
            "tức ngực": {"id": "dau_nguc", "standard_term": "Đau ngực / Tức ngực", "category": "Tim mạch"},
            "khó thở": {"id": "kho_tho", "standard_term": "Khó thở", "category": "Hô hấp"},
            "chóng mặt": {"id": "chong_mat", "standard_term": "Chóng mặt", "category": "Thần kinh"},
            "nhức đầu": {"id": "dau_dau", "standard_term": "Đau đầu", "category": "Thần kinh"},
            "đau đầu": {"id": "dau_dau", "standard_term": "Đau đầu", "category": "Thần kinh"},
            "mờ mờ": {"id": "sym_nhin_mo", "standard_term": "Nhìn mờ / Giảm thị lực", "category": "Mắt"},
            "nhòe nhòe": {"id": "sym_nhin_mo", "standard_term": "Nhìn mờ / Giảm thị lực", "category": "Mắt"},
            "cộm xốn": {"id": "sym_kho_mat", "standard_term": "Khô mắt / Cộm rát mắt", "category": "Mắt"},
            "xốn xốn": {"id": "sym_kho_mat", "standard_term": "Khô mắt / Cộm rát mắt", "category": "Mắt"},
            "cộm cộm": {"id": "sym_kho_mat", "standard_term": "Khô mắt / Cộm rát mắt", "category": "Mắt"},
        }
        for phr, entry in specific_synonyms.items():
            self.exact_lookup[phr] = entry
            if phr not in seen_terms:
                self.concepts.append(entry)
                seen_terms.add(phr)

        # Backward compatibility view
        for c in self.concepts:
            self.synonyms_map[c["id"]] = {"standard_term": c["standard_term"], "synonyms": []}

    def _init_dense_embedder(self):
        """Khởi tạo không gian vector ngữ nghĩa ký tự (Character N-gram TF-IDF Vector Space)."""
        terms = [c["standard_term"] for c in self.concepts]
        if not terms:
            return
        try:
            self.vectorizer = TfidfVectorizer(analyzer='char_wb', ngram_range=(2, 4))
            self.concept_embeddings = self.vectorizer.fit_transform(terms)
            logger.info(f"TF-IDF Char N-Gram Normalizer initialized with {len(terms)} concepts and {self.concept_embeddings.shape[1]} features.")
        except Exception as e:
            logger.error(f"Error initializing TF-IDF Char N-Gram Normalizer: {e}")

    def normalize(self, raw_entity: str) -> Dict[str, Any]:
        """
        Ánh xạ một thực thể lâm sàng về khái niệm y khoa chuẩn sử dụng:
        1. Tra cứu chính xác từ vựng lâm sàng (Exact & Synonym Lookup O(1)).
        2. Cosine Similarity trong Không gian Vector TF-IDF Char N-gram.
        3. Tích hợp Bộ Lọc Ranh Giới Giải Phẫu (Anatomical Domain Consistency) để triệt tiêu False Positives.
        """
        cleaned = raw_entity.strip()
        if not cleaned:
            return {"id": "unknown", "standard_term": "", "matched": False}

        cleaned_lower = cleaned.lower()

        # Bỏ qua các từ phụ trợ, trạng từ chỉ mức độ quá chung chung
        stop_words = {"quá", "rất", "hơi", "lắm", "nhiều", "ít", "mới", "tự nhiên", "bùng phát", "sau khi"}
        if cleaned_lower in stop_words or len(cleaned_lower) < 2:
            return {"id": "unknown", "standard_term": "", "matched": False}

        # 1. Tra cứu nhanh trực tiếp trong từ điển đồng nghĩa (Exact Synonym Lookup)
        if cleaned_lower in self.exact_lookup:
            matched = self.exact_lookup[cleaned_lower]
            return {
                "id": matched["id"],
                "standard_term": matched["standard_term"],
                "similarity_score": 1.0,
                "matched": True,
                "method": "exact_lexicon_synonym"
            }

        # 2. Nếu mô hình nhúng vector hoạt động
        if self.concept_embeddings is not None and self.vectorizer is not None and len(self.concepts) > 0:
            try:
                query_vec = self.vectorizer.transform([cleaned])
                similarities = cosine_similarity(self.concept_embeddings, query_vec).flatten()
                best_idx = int(np.argmax(similarities))
                best_score = float(similarities[best_idx])
                matched_concept = self.concepts[best_idx]
                target_id = matched_concept.get("id", "").lower()
                target_term = matched_concept.get("standard_term", "").lower()

                # Kiểm tra tính nhất quán giải phẫu y khoa (Anatomical Consistency Guard)
                # 1. Hô hấp (Ho, Đờm): Tuyệt đối không map nếu cụm từ không chứa gốc từ hô hấp
                respiratory_roots = ["ho", "đờm", "dom", "khạc", "họng", "phổi", "thở", "suyễn", "phế quản"]
                if ("ho" in target_id or "dom" in target_id or "ho" in target_term or "đờm" in target_term) and not any(k in cleaned_lower for k in respiratory_roots):
                    best_score = 0.0

                # Nếu cụm từ rõ ràng là triệu chứng da liễu, cấm map sang bệnh/triệu chứng hô hấp
                dermatology_roots = ["da", "mặt", "mẩn", "ửng", "ngứa", "chàm", "nắng", "mỹ phẩm", "kem", "dị ứng", "rát", "sẩn", "vảy"]
                if any(dr in cleaned_lower for dr in dermatology_roots):
                    if any(rr in target_id or rr in target_term for rr in ["ho_", "dom", "phe_quan", "phoi", "amidan"]):
                        best_score = 0.0

                # 2. Tiêu hóa (Bụng, Tiêu chảy): Không map nếu không có gốc tiêu hóa
                if ("tieu_chay" in target_id or "dau_bung" in target_id) and not any(k in cleaned_lower for k in ["bụng", "tiêu", "phân", "dạ dày", "ruột", "đi ngoài", "nôn", "ói"]):
                    best_score = 0.0

                # 3. Tim mạch (Đau ngực): Không map nếu không có ngực/tim
                if "dau_nguc" in target_id and not any(k in cleaned_lower for k in ["ngực", "tim", "sườn", "vành"]):
                    best_score = 0.0

                # 4. Tiết niệu (Tiểu buốt, Tiểu rắt): Cấm map nếu không có từ liên quan đến tiểu tiện
                if ("tieu_" in target_id or "tiểu" in target_term or "tieu_buot" in target_id) and not any(k in cleaned_lower for k in ["tiểu", "đái", "niệu", "bàng quang"]):
                    best_score = 0.0

                # 5. Răng hàm mặt: Cấm map sang răng nếu không chứa răng, nướu, lợi
                if ("rang" in target_id or "răng" in target_term) and not any(k in cleaned_lower for k in ["răng", "nướu", "lợi", "nhai"]):
                    best_score = 0.0

                # 6. Nhi khoa / Khuyết tật: Cấm map sang chậm phát triển ngôn ngữ
                if "cham_phat_trien" in target_id or "ngôn ngữ" in target_term:
                    best_score = 0.0

                # 7. Mắt & Thị giác: Nếu cụm từ chứa mắt/nhìn, tuyệt đối cấm map sang cơ toàn thân hoặc da liễu
                eye_roots = ["mắt", "mat", "thị", "nhìn", "nhãn"]
                if any(er in cleaned_lower for er in eye_roots):
                    if not any(er in target_id or er in target_term for er in eye_roots):
                        best_score = 0.0

                # 8. Thần kinh / Đau đầu: Cấm map sang đau đầu nếu cụm từ không chứa gốc từ sọ não / đầu
                head_roots = ["đầu", "dau", "trán", "thái dương", "nửa đầu", "chẩm", "đỉnh đầu"]
                if ("dau_dau" in target_id or "đầu" in target_term) and not any(k in cleaned_lower for k in head_roots):
                    best_score = 0.0

                # 9. Đau mỏi cơ / Toàn thân: Nếu cụm từ là cảm giác mỏi cơ/ê ẩm, cấm map sang đau đầu hoặc tim mạch
                if any(m_kw in cleaned_lower for m_kw in ["mỏi", "mệt", "ê ẩm", "toàn thân"]):
                    if "dau_dau" in target_id or "dau_nguc" in target_id:
                        best_score = 0.0

                # Ngưỡng cosine similarity lâm sàng nghiêm ngặt: nâng lên >= 0.65
                if best_score >= 0.65:
                    return {
                        "id": matched_concept["id"],
                        "standard_term": matched_concept["standard_term"],
                        "similarity_score": round(best_score, 4),
                        "matched": True,
                        "method": "dense_vector_embedding"
                    }
            except Exception as e:
                logger.error(f"Error during semantic vector normalization: {e}")

        # Loại bỏ các token rác, cụm từ con hoặc tính từ đệm không có giá trị triệu chứng độc lập
        adjective_noise = {"ẩm", "ê ẩm", "nặng", "nhẹ", "lâu", "nhiều", "ít", "đỡ", "tăng", "hẳn", "mấy", "quá", "lắm", "_m"}
        if len(cleaned.strip()) < 3 or cleaned_lower in adjective_noise:
            return {
                "id": "unknown",
                "standard_term": "",
                "similarity_score": 0.0,
                "matched": False,
                "method": "filtered_noise_fragment"
            }

        # Giữ nguyên nhãn nơ-ron nếu độ tương đồng dưới ngưỡng
        clean_id = re.sub(r'[^a-zA-Z0-9_]', '_', cleaned.lower())
        return {
            "id": clean_id,
            "standard_term": cleaned.capitalize(),
            "similarity_score": 0.0,
            "matched": False,
            "method": "neural_token_literal"
        }
