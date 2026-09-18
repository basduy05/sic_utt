import os
import uuid
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from ....services.triage_service import triage_service
from ....models.pydantic.medical_schema import (
    TranscribeResponse,
    OCRAnalysisResponse,
    TriageAnalysisRequest,
    TriageAnalysisResponse
)

router = APIRouter()

@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str = Form("vi")
):
    """
    POST /api/v1/medical/transcribe (hoặc /audio/transcribe)
    Nhận file âm thanh (wav/webm) -> Chuyển đổi thành text tiếng Việt qua Whisper.
    """
    audio_bytes = await file.read()
    stt_res = triage_service.pipeline.stt_engine.transcribe(audio_bytes, filename=file.filename, language=language)
    return TranscribeResponse(
        text=stt_res.get("text", ""),
        language=stt_res.get("language", "vi"),
        duration_seconds=stt_res.get("duration_seconds", 0.0),
        latency_seconds=stt_res.get("latency_seconds", 0.0),
        status=stt_res.get("status", "success")
    )

@router.post("/ocr", response_model=OCRAnalysisResponse)
async def analyze_document_ocr(
    files: List[UploadFile] = File(default=[]),
    file: Optional[UploadFile] = File(default=None)
):
    """
    POST /api/v1/medical/ocr (hoặc /documents/ocr)
    Hỗ trợ bóc tách đồng thời NHIỀU FILE (Ảnh PNG, JPG, PDF) và hợp nhất toàn bộ chỉ số xét nghiệm sinh hóa máu.
    """
    upload_list = []
    if files:
        upload_list.extend(files)
    if file and file not in upload_list:
        upload_list.append(file)

    if not upload_list:
        raise HTTPException(status_code=400, detail="Không tìm thấy tệp xét nghiệm được tải lên.")

    combined_indicators = {}
    combined_flags = []
    combined_raw_texts = []

    for uploaded_f in upload_list:
        file_bytes = await uploaded_f.read()
        if not file_bytes:
            continue
        doc_ext = uploaded_f.filename.lower().split(".")[-1] if uploaded_f.filename else ""

        if doc_ext == "pdf":
            res = triage_service.pipeline.pdf_parser.parse_pdf(file_bytes)
        else:
            res = triage_service.pipeline.image_ocr.process_image(file_bytes)

        indicators = res.get("parsed_indicators", {})
        combined_indicators.update(indicators)
        for flag in res.get("critical_flags", []):
            if flag not in combined_flags:
                combined_flags.append(flag)
        
        t = res.get("ocr_text", "")
        if t:
            combined_raw_texts.append(f"[{uploaded_f.filename}]:\n{t}")

    return OCRAnalysisResponse(
        parsed_indicators=combined_indicators,
        critical_flags=combined_flags,
        total_indicators_found=len(combined_indicators),
        raw_text="\n\n".join(combined_raw_texts)
    )

@router.post("/analyze", response_model=TriageAnalysisResponse)
async def triage_analyze(request: TriageAnalysisRequest):
    """
    POST /api/v1/medical/analyze (hoặc /triage/analyze)
    Phân tích triệu chứng văn bản + chỉ số lab -> Dự đoán Top 3-5 nguy cơ bệnh.
    """
    res = triage_service.analyze(text=request.user_text)
    return TriageAnalysisResponse(
        processed_text=res.get("processed_text", ""),
        is_emergency=res.get("is_emergency", False),
        red_flag_details=res.get("red_flag_details", {}),
        extracted_entities=res.get("extracted_entities", {}),
        lab_indicators=res.get("lab_indicators", {}),
        triage_results=res.get("triage_results", []),
        fusion_metadata=res.get("fusion_metadata", {}),
        clarification_loop=res.get("clarification_loop", {}),
        latency_seconds=res.get("latency_seconds", 0.0)
    )

# --- Phân hệ Bệnh Án Điện Tử & Phản Hồi (Medical Records & Feedback) ---

from ....core.database import db_service
from pydantic import BaseModel
from typing import Dict, Any

class FeedbackRequest(BaseModel):
    category: str = "AI_QUALITY" # AI_QUALITY, BUG_REPORT, FEATURE_REQUEST
    rating: int = 5
    content: str
    user_name: Optional[str] = "Nguyễn Bá Duy"
    user_email: Optional[str] = None

@router.get("/records")
async def get_medical_records(
    user_id: Optional[str] = None,
    include_drafts: bool = False
):
    """
    Lấy danh sách bệnh án điện tử từ MongoDB/Database.
    include_drafts = False: Chỉ lấy bệnh án chính thức (không hiện bệnh án nháp/lưu tạm ẩn).
    include_drafts = True: Lấy toàn bộ gồm cả bản lưu tạm (dành cho admin/audit).
    """
    records = await db_service.get_medical_records(user_id=user_id, include_drafts=include_drafts)
    return {
        "total": len(records),
        "records": records
    }

@router.post("/records")
async def create_medical_record(record_data: Dict[str, Any]):
    """
    Tạo hoặc lưu bệnh án vào MongoDB/Database.
    Nếu is_draft=True: Lưu tạm thời vào DB ở chế độ ẩn (soft delete style), không hiện trong data người dùng.
    Nếu is_draft=False: Lưu chính thức vào hồ sơ bệnh án của người dùng.
    """
    saved = await db_service.add_medical_record(record_data)
    return {
        "status": "success",
        "message": "Đã lưu bệnh án thành công" if not saved.get("is_draft") else "Đã lưu tạm thời vào hệ thống",
        "record": saved
    }

@router.delete("/records/{record_id}")
async def delete_medical_record(record_id: str):
    """
    Xóa bệnh án khỏi hệ thống.
    """
    success = await db_service.delete_medical_record(record_id)
    if not success:
        raise HTTPException(status_code=404, detail="Không tìm thấy bệnh án")
    return {"status": "success", "message": "Đã xóa bệnh án thành công"}

@router.post("/feedback")
async def submit_feedback(fb: FeedbackRequest):
    """
    Gửi báo cáo sự cố & góp ý từ người dùng vào MongoDB/Database.
    """
    feedback_doc = {
        "id": f"fb-{uuid.uuid4().hex[:8]}",
        "category": fb.category,
        "rating": fb.rating,
        "content": fb.content,
        "user_name": fb.user_name,
        "user_email": fb.user_email,
        "created_at": datetime.utcnow().isoformat()
    }
    saved_fb = await db_service.add_feedback(feedback_doc)
    return {
        "status": "success",
        "message": "Cảm ơn bạn đã gửi đóng góp ý kiến để hoàn thiện MediBot AI!",
        "feedback_id": saved_fb.get("id")
    }

# --- Phân Hệ Mới: Phác Đồ Bộ Y Tế, Tra Cứu ICD-10, Dược Thư & Cấp Cứu Red Flag ---

import json
from functools import lru_cache

def _get_base_dir():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = current_dir
    while base_dir and not os.path.exists(os.path.join(base_dir, "data")):
        parent = os.path.dirname(base_dir)
        if parent == base_dir:
            break
        base_dir = parent
    return base_dir

@lru_cache(maxsize=1)
def _load_red_flags_data():
    base_dir = _get_base_dir()
    p = os.path.join(base_dir, "data", "medical_lexicon", "red_flags.json")
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"red_flag_rules": []}

@lru_cache(maxsize=1)
def _load_rag_protocols_data():
    base_dir = _get_base_dir()
    p = os.path.join(base_dir, "apps", "ai_engine", "models_weights", "rag_knowledge_store.json")
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

@lru_cache(maxsize=1)
def _load_icd10_data():
    base_dir = _get_base_dir()
    p = os.path.join(base_dir, "data", "medical_lexicon", "icd10_codes.json")
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

@lru_cache(maxsize=1)
def _load_drugs_data():
    base_dir = _get_base_dir()
    p = os.path.join(base_dir, "data", "medical_lexicon", "drug_database.json")
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"drugs": [], "drug_groups": []}

@router.get("/red-flags")
async def get_emergency_red_flags():
    """
    Trả về danh mục báo động đỏ cấp cứu, các hội chứng tử vong khẩn cấp và quy trình sơ cứu.
    """
    rf_data = _load_red_flags_data()
    hotlines = [
        {"name": "Cấp cứu Y tế Toàn quốc", "phone": "115", "description": "Tổng đài điều phối xe cấp cứu và kíp cấp cứu ngoại viện 24/7", "type": "national"},
        {"name": "Trung tâm Cấp cứu 115 Hà Nội", "phone": "024 115", "description": "Điều phối xe cấp cứu tại khu vực Hà Nội", "type": "regional"},
        {"name": "Trung tâm Cấp cứu 115 TP.HCM", "phone": "028 115", "description": "Mạng lưới trạm vệ tinh cấp cứu TP.HCM", "type": "regional"},
        {"name": "Trung tâm Chống độc - BV Bạch Mai", "phone": "024 3869 3731", "description": "Cấp cứu ngộ độc hóa chất, thuốc, nấm độc, rắn cắn", "type": "specialized"},
        {"name": "Cấp cứu Bệnh viện Chợ Rẫy", "phone": "028 3855 4137", "description": "Cấp cứu đa chấn thương và hồi sức tích cực miền Nam", "type": "specialized"},
        {"name": "Viện Tim Mạch Việt Nam", "phone": "024 3629 0880", "description": "Cấp cứu nhồi máu cơ tim & can thiệp mạch vành khẩn", "type": "specialized"}
    ]
    first_aid_guides = [
        {
            "id": "cpr",
            "title": "Hồi sinh tim phổi cơ bản (CPR)",
            "subtitle": "Áp dụng khi nạn nhân bất tỉnh, ngừng thở hoặc thở ngáp",
            "steps": [
                "1. Gọi ngay cấp cứu 115 và yêu cầu người xung quanh hỗ trợ.",
                "2. Đặt nạn nhân nằm ngửa trên mặt phẳng cứng, quỳ cạnh ngực nạn nhân.",
                "3. Đặt gót bàn tay vào giữa ngực (nửa dưới xương ức), đan các ngón tay lại.",
                "4. Ép tim mạnh và nhanh với tần số 100 - 120 lần/phút, độ sâu 5 - 6 cm.",
                "5. Sau mỗi 30 lần ép tim, thực hiện 2 lần thổi ngạt liên tục (nếu có kỹ năng)."
            ]
        },
        {
            "id": "fast",
            "title": "Quy tắc FAST nhận diện & sơ cứu Đột quỵ",
            "subtitle": "Xử trí trong 'Giờ vàng' (dưới 3 - 4.5 giờ)",
            "steps": [
                "F (Face): Yêu cầu cười - xem một bên mặt có bị méo, xệ không.",
                "A (Arm): Yêu cầu giơ 2 tay lên - xem một bên tay có bị rơi xuống hoặc yếu không.",
                "S (Speech): Yêu cầu nói câu đơn giản - xem có nói ngọng, nói đớ hoặc ú ớ không.",
                "T (Time): Nếu có bất kỳ dấu hiệu nào, gọi 115 khẩn cấp và ghi nhớ mốc thời gian khởi phát.",
                "Lưu ý tuyệt đối: Không cho ăn uống, không cạo gió, không chích lể đầu ngón tay."
            ]
        },
        {
            "id": "heimlich",
            "title": "Thủ thuật Heimlich tống dị vật đường thở",
            "subtitle": "Áp dụng khi nghẹn, sặc dị vật tím tái không thở được",
            "steps": [
                "1. Đứng sau lưng nạn nhân, vòng 2 tay qua eo nạn nhân.",
                "2. Nắm một bàn tay thành nắm đấm, đặt ngón cái ngay trên rốn và dưới mũi ức.",
                "3. Bàn tay kia ôm lấy nắm đấm, giật mạnh theo hướng vào trong và lên trên.",
                "4. Lặp lại động tác dứt khoát cho đến khi dị vật bật ra ngoài hoặc nạn nhân thở lại được."
            ]
        },
        {
            "id": "recovery",
            "title": "Tư thế hồi sức an toàn (Recovery Position)",
            "subtitle": "Áp dụng cho nạn nhân hôn mê nhưng vẫn còn thở tự nhiên",
            "steps": [
                "1. Quỳ bên cạnh nạn nhân, đặt cánh tay gần bạn nhất vuông góc với thân mình.",
                "2. Đưa cánh tay xa hơn vắt qua ngực, áp mu bàn tay vào má phía đối diện.",
                "3. Gập đầu gối chân phía xa, dùng lực kéo nhẹ nạn nhân nghiêng về phía bạn.",
                "4. Ngửa nhẹ đầu nạn nhân ra sau để đường thở thông thoáng và đờm dãi chảy ra ngoài tự nhiên."
            ]
        }
    ]
    return {
        "status": "success",
        "red_flag_rules": rf_data.get("red_flag_rules", []),
        "hotlines": hotlines,
        "first_aid_guides": first_aid_guides
    }

@router.get("/protocols")
async def get_protocols(
    q: Optional[str] = None,
    department: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """
    Tra cứu danh mục 640+ tài liệu phác đồ chẩn đoán và điều trị chuẩn Bộ Y Tế.
    """
    protocols = _load_rag_protocols_data()
    filtered = protocols

    if department and department != "ALL":
        filtered = [
            p for p in filtered
            if department.lower() in p.get("department", "").lower()
        ]

    if q and q.strip():
        query_norm = q.strip().lower()
        filtered = [
            p for p in filtered
            if query_norm in p.get("title", "").lower()
            or query_norm in p.get("content", "").lower()
            or query_norm in p.get("code", "").lower()
            or query_norm in p.get("department", "").lower()
        ]

    # Thu thập danh sách chuyên khoa duy nhất
    departments = sorted(list({p.get("department", "Chuyên khoa") for p in protocols if p.get("department")}))

    total = len(filtered)
    paged = filtered[offset: offset + limit]

    return {
        "status": "success",
        "total": total,
        "offset": offset,
        "limit": limit,
        "departments": departments,
        "protocols": paged
    }

@router.get("/icd10")
async def get_icd10_codes(
    q: Optional[str] = None,
    department: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 60,
    offset: int = 0
):
    """
    Tra cứu danh mục 211 mã bệnh ICD-10, triệu chứng lâm sàng và mức độ nguy cơ.
    """
    raw_icd = _load_icd10_data()
    items = []
    for code, info in raw_icd.items():
        item = {
            "code": code,
            "name_vi": info.get("name_vi", ""),
            "name_en": info.get("name_en", ""),
            "department": info.get("department", "Chuyên khoa"),
            "severity": info.get("severity", "Medium"),
            "description": info.get("description", ""),
            "all_symptoms": info.get("all_symptoms", []),
            "precautions": info.get("precautions", []),
            "emergency_warning": info.get("emergency_warning", "")
        }
        items.append(item)

    filtered = items

    if department and department != "ALL":
        filtered = [it for it in filtered if department.lower() in it["department"].lower()]

    if severity and severity != "ALL":
        filtered = [it for it in filtered if severity.lower() == it["severity"].lower()]

    if q and q.strip():
        query_norm = q.strip().lower()
        filtered = [
            it for it in filtered
            if query_norm in it["code"].lower()
            or query_norm in it["name_vi"].lower()
            or query_norm in it["name_en"].lower()
            or query_norm in it["department"].lower()
            or any(query_norm in s.lower() for s in it["all_symptoms"])
        ]

    departments = sorted(list({it["department"] for it in items if it.get("department")}))
    total = len(filtered)
    paged = filtered[offset: offset + limit]

    return {
        "status": "success",
        "total": total,
        "departments": departments,
        "items": paged
    }

@router.get("/drugs")
async def get_drugs(
    q: Optional[str] = None,
    group_id: Optional[str] = None
):
    """
    Tra cứu Dược thư Quốc gia Việt Nam thiết yếu.
    """
    data = _load_drugs_data()
    drugs = data.get("drugs", [])

    if group_id and group_id != "ALL":
        drugs = [d for d in drugs if d.get("group_id") == group_id]

    if q and q.strip():
        qn = q.strip().lower()
        drugs = [
            d for d in drugs
            if qn in d.get("name", "").lower()
            or any(qn in b.lower() for b in d.get("brand_names", []))
            or qn in d.get("class", "").lower()
            or qn in d.get("indications", "").lower()
        ]

    return {
        "status": "success",
        "total": len(drugs),
        "groups": data.get("drug_groups", []),
        "drugs": drugs
    }

class InteractionCheckRequest(BaseModel):
    drug_ids: List[str]

@router.post("/drugs/check-interactions")
async def check_drug_interactions(req: InteractionCheckRequest):
    """
    Kiểm tra tương tác thuốc giữa danh sách 2 hoặc nhiều loại thuốc được chọn.
    """
    data = _load_drugs_data()
    all_drugs = {d["id"]: d for d in data.get("drugs", [])}

    selected_drugs = [all_drugs[did] for did in req.drug_ids if did in all_drugs]
    interactions_found = []

    # Kiểm tra ma trận tương tác từng cặp
    for i in range(len(selected_drugs)):
        for j in range(i + 1, len(selected_drugs)):
            d1 = selected_drugs[i]
            d2 = selected_drugs[j]

            # Kiểm tra xem d1 có lưu tương tác với d2 không
            for inter in d1.get("interactions", []):
                target = inter.get("with_drug", "").lower()
                if target in d2["id"].lower() or target in d2["name"].lower() or any(target in b.lower() for b in d2.get("brand_names", [])):
                    interactions_found.append({
                        "drug_a": d1["name"],
                        "drug_b": d2["name"],
                        "severity": inter.get("severity", "MODERATE"),
                        "warning": inter.get("warning", "")
                    })

            # Kiểm tra ngược lại từ d2 với d1
            for inter in d2.get("interactions", []):
                target = inter.get("with_drug", "").lower()
                if target in d1["id"].lower() or target in d1["name"].lower() or any(target in b.lower() for b in d1.get("brand_names", [])):
                    # Tránh trùng lặp
                    if not any(f["drug_a"] == d2["name"] and f["drug_b"] == d1["name"] for f in interactions_found):
                        interactions_found.append({
                            "drug_a": d2["name"],
                            "drug_b": d1["name"],
                            "severity": inter.get("severity", "MODERATE"),
                            "warning": inter.get("warning", "")
                        })

    return {
        "status": "success",
        "checked_drugs_count": len(selected_drugs),
        "total_interactions_found": len(interactions_found),
        "has_critical_interaction": any(it["severity"] == "MAJOR" for it in interactions_found),
        "interactions": interactions_found
    }

# --- Module Auto-Crawler & Clinical Calculators ---

from ....services.crawler_service import crawler_service

class CrawlerSyncRequest(BaseModel):
    source: str = "all"  # protocols, drugs, icd10, red_flags, all

@router.get("/crawler/status")
async def get_crawler_status():
    """Lấy trạng thái dữ liệu và lịch sử đồng bộ từ các nguồn y tế uy tín."""
    return crawler_service.get_sync_status()

@router.post("/crawler/sync")
async def run_crawler_sync(req: CrawlerSyncRequest):
    """Kích hoạt cào và làm giàu dữ liệu từ nguồn y tế uy tín."""
    # Xóa cache LRU để cập nhật dữ liệu mới nạp
    _load_red_flags_data.cache_clear()
    _load_rag_protocols_data.cache_clear()
    _load_icd10_data.cache_clear()
    _load_drugs_data.cache_clear()

    res = crawler_service.sync_data(target_source=req.source)
    return res

class CalculationRequest(BaseModel):
    calc_type: str  # bmi, egfr, curb65, pediatric_dose
    params: Dict[str, Any]

@router.post("/calculate")
async def calculate_clinical_metrics(req: CalculationRequest):
    """Hỗ trợ tính toán chỉ số y khoa lâm sàng chuẩn xác."""
    t = req.calc_type.lower()
    p = req.params

    if t == "bmi":
        height_cm = float(p.get("height_cm", 170))
        weight_kg = float(p.get("weight_kg", 65))
        if height_cm <= 0 or weight_kg <= 0:
            raise HTTPException(status_code=400, detail="Chiều cao và cân nặng phải lớn hơn 0")
        h_m = height_cm / 100.0
        bmi = round(weight_kg / (h_m * h_m), 1)

        category = "Bình thường"
        color = "emerald"
        if bmi < 18.5:
            category = "Gầy / Thiếu cân"
            color = "amber"
        elif 23.0 <= bmi < 25.0:
            category = "Thừa cân (Chuẩn châu Á IDI & WPRO)"
            color = "amber"
        elif bmi >= 25.0:
            category = "Béo phì (Chuẩn châu Á IDI & WPRO)"
            color = "red"

        ideal_weight_min = round(18.5 * (h_m * h_m), 1)
        ideal_weight_max = round(22.9 * (h_m * h_m), 1)

        return {
            "status": "success",
            "bmi": bmi,
            "category": category,
            "color": color,
            "ideal_weight_range": f"{ideal_weight_min}kg - {ideal_weight_max}kg"
        }

    elif t == "egfr":
        # Công thức Cockcroft-Gault & CKD-EPI cơ bản
        creat = float(p.get("creatinine_umol", 90)) # umol/L
        age = int(p.get("age", 50))
        gender = p.get("gender", "male").lower() # male or female
        weight = float(p.get("weight_kg", 60))

        if creat <= 0:
            raise HTTPException(status_code=400, detail="Creatinine phải lớn hơn 0")

        # Cockcroft-Gault (mL/phút)
        cg = ((140 - age) * weight) / (0.814 * creat)
        if gender == "female":
            cg = cg * 0.85
        egfr_val = round(cg, 1)

        stage = "G1: Chức năng thận bình thường (eGFR >= 90)"
        color = "emerald"
        if egfr_val < 15:
            stage = "G5: Suy thận mạn giai đoạn cuối (eGFR < 15)"
            color = "red"
        elif egfr_val < 30:
            stage = "G4: Suy giảm chức năng thận nặng (eGFR 15 - 29)"
            color = "red"
        elif egfr_val < 60:
            stage = "G3: Suy giảm chức năng thận vừa (eGFR 30 - 59)"
            color = "amber"
        elif egfr_val < 90:
            stage = "G2: Suy giảm chức năng thận nhẹ (eGFR 60 - 89)"
            color = "amber"

        return {
            "status": "success",
            "egfr": egfr_val,
            "stage": stage,
            "color": color,
            "unit": "mL/phút"
        }

    elif t == "pediatric_dose":
        weight_kg = float(p.get("weight_kg", 15))
        drug_id = p.get("drug_id", "paracetamol").lower()

        if weight_kg <= 0:
            raise HTTPException(status_code=400, detail="Cân nặng phải lớn hơn 0")

        if "paracetamol" in drug_id:
            dose_per_time_min = round(weight_kg * 10, 1)
            dose_per_time_max = round(weight_kg * 15, 1)
            return {
                "status": "success",
                "drug": "Paracetamol",
                "dose_single": f"{dose_per_time_min}mg - {dose_per_time_max}mg",
                "interval": "Mỗi 4 - 6 giờ khi sốt >= 38.5 độ C",
                "max_daily": f"{round(weight_kg * 60, 1)}mg/ngày",
                "commercial_format": f"Gói bột {int(dose_per_time_max // 80 * 80) if dose_per_time_max >= 80 else 80}mg hoặc {int(dose_per_time_max // 150 * 150) if dose_per_time_max >= 150 else 150}mg hoặc Siro Hapacol/Efferalgan"
            }
        elif "ibuprofen" in drug_id:
            dose_per_time_min = round(weight_kg * 5, 1)
            dose_per_time_max = round(weight_kg * 10, 1)
            return {
                "status": "success",
                "drug": "Ibuprofen",
                "dose_single": f"{dose_per_time_min}mg - {dose_per_time_max}mg",
                "interval": "Mỗi 6 - 8 giờ sau khi ăn no",
                "max_daily": f"{round(weight_kg * 30, 1)}mg/ngày",
                "commercial_format": f"Hỗn dịch siro Brufen 100mg/5ml (uống khoảng {round(dose_per_time_max / 20, 1)}ml/lần)"
            }
        elif "amoxicillin" in drug_id or "augmentin" in drug_id:
            dose_per_day_min = round(weight_kg * 40, 1)
            dose_per_day_max = round(weight_kg * 50, 1)
            return {
                "status": "success",
                "drug": "Amoxicillin / Augmentin",
                "dose_daily": f"{dose_per_day_min}mg - {dose_per_day_max}mg / ngày",
                "interval": "Chia 2 lần uống trong ngày sau ăn (mỗi lần ~{round(dose_per_day_max / 2, 1)}mg)",
                "commercial_format": "Gói bột pha Augmentin 250mg hoặc hỗn dịch 125mg/5ml"
            }
        else:
            return {
                "status": "success",
                "drug": drug_id,
                "message": "Tra cứu liều theo cân nặng trong bảng Dược thư bên dưới."
            }

    raise HTTPException(status_code=400, detail="Loại tính toán không được hỗ trợ")

