import urllib.request
import json
import time
import sys

sys.stdout.reconfigure(encoding='utf-8')

url = "http://127.0.0.1:8000/api/v1/chat/message"
session_id = "test-session-multiturn-stomach"

# Turn 1
msg1 = "Tôi bị đau quặn bụng cồn cào trên rốn sau khi ăn kèm buồn nôn và ợ chua"
payload1 = {
    "session_id": session_id,
    "message": msg1,
    "message_type": "text",
    "chat_history": []
}

data1 = json.dumps(payload1).encode("utf-8")
req1 = urllib.request.Request(url, data=data1, headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req1, timeout=30) as resp1:
    res1 = json.loads(resp1.read().decode("utf-8"))
    print("=== TURN 1 RESULTS ===")
    print("Top predictions:", [(p.get('icd_code'), p.get('disease_name_vi'), p.get('probability_percentage')) for p in res1.get('telemetry', {}).get('top_predictions', [])])

# Turn 2: Clarification
msg2 = 'Trả lời câu hỏi làm rõ: "Tôi xin bổ sung thông tin lâm sàng: Cơn đau bụng của bạn khu trú ở đâu và xuất hiện vào lúc nào?: Đau quặn / cồn cào vùng thượng vị (trên rốn) | Bạn có gặp các triệu chứng trào ngược tiêu hóa đi kèm không?: Buồn nôn hoặc nôn mửa thức ăn, Ợ chua, ợ hơi nóng rát lên cổ, Chướng bụng, đầy hơi khó tiêu"'
history = [
    {"sender": "user", "content": msg1},
    {"sender": "assistant", "content": res1.get("text_content")}
]
payload2 = {
    "session_id": session_id,
    "message": msg2,
    "message_type": "text",
    "chat_history": history
}

data2 = json.dumps(payload2).encode("utf-8")
req2 = urllib.request.Request(url, data=data2, headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req2, timeout=30) as resp2:
    res2 = json.loads(resp2.read().decode("utf-8"))
    print("\n=== TURN 2 (CLARIFICATION) RESULTS ===")
    print("Latency:", res2.get("latency_ms"), "ms")
    print("Top predictions:", [(p.get('icd_code'), p.get('disease_name_vi'), p.get('probability_percentage')) for p in res2.get('telemetry', {}).get('top_predictions', [])])
    print("\n--- TURN 2 AI TEXT ---")
    print(res2.get("text_content"))
