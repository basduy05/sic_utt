import pytest
from ..src.ner.medical_ner import MedicalNER
from ..src.ner.red_flag_detector import RedFlagDetector

def test_red_flag_cardiac_emergency():
    detector = RedFlagDetector()
    text = "Bệnh nhân đau ngực dữ dội lan ra cánh tay trái và vã mồ hôi khó thở."
    res = detector.evaluate(text)
    assert res["is_emergency"] is True
    assert res["latency_seconds"] <= 0.5
    assert len(res["triggered_flags"]) > 0
    assert "Nhồi máu cơ tim" in res["triggered_flags"][0]["disease_group"]

def test_red_flag_stroke_emergency():
    detector = RedFlagDetector()
    text = "Bác nhà tôi bị méo miệng và nói ngọng đột ngột."
    res = detector.evaluate(text)
    assert res["is_emergency"] is True
    assert res["latency_seconds"] <= 0.5

def test_medical_ner_symptom_extraction():
    ner = MedicalNER()
    text = "Tôi bị sốt cao 39 độ, đau đầu và chảy máu chân răng từ 3 ngày trước."
    res = ner.extract_entities(text)
    symptoms = [s["standard_term"] for s in res["symptoms_normalized"]]
    assert any("Sốt" in s for s in symptoms)
    assert any("Đau đầu" in s for s in symptoms)
    assert res["vital_signs"]["temperature"] == 39.0
