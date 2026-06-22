from pydantic import BaseModel


class SolutionReviewOut(BaseModel):
    approved: bool
    comments: list[str] = []
