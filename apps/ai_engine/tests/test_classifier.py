import pytest
from ..src.classification.predictor import HybridClinicalPredictor
from ..src.classification.fusion_layer import HybridLateFusionLayer
from ..src.pipeline import MultimodalTriagePipeline

def test_hybrid_prediction_dengue():
    predictor = HybridClinicalPredictor()
    symptoms = [{"id": "sot_cao", "standard_term": "Sốt cao"}, {"id": "chay_mau_chan_rang", "standard_term": "Xuất huyết"}]
    lab_indicators = {"WBC": {"value": 3.1}, "PLT": {"value": 55.0}}
    
    res = predictor.predict("Sốt cao và chảy máu chân răng", symptoms, lab_indicators)
    top_pred = res["top_predictions"][0]
    assert top_pred["icd_code"] == "A90"
    assert "Dengue" in top_pred["disease_name_vi"]
    assert top_pred["probability"] > 0.40

def test_clarification_loop_trigger_on_ambiguous_symptoms():
    predictor = HybridClinicalPredictor()
    symptoms = [{"id": "dau_dau", "standard_term": "Đau đầu"}]
    lab_indicators = {}
    
    res = predictor.predict("Hơi đau đầu", symptoms, lab_indicators)
    clarification = res["clarification"]
    assert clarification["needs_clarification"] is True
    assert len(clarification["questions"]) > 0

def test_multimodal_pipeline_orchestration():
    pipeline = MultimodalTriagePipeline()
    result = pipeline.process_multimodal_request(text="Tôi bị sốt cao 39 độ và mệt mỏi")
    assert "triage_results" in result
    assert len(result["triage_results"]) > 0
    assert result["is_emergency"] is False
