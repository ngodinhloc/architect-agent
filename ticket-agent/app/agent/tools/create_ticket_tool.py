import json
from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool

from app.agent.tools.mcp_client import McpClient


class TicketInput(BaseModel):
    id: str = Field(description="Unique identifier for the ticket")
    epicId: str = Field(description="ID of the parent epic")
    name: str = Field(description="Name/title of the ticket")
    requirements: list[dict] = Field(default=[], description="List of requirement objects")
    acceptance_criteria: list[dict] = Field(default=[], description="List of acceptance criterion objects")


def make_create_ticket_tool(mcp_client: McpClient) -> StructuredTool:
    async def _run(
        id: str,
        epicId: str,
        name: str,
        requirements: list[dict] = [],
        acceptance_criteria: list[dict] = [],
    ) -> str:
        result = await mcp_client.call("create_ticket", {
            "ticket": {
                "id": id,
                "epicId": epicId,
                "name": name,
                "requirements": requirements,
                "acceptance_criteria": acceptance_criteria,
            }
        })
        return json.dumps(result)

    return StructuredTool.from_function(
        name="create_ticket",
        description="Create a development ticket in the ticket service. Call this for each ticket in the plan.",
        args_schema=TicketInput,
        coroutine=_run,
    )
