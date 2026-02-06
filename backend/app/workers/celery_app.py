"""Celery application configuration."""

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "solarcommand",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="US/Eastern",
    enable_utc=True,
    # Beat schedule for periodic tasks
    beat_schedule={
        "process-outreach-queue": {
            "task": "app.workers.tasks.process_outreach_queue",
            "schedule": 60.0,  # Every 60 seconds
        },
    },
)
