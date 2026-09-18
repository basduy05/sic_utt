import uuid
import time
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# In-memory store cho feedback (sẽ được persist vào DB khi MongoDB kết nối)
_feedback_store: List[Dict[str, Any]] = []


def save_feedback(
    message_id: str,
    session_id: str,
    user_id: str,
    rating: str,          # "like" | "dislike"
    reason: Optional[str] = None,
    answer_index: int = 0,
    answer_provider: Optional[str] = None,
    message_preview: Optional[str] = None,
) -> Dict[str, Any]:
    """Lưu feedback của người dùng về một câu trả lời."""
    record = {
        "id": str(uuid.uuid4()),
        "message_id": message_id,
        "session_id": session_id,
        "user_id": user_id,
        "rating": rating,
        "reason": reason or "",
        "answer_index": answer_index,
        "answer_provider": answer_provider or "unknown",
        "message_preview": (message_preview or "")[:200],
        "created_at": time.time(),
        "created_at_iso": __import__("datetime").datetime.utcnow().isoformat(),
    }
    _feedback_store.append(record)
    logger.info(f"Feedback saved: {rating} for message {message_id} by user {user_id}")
    return record


def get_all_feedback(
    rating_filter: Optional[str] = None,
    limit: int = 200,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """Lấy danh sách feedback (chỉ dành cho admin)."""
    data = _feedback_store
    if rating_filter in ("like", "dislike"):
        data = [f for f in data if f.get("rating") == rating_filter]
    # Newest first
    data_sorted = sorted(data, key=lambda x: x.get("created_at", 0), reverse=True)
    return data_sorted[offset : offset + limit]


def get_feedback_stats() -> Dict[str, Any]:
    """Thống kê tổng hợp feedback."""
    total = len(_feedback_store)
    likes = sum(1 for f in _feedback_store if f.get("rating") == "like")
    dislikes = total - likes
    return {
        "total": total,
        "likes": likes,
        "dislikes": dislikes,
        "like_rate": round(likes / total * 100, 1) if total > 0 else 0,
    }
