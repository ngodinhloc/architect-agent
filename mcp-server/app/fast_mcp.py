from fastmcp import FastMCP
from app.container import container

fast_mcp = FastMCP("Architect MCP Server")


@fast_mcp.tool()
async def create_epic(epic: dict) -> dict:
    """Create an epic in the ticket service. Pass the full EpicInterface object as a dict."""
    return await container.epic_tool.create(epic)


@fast_mcp.tool()
async def create_ticket(ticket: dict) -> dict:
    """Create a ticket in the ticket service. Pass the full TicketInterface object as a dict."""
    return await container.ticket_tool.create(ticket)
