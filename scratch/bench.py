import time
import sys
import os

sys.path.append(os.path.abspath("apps/ai_engine"))
from src.pipeline import MultimodalTriagePipeline

t0 = time.time()
p = MultimodalTriagePipeline()
t1 = time.time()
print(f"Pipeline init time: {t1 - t0:.2f}s")

res = p.process_multimodal_request(text="Tôi bị sốt 38.5 độ và đau mỏi hốc mắt")
t2 = time.time()
print(f"Pipeline process time: {t2 - t1:.2f}s")
syms = [s.get('standard_term') for s in res.get('extracted_entities', {}).get('symptoms', [])]
print(f"Symptoms count: {len(syms)}")
print(f"Top triage: {[t.get('disease_name') for t in res.get('triage_results', [])[:2]]}")
