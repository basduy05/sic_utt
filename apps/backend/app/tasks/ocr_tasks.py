import logging
from .celery_app import celery_app
from ..services.triage_service import triage_service

logger = logging.getLogger(__name__)

def process_async_ocr(file_bytes: bytes, filename: str):
    logger.info(f"Processing OCR background task: {filename}")
    doc_ext = filename.lower().split(".")[-1] if filename else ""
    if doc_ext == "pdf":
        return triage_service.pipeline.pdf_parser.parse_pdf(file_bytes)
    return triage_service.pipeline.image_ocr.process_image(file_bytes)

if celery_app is not None:
    @celery_app.task(name="tasks.process_ocr")
    def celery_process_ocr(file_bytes: bytes, filename: str):
        return process_async_ocr(file_bytes, filename)
