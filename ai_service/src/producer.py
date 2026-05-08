from aio_pika.abc import AbstractConnection
from aio_pika import DeliveryMode, Message
import json

class Producer:
    def __init__(self, connection: AbstractConnection):
        self.connection = connection
        self.channel = None
    
    async def init_channel_and_queue(self):
        self.channel = await self.connection.channel()
        await self.channel.declare_queue("processed_images", durable=True)
    
    async def publish_response(self, data: dict):
        msg_body = json.dumps(data).encode()
        await self.channel.default_exchange.publish(
            message=Message(
                body=msg_body,
                delivery_mode=DeliveryMode.PERSISTENT
            ),
            routing_key="processed_images"
        )
    
    async def close(self):
        if self.channel:
            await self.channel.close()