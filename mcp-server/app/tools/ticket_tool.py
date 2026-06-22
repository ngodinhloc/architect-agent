import httpx
from app.configs.settings import settings


class TicketTool:
    async def create(self, ticket: dict) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{settings.ticket_service_url}/api/ticket/", json=ticket)
            resp.raise_for_status()
            return resp.json()
