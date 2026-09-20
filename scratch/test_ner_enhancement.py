import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("apps/ai_engine"))
import json

from apps.ai_engine.src.ner.medical_ner import MedicalNER

ner = MedicalNER()

test_cases = [
    "tôi bị ho và sốt nhẹ từ hôm qua",
    "mắt em cứ mờ mờ nhòe nhòe cộm xốn, nhìn gần không rõ",
    "bụng ậm ạch cồn cào buồn nôn sau khi ăn",
    "ngực cứ tức tức khó thở khi leo cầu thang",
    "tôi không bị ho, chỉ bị ngứa ngáy và rát da thôi"
]

print("=== TESTING ENHANCED MEDICAL NER & NORMALIZER ===")
for text in test_cases:
    res = ner.extract_entities(text)
    syms = [s["standard_term"] for s in res["symptoms_normalized"]]
    negs = [s["standard_term"] for s in res["negated_symptoms"]]
    print(f"\nText: \"{text}\"")
    print(f"  -> Extracted Symptoms: {syms}")
    print(f"  -> Negated: {negs}")
    if res.get("duration"):
        print(f"  -> Duration: {res['duration']}")
