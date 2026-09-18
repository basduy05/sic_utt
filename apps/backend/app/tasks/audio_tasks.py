import logging
from .celery_app import celery_app
from ..services.triage_service import triage_service

logger = logging.getLogger(__name__)

def process_async_audio(audio_bytes: bytes, filename: str):
    logger.info(f"Processing audio background task: {filename}")
    return triage_service.pipeline.stt_engine.transcribe(audio_bytes, filename)

if celery_app is not None:
    @celery_app.task(name="tasks.process_audio")
    def celery_process_audio(audio_bytes: bytes, filename: str):
        return process_async_audio(audio_bytes, filename)
