from pydantic import BaseModel


class PlanReviewOut(BaseModel):
    approved: bool
    comments: list[str] = []
