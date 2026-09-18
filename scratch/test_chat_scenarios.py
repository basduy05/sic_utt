import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath("."))
sys.stdout.reconfigure(encoding='utf-8')
from apps.backend.app.services.chat_service import chat_service

async def test_scenarios():
    test_cases = [
        ("Xin chào", "Greeting test"),
        ("Tôi hơi mệt và khó chịu trong người", "Vague symptom test"),
        ("Tôi bị đau đầu chóng mặt buồn nôn", "Clinical symptom test"),
        ("Tôi bị đau thắt ngực trái dữ dội lan lên cổ vã mồ hôi", "Red flag emergency test"),
    ]

    for user_msg, desc in test_cases:
        print(f"\n=======================================================")
        print(f"TEST: {desc} -> '{user_msg}'")
        try:
            res = await chat_service.process_patient_message(
                user_message=user_msg,
                session_id=f"test_session_{desc.replace(' ', '_')}"
            )
            text = res.get("text_content", "")
            provider = res.get("telemetry", {}).get("llm_provider", "unknown")
            is_emergency = res.get("telemetry", {}).get("is_emergency", False)
            print(f"Status: SUCCESS | Provider: {provider} | Emergency: {is_emergency}")
            print(f"Response (first 250 chars):\n{text[:250]}...")
        except Exception as e:
            print(f"FAILED with error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_scenarios())
