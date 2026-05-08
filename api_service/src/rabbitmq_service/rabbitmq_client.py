import json
from aio_pika import connect_robust, DeliveryMode, Message
from aio_pika.abc import AbstractRobustConnection, AbstractChannel
from src.config import RABBITMQ_CONNECT_URL

class RabbitMQClient:
    def __init__(self):
        self.connection: None | AbstractRobustConnection = None
        self.channel: None | AbstractChannel = None 
        
    async def init_connect(self):
        self.connection = await connect_robust(url=RABBITMQ_CONNECT_URL)
        self.channel = await self.connection.channel()
        await self.channel.declare_queue("raw_images", durable=True)
    
    async def publish_task(self, data: dict):
        msg_body = json.dumps(data).encode()

        await self.channel.default_exchange.publish(
            message=Message(
                body=msg_body,
                delivery_mode=DeliveryMode.PERSISTENT
            ),
            routing_key="raw_images"
        )
        
    async def close(self):
        if self.connection:
            await self.connection.close()
        await self.channel.close()

rabbitmq_client = RabbitMQClient()