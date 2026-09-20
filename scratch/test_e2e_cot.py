import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
import urllib.request
import json

url = "http://127.0.0.1:8000/api/v1/chat/message"
payload = {
    "session_id": "test_e2e_cot_001",
    "message": "Mắt tôi cứ mờ mờ, nhìn gần không rõ, đọc sách hay dùng máy tính khoảng 15 phút là bị mỏi mắt cộm xốn",
    "chat_history": []
}

req = urllib.request.Request(
    url,
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)

print("=== SENDING TEST MESSAGE TO BACKEND ===")
with urllib.request.urlopen(req, timeout=45) as resp:
    data = json.loads(resp.read().decode("utf-8"))
    
    telemetry = data.get("telemetry") or {}
    clarification = telemetry.get("clarification") or {}
    
    print("\n--- STATUS ---")
    print(f"Status Code: {resp.status}")
    print(f"Session ID: {data.get('session_id')}")
    print(f"Clinical Stage: {clarification.get('clinical_stage')}")
    print(f"Provider: {data.get('alternative_answers', [{}])[0].get('provider', 'N/A')}")
    
    print("\n--- SYMPTOMS EXTRACTED ---")
    for s in telemetry.get("symptoms", []):
        print(f"  - ID: {s.get('id')}, Standard Term: {s.get('standard_term')}")
        
    print("\n--- TOP PREDICTED DISEASES ---")
    for d in telemetry.get("top_predictions", [])[:3]:
        print(f"  - {d.get('disease_name_vi')} ({d.get('icd_code')}): {d.get('probability_percentage')} [{d.get('department')}]")
        
    print("\n--- CLINICAL THINKING (COT) CHECK ---")
    text = data.get("text_content", "")
    if "<clinical_thinking>" in text and "</clinical_thinking>" in text:
        cot_start = text.find("<clinical_thinking>") + len("<clinical_thinking>")
        cot_end = text.find("</clinical_thinking>")
        cot_content = text[cot_start:cot_end].strip()
        print("✅ CLINICAL THINKING FOUND:")
        print(cot_content)
    else:
        print("❌ NO CLINICAL THINKING FOUND IN RESPONSE!")
        
    print("\n--- FULL RESPONSE PREVIEW (First 700 chars) ---")
    print(text[:700] + "...")
