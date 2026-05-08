from src.services.sending_code import SendCode
from src.celery_service.init_celery import celery
from src.database.connect_db import async_session_maker
from src.models.image_analysis import ImageAnalysis
from sqlalchemy import select
from datetime import datetime, timezone, timedelta
from src.models.process_status import ProcessStatus
from src.services.s3_storage.s3_service import s3_client
from loguru import logger
import asyncio    
    
    
@celery.task(queue="messages")
def send_messages(email: str, cnt: str, code: str):
    logger_celery = logger.bind(service="Celery")
    try:
        SendCode.send_code_email(email=email, cnt=cnt, code=code)
    except Exception as exp:
        logger_celery.error(f"Ошибка при отправке сообщения на почту: {exp}")

@celery.task(
    queue="cleanup_garbage",
    bind=True, 
    default_retry_delay=300,
    max_retries=3
)
def cleaning_failed(self):
    logger_celery = logger.bind(service="Celery")
    try:
        asyncio.run(run_cleaning_failed())
    except Exception as exc:
        logger_celery.error(f"Ошибка в задаче очистки: {exc}")
        raise self.retry()

async def run_cleaning_failed():
    logger_celery = logger.bind(service="Celery")
    cur_time = datetime.now(timezone.utc) - timedelta(hours=1)
    async with async_session_maker() as db:
        query = (select(ImageAnalysis)
                 .where(ImageAnalysis.create_at <= cur_time,
                        ImageAnalysis.status != ProcessStatus.SUCCESS)
                )
        tmp = await db.scalars(query)
        failed_tasks = tmp.all()
        
        if not failed_tasks:
            logger_celery.info("Очистка провальных данных завершена. Удалено 0 записей.")
            return
        
        deleted_count = 0
        for task in failed_tasks:
            try:
                await s3_client.delete_image("food-images", task.s3_key)
                await db.delete(task)
                await db.commit()
                deleted_count += 1
            except Exception as exp:
                logger_celery.error(f"Ошибка при очистке по ключу: {task.s3_key}. Ошибка: {exp}")
        
        logger_celery.info(f"Очистка провальных данных завершена. Удалено {deleted_count} записей из {len(failed_tasks)}")