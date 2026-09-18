import logging
from ..core.config import settings

logger = logging.getLogger(__name__)

try:
    from celery import Celery
    celery_app = Celery(
        "medical_tasks",
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND
    )
    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="Asia/Ho_Chi_Minh",
        enable_utc=True,
    )
except Exception as e:
    logger.warning(f"Celery could not be initialized directly ({e}). Tasks will run synchronously if called.")
    celery_app = None
