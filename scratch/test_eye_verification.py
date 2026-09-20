import sys
import os
import json

sys.path.insert(0, os.path.abspath('apps/backend'))
sys.path.insert(0, os.path.abspath('apps/ai_engine'))

from src.ner.entity_normalizer import EntityNormalizer
from src.classification.clarification_engine import clarification_engine

norm = EntityNormalizer()
res_moi = norm.normalize("mỏi mắt")
res_dau = norm.normalize("đau mắt")
res_kho = norm.normalize("khô mắt")

print("NORM MOI MAT:", res_moi.get("id"), res_moi.get("similarity_score"))
print("NORM DAU MAT:", res_dau.get("id"), res_dau.get("similarity_score"))
print("NORM KHO MAT:", res_kho.get("id"), res_kho.get("similarity_score"))

# Test Clarification Engine
qs_eye = clarification_engine.generate_context_aware_questions(
    user_text="tôi bị mỏi mắt",
    detected_symptoms=[res_moi.get("standard_term")],
    top_disease_codes=["H52.4"]
)
print("QUESTIONS COUNT:", len(qs_eye))
for q in qs_eye:
    print("Q_ID:", q.get("id"))
    print("OPTIONS_COUNT:", len(q.get("options", [])))

has_derma = any("da" in q.get("id") or "da" in q.get("question").lower() for q in qs_eye)
print("HAS DERMA QUESTIONS:", has_derma)
assert not has_derma, "FAIL: Dermatology questions should NOT be asked for eye symptoms!"
print("TEST SUCCESS: 100% EYE QUESTIONS RELEVANT!")
