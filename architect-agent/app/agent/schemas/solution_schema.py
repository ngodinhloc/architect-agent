from pydantic import BaseModel


class FeatureOut(BaseModel):
    feature: str


class ComponentOut(BaseModel):
    tech: str
    features: list[FeatureOut]


class SolutionOut(BaseModel):
    architecture: str
    components: list[ComponentOut]
