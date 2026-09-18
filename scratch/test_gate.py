import sys, os, json
sys.path.append(os.path.abspath('apps/ai_engine'))
from src.classification.predictor import HybridClinicalPredictor

p = HybridClinicalPredictor()
user_text = 'tôi bị đau đầu . Đau giật nhói theo nhịp mạch ở nửa bên đầu, Đau căng tức cả hai bên thái dương và trán, Cảm giác chao đảo, bồng bềnh, đồ vật xoay tròn . Sợ ánh sáng chói hoặc tiếng động lớn, Kèm buồn nôn hoặc nôn mửa đột ngột'
info = p.icd_db.get('G43.9', {})

# Let's see what p.predict does step by step:
# 1. NLP probabilities:
X_vec = p.nlp_vectorizer.transform([user_text])
inferred_probs = p.nlp_clf.predict_proba(X_vec)[0]

# Find index of G43.9
g43_idx = [i for i, d in enumerate(p.disease_classes) if d.get('code') == 'G43.9'][0]

res = p.predict(user_text, [], {})

out = {
    "G43.9_code": "G43.9",
    "G43.9_name": p.disease_classes[g43_idx].get('name'),
    "G43.9_prob_nlp": float(inferred_probs[g43_idx]),
    "G43.9_icd_info": info,
    "predict_result": res
}

with open('scratch/gate_check.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print("Done writing scratch/gate_check.json")
