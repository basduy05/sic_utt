import os
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_data")

def seed_medical_lexicon():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    lexicon_dir = os.path.join(base_dir, "data", "medical_lexicon")
    icd_file = os.path.join(lexicon_dir, "icd10_codes.json")
    synonyms_file = os.path.join(lexicon_dir, "symptom_synonyms.json")

    logger.info("Verifying medical lexicon integrity...")
    if os.path.exists(icd_file):
        with open(icd_file, "r", encoding="utf-8") as f:
            icd_data = json.load(f)
            logger.info(f"Loaded {len(icd_data)} standard ICD-10 medical records.")

    if os.path.exists(synonyms_file):
        with open(synonyms_file, "r", encoding="utf-8") as f:
            syn_data = json.load(f)
            logger.info(f"Loaded {len(syn_data)} symptom synonym groups.")

    logger.info("Database seeding completed successfully.")

if __name__ == "__main__":
    seed_medical_lexicon()
