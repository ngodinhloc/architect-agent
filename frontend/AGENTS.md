# Frontend — Agent Instructions

Next.js 16 / React 19 / Tailwind CSS 4 app. Proxies all `/api/*` requests to the backend (port 8000). Opens a WebSocket to receive live agent progress updates.

## Stack

- **Next.js 16** with App Router (`src/app/`)
- **React 19** — `"use client"` only where interactivity is required
- **Tailwind CSS 4** — utility-first, no component library
- **TypeScript 5** — strict mode

## File structure

```
src/
  app/
    layout.tsx                Root layout — Sidebar + main content area
    page.tsx                  Home page — renders <ArchitectChat> in a Suspense boundary
    globals.css               Tailwind imports + CSS variables
  components/
    ArchitectChat.tsx          Main chat component — manages WebSocket, state, multi-turn flow
    PlanCard.tsx               Renders ReplyInterface (solution architecture + ticket list)
    FinalReplyCard.tsx         Renders FinalReplyInterface (epicId + ticketIds)
    SearchBar.tsx              Controlled input + submit button
    LoadingSkeleton.tsx        Animated placeholder while agent is working
    Sidebar.tsx                Collapsible conversation history sidebar
  lib/
    api.ts                    Fetch helpers — newChat, continueChat, getChat, stopChat, getHistory
  types/
    chat.ts                   All TypeScript interfaces mirroring the backend contracts
```

## Key component: `ArchitectChat`

`ArchitectChat` is the only stateful component. It:

1. Calls `newChat(message)` → receives `{ id }`
2. Opens WebSocket to `ws://localhost:8000/ws` and sends `{ event: "subscribe", data: id }`
3. Receives `chat-update` events; extracts `MessageInterface[]` from `chat.messages`
4. Shows thinking-log entries (all `isThinking` messages) and a loading skeleton while `agentStatus !== "hasReplied"`
5. On `agentStatus === "hasReplied"`: extracts the final message's `content` and renders either `<PlanCard>` (ReplyInterface) or `<FinalReplyCard>` (FinalReplyInterface)
6. For follow-up turns, calls `continueChat(id, message)` — completed turns are stored in `completedTurns` state

### Accept flow

`PlanCard` renders a "Looks good" button (only when `showActions=true`). Clicking it calls `handleAccept()` which calls `handleContinue("Looks good, please create the epic and tickets.")`. The AI agent's `intent_node` classifies this as `"accept"` and routes to `create_node`.

### Differentiate ReplyInterface vs FinalReplyInterface

```typescript
function isReplyInterface(c: unknown): c is ReplyInterface {
  return typeof c === "object" && c !== null && "epic" in c && "tickets" in c;
}

function isFinalReplyInterface(c: unknown): c is FinalReplyInterface {
  return typeof c === "object" && c !== null && "epicId" in c && "ticketIds" in c;
}
```

## Types (`types/chat.ts`)

Keep in sync with the backend's `src/chat/contracts/chat.interface.ts`. The field name is `content` (not `text` as in tourguide-agent).

```typescript
interface MessageInterface {
  actor:       "User" | "Agent"
  timestamp:   string
  content:     string | ReplyInterface | FinalReplyInterface
  agentStatus: "isThinking" | "hasReplied" | null
}

interface ChatInterface {
  id:          string
  title:       string | null
  messages:    MessageInterface[]     // note: "messages", not "content"
  status:      "isActive" | "isStopped"
  agentStatus: "isThinking" | "hasReplied"
}
```

## API proxy

`next.config.ts` rewrites `/api/*` → `{API_TARGET}/api/*`. Never call the backend URL directly from components — always use relative `/api/` paths via `lib/api.ts`.

## WebSocket URL

Built by `buildWsUrl()`:
- Uses `NEXT_PUBLIC_WS_URL` env var if set (Docker: `ws://localhost:8000`)
- Falls back to `ws://{window.location.hostname}:8000/ws`

## Patterns

- Data fetching: `lib/api.ts` helpers in Client Components
- WebSocket: single `wsRef` ref; always disconnect before re-subscribing
- Idle timeout: 30 s after `hasReplied` — calls `stopChat` to persist to PostgreSQL
- Multi-turn history: completed turns stored in `completedTurns` state; offset tracked in `agentMessageOffsetRef`
- Scroll: `conversationEndRef.current?.scrollIntoView({ behavior: "smooth" })` after each update

## Environment

```
NODE_ENV=development
API_TARGET=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

## Dev commands

```bash
npm install
npm run dev     # http://localhost:3000
npm run build
npm run lint
```
