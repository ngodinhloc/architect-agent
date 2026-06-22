# Plan: Multi-Agent Architect

## Overview

Build a multi-agent system that takes a natural-language software requirement, runs it through a 4-agent approval loop (solution design → solution review → ticket planning → ticket review), and returns a `ReplyInterface` (solution architecture + development tickets). The user can then accept the plan — triggering `create_epic` and `create_ticket` MCP tool calls — or refine it with follow-up messages that restart the planning loop.

---

## Project structure

```
multi-agent-archiect/
├── docker-compose.yml
├── frontend/              Next.js 16 / React 19 / Tailwind CSS 4
├── backend/               NestJS 11, TypeORM, Redis, RabbitMQ
├── ai-agent/              FastAPI, LangGraph, LangChain Anthropic
├── mcp-server/            FastMCP, FastAPI
└── ticket-service/        NestJS 11, TypeORM (separate PostgreSQL)
```

---

## 1. docker-compose.yml

Eight services with health checks and named volumes:

| Service | Port | Depends on |
|---------|------|-----------|
| rabbitmq | 5672, 15672 | — |
| postgres-backend | 5432 | — |
| postgres-tickets | 5433 | — |
| redis | internal | — |
| ticket-service | 8003 | postgres-tickets |
| mcp-server | 8002 | ticket-service |
| ai-agent | 8001 | mcp-server, rabbitmq, redis |
| backend | 8000 | postgres-backend, redis, rabbitmq |
| frontend | 3000 | backend |

Key environment wiring:
- `backend` → `DATABASE_URL=postgresql://architect:architect@postgres-backend:5432/architect`
- `ticket-service` → `DATABASE_URL=postgresql://tickets:tickets@postgres-tickets:5432/tickets`
- `ai-agent` → `ANTHROPIC_API_KEY` (from `ai-agent/.env`), `MCP_SERVER_URL=http://mcp-server:8000`, `REDIS_URL`, `RABBITMQ_URL`
- `mcp-server` → `TICKET_SERVICE_URL=http://ticket-service:8000`

---

## 2. Backend (NestJS 11)

### Module layout

```
src/
  chat/
    contracts/chat.interface.ts       All domain types (MessageInterface, ChatInterface, ReplyInterface, …)
    controllers/chat.controller.ts    REST API
    services/chat.service.ts          PostgreSQL + Redis reads/writes
    services/agent.service.ts         Publishes ChatEvent to RabbitMQ
    gateways/chat.gateway.ts          WebSocket, polls Redis at 500 ms
  database/
    entities/conversation.entity.ts   id, title, messages (jsonb), createdAt, updatedAt
  redis/services/redis.service.ts     getJson / setJson / del
  rabbitmq/services/rabbitmq.service.ts  asserts queue, publish()
```

### REST API

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/chat/new` | Create conversation in PostgreSQL + Redis, publish `ChatEvent`, return `{ id }` |
| `POST` | `/api/chat/:id/cont` | Append user message, publish `ChatEvent`, return `{ accepted: true }` |
| `POST` | `/api/chat/:id/stop` | Persist messages to PostgreSQL, delete Redis key |
| `GET` | `/api/chat/history` | All conversations (id, title, createdAt) |
| `GET` | `/api/chat/:id` | Live from Redis or persisted from PostgreSQL |
| `WS` | `/ws` | Subscribe with `{ event: "subscribe", data: chatId }`, receive `chat-update` events |

### Data model

```typescript
interface MessageInterface {
    actor:       "User" | "Agent";
    timestamp:   Date;
    content:     string | ReplyInterface | FinalReplyInterface;
    agentStatus: "isThinking" | "hasReplied" | null;
}

interface ChatInterface {
    id:          string;
    title:       string | null;
    messages:    MessageInterface[];     // jsonb column in PostgreSQL
    status:      "isActive" | "isStopped";
    agentStatus: "isThinking" | "hasReplied";
}
```

### Key decisions

- **`messages` (not `content`)** — the PostgreSQL jsonb column and Redis object both use `messages: MessageInterface[]`. Thinking-log entries and the final reply live in the same array, distinguished by `agentStatus`.
- **RabbitMQ queue name** — `architecture-agent.chat` (durable, `persistent: true`).
- **Redis key** — `chat:{uuid}`. Written by the backend on `newChat`, mutated in-place by the ai-agent during streaming, deleted on `stopChat`.
- **TypeORM `synchronize: true`** — no migration files in dev. Tables are created on startup.

---

## 3. AI Agent (Python / FastAPI / LangGraph)

### Architecture

```
FastAPI app
  └── lifespan: starts RabbitMQConsumer (aio-pika)
        └── queue: architecture-agent.chat
              └── ChatEventHandler.handle(message)
                    └── ChatService.handle(event)
                          └── graph.astream(initial_state)
                                → per-node: append thinking message to Redis
                          └── append reply message to Redis (agentStatus: hasReplied)
```

### LangGraph state

```python
class ArchitectState(MessagesState):
    requirement: str = ""
    raw_history: list[dict] = []        # raw MessageInterface dicts from the event
    user_intent: str = "plan"           # "plan" | "refine" | "accept"
    solution: dict | None = None        # SolutionInterface as dict
    solution_review_comments: list[str] = []
    solution_approved: bool = False
    tickets: list[dict] = []            # list[TicketInterface] as dicts
    ticket_review_comments: list[str] = []
    tickets_approved: bool = False
    final_reply: dict | None = None     # ReplyInterface or FinalReplyInterface as dict
```

### Graph

```
START → intent_node
         ├──[plan/refine]──► solution_node → solution_review_node
         │                                     ├──[approved]──► plan_node → plan_review_node
         │                                     │                              ├──[approved]──► reply_node → END
         │                                     │                              └──[rejected]──► plan_node
         │                                     └──[rejected]──► solution_node
         └──[accept]──► create_node → END
```

### Node contracts

| Node | LLM | Structured output | State written |
|------|-----|-------------------|---------------|
| `intent_node` | Yes | `IntentResult { intent: "plan"|"refine"|"accept" }` | `user_intent`; on accept also `solution`, `tickets`, `final_reply` |
| `solution_node` | Yes | `SolutionOut { architecture, components }` | `solution`, `solution_approved=False` |
| `solution_review_node` | Yes | `SolutionReviewOut { approved, comments }` | `solution_approved`, `solution_review_comments` |
| `plan_node` | Yes | `PlanOut { tickets }` | `tickets`, `tickets_approved=False` |
| `plan_review_node` | Yes | `PlanReviewOut { approved, comments }` | `tickets_approved`, `ticket_review_comments` |
| `reply_node` | No | — | `final_reply` (ReplyInterface dict) |
| `create_node` | No | — | `final_reply` (FinalReplyInterface dict) |

All LLM nodes use `ChatAnthropic(model="claude-sonnet-4-6").with_structured_output(PydanticModel)`.

### Accept flow

When `intent_node` classifies the message as `"accept"`:
1. Scans `raw_history` for the most recent agent message with `content.epic` and `content.tickets`.
2. Populates `solution`, `tickets`, and `final_reply` from that entry so `create_node` has everything it needs.
3. `create_node` calls `McpClient.call("create_epic", ...)` then `McpClient.call("create_ticket", ...)` per ticket.
4. Writes `FinalReplyInterface { epicId, ticketIds }` to `final_reply`.

### File layout

```
app/
  main.py                                     FastAPI app
  container.py                                Cached-property singletons
  configs/settings.py                         Typed settings (pydantic-settings)
  agent/
    architect_graph.py                        ArchitectGraph.build()
    contracts/agent_interface.py              ArchitectState
    nodes/                                    intent, solution, solution_review, plan, plan_review, reply, create
    tools/mcp_client.py                       McpClient (FastMCP Client)
  events/
    contracts/chat_interface.py               All Pydantic models mirroring SPECS
    handlers/chat_event_handler.py
    rabbitmq_consumer.py
  services/
    chat_service.py                           Streams graph, writes Redis
    chat_manager.py                           Load/save ChatInterface from/to Redis
    redis_client.py
```

---

## 4. MCP Server (FastMCP / FastAPI)

### Tools

```python
@fast_mcp.tool()
async def create_epic(epic: dict) -> dict:
    return await container.epic_tool.create(epic)

@fast_mcp.tool()
async def create_ticket(ticket: dict) -> dict:
    return await container.ticket_tool.create(ticket)
```

`EpicTool.create()` → `POST {ticket_service_url}/api/epic/`
`TicketTool.create()` → `POST {ticket_service_url}/api/ticket/`

MCP endpoint: `POST /mcp/` (streamable HTTP). Called by `McpClient` in the ai-agent.

### File layout

```
app/
  main.py
  fast_mcp.py                  FastMCP instance + @fast_mcp.tool() decorators
  container.py
  configs/settings.py          ticket_service_url, cors_origins
  tools/
    epic_tool.py
    ticket_tool.py
  routers/health_router.py
```

---

## 5. Ticket Service (NestJS 11)

Standalone NestJS CRUD app with its own PostgreSQL database (`tickets`). No RabbitMQ, no Redis, no WebSocket.

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/epic/` | Create epic; id is agent-generated UUID |
| `GET` | `/api/epic/:id` | Get epic |
| `POST` | `/api/ticket/` | Create ticket; id and epicId are agent-generated |
| `GET` | `/api/epic/:epicId/tickets` | Get all tickets for an epic |
| `GET` | `/api/health` | Health check |

### Entities

```typescript
// epics table
@Entity('epics')
class Epic {
    @PrimaryColumn({ type: 'uuid' }) id: string;
    @Column() name: string;
    @Column({ type: 'jsonb' }) requirements: RequirementInterface[];
    @Column({ type: 'jsonb' }) solution: SolutionInterface;
    @CreateDateColumn() createdAt: Date;
}

// tickets table
@Entity('tickets')
class Ticket {
    @PrimaryColumn({ type: 'uuid' }) id: string;
    @Column({ type: 'uuid' }) epicId: string;
    @Column() name: string;
    @Column({ type: 'jsonb' }) requirements: RequirementInterface[];
    @Column({ type: 'jsonb' }) acceptance_criteria: AcceptanceCriterionInterface[];
    @CreateDateColumn() createdAt: Date;
}
```

IDs are generated by `plan_node` (`uuid.uuid4()`) before any MCP call. The ticket-service stores them as provided. `TypeORM synchronize: true` creates both tables on startup.

### File layout

```
src/
  database/entities/epic.entity.ts, ticket.entity.ts
  epic/controllers/epic.controller.ts, services/epic.service.ts, dto/create-epic.dto.ts
  ticket/controllers/ticket.controller.ts, services/ticket.service.ts, dto/create-ticket.dto.ts
  health/controllers/health.controller.ts
```

---

## 6. Frontend (Next.js 16 / React 19 / Tailwind CSS 4)

### Component architecture

```
app/layout.tsx          Root layout — Sidebar + main area
app/page.tsx            Renders <ArchitectChat>
components/
  ArchitectChat.tsx     All state: WebSocket, multi-turn, accept/refine flow
  PlanCard.tsx          Renders ReplyInterface — architecture sections + ticket list + "Looks good" button
  FinalReplyCard.tsx    Renders FinalReplyInterface — epicId + ticketIds
  Sidebar.tsx           Conversation history
lib/api.ts              newChat, continueChat, getChat, stopChat, getHistory
types/chat.ts           TypeScript interfaces mirroring SPECS
```

### Key flows

**New requirement**
1. User submits → `newChat(message)` → `{ id }`
2. Open `WebSocket` at `/ws`, send `{ event: "subscribe", data: id }`
3. On `chat-update`: render thinking-log entries; when `agentStatus === "hasReplied"`, render `PlanCard`

**Accept**
- "Looks good" button → `continueChat(id, "Looks good, please create the epic and tickets.")`
- Next `chat-update` with `FinalReplyInterface` content → render `FinalReplyCard`

**Refine**
- Free-text input → `continueChat(id, message)` → new planning loop → new `PlanCard`

### Type guards

```typescript
function isReplyInterface(c: unknown): c is ReplyInterface {
    return typeof c === "object" && c !== null && "epic" in c && "tickets" in c;
}
function isFinalReplyInterface(c: unknown): c is FinalReplyInterface {
    return typeof c === "object" && c !== null && "epicId" in c && "ticketIds" in c;
}
```

`MessageInterface.content` is `string | ReplyInterface | FinalReplyInterface`. Field is named `content` (not `text`). Chat array is named `messages` (not `content`).

### Environment

```
API_TARGET=http://backend:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

All REST calls use relative `/api/` paths (proxied by Next.js to `API_TARGET`).

---

## Verification checklist

1. `cp ai-agent/.env.example ai-agent/.env` — set `ANTHROPIC_API_KEY`
2. `docker compose up --build` — all 9 services start healthy
3. Open `http://localhost:3000`, type "implement an SFTP solution"
4. Watch thinking-log stream: Analyzing → Designing → Reviewing solution → Creating tickets → Reviewing tickets → Preparing response
5. `ReplyInterface` renders in `PlanCard` with solution architecture and ticket list
6. Click "Looks good" → `FinalReplyCard` shows `epicId` and `ticketIds`
7. `GET http://localhost:8003/api/epic/{epicId}` — confirm epic in ticket-service PostgreSQL
8. `GET http://localhost:8003/api/epic/{epicId}/tickets` — confirm all tickets persisted
9. Type "add a security ticket" → new planning loop → updated `PlanCard`
