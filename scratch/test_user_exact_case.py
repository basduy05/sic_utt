import urllib.request
import json
import time
import sys

sys.stdout.reconfigure(encoding='utf-8')

url = "http://127.0.0.1:8000/api/v1/chat/message"
session_id = f"test-user-headache-{int(time.time())}"

print("=== STARTING MULTI-TURN TEST (HEADACHE TO MIGRAINE) ===")

# Turn 1
msg1 = "tôi bị đau đầu ý"
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
    print("\n--- TURN 1 RESPONSE ---")
    print("Clinical stage / Needs clarification:", res1.get("clarification", {}))
    print("Top predictions:", [(p.get('icd_code'), p.get('disease_name_vi'), p.get('probability_percentage')) for p in res1.get('telemetry', {}).get('top_predictions', [])])
    print("Content:")
    print(res1.get("text_content"))
    turn1_text = res1.get("text_content")

# Turn 2: User answers clarification exactly as in user's prompt
msg2 = 'Trả lời câu hỏi làm rõ: "Tôi xin bổ sung thông tin lâm sàng: Cơn đau đầu hoặc choáng váng của bạn diễn biến như thế nào?: Đau giật nhói theo nhịp mạch ở nửa bên đầu, Đau căng tức cả hai bên thái dương và trán, Cảm giác chao đảo, bồng bềnh, đồ vật xoay tròn | Bạn có các dấu hiệu thần kinh giác quan nào đi kèm dưới đây không?: Sợ ánh sáng chói hoặc tiếng động lớn, Kèm buồn nôn hoặc nôn mửa đột ngột"'

history = [
    {"sender": "user", "content": msg1},
    {"sender": "assistant", "content": turn1_text}
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
    print("\n--- TURN 2 RESPONSE ---")
    print("Clinical stage / Needs clarification:", res2.get("clarification", {}))
    print("Top predictions:", [(p.get('icd_code'), p.get('disease_name_vi'), p.get('probability_percentage')) for p in res2.get('telemetry', {}).get('top_predictions', [])])
    print("Content:")
    print(res2.get("text_content"))
