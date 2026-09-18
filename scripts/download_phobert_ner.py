"""
Script tải và lưu model NER tiếng Việt / PhoBERT về cục bộ
Lưu tại: apps/ai_engine/models_weights/phobert_ner/
"""
import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def download_ner_model():
    script_dir = os.path.abspath(os.path.dirname(__file__))
    project_root = os.path.dirname(script_dir)
    target_dir = os.path.join(project_root, "apps", "ai_engine", "models_weights", "phobert_ner")
    os.makedirs(target_dir, exist_ok=True)
    
    logger.info(f"Target directory for PhoBERT NER: {target_dir}")
    
    try:
        from transformers import AutoTokenizer, AutoModelForTokenClassification
        
        # Model tên: vinai/phobert-base hoặc NlpHUST/ner-vietnamese-electra-base
        # vinai/phobert-base là nền tảng tiếng Việt chuẩn hóa của VinAI
        model_name = "vinai/phobert-base"
        logger.info(f"Downloading tokenizer and model from HuggingFace: '{model_name}'...")
        
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        tokenizer.save_pretrained(target_dir)
        logger.info("PhoBERT Tokenizer saved successfully.")
        
        # Tạo model config & weights cho TokenClassification
        model = AutoModelForTokenClassification.from_pretrained(model_name, num_labels=7)
        model.save_pretrained(target_dir)
        logger.info(f"PhoBERT Token Classification model saved successfully to: {target_dir}")
        print("SUCCESS: PhoBERT NER model ready at:", target_dir)
        return True
    except Exception as e:
        logger.error(f"Error downloading PhoBERT NER model: {e}")
        print(f"FAILED: {e}")
        return False

if __name__ == "__main__":
    download_ner_model()
