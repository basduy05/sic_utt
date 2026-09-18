import urllib.request
import json
import time

url = "http://127.0.0.1:8000/api/v1/chat/message"
payload = {
    "session_id": "test-speed-appendicitis",
    "message": "Tôi bị đau quặn bụng dưới bên phải, sốt nhẹ và buồn nôn",
    "message_type": "text",
    "chat_history": []
}

data = json.dumps(payload).encode("utf-8")
req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

print("Sending new clinical query...")
start_time = time.time()
try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        elapsed = time.time() - start_time
        res_json = json.loads(resp.read().decode("utf-8"))
        print(f"Success in {elapsed:.2f} seconds!")
        print("Status code:", resp.status)
        print("Latency reported by backend:", res_json.get("latency_ms"), "ms")
        print("Provider breakdown:", res_json.get("pipeline_breakdown", {}))
        telemetry = res_json.get("telemetry", {})
        print("Detected symptoms:", [s.get("standard_term") for s in telemetry.get("symptoms", [])])
        print("Top predictions:", [(p.get("icd_code"), p.get("disease_name"), f"{p.get('confidence_score', 0)*100:.1f}%") for p in telemetry.get("top_predictions", [])[:2]])
except Exception as e:
    elapsed = time.time() - start_time
    print(f"Failed after {elapsed:.2f}s: {e}")
