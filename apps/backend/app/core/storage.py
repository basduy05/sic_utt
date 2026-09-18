import os
import uuid
import logging
from typing import Optional
from .config import settings

logger = logging.getLogger(__name__)

class StorageManager:
    """Quản lý lưu trữ tập tin âm thanh, tài liệu PDF, hình ảnh xét nghiệm."""
    def __init__(self):
        self.local_upload_dir = os.path.join(os.getcwd(), "uploads")
        os.makedirs(self.local_upload_dir, exist_ok=True)

    async def save_file(self, file_bytes: bytes, filename: str) -> str:
        unique_name = f"{uuid.uuid4().hex}_{filename}"
        file_path = os.path.join(self.local_upload_dir, unique_name)
        with open(file_path, "wb") as f:
            f.write(file_bytes)
        logger.info(f"Saved file locally at {file_path}")
        return f"/uploads/{unique_name}"

storage_manager = StorageManager()
