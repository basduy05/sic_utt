import urllib.request
import json
import time
import sys

sys.stdout.reconfigure(encoding='utf-8')

url = "http://127.0.0.1:8000/api/v1/chat/message"
session_id = f"test-provisional-{int(time.time())}"

print("=== TESTING PROVISIONAL HYPOTHESIS TIER (40% - 75%) ===")

# Message with 2 moderate symptoms giving ~50-60% confidence
msg = "Tôi bị ợ chua và cảm thấy hơi tức tức ở vùng ngực"
payload = {
    "session_id": session_id,
    "message": msg,
    "message_type": "text",
    "chat_history": []
}

data = json.dumps(payload).encode("utf-8")
req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req, timeout=30) as resp:
    res = json.loads(resp.read().decode("utf-8"))
    print("\n--- RESPONSE ---")
    telemetry = res.get("telemetry", {})
    print("Telemetry keys:", telemetry.keys())
    print("Clarification in telemetry:", telemetry.get("clarification"))
    print("Top predictions:", [(p.get('icd_code'), p.get('disease_name_vi'), p.get('probability_percentage')) for p in telemetry.get('top_predictions', [])])
    print("\nAI Response text:")
    print(res.get("text_content"))
