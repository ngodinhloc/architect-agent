import json
from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool

from app.agent.tools.mcp_client import McpClient


class EpicInput(BaseModel):
    id: str = Field(description="Unique identifier for the epic")
    name: str = Field(description="Name/title of the epic")
    requirements: list[dict] = Field(default=[], description="List of requirement objects")
    solution: dict = Field(default={}, description="Solution architecture dict")


def make_create_epic_tool(mcp_client: McpClient) -> StructuredTool:
    async def _run(id: str, name: str, requirements: list[dict] = [], solution: dict = {}) -> str:
        result = await mcp_client.call("create_epic", {
            "epic": {"id": id, "name": name, "requirements": requirements, "solution": solution}
        })
        return json.dumps(result)

    return StructuredTool.from_function(
        name="create_epic",
        description="Create an epic in the ticket service. Call this when the plan contains an epic to persist.",
        args_schema=EpicInput,
        coroutine=_run,
    )
