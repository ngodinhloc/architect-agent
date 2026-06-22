import httpx
from app.configs.settings import settings


class EpicTool:
    async def create(self, epic: dict) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{settings.ticket_service_url}/api/epic/", json=epic)
            resp.raise_for_status()
            return resp.json()
