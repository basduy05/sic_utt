import sys
import os
import json
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.abspath("apps/ai_engine"))
from src.classification.predictor import HybridClinicalPredictor

predictor = HybridClinicalPredictor()

text = "Tôi bị đau quặn bụng cồn cào trên rốn sau khi ăn kèm buồn nôn và ợ chua"
symptoms = [
    {"id": "dau_bung", "standard_term": "Đau cồn cào"},
    {"id": "sym_đắng_miệng", "standard_term": "Đắng miệng"},
    {"id": "sym_buồn_nôn", "standard_term": "Buồn nôn"},
    {"id": "sym_ợ_chua", "standard_term": "Ợ chua"}
]

res = predictor.predict(user_text=text, normalized_symptoms=symptoms, lab_indicators={})

print("Predicted count:", len(res['top_predictions']))
for p in res['top_predictions']:
    print(p)
print("Clarification:", res['clarification'])
