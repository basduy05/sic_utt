import sys
import os
import json

sys.stdout.reconfigure(encoding='utf-8')

sys.path.append(os.path.abspath("apps/ai_engine"))
from src.pipeline import MultimodalTriagePipeline

p = MultimodalTriagePipeline()

# Test 1: User message 1
text1 = "Tôi bị đau quặn bụng cồn cào trên rốn sau khi ăn kèm buồn nôn và ợ chua"
res1 = p.process_multimodal_request(text=text1)
print("=== TEST 1 ===")
print("Symptoms count:", len(res1['extracted_entities']['symptoms']))
for s in res1['extracted_entities']['symptoms']:
    print("  -", s.get('standard_term'), "id:", s.get('id'))
print("Triage results count:", len(res1['triage_results']))
for t in res1['triage_results']:
    print("  -", t.get('icd_code'), t.get('disease_name_vi'), t.get('probability_percentage'))

# Test 2: Clarification message
text2 = "Đau quặn / cồn cào vùng thượng vị (trên rốn) . Buồn nôn hoặc nôn mửa thức ăn . Ợ chua, ợ hơi nóng rát lên cổ . Chướng bụng, đầy hơi khó tiêu"
res2 = p.process_multimodal_request(text=text2)
print("=== TEST 2 ===")
print("Symptoms count:", len(res2['extracted_entities']['symptoms']))
for s in res2['extracted_entities']['symptoms']:
    print("  -", s.get('standard_term'), "id:", s.get('id'))
print("Triage results count:", len(res2['triage_results']))
for t in res2['triage_results']:
    print("  -", t.get('icd_code'), t.get('disease_name_vi'), t.get('probability_percentage'))
