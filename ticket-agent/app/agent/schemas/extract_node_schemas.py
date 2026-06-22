from pydantic import BaseModel


class ExtractOut(BaseModel):
    epicId: str
    ticketIds: list[str] = []
