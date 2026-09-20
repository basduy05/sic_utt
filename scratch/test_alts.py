import sys
import json
import urllib.request
sys.stdout.reconfigure(encoding='utf-8')

url = "http://127.0.0.1:8000/api/v1/chat/message"
payload = {
    "session_id": "test_alts_001",
    "message": "Tôi bị sốt xuất huyết, và triệu chứng của nó",
    "chat_history": []
}

req = urllib.request.Request(
    url,
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)

with urllib.request.urlopen(req, timeout=30) as resp:
    data = json.loads(resp.read().decode("utf-8"))
    print("=== PRIMARY RESPONSE ===")
    print("Provider:", data.get("provider"))
    print(data.get("text_content")[:400] + "...")
    print("\n=== ALTERNATIVE ANSWERS ===")
    alts = data.get("alternative_answers", [])
    for idx, alt in enumerate(alts):
        print(f"Alt {idx+1} Provider:", alt.get("provider"))
        print(f"Alt {idx+1} Text:\n", alt.get("text")[:500] + "...")
