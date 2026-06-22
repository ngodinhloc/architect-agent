import json
import logging
from app.events.contracts.accept_event import AcceptEvent
from app.events.contracts.consumer_message import ConsumerMessage
from app.services.ticket_service import TicketService


class AcceptEventHandler:
    def __init__(self, ticket_service: TicketService, logger: logging.Logger):
        self._ticket_service = ticket_service
        self._logger = logger

    async def handle(self, message: ConsumerMessage) -> None:
        try:
            payload = json.loads(message.body)
            event = AcceptEvent(
                conversationId=payload["conversationId"],
                content=payload["content"],
            )
            self._logger.info("Received accept event conversationId=%s", event.conversationId)
            await self._ticket_service.handle(event)
        except Exception:
            self._logger.exception("Failed to process accept event: %s", message.body)
