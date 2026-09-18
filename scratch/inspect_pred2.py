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

# Let's see num_classes
print("Total disease classes:", len(predictor.disease_classes))

# Run internal step
symptom_ids = [s.get("id", "") for s in symptoms]
prob_tab = predictor.tabular_model.predict_proba({}, symptom_ids)
print("prob_tab length:", len(prob_tab))
print("prob_tab sum:", np.sum(prob_tab))

# Let's inspect NLP clf
print("nlp_clf loaded:", predictor.nlp_clf is not None)
if predictor.nlp_clf is not None:
    X = predictor.nlp_vectorizer.transform([text])
    p_nlp = predictor.nlp_clf.predict_proba(X)[0]
    print("p_nlp length:", len(p_nlp))
    print("p_nlp max:", np.max(p_nlp), "at idx:", np.argmax(p_nlp))

# Let's check overlap mask
num_classes = len(predictor.disease_classes)
for idx, d in enumerate(predictor.disease_classes):
    code = d.get("code")
    name = d.get("name")
    if code in ["K29.7", "K21.9", "A09", "K35.8"]:
        print(f"Disease {code} - {name} at index {idx}")
