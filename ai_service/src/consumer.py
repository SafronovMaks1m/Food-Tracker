from src.services.s3_service import s3_client
from src.producer import Producer
from aiobotocore.client import AioBaseClient
from functools import partial
from aio_pika import connect_robust, IncomingMessage
from aio_pika.abc import AbstractConnection
from src.config import RABBITMQ_CONNECT_URL
from src.logging_config import setup_logging
from src.services.food_recognition_service.ai_handler import AIHandler
from loguru import logger
import asyncio, json, os

async def image_processing(
    message: IncomingMessage,
    producer: Producer,
    client: AioBaseClient,
    ai_client: AIHandler
):
    async with message.process(requeue=True):
        logger_rabbit = logger.bind(service="RabbitMQ consumer", message_id=message.message_id)
        try:
            data = json.loads(message.body.decode())
            user_id = data["user_id"]
            key = data["key"]
            logger_rabbit = logger.bind(service="RabbitMQ consumer", key_id=key)
            image_bytes = await s3_client.download_image(client, key, "food-images")
            result = await asyncio.to_thread(ai_client.analyze, image_bytes)
            response = {
                "user_id": user_id,
                "key": key,
                "result": result
            }
            await producer.publish_response(response)
            if result["status"] == "failed":
                logger_rabbit.warning(f"{result["detail"]}")
            else:
                logger_rabbit.info("Изображение успешно обработалось") 
        except Exception as exp:
            logger_rabbit.error(f"Произошла ошибка при обработке изображения. Ошибка: {exp}")
            raise

async def main():
    while True:
        try:    
            connection: AbstractConnection = await connect_robust(url=RABBITMQ_CONNECT_URL)
            break
        except Exception:
            await asyncio.sleep(3)
    setup_logging()
    logger_rabbit = logger.bind(service="RabbitMQ consumer")
    ai_client = AIHandler()
    async with s3_client.session.create_client("s3", **s3_client.config) as client:
        async with connection:
            producer = Producer(connection)
            await producer.init_channel_and_queue()
            async with connection.channel() as channel:
                queue = await channel.declare_queue(
                    name="raw_images",
                    durable=True
                )
                await channel.set_qos(prefetch_count=1)
                await queue.consume(
                    partial(image_processing, producer=producer, client=client, ai_client=ai_client)
                )
                try:
                    await asyncio.Future()
                except Exception:
                    logger_rabbit.info("Конец работы")
                    await producer.close()

if __name__ == "__main__":
    asyncio.run(main())