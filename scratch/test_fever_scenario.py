import urllib.request
import json
import time
import sys

sys.stdout.reconfigure(encoding='utf-8')

url = "http://127.0.0.1:8000/api/v1/chat/message"
session_id = f"test-fever-{int(time.time())}"

turns = [
    "Tôi bị sốt cao 39 độ từ tối qua, uống thuốc hạ sốt mà không thấy đỡ thì bị gì?",
    "Người tôi đau nhức khắp các khớp với ê buốt hai hốc mắt nữa, có phải bị cúm hay sốt xuất huyết không?",
    "Hôm nay sang ngày thứ 3 tôi thấy da nổi mấy chấm đỏ li ti ở tay, ấn vào không mất, thế là dấu hiệu gì?",
    "Bây giờ tôi nên uống thuốc gì và ăn uống thế nào để hạ sốt?",
    "Dấu hiệu nào thì bắt buộc phải vào viện cấp cứu ngay?"
]

history = []

for i, turn_text in enumerate(turns, 1):
    print(f"\n==================== TURN {i} ====================")
    print(f"USER: {turn_text}")
    payload = {
        "session_id": session_id,
        "message": turn_text,
        "message_type": "text",
        "chat_history": history
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        telemetry = res.get("telemetry", {})
        symptoms = [s.get("standard_term") for s in telemetry.get("symptoms", [])]
        preds = [(p.get("icd_code"), p.get("disease_name_vi"), p.get("probability_percentage")) for p in telemetry.get("top_predictions", [])]
        stage = telemetry.get("clarification", {}).get("clinical_stage")
        print(f"Stage: {stage}")
        print(f"Detected symptoms: {symptoms}")
        print(f"Top predictions: {preds}")
        print("\nAI CONTENT:\n" + res.get("text_content", ""))

        history.append({"sender": "user", "content": turn_text})
        history.append({"sender": "assistant", "content": res.get("text_content", "")})
