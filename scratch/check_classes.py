import sys
import os
import json

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.abspath("apps/ai_engine"))
from src.classification.predictor import HybridClinicalPredictor

predictor = HybridClinicalPredictor()
print("Predictor disease classes count:", len(predictor.disease_classes))
print("icd10_codes.json count:", len(predictor.icd_db))

# What are the classes in predictor.disease_classes?
codes_in_pred = [d["code"] for d in predictor.disease_classes]
print("Unique codes in pred:", len(set(codes_in_pred)))

# Check duplicates or extras
from collections import Counter
c = Counter(codes_in_pred)
duplicates = [k for k, v in c.items() if v > 1]
print("Duplicates in pred:", duplicates)

# What are the classes in nlp_clf?
if predictor.nlp_clf is not None:
    print("NLP classes count:", len(predictor.nlp_clf.classes_))
    # difference
    diff1 = set(codes_in_pred) - set(predictor.nlp_clf.classes_)
    diff2 = set(predictor.nlp_clf.classes_) - set(codes_in_pred)
    print("In pred but not in NLP clf:", diff1)
    print("In NLP clf but not in pred:", diff2)
