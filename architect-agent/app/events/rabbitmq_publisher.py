import json
import logging
import aio_pika

logger = logging.getLogger(__name__)


class RabbitMQPublisher:
    def __init__(self, rabbitmq_url: str):
        self._url = rabbitmq_url
        self._connection: aio_pika.abc.AbstractRobustConnection | None = None
        self._channel: aio_pika.abc.AbstractChannel | None = None

    async def publish(self, queue: str, payload: dict) -> None:
        if self._connection is None or self._connection.is_closed:
            self._connection = await aio_pika.connect_robust(self._url)
            self._channel = await self._connection.channel()

        await self._channel.declare_queue(queue, durable=True)
        await self._channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(payload, default=str).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=queue,
        )
        logger.info("Published to queue=%s conversationId=%s", queue, payload.get("conversationId"))
