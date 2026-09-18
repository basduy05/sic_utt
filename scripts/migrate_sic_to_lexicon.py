import os
import json
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("MigrateSIC")

def main():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    sic_path = os.path.join(base_dir, "data", "sic", "icd10.json")
    lexicon_path = os.path.join(base_dir, "data", "medical_lexicon", "icd10_codes.json")
    
    if not os.path.exists(sic_path):
        logger.error(f"Cannot find {sic_path}")
        return
        
    with open(sic_path, "r", encoding="utf-8") as f:
        sic_data = json.load(f)
        
    new_icd_codes = {}
    
    for d in sic_data.get("diseases", []):
        code = d.get("disease_id")
        if not code:
            continue
            
        name = d.get("disease_name", "")
        dept = d.get("chapter_specialty", "Đa khoa")
        symptoms_raw = d.get("symptoms", [])
        
        cardinal = []
        all_syms = []
        for s in symptoms_raw:
            s_name = s.get("symptom_name", "")
            if s_name:
                all_syms.append(s_name)
                # If omega > 0.65 or weight_disease > 0.8, consider it cardinal
                if s.get("omega", 0) > 0.65 or s.get("weight_disease", 0) > 0.8:
                    cardinal.append(s_name)
                    
        # If no cardinal found based on weights, just take the first 2-3
        if not cardinal and all_syms:
            cardinal = all_syms[:3]
            
        # Description can be joined from symptom descriptions if not provided at disease level
        desc = name
        
        new_icd_codes[code] = {
            "name_vi": name,
            "department": dept,
            "cardinal_symptoms": cardinal,
            "all_symptoms": all_syms,
            "description": desc,
            "emergency_warning": "Theo dõi và thăm khám nếu triệu chứng trở nặng.",
            "severity": "Medium"
        }
        
    # Read existing lexicon and update it
    existing = {}
    if os.path.exists(lexicon_path):
        with open(lexicon_path, "r", encoding="utf-8") as f:
            existing = json.load(f)
            
    existing.update(new_icd_codes)
    
    with open(lexicon_path, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
        
    logger.info(f"Successfully migrated {len(new_icd_codes)} diseases from SIC to medical_lexicon. Total in lexicon now: {len(existing)}")

if __name__ == "__main__":
    main()
