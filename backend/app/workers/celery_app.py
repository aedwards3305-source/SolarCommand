"""Celery application configuration."""

from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "solarcommand",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.workers.tasks",
        "app.workers.ai_tasks",
        "app.workers.ai_operator_tasks",
        "app.workers.voice_tasks",
        "app.workers.enrichment_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="US/Eastern",
    enable_utc=True,
    # Reliability: acknowledge tasks only after completion
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    # Default retry policy for all tasks
    task_default_retry_delay=60,  # 1 minute initial delay
    task_max_retries=3,
    # Prevent worker from prefetching too many tasks
    worker_prefetch_multiplier=1,
    beat_schedule={
        # Existing: process outreach queue
        "process-outreach-queue": {
            "task": "app.workers.tasks.process_outreach_queue",
            "schedule": 60.0,
        },
        # Every 5 min: process new conversations/messages
        "ai-process-new-conversations": {
            "task": "app.workers.ai_operator_tasks.task_process_new_conversations",
            "schedule": 300.0,
        },
        # Nightly at 2am ET: recompute NBA for active leads
        "ai-nightly-nba-batch": {
            "task": "app.workers.ai_operator_tasks.task_nightly_nba_batch",
            "schedule": crontab(hour=2, minute=0),
        },
        # Weekly Mon 7am ET: insights + script suggestions + memory update
        "ai-weekly-operator-run": {
            "task": "app.workers.ai_operator_tasks.task_weekly_operator_run",
            "schedule": crontab(hour=7, minute=0, day_of_week="monday"),
        },
        # Daily at 3am ET: batch enrich hot/warm leads
        "enrichment-daily-batch": {
            "task": "app.workers.enrichment_tasks.task_enrich_batch",
            "schedule": crontab(hour=3, minute=0),
        },
    },
)
