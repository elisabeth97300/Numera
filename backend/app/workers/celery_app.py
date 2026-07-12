"""
Configuration Celery. Les tâches longues (OCR, appel LLM) passent par ici
plutôt que dans le corps d'une requête FastAPI, pour ne jamais bloquer une
réponse HTTP en attendant un traitement de plusieurs secondes.
"""

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "comptacopilot",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.ocr_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
)
