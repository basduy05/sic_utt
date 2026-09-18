import json
import asyncio
import uuid
import datetime
from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import StreamingResponse
from typing import List, Optional
from ....services.chat_service import chat_service
from ....core.database import db_service
from ....models.pydantic.chat_schema import ChatMessageRequest, ChatMessageResponse, MedicalRecordRequest

router = APIRouter()

@router.post("/message", response_model=ChatMessageResponse)
async def send_chat_message(
    req: ChatMessageRequest,
    x_gemini_api_key: Optional[str] = Header(None)
):
    """
    REST Endpoint gửi tin nhắn kèm lịch sử hội thoại nhiều lượt (Multi-turn Context).
    """
    # Lưu tin nhắn của bệnh nhân vào Database
    user_record = {
        "message_id": str(uuid.uuid4()),
        "session_id": req.session_id,
        "sender": "user",
        "text_content": req.message,
        "created_at": datetime.datetime.utcnow().isoformat(),
        "metadata": {"message_type": req.message_type}
    }
    await db_service.save_message(user_record)

    res = await chat_service.process_patient_message(
        session_id=req.session_id,
        user_message=req.message,
        chat_history=req.chat_history,
        gemini_api_key=x_gemini_api_key
    )
    # Lưu vào database (MongoDB / In-Memory Fallback)
    await db_service.save_message(res)
    return ChatMessageResponse(**res)

@router.post("/stream")
async def stream_chat_message(
    req: ChatMessageRequest,
    x_gemini_api_key: Optional[str] = Header(None)
):
    """
    Server-Sent Events (SSE) Streaming Endpoint kèm Multi-turn Context Memory:
    Chunking văn bản trả lời và streaming từng token mượt mà về client.
    """
    # Lưu tin nhắn của bệnh nhân vào Database
    user_record = {
        "message_id": str(uuid.uuid4()),
        "session_id": req.session_id,
        "sender": "user",
        "text_content": req.message,
        "created_at": datetime.datetime.utcnow().isoformat(),
        "metadata": {"message_type": req.message_type}
    }
    await db_service.save_message(user_record)

    res = await chat_service.process_patient_message(
        session_id=req.session_id,
        user_message=req.message,
        chat_history=req.chat_history,
        gemini_api_key=x_gemini_api_key
    )
    await db_service.save_message(res)

    full_text = res.get("text_content", "")
    telemetry = res.get("telemetry", {})
    message_id = res.get("message_id")

    async def event_generator():
        # Chunking text into small word tokens for typewriter effect
        words = full_text.split(" ")
        buffer = []
        for i, word in enumerate(words):
            buffer.append(word)
            if len(buffer) >= 3 or i == len(words) - 1:
                chunk_str = " ".join(buffer) + (" " if i < len(words) - 1 else "")
                chunk_payload = {
                    "type": "chunk",
                    "content": chunk_str,
                    "message_id": message_id
                }
                yield f"data: {json.dumps(chunk_payload, ensure_ascii=False)}\n\n"
                buffer = []
                await asyncio.sleep(0.02)

        # Final Done Event with complete Telemetry Data and Latency Breakdown
        done_payload = {
            "type": "done",
            "message_id": message_id,
            "session_id": req.session_id,
            "full_text": full_text,
            "telemetry": telemetry,
            "latency_ms": res.get("latency_ms", 0),
            "pipeline_breakdown": res.get("pipeline_breakdown", {})
        }
        yield f"data: {json.dumps(done_payload, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.post("/medical-record")
async def generate_patient_medical_record(
    req: MedicalRecordRequest,
    x_gemini_api_key: Optional[str] = Header(None)
):
    """
    Tạo BẢN TỔNG HỢP BỆNH ÁN HOÀN CHỈNH từ toàn bộ quá trình hội thoại và dữ liệu cận lâm sàng.
    """
    record_markdown = chat_service.generate_medical_record(
        session_id=req.session_id,
        chat_history=req.chat_history,
        telemetry=req.telemetry,
        gemini_api_key=x_gemini_api_key
    )
    return {
        "session_id": req.session_id,
        "medical_record_markdown": record_markdown
    }

@router.get("/history/{session_id}")
async def get_chat_history(session_id: str):
    """Lấy toàn bộ lịch sử tin nhắn của một phiên hội thoại từ Database/MongoDB."""
    history = await db_service.get_messages_by_session(session_id)
    return {"session_id": session_id, "messages": history}

@router.get("/export-audit/{session_id}")
async def export_session_audit(session_id: str):
    """
    Xuất báo cáo chi tiết toàn bộ cuộc trò chuyện, latency, pipeline breakdown,
    telemetry cận lâm sàng và metadata phục vụ bảo trì hệ thống AI (Admin only).
    """
    import datetime
    history = await db_service.get_messages_by_session(session_id)
    
    latencies = [
        m.get("latency_ms", 0) for m in history 
        if isinstance(m.get("latency_ms"), (int, float)) and m.get("latency_ms", 0) > 0
    ]
    avg_latency = round(sum(latencies) / len(latencies), 1) if latencies else 0
    max_latency = max(latencies) if latencies else 0
    min_latency = min(latencies) if latencies else 0

    audit_payload = {
        "metadata": {
            "session_id": session_id,
            "exported_at": datetime.datetime.utcnow().isoformat() + "Z",
            "exporter_role": "admin",
            "system_version": "MediBot AI v2.2 - Multi-Modal Healthcare Agent",
            "rag_engine": "Dense Embedding MiniLM-L6-v2 (640 Q&A BYT Medical Protocol)",
            "ner_model": "PhoBERT-Medical-NER v1.0",
            "llm_engine": "Google Gemini 2.0 Flash",
            "total_turns": len(history),
            "performance_metrics": {
                "total_recorded_responses": len(latencies),
                "avg_latency_ms": avg_latency,
                "min_latency_ms": min_latency,
                "max_latency_ms": max_latency
            }
        },
        "dialogue_history": history
    }
    return audit_payload

