from aio_pika import connect_robust, IncomingMessage
from aio_pika.abc import AbstractConnection
from src.config import RABBITMQ_CONNECT_URL
from sqlalchemy import select
from src.models.image_analysis import ImageAnalysis
from src.models.process_status import ProcessStatus
from src.database.connect_db import async_session_maker
from src.logging_config import setup_logging
from loguru import logger
import asyncio, json

async def result_processing(
    message: IncomingMessage,
):
    async with message.process():
        try:
            data = json.loads(message.body.decode())
            key = data["key"]
            logger_rabbit = logger.bind(service="RabbitMQ consumer", log_id=key)
            status = data["result"]["status"]
            detail = data["result"]["detail"]
            async with async_session_maker() as db:
                entry_db: ImageAnalysis = await db.scalar(select(ImageAnalysis).where(ImageAnalysis.s3_key == key))
                if not entry_db:
                    logger_rabbit.error(f"Запись с данным ключом в бд не найдена")
                elif entry_db.status == ProcessStatus.FAILED:
                    logger_rabbit.error(f"Изображение с данным ключом слишком долго обрабатывалось ")
                else:
                    if status == "success":
                        entry_db.status = ProcessStatus.SUCCESS 
                        entry_db.result = detail
                    else:
                        entry_db.status = ProcessStatus.FAILED
                        entry_db.result = {"error": detail}
                    await db.commit()
        except Exception as exp:
            logger_rabbit.error(f"Ошибка при обработке задачи. Ошибка: {exp}")
        
async def main():
    setup_logging()
    logger_rabbit = logger.bind(service="RabbitMQ consumer")
    connection: AbstractConnection = await connect_robust(url=RABBITMQ_CONNECT_URL)
    async with connection:
        async with connection.channel() as channel:
            queue = await channel.declare_queue(
                name="processed_images",
                durable=True
            )
            await channel.set_qos(prefetch_count=1)
            await queue.consume(result_processing)
            try:
                await asyncio.Future()
            except Exception:
                logger_rabbit.info("Конец работы")

asyncio.run(main())