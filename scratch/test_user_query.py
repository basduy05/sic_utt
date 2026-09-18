import urllib.request
import json
import time
import sys

sys.stdout.reconfigure(encoding='utf-8')

url = "http://127.0.0.1:8000/api/v1/chat/message"

# Test message from user
payload = {
    "session_id": "test-user-stomach-issue",
    "message": "Tôi bị đau quặn bụng cồn cào trên rốn sau khi ăn kèm buồn nôn và ợ chua",
    "message_type": "text",
    "chat_history": []
}

data = json.dumps(payload).encode("utf-8")
req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

print("Sending user request...")
start_time = time.time()
with urllib.request.urlopen(req, timeout=30) as resp:
    elapsed = time.time() - start_time
    res_json = json.loads(resp.read().decode("utf-8"))
    print(f"Success in {elapsed:.2f} seconds!")
    print("Latency reported by backend:", res_json.get("latency_ms"), "ms")
    print("\n--- AI TEXT CONTENT ---")
    print(res_json.get("text_content"))
    print("\n--- TELEMETRY TOP PREDICTIONS ---")
    top_preds = res_json.get("telemetry", {}).get("top_predictions", [])
    print("Count:", len(top_preds))
    for p in top_preds:
        print(" ->", p.get("icd_code"), p.get("disease_name_vi"), p.get("probability_percentage"), p.get("department"))
