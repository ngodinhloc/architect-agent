# AI Agent — Agent Instructions

Python FastAPI service that runs a LangGraph state graph with six nodes to produce a software architecture plan and development tickets. The graph handles two flows: a planning loop (solution → review → plan → review → reply) and an accept flow (create epic + tickets via MCP).

## Stack

- **FastAPI** — HTTP server, lifespan starts the RabbitMQ consumer
- **LangGraph** — stateful graph with conditional edges and approval loops
- **LangChain Anthropic** — Claude (`claude-sonnet-4-6`) via `langchain-anthropic`
- **FastMCP Client** — calls the MCP server's `create_epic` and `create_ticket` tools
- **aio-pika** — async RabbitMQ consumer on queue `architecture-agent.chat`
- **redis[asyncio]** — reads and writes `ChatInterface` in Redis
- **pydantic-settings** — typed config from `.env`

## File structure

```
app/
  main.py                                 FastAPI app, lifespan starts RabbitMQConsumer
  container.py                            Container (cached_property singletons)
  configs/
    settings.py                           Settings (anthropic_api_key, mcp_server_url, …)
  agent/
    architect_graph.py                    ArchitectGraph.build() — compiles the LangGraph StateGraph
    contracts/
      agent_interface.py                  ArchitectState (extends MessagesState)
    nodes/
      intent_node.py                      Classify user intent: plan | refine | accept
      solution_node.py                    Generate SolutionInterface from requirement
      solution_review_node.py             Approve/reject solution; return comments
      plan_node.py                        Generate TicketInterface[] from solution
      plan_review_node.py                 Approve/reject tickets; return comments
      reply_node.py                       Assemble ReplyInterface, set final_reply in state
      create_node.py                      Call create_epic + create_ticket MCP tools; set FinalReplyInterface
    tools/
      mcp_client.py                       McpClient (FastMCP Client over streamable HTTP)
  events/
    contracts/
      chat_interface.py                   ChatEvent, ChatInterface, MessageInterface, ReplyInterface, …
      consumer_message.py                 ConsumerMessage typing.Protocol
    handlers/
      chat_event_handler.py               ChatEventHandler — deserialises message, calls ChatService
    rabbitmq_consumer.py                  RabbitMQConsumer — aio-pika queue iterator
  services/
    chat_service.py                       ChatService — streams graph, writes Redis
    chat_manager.py                       ChatManager — Redis load/save, append thinking/reply messages
    redis_client.py                       RedisClient — lazy aioredis singleton
    redis_helper.py                       RedisHelper.chat_key(conversation_id)
  routers/
    health_router.py                      GET /api/health
```

## Agent graph

```
START → intent_node
         ├──[plan/refine]──► solution_node → solution_review_node
         │                                     ├──[approved]──► plan_node → plan_review_node
         │                                     │                              ├──[approved]──► reply_node → END
         │                                     │                              └──[rejected]──► plan_node
         │                                     └──[rejected]──► solution_node
         └──[accept]──► create_node → END
```

### State (`ArchitectState`)

```python
class ArchitectState(MessagesState):
    requirement: str = ""
    raw_history: list[dict] = []        # raw MessageInterface dicts from the event
    user_intent: str = "plan"           # "plan" | "accept" | "refine"
    solution: dict | None = None        # SolutionInterface as dict
    solution_review_comments: list[str] = []
    solution_approved: bool = False
    tickets: list[dict] = []            # list[TicketInterface] as dicts
    ticket_review_comments: list[str] = []
    tickets_approved: bool = False
    final_reply: dict | None = None     # ReplyInterface or FinalReplyInterface as dict
```

### Node contracts

Each node is an `async def` function that receives `ArchitectState` and returns a partial state dict.

| Node | LLM call | Structured output | State written |
|------|----------|------------------|---------------|
| `intent_node` | Yes | `IntentResult { intent }` | `user_intent`, `solution`, `tickets`, `final_reply` (if accept) |
| `solution_node` | Yes | `SolutionOut { architecture, components }` | `solution`, `solution_approved=False` |
| `solution_review_node` | Yes | `SolutionReviewOut { approved, comments }` | `solution_approved`, `solution_review_comments` |
| `plan_node` | Yes | `PlanOut { tickets }` | `tickets`, `tickets_approved=False` |
| `plan_review_node` | Yes | `PlanReviewOut { approved, comments }` | `tickets_approved`, `ticket_review_comments` |
| `reply_node` | No | — | `final_reply` (ReplyInterface dict) |
| `create_node` | No | — | `final_reply` (FinalReplyInterface dict) |

All LLM nodes use `ChatAnthropic(...).with_structured_output(PydanticModel)` — no JSON parsing needed.

### Accept flow

When `intent_node` classifies the message as `"accept"`:
1. It scans `raw_history` for the most recent message with `content.epic` and `content.tickets`
2. Populates `solution`, `tickets`, and `final_reply` from that history entry
3. Routing sends to `create_node`
4. `create_node` calls `McpClient.call("create_epic", epic_data)` then `McpClient.call("create_ticket", ticket_data)` for each ticket
5. Writes `FinalReplyInterface { epicId, ticketIds }` to `final_reply`

## Event pipeline

```
RabbitMQConsumer (queue: architecture-agent.chat)
  → ChatEventHandler.handle(message)
      → ChatService.handle(event)
          → chat_manager.load_chat(key)      # set agentStatus = isThinking, save to Redis
          → graph.astream(initial_state)
              for each node update:
                → chat_manager.append_thinking_message(node_name)
                → chat_manager.save_chat(key)   # frontend WebSocket sees the update
          → chat_manager.append_reply_message(final_reply)   # set agentStatus = hasReplied
```

## Redis key convention

`chat:{uuid}` — JSON-serialised `ChatInterface`. Written by the NestJS backend, updated in place by the agent during streaming. The backend's WebSocket gateway polls this key at 500 ms.

## Thinking messages (streamed to Redis)

`chat_manager.append_thinking_message()` maps each node name to a display label:

| Node | Label shown in frontend |
|------|------------------------|
| `intent_node` | Analyzing your request... |
| `solution_node` | Designing solution architecture... |
| `solution_review_node` | Reviewing solution... |
| `plan_node` | Creating development tickets... |
| `plan_review_node` | Reviewing tickets... |
| `reply_node` | Preparing response... |
| `create_node` | Creating epic and tickets... |

## MCP tools

`McpClient` (in `app/agent/tools/mcp_client.py`) wraps the FastMCP `Client` to call tools on the MCP server at `{MCP_SERVER_URL}/mcp/`:

```python
await client.call("create_epic", {"epic": epic_dict})
await client.call("create_ticket", {"ticket": ticket_dict})
```

## Environment

```
ANTHROPIC_API_KEY=sk-ant-...
MCP_SERVER_URL=http://localhost:8002
REDIS_URL=redis://localhost:6379
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
CORS_ORIGINS=http://localhost:3000
```

## Dev commands

```bash
pip install .
uvicorn app.main:app --reload --port 8001
```
