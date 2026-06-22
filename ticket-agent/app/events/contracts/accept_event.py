from pydantic import BaseModel


class AcceptEvent(BaseModel):
    conversationId: str
    content: dict
