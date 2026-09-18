import sys, os, json, numpy as np
sys.path.append(os.path.abspath('apps/ai_engine'))
from src.classification.predictor import HybridClinicalPredictor

p = HybridClinicalPredictor()
user_text = 'tôi bị đau đầu . Đau giật nhói theo nhịp mạch ở nửa bên đầu, Đau căng tức cả hai bên thái dương và trán, Cảm giác chao đảo, bồng bềnh, đồ vật xoay tròn . Sợ ánh sáng chói hoặc tiếng động lớn, Kèm buồn nôn hoặc nôn mửa đột ngột'

# Run step by step
X_vec = p.nlp_vectorizer.transform([user_text])
inferred_probs = p.nlp_clf.predict_proba(X_vec)[0]

g43_idx = [i for i, d in enumerate(p.disease_classes) if d.get('code') == 'G43.9'][0]

# check tabular
prob_tabular = p.tabular_model.predict_proba({}, [])
p_final, alpha_used = p.fusion_layer.fuse(prob_tabular, inferred_probs, has_lab_data=False)
p_final_after_fuse = float(p_final[g43_idx])

# check overlap mask
overlap_mask = np.zeros(len(p.disease_classes), dtype=bool)
# check for G43.9
d = p.disease_classes[g43_idx]
code = d.get("code")
info = p.icd_db.get(code, {})
cardinal = [cs.lower() for cs in info.get("cardinal_symptoms", [])]
all_syms = [s.lower() for s in info.get("all_symptoms", [])]
name_vi = d.get("name", "").lower()

# Let's see what full p.predict does
res = p.predict(user_text, [], {})

# Check what happened in overlap_mask
step_log = {
    "g43_idx": g43_idx,
    "p_final_after_fuse": p_final_after_fuse,
    "cardinal": cardinal,
    "all_syms": all_syms,
}

# Reproduce gatekeeper exactly:
user_text_lower = user_text.lower()
words = [w for w in user_text_lower.replace('.', ' ').replace(',', ' ').split() if len(w) >= 2]
step_log["user_text_words_sample"] = words[:10]

with open('scratch/step_log.json', 'w', encoding='utf-8') as f:
    json.dump(step_log, f, ensure_ascii=False, indent=2)
