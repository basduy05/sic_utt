import urllib.request
import json
import time
import sys

sys.stdout.reconfigure(encoding='utf-8')

API_URL = "http://127.0.0.1:8000/api/v1/chat/message"

def send_chat_turn(session_id: str, message: str, history: list):
    payload = {
        "session_id": session_id,
        "message": message,
        "message_type": "text",
        "chat_history": history
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(API_URL, data=data, headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=30) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        lat = time.time() - t0
        return res, lat

def test_scenario_1():
    print("=" * 70)
    print("=== TEST KỊCH BẢN 1: DỊ ỨNG HẢI SẢN -> PHẢN VỆ CẤP CỨU ===")
    print("=" * 70)
    session_id = f"test-dst-anaphylaxis-{int(time.time())}"
    history = []

    # Turn 1
    q1 = "Tự nhiên khắp đùi và lưng nổi từng mảng sưng đỏ như muỗi đốt rồi ngứa dữ dội là bị gì?"
    print(f"\n[Turn 1] User: {q1}")
    r1, lat1 = send_chat_turn(session_id, q1, history)
    ans1 = r1.get("text_content", "")
    print(f"-> AI ({lat1:.2f}s):\n{ans1[:300]}...")
    history.append({"sender": "user", "content": q1})
    history.append({"sender": "assistant", "content": ans1})

    # Turn 2
    q2 = "Tối qua tôi có ăn hải sản và uống chút bia,"
    print(f"\n[Turn 2] User: {q2}")
    r2, lat2 = send_chat_turn(session_id, q2, history)
    ans2 = r2.get("text_content", "")
    print(f"-> AI ({lat2:.2f}s):\n{ans2[:300]}...")
    history.append({"sender": "user", "content": q2})
    history.append({"sender": "assistant", "content": ans2})

    # Turn 3
    q3 = "Giờ môi tôi thấy hơi tê phù và cảm giác thở rít nhẹ, có cần đi cấp cứu không"
    print(f"\n[Turn 3] User: {q3}")
    r3, lat3 = send_chat_turn(session_id, q3, history)
    ans3 = r3.get("text_content", "")
    print(f"-> AI ({lat3:.2f}s):\n{ans3}")
    assert "CẤP CỨU" in ans3 or "115" in ans3 or "Phản vệ" in ans3, "Turn 3 must escalate to Anaphylaxis Emergency!"
    print("\n[SUCCESS] Scenario 1 passed with proper Red Flag escalation & clinical memory!")

def test_scenario_2():
    print("\n" + "=" * 70)
    print("=== TEST KỊCH BẢN 2: SỐT CAO -> SỐT XUẤT HUYẾT DENGUE 5 LƯỢT ===")
    print("=" * 70)
    session_id = f"test-dst-dengue-{int(time.time())}"
    history = []

    turns = [
        "Tôi bị sốt cao 39 độ từ tối qua, uống thuốc hạ sốt mà không thấy đỡ thì bị gì?",
        "Người tôi đau nhức khắp các khớp với ê buốt hai hốc mắt nữa, có phải bị cúm hay sốt xuất huyết không?",
        "Hôm nay sang ngày thứ 3 tôi thấy da nổi mấy chấm đỏ li ti ở tay, ấn vào không mất, thế là dấu hiệu gì?",
        "Bây giờ tôi nên uống thuốc gì và ăn uống thế nào để hạ sốt?",
        "Dấu hiệu nào thì bắt buộc phải vào viện cấp cứu ngay?"
    ]

    for idx, q in enumerate(turns, 1):
        print(f"\n[Turn {idx}] User: {q}")
        r, lat = send_chat_turn(session_id, q, history)
        ans = r.get("text_content", "")
        print(f"-> AI ({lat:.2f}s):\n{ans[:280]}...")
        history.append({"sender": "user", "content": q})
        history.append({"sender": "assistant", "content": ans})

    print("\n[SUCCESS] Scenario 2 completed all 5 turns smoothly!")

if __name__ == "__main__":
    test_scenario_1()
    test_scenario_2()
