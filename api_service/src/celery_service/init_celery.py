from celery import Celery
from celery.schedules import crontab
from zoneinfo import ZoneInfo
from src.config import RABBITMQ_CONNECT_URL

celery = Celery(
    "init_celery",
    broker=RABBITMQ_CONNECT_URL
)

celery.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    include=['src.celery_service.bg_tasks'],
    timezone=ZoneInfo("UTC")
)

celery.conf.beat_schedule = {
    'run-me-background-task': {
        'task': 'src.celery_service.bg_tasks.cleaning_failed',
        'schedule': crontab(minute=0, hour=0),
    }
}