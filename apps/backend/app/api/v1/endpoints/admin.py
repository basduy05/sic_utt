import json
import os
import time
from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List, Dict, Any, Optional
from ....core.database import db_fallback, db_service
from ....models.pydantic.admin_schema import (
    GlossaryItem, FeedbackCreate,
    UserRoleUpdate, ColabConnectRequest,
    TrainingStartRequest, RagDocumentAdd,
)
from ....services import model_registry, training_service

router = APIRouter()

# ─── Helper: Lexicon directory ───────────────────────────────────────────────

def get_lexicon_dir():
    cand1 = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "data", "medical_lexicon"))
    if os.path.exists(cand1):
        return cand1
    cand2 = os.path.abspath(os.path.join(os.getcwd(), "..", "data", "medical_lexicon"))
    if os.path.exists(cand2):
        return cand2
    cand3 = os.path.abspath(os.path.join(os.getcwd(), "data", "medical_lexicon"))
    if os.path.exists(cand3):
        return cand3
    return r"c:\Users\basduy05\Downloads\ai_utt_sic\data\medical_lexicon"

LEXICON_DIR = get_lexicon_dir()

# ─── LEGACY ENDPOINTS (giữ lại) ──────────────────────────────────────────────

@router.get("/glossary")
async def get_glossary():
    """Lấy danh sách từ điển triệu chứng và từ đồng nghĩa y khoa."""
    synonyms_path = os.path.join(LEXICON_DIR, "symptom_synonyms.json")
    if os.path.exists(synonyms_path):
        with open(synonyms_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return db_fallback.glossary

@router.get("/icd-codes")
async def get_icd_codes():
    """Lấy danh mục mã bệnh ICD-10 chuẩn hóa và phác đồ điều trị."""
    icd_path = os.path.join(LEXICON_DIR, "icd10_codes.json")
    if os.path.exists(icd_path):
        with open(icd_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

@router.get("/rag-knowledge")
async def get_rag_knowledge():
    """Lấy toàn bộ tài liệu tri thức RAG vector store."""
    base_dir = os.path.dirname(os.path.dirname(LEXICON_DIR))
    rag_path = os.path.join(base_dir, "apps", "ai_engine", "models_weights", "rag_knowledge_store.json")
    if os.path.exists(rag_path):
        with open(rag_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

@router.post("/glossary")
async def add_or_update_glossary_term(item: GlossaryItem):
    """Thêm hoặc chỉnh sửa từ đồng nghĩa triệu chứng."""
    synonyms_path = os.path.join(LEXICON_DIR, "symptom_synonyms.json")
    data = {}
    if os.path.exists(synonyms_path):
        with open(synonyms_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    data[item.key] = {
        "standard_term": item.standard_term,
        "icd_mapping": item.icd_mapping,
        "synonyms": item.synonyms,
        "category": item.category,
        "is_red_flag_potential": item.is_red_flag_potential
    }
    with open(synonyms_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return {"status": "success", "message": f"Updated glossary item {item.key}"}

@router.post("/qa-feedback")
async def submit_qa_feedback(feedback: FeedbackCreate):
    """Lưu phản hồi đánh giá độ chính xác chẩn đoán từ bác sĩ."""
    feedback_doc = feedback.dict()
    saved = await db_service.add_feedback(feedback_doc)
    fbs = await db_service.get_feedback()
    return {"status": "success", "total_feedback_logs": len(fbs)}

@router.get("/validation-results")
async def get_validation_results():
    """Lấy kết quả đánh giá trên tập kiểm thử Validation Hold-out."""
    base_dir = os.path.dirname(os.path.dirname(LEXICON_DIR))
    val_path = os.path.join(base_dir, "data", "datasets", "validation_holdout_set.json")
    if os.path.exists(val_path):
        with open(val_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

@router.get("/feedback/reports")
async def get_feedback_reports():
    """Lấy báo cáo tổng hợp QA từ Database/MongoDB."""
    fbs = await db_service.get_feedback()
    total = len(fbs)
    correct_count = sum(1 for f in fbs if f.get("doctor_label_correct"))
    accuracy = (correct_count / total * 100.0) if total > 0 else 100.0
    return {
        "total_cases_reviewed": total,
        "correct_predictions": correct_count,
        "accuracy_rate_percentage": round(accuracy, 2),
        "recent_logs": fbs[:10]
    }

# ─── NEW: USER MANAGEMENT ────────────────────────────────────────────────────

@router.get("/users")
async def list_users():
    """Lấy danh sách tất cả người dùng từ MongoDB/Database."""
    users = await db_service.list_users()
    # Ẩn password hash
    safe_users = []
    for u in users:
        safe_u = {k: v for k, v in u.items() if k != "password_hash"}
        # Thống kê số lượng session của user
        safe_u["session_count"] = await db_service.get_session_count_for_user(u.get("id"))
        safe_users.append(safe_u)
    return {"users": safe_users, "total": len(safe_users)}

@router.put("/users/{user_id}/role")
async def update_user_role(user_id: str, body: UserRoleUpdate):
    """Thay đổi vai trò của người dùng."""
    valid_roles = {"admin", "user", "doctor", "guest"}
    if body.role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Role không hợp lệ. Phải là một trong: {valid_roles}")
    user = await db_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
    await db_service.update_user_role(user_id, body.role)
    return {"status": "success", "user_id": user_id, "new_role": body.role}

@router.delete("/users/{user_id}")
async def delete_user(user_id: str):
    """Xóa tài khoản người dùng."""
    user = await db_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
    await db_service.delete_user(user_id)
    return {"status": "success", "message": f"Đã xóa tài khoản: {user.get('email', user_id)}"}

# ─── NEW: AI MODEL MANAGEMENT ────────────────────────────────────────────────

@router.get("/models")
async def list_ai_models():
    """Lấy thông tin tất cả model AI đang được sử dụng."""
    models = model_registry.list_models()
    return {"models": models, "total": len(models)}

@router.get("/models/{filename}")
async def get_model_detail(filename: str):
    """Lấy chi tiết một model cụ thể."""
    detail = model_registry.get_model_detail(filename)
    if "error" in detail:
        raise HTTPException(status_code=404, detail=detail["error"])
    return detail

# ─── NEW: TRAINING DATA ───────────────────────────────────────────────────────

@router.get("/datasets")
async def list_datasets():
    """Lấy danh sách dataset đã có trong hệ thống."""
    datasets = model_registry.get_dataset_list()
    return {"datasets": datasets, "total": len(datasets)}

@router.post("/datasets/upload")
async def upload_dataset(file: UploadFile = File(...)):
    """Upload file dataset (CSV/JSON) trực tiếp."""
    allowed_exts = {".csv", ".json", ".jsonl"}
    ext = os.path.splitext(file.filename or "")[-1].lower()
    if ext not in allowed_exts:
        raise HTTPException(status_code=400, detail=f"Định dạng không hỗ trợ. Chỉ chấp nhận: {allowed_exts}")
    content = await file.read()
    result = training_service.save_uploaded_dataset(file.filename, content)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

@router.post("/rag-knowledge/add")
async def add_rag_document(doc: RagDocumentAdd):
    """Thêm tài liệu mới vào RAG knowledge base."""
    base_dir = os.path.dirname(os.path.dirname(LEXICON_DIR))
    rag_path = os.path.join(base_dir, "apps", "ai_engine", "models_weights", "rag_knowledge_store.json")
    
    if os.path.exists(rag_path):
        with open(rag_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = []
    
    new_doc = {
        "id": f"doc_{int(time.time())}",
        "title": doc.title,
        "content": doc.content,
        "source": doc.source or "Manual Entry",
        "icd_codes": doc.icd_codes or [],
        "added_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    
    if isinstance(data, list):
        data.append(new_doc)
    elif isinstance(data, dict):
        docs = data.get("documents", data.get("entries", []))
        docs.append(new_doc)
    
    with open(rag_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return {"status": "success", "doc_id": new_doc["id"], "message": "Đã thêm tài liệu vào RAG Knowledge Base"}

# ─── NEW: TRAINING CENTER ─────────────────────────────────────────────────────

@router.post("/training/start")
async def start_training(req: TrainingStartRequest):
    """Khởi chạy training job từ giao diện."""
    result = training_service.start_training_job(
        job_type=req.job_type,
        dataset_file=req.dataset_file,
        config=req.config,
    )
    if "error" in result:
        raise HTTPException(status_code=409, detail=result["error"])
    return result

@router.get("/training/status")
async def get_training_status():
    """Lấy trạng thái training job hiện tại."""
    current = training_service.get_current_job()
    if not current:
        return {"status": "idle", "message": "Không có training job nào đang chạy."}
    return current

@router.get("/training/jobs")
async def list_training_jobs():
    """Lấy lịch sử tất cả training jobs."""
    jobs = training_service.list_jobs()
    return {"jobs": jobs, "total": len(jobs)}

@router.get("/training/jobs/{job_id}")
async def get_job_detail(job_id: str):
    """Lấy chi tiết một training job."""
    job = training_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Không tìm thấy training job")
    return job

@router.get("/training/logs/{job_id}")
async def get_training_logs(job_id: str, offset: int = 0):
    """Lấy log training của một job (polling endpoint, dùng khi WebSocket không khả dụng)."""
    job = training_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Không tìm thấy training job")
    logs = job.get("logs", [])
    return {
        "job_id": job_id,
        "status": job["status"],
        "progress": job["progress"],
        "logs": logs[offset:],
        "total_lines": len(logs),
        "metrics": job.get("metrics", {}),
    }

# ─── NEW: GOOGLE COLAB / DRIVE ───────────────────────────────────────────────

@router.post("/colab/download")
async def download_from_colab(req: ColabConnectRequest):
    """Download dataset từ Google Drive link."""
    result = training_service.download_from_google_drive(req.drive_url, req.filename)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

# ─── NEW: SYSTEM HEALTH ───────────────────────────────────────────────────────

@router.get("/system/health")
async def get_system_health():
    """Kiểm tra trạng thái sức khỏe của các service."""
    import time

    start = time.time()

    # Kiểm tra model files
    models = model_registry.list_models()
    models_ok = all(m["status"] == "active" for m in models)
    models_missing = [m["filename"] for m in models if m["status"] == "missing"]

    # Kiểm tra datasets
    datasets = model_registry.get_dataset_list()

    # Kiểm tra lexicon
    synonyms_path = os.path.join(LEXICON_DIR, "symptom_synonyms.json")
    icd_path = os.path.join(LEXICON_DIR, "icd10_codes.json")
    lexicon_ok = os.path.exists(synonyms_path) and os.path.exists(icd_path)

    # Kiểm tra training job
    current_job = training_service.get_current_job()
    
    latency_ms = round((time.time() - start) * 1000, 2)

    return {
        "status": "healthy" if (models_ok and lexicon_ok) else "degraded",
        "latency_ms": latency_ms,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "components": {
            "ai_models": {
                "status": "ok" if models_ok else "degraded",
                "total": len(models),
                "active": sum(1 for m in models if m["status"] == "active"),
                "missing": models_missing,
            },
            "lexicon": {
                "status": "ok" if lexicon_ok else "missing",
                "synonyms_exists": os.path.exists(synonyms_path),
                "icd_codes_exists": os.path.exists(icd_path),
            },
            "datasets": {
                "status": "ok",
                "count": len(datasets),
            },
            "training": {
                "status": "running" if (current_job and current_job["status"] == "running") else "idle",
                "current_job": current_job["job_id"] if current_job else None,
            },
            "database": {
                "status": "connected_mongodb" if db_service.is_mongo_connected else "in_memory_resilient",
                "persistence": "MongoDB Motor Async" if db_service.is_mongo_connected else "In-Memory Fallback (Auto-Failover)",
                "users": len(await db_service.list_users()),
                "is_mongo": db_service.is_mongo_connected,
            },
        },
    }


# ─── ADMIN: Conversations Viewer ─────────────────────────────────────────────

@router.get("/conversations")
async def get_all_conversations(limit: int = 50, offset: int = 0):
    """Admin: Lấy tất cả session hội thoại của người dùng (phân trang)."""
    try:
        sessions = await db_service.list_all_sessions(limit=limit, offset=offset)
        return {"sessions": sessions, "total": len(sessions), "limit": limit, "offset": offset}
    except Exception as e:
        return {"sessions": [], "total": 0, "error": str(e)}


@router.get("/conversations/{session_id}/messages")
async def get_session_messages(session_id: str):
    """Admin: Lấy toàn bộ tin nhắn của một phiên hội thoại."""
    try:
        msgs = await db_service.get_messages_by_session(session_id)
        return {"session_id": session_id, "messages": msgs, "count": len(msgs)}
    except Exception as e:
        return {"session_id": session_id, "messages": [], "error": str(e)}


# ─── FEEDBACK Endpoints ───────────────────────────────────────────────────────

from ....services.feedback_service import save_feedback, get_all_feedback, get_feedback_stats
from pydantic import BaseModel as PydanticBaseModel

class FeedbackSubmit(PydanticBaseModel):
    message_id: str
    session_id: str
    user_id: Optional[str] = "anonymous"
    rating: str          # "like" | "dislike"
    reason: Optional[str] = None
    answer_index: int = 0
    answer_provider: Optional[str] = None
    message_preview: Optional[str] = None


@router.post("/feedback")
async def submit_feedback(body: FeedbackSubmit):
    """Người dùng gửi feedback (like/dislike) về câu trả lời AI."""
    if body.rating not in ("like", "dislike"):
        raise HTTPException(status_code=400, detail="rating phải là 'like' hoặc 'dislike'")
    record = save_feedback(
        message_id=body.message_id,
        session_id=body.session_id,
        user_id=body.user_id or "anonymous",
        rating=body.rating,
        reason=body.reason,
        answer_index=body.answer_index,
        answer_provider=body.answer_provider,
        message_preview=body.message_preview,
    )
    return {"status": "ok", "feedback_id": record["id"]}


@router.get("/feedback")
async def get_feedback_list(rating: Optional[str] = None, limit: int = 100, offset: int = 0):
    """Admin: Lấy danh sách feedback của người dùng."""
    items = get_all_feedback(rating_filter=rating, limit=limit, offset=offset)
    stats = get_feedback_stats()
    return {"feedback": items, "stats": stats, "total": len(items)}
