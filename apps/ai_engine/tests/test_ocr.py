import pytest
from ..src.ocr.lab_sanity_checker import LabSanityChecker
from ..src.ocr.pdf_parser import PDFLabParser

def test_lab_sanity_checker_wbc_autocorrect():
    checker = LabSanityChecker()
    # Test case: OCR reading missing decimal (e.g. 320 instead of 3.2)
    corrected, status, msg = checker.validate_and_correct("WBC", 320.0)
    assert corrected == 3.2
    assert status == "LOW"

def test_lab_sanity_checker_plt_critical():
    checker = LabSanityChecker()
    # Test case: Low platelet count < 50
    corrected, status, msg = checker.validate_and_correct("PLT", 38.0)
    assert corrected == 38.0
    assert status == "CRITICAL_LOW"

def test_pdf_lab_parser_extraction():
    parser = PDFLabParser()
    sample_text = """
    KẾT QUẢ XÉT NGHIỆM MÁU
    WBC : 3.4 10^9/L
    PLT : 75 10^9/L
    RBC : 4.5 10^12/L
    HGB : 138 g/L
    """
    res = parser.extract_lab_values_from_text(sample_text)
    assert "WBC" in res["parsed_indicators"]
    assert "PLT" in res["parsed_indicators"]
    assert res["parsed_indicators"]["PLT"]["value"] == 75.0
    assert res["parsed_indicators"]["PLT"]["status"] == "LOW"
