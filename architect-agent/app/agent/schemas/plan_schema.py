from pydantic import BaseModel


class RequirementOut(BaseModel):
    requirement: str


class AcceptanceCriterionOut(BaseModel):
    criterion: str


class TicketOut(BaseModel):
    name: str
    requirements: list[RequirementOut]
    acceptance_criteria: list[AcceptanceCriterionOut]


class PlanOut(BaseModel):
    tickets: list[TicketOut]
