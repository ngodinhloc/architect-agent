# Backend — Agent Instructions

NestJS 11 API that manages chat conversations. It owns state (PostgreSQL + Redis), exposes a WebSocket gateway that polls Redis for agent progress, and publishes events to RabbitMQ for the AI agent to consume.

## Stack

- **NestJS 11** — modules, controllers, services, gateway
- **TypeORM 0.3** — PostgreSQL, `synchronize: true` in dev (no migration files)
- **ioredis 5** — Redis client via global `RedisService`
- **amqplib** — RabbitMQ publisher via `RabbitMQService`
- **@nestjs/platform-ws** — native WebSocket adapter
- **class-validator / class-transformer** — DTO validation via global `ValidationPipe`

## Module structure

```
src/
  main.ts                               NestJS bootstrap, CORS, WsAdapter, ValidationPipe
  app.module.ts                         Root module
  chat/
    chat.module.ts
    contracts/
      chat.interface.ts                 All domain types: MessageInterface, ChatInterface,
                                        ReplyInterface, FinalReplyInterface, SolutionInterface, etc.
    controllers/
      chat.controller.ts                REST endpoints under /api/chat
    services/
      chat.service.ts                   Core business logic — PostgreSQL + Redis reads/writes
      agent.service.ts                  Publishes ChatEvent to RabbitMQ (fire-and-forget)
    dto/
      new-chat.dto.ts                   { message: string }
      continue-chat.dto.ts              { message: string }
    gateways/
      chat.gateway.ts                   WebSocket gateway at /ws — polls Redis at 500 ms
  database/
    database.module.ts                  TypeORM root config (async, url from DATABASE_URL)
    entities/
      conversation.entity.ts            uuid, title, messages (jsonb), createdAt, updatedAt
  redis/
    redis.module.ts                     @Global() module
    services/
      redis.service.ts                  getJson<T> / setJson / del
  rabbitmq/
    rabbitmq.module.ts                  @Global() module
    contracts/
      chat-event.interface.ts           ChatEvent { conversationId, message, history }
    services/
      rabbitmq.service.ts               Connects on init, asserts queue, publish()
  health/
    health.module.ts
    controllers/
      health.controller.ts              GET /api/health → { status: 'ok' }
  common/
    middleware/
      logging.middleware.ts             HTTP request/response logger
```

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/chat/new` | Create conversation in PostgreSQL + Redis; publish `ChatEvent`; return `{ id }` |
| `POST` | `/api/chat/:id/cont` | Append user message to Redis; publish `ChatEvent`; return `{ accepted: true }` |
| `POST` | `/api/chat/:id/stop` | Persist `messages` to PostgreSQL; delete Redis key; return `{ stopped: true }` |
| `GET` | `/api/chat/history` | All conversations (id, title, createdAt) from PostgreSQL |
| `GET` | `/api/chat/:id` | Live `ChatInterface` from Redis, or persisted from PostgreSQL |
| `WS` | `/ws` | Subscribe to a chat id; polls Redis at 500 ms; sends `chat-update` events |
| `GET` | `/api/health` | `{ status: 'ok' }` |

## WebSocket protocol

The client connects to `ws://localhost:8000/ws` and sends:

```json
{ "event": "subscribe", "data": "<chatId>" }
```

The gateway polls `chat:{chatId}` in Redis every 500 ms. Each poll pushes:

```json
{ "event": "chat-update", "data": <ChatInterface> }
```

Polling stops when `agentStatus === "hasReplied"` or after 180 polls (90 s timeout).

## Redis key convention

`chat:{uuid}` — JSON-serialised `ChatInterface`. Written on `newChat`, updated by the AI agent during streaming, deleted on `stopChat`.

## RabbitMQ queue

Queue name: `architecture-agent.chat` (durable). Published by `RabbitMQService.publish()` with `persistent: true`. The AI agent subscribes with `prefetch_count=1`.

## ChatInterface shape (canonical — `contracts/chat.interface.ts`)

```typescript
enum ChatStatus  { isActive, isStopped }
enum AgentStatus { isThinking, hasReplied }
enum ChatActor   { user = 'User', agent = 'Agent' }

interface MessageInterface {
  actor:       ChatActor
  timestamp:   Date
  content:     string | ReplyInterface | FinalReplyInterface
  agentStatus: AgentStatus | null
}

interface ChatInterface {
  id:          string
  title:       string | null
  messages:    MessageInterface[]
  status:      ChatStatus
  agentStatus: AgentStatus
}
```

The `messages` column in PostgreSQL stores `MessageInterface[]` as `jsonb`. Tool-call progress messages (`isThinking`) and the final reply (`hasReplied`) live in the same array.

## Environment

```
PORT=8000
DATABASE_URL=postgresql://architect:architect@localhost:5432/architect
REDIS_URL=redis://localhost:6379
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
CORS_ORIGINS=http://localhost:3000
```

## Dev commands

```bash
npm install
npm run start:dev   # http://localhost:8000 with watch mode
npm run build
npm run lint
```
