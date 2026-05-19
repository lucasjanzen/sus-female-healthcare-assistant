from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "casf",
    broker=settings.celery_broker_url,
    backend=settings.celery_broker_url,
    include=["app.tasks.analise_task"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    worker_prefetch_multiplier=1,
)
