from aio_pika import connect_robust, IncomingMessage
from aio_pika.abc import AbstractConnection
from src.config import RABBITMQ_CONNECT_URL
from sqlalchemy import select
from src.models.image_analysis import ImageAnalysis
from src.models.process_status import ProcessStatus
from src.database.connect_db import async_session_maker
from src.models.products_nutrition import ProductsNutrition
from sqlalchemy.ext.asyncio import AsyncSession
from src.logging_config import setup_logging
from loguru import logger
import asyncio, json

async def filling_result_dishes(detail: list, db: AsyncSession):
    result = {}
    nutrients = ("calories", "protein", "fat", "carbs", "sugar", "cholesterol", "iron")
    for food in detail:
        food_name = food["name_food"]
        weight = food["weight"]
        food_info = await db.scalar(
            select(ProductsNutrition)
            .where(ProductsNutrition.product_name == food["name_food"])
        )
        if not food_info:
            logger.warning(f"Продукт {food_name} не найден в бд")
            continue
        result[food_name] = {"weight": weight, "nutrients": {}}
        for nut in nutrients:
            value = getattr(food_info, nut)
            result[food_name]["nutrients"][nut] = round((value/100)*weight, 2)
    result["total_dishes"] = len(detail)
    return result

async def result_processing(message: IncomingMessage):
    async with message.process():
        logger_rabbit = logger.bind(service="RabbitMQ consumer", message_id=message.message_id)
        try:
            data = json.loads(message.body.decode())
            key = data["key"]
            logger_rabbit = logger.bind(service="RabbitMQ consumer", key_id=key)
            status = data["result"]["status"]
            detail = data["result"]["detail"]
            async with async_session_maker() as db:
                entry_db: ImageAnalysis = await db.scalar(select(ImageAnalysis).where(ImageAnalysis.s3_key == key))
                if not entry_db:
                    logger_rabbit.error(f"Запись с данным ключом в бд не найдена")
                elif entry_db.status == ProcessStatus.FAILED:
                    logger_rabbit.error(f"Изображение с данным ключом слишком долго обрабатывалось.")
                else:
                    if status == "success":
                        result = await filling_result_dishes(detail, db)
                        entry_db.status = ProcessStatus.SUCCESS
                        entry_db.result = result
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

if __name__ == "__main__":
    asyncio.run(main())