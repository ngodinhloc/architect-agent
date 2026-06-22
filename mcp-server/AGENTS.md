# MCP Server — Agent Instructions

FastMCP + FastAPI service that exposes two tools over the MCP protocol. All tool calls from the AI agent arrive as streamable HTTP at `POST /mcp/`. Translates each tool call into a REST request to the ticket-service.

## Stack

- **FastMCP 2** — MCP protocol server
- **FastAPI** — HTTP server, mounts FastMCP at `/mcp`
- **httpx** — async HTTP calls to ticket-service
- **pydantic-settings** — typed config from environment / `.env`

## File structure

```
app/
  main.py                   FastAPI app, CORS, logging middleware, mounts /mcp
  fast_mcp.py               FastMCP instance + @fast_mcp.tool() definitions
  container.py              Container (EpicTool, TicketTool as cached_property)
  configs/
    settings.py             Settings (ticket_service_url, cors_origins)
  routers/
    health_router.py        GET /api/health
  tools/
    epic_tool.py            EpicTool.create() — POST {ticket_service_url}/api/epic/
    ticket_tool.py          TicketTool.create() — POST {ticket_service_url}/api/ticket/
```

## Tools

| Tool | MCP name | Calls | Description |
|------|----------|-------|-------------|
| `create_epic` | `create_epic` | `POST /api/epic/` | Create an epic in the ticket service |
| `create_ticket` | `create_ticket` | `POST /api/ticket/` | Create a ticket in the ticket service |

Both tools accept a `dict` argument matching the respective interface shape and return the ticket-service JSON response.

## Endpoints

| Method | Path | Protocol | Description |
|--------|------|----------|-------------|
| `POST` | `/mcp/` | MCP streamable HTTP | FastMCP tool endpoint — called by the AI agent's `McpClient` |
| `GET` | `/api/health` | REST | Health check |

## Tool flow

```
AI agent McpClient.call("create_epic", { epic: {...} })
  → POST /mcp/   (MCP protocol)
  → fast_mcp.tool create_epic(epic)
  → container.epic_tool.create(epic)
  → httpx POST {ticket_service_url}/api/epic/
  → returns ticket-service JSON response
```

## Environment

```
TICKET_SERVICE_URL=http://localhost:8003
CORS_ORIGINS=http://localhost:3000
```

`TICKET_SERVICE_URL` is injected by Docker Compose as `http://ticket-service:8000`.

## Dev commands

```bash
pip install .
uvicorn app.main:app --reload --port 8002
```
