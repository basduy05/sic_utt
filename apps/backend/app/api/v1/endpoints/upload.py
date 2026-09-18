from fastapi import APIRouter, UploadFile, File, HTTPException
from ....core.storage import storage_manager

router = APIRouter()

@router.post("/file")
async def upload_file(file: UploadFile = File(...)):
    """Upload tập tin âm thanh hoặc hình ảnh phiếu xét nghiệm lên hệ thống."""
    try:
        content = await file.read()
        url = await storage_manager.save_file(content, file.filename)
        return {
            "filename": file.filename,
            "url": url,
            "size": len(content)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {e}")
