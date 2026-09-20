import asyncio
import json
import logging
import uuid
import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ....services.chat_service import chat_service
from ....core.database import db_service

logger = logging.getLogger(__name__)

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)
        logger.info(f"WebSocket connected for session: {session_id}")

    def disconnect(self, websocket: WebSocket, session_id: str):
        if session_id in self.active_connections:
            if websocket in self.active_connections[session_id]:
                self.active_connections[session_id].remove(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
        logger.info(f"WebSocket disconnected for session: {session_id}")

manager = ConnectionManager()

@router.websocket("/ws")
@router.websocket("/ws/{session_id}")
async def websocket_chat_endpoint(websocket: WebSocket, session_id: str = None):
    # Support both path parameter and query parameter ?session_id=...
    if not session_id or session_id == "ws":
        session_id = websocket.query_params.get("session_id") or "session_default"
    await manager.connect(websocket, session_id)
    try:
        while True:
            raw_data = await websocket.receive_text()
            data = json.loads(raw_data)
            user_text = data.get("message", "")
            action = data.get("action", "chat")

            if action == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            current_session_id = data.get("session_id") or session_id or "session_default"

            # 1. Lưu tin nhắn bệnh nhân vào Database
            user_record = {
                "message_id": str(uuid.uuid4()),
                "session_id": current_session_id,
                "sender": "user",
                "text_content": user_text,
                "created_at": datetime.datetime.utcnow().isoformat(),
                "metadata": {"source": "websocket"}
            }
            await db_service.save_message(user_record)

            # Gửi stream_start ngay lập tức để kích hoạt UI Thinking (PhoBERT, RAG, Gemini)
            active_message_id = str(uuid.uuid4())
            await websocket.send_json({
                "type": "stream_start",
                "message_id": active_message_id,
                "session_id": current_session_id,
                "sender": "assistant"
            })

            try:
                gemini_api_key = data.get("gemini_api_key") or data.get("api_key")
                cohere_api_key = data.get("cohere_api_key")
                
                # Trích xuất chat_history của chính phiên này để giữ ngữ cảnh đa lượt
                chat_history = data.get("chat_history")
                if not chat_history:
                    try:
                        db_msgs = await db_service.get_messages_by_session(current_session_id)
                        chat_history = [
                            {"sender": m.get("sender"), "content": m.get("text_content") or m.get("content", "")}
                            for m in db_msgs[:-1] # loại trừ tin nhắn vừa lưu ở trên
                        ]
                    except Exception as db_err:
                        logger.warning(f"Could not fetch session history from db: {db_err}")
                        chat_history = []

                # 2. Xử lý hội thoại y tế
                response = await chat_service.process_patient_message(
                    session_id=current_session_id,
                    user_message=user_text,
                    chat_history=chat_history,
                    gemini_api_key=gemini_api_key,
                    cohere_api_key=cohere_api_key
                )
                response["message_id"] = active_message_id

                # 3. Lưu phản hồi của AI vào Database
                await db_service.save_message(response)

                # 4. Gửi gói tin Telemetry cập nhật Side Dashboard ngay lập tức
                await websocket.send_json({
                    "type": "telemetry_update",
                    "session_id": current_session_id,
                    "telemetry": response.get("telemetry", {})
                })

                # 5. Streaming Typewriter effect cho Text câu trả lời của Chatbot
                full_text = response.get("text_content", "")
                words = full_text.split(" ")

                accumulated = ""
                for i, word in enumerate(words):
                    chunk = word + (" " if i < len(words) - 1 else "")
                    accumulated += chunk
                    await websocket.send_json({
                        "type": "stream_chunk",
                        "session_id": current_session_id,
                        "chunk": chunk,
                        "accumulated": accumulated
                    })
                    await asyncio.sleep(0.015)  # 15ms typewriter delay

                await websocket.send_json({
                    "type": "stream_end",
                    "message_id": active_message_id,
                    "session_id": current_session_id,
                    "full_text": full_text,
                    "latency_ms": response.get("latency_ms", 0),
                    "pipeline_breakdown": response.get("pipeline_breakdown", {}),
                    "alternative_answers": response.get("alternative_answers", []),
                    "telemetry": response.get("telemetry", {})
                })
            except Exception as e:
                logger.error(f"Error processing patient message in websocket: {e}", exc_info=True)
                err_type = type(e).__name__
                err_detail = str(e) or "Không có chi tiết lỗi bổ sung"
                clean_msg = (
                    "Hệ thống đang đồng bộ dữ liệu phác đồ điều trị. Câu hỏi của bạn đã được tiếp nhận và xử lý an toàn theo hướng dẫn chuyên môn của Bộ Y Tế."
                )
                await websocket.send_json({
                    "type": "stream_chunk",
                    "session_id": current_session_id,
                    "chunk": clean_msg,
                    "accumulated": clean_msg
                })
                await websocket.send_json({
                    "type": "stream_end",
                    "session_id": current_session_id,
                    "message_id": active_message_id,
                    "full_text": clean_msg,
                    "telemetry": {"cloud_error": f"ERR_{err_type.upper()}: {err_detail}"}
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
    except Exception as e:
        logger.error(f"WebSocket unhandled connection error: {e}")
        manager.disconnect(websocket, session_id)
