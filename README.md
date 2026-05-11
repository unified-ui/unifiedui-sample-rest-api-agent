# unified-ui Sample REST API Agent

A sample FastAPI service demonstrating how to build a REST API agent for the [unified-ui](https://github.com/unified-ui) platform using the [`unifiedui-sdk`](https://github.com/unified-ui/unifiedui-sdk).

This service serves as a **reference implementation** showing how to integrate custom LangChain/LangGraph agents with unified-ui via the REST API agent type.

## Features

- **LangChain Agent** — ReACT agent with sample tools, streamed via unified-ui SSE protocol
- **LangGraph Agent** — LangGraph-based agent with sample tools
- **Echo Agent** — Simple echo agent (no LLM needed, useful for testing)
- **Foundry Proxy Agent** — Proxies requests to Microsoft Foundry, streaming responses as unified-ui SSE events
- **5 Auth Modes** — Anonymous, Basic Auth, API Key, Entra ID User Token, Entra ID App Registration
- **In-Memory Sessions** — Conversation management with dict-based session store
- **SSE Streaming** — All 22 unified-ui event types via `unifiedui-sdk`

## Quick Start

```bash
# Install dependencies
uv sync

# Copy env and configure
cp .env.example .env
# Edit .env — set your Azure OpenAI endpoint and key

# Run
uv run uvicorn app.main:app --reload --port 8087
```

Open [http://localhost:8087/docs](http://localhost:8087/docs) for the Swagger UI.

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI resource endpoint | — |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key | — |
| `AZURE_OPENAI_DEPLOYMENT` | Model deployment name | `gpt-4.1` |
| `AZURE_OPENAI_API_VERSION` | API version | `2024-05-01-preview` |
| `API_KEY` | API key for API Key auth mode | `default-api-key` |
| `BASIC_AUTH_USERNAME` | Username for Basic Auth | `admin` |
| `BASIC_AUTH_PASSWORD` | Password for Basic Auth | `password` |
| `FOUNDRY_PROJECT_ENDPOINT` | Microsoft Foundry project endpoint | — |
| `FOUNDRY_PROJECT_API_KEY` | Foundry API key (for api-key proxy mode) | — |
| `FOUNDRY_AGENT` | Foundry agent name | — |
| `FOUNDRY_API_VERSION` | Foundry API version | `2025-11-15-preview` |

## Endpoints

### Health

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Service health check |

### Conversations (create session)

| Endpoint | Auth |
|----------|------|
| `POST /api/v1/anonymous/conversations` | None |
| `POST /api/v1/basic-auth/conversations` | Basic Auth |
| `POST /api/v1/api-key/conversations` | Bearer `<api-key>` |
| `POST /api/v1/entra-id/conversations` | Bearer `<token>` |

**Request:** `CreateConversationRequest` — `{"config": {}}`
**Response:** `CreateConversationResponse` — `{"conversation_id": "uuid"}`

### Agent Invoke (SSE stream)

| Endpoint | Auth | Agent |
|----------|------|-------|
| `POST /api/v1/anonymous/agent/langchain/invoke` | None | LangChain |
| `POST /api/v1/anonymous/agent/langgraph/invoke` | None | LangGraph |
| `POST /api/v1/anonymous/agent/echo/invoke` | None | Echo |
| `POST /api/v1/basic-auth/agent/langchain/invoke` | Basic Auth | LangChain |
| `POST /api/v1/basic-auth/agent/langgraph/invoke` | Basic Auth | LangGraph |
| `POST /api/v1/api-key/agent/langchain/invoke` | Bearer | LangChain |
| `POST /api/v1/api-key/agent/langgraph/invoke` | Bearer | LangGraph |
| `POST /api/v1/api-key/agent/echo/invoke` | Bearer | Echo |
| `POST /api/v1/entra-id/agent/langchain/invoke` | Bearer | LangChain |
| `POST /api/v1/entra-id/agent/langgraph/invoke` | Bearer | LangGraph |
| `POST /api/v1/api-key/agent/foundry-proxy/invoke` | API Key | Foundry Proxy |
| `POST /api/v1/entra-id/agent/foundry-proxy/invoke` | Bearer | Foundry Proxy |

**Request:** `RestApiAgentInvokeRequest`

```json
{
  "conversation_id": "uuid-from-create-conversation",
  "unified_ui_conversation_id": "unified-ui-internal-id",
  "message_history": [
    {"role": "user", "content": "What is the weather in Berlin?"}
  ],
  "config": {}
}
```

**Response:** SSE stream (`text/event-stream`) with unified-ui event types:

```
event: STREAM_START
data: {"type":"STREAM_START","content":"","config":{}}

event: TOOL_CALL_START
data: {"type":"TOOL_CALL_START","content":"","config":{"tool_call_id":"...","tool_name":"get_weather","tool_arguments":{"city":"Berlin"}}}

event: TOOL_CALL_END
data: {"type":"TOOL_CALL_END","content":"","config":{"tool_call_id":"...","tool_name":"get_weather","tool_status":"success","tool_result":"Berlin: 18°C, Partly Cloudy"}}

event: TEXT_STREAM
data: {"type":"TEXT_STREAM","content":"The weather in ","config":{}}

event: TEXT_STREAM
data: {"type":"TEXT_STREAM","content":"Berlin is 18°C.","config":{}}

event: STREAM_END
data: {"type":"STREAM_END","content":"","config":{}}
```

## Project Structure

```
app/
├── main.py                    # FastAPI app factory
├── config.py                  # Settings (pydantic-settings, .env)
├── agents/
│   ├── langchain_agent.py     # LangchainStreamAdapter setup (Azure OpenAI)
│   ├── langgraph_agent.py     # LanggraphStreamAdapter setup (Azure OpenAI)
│   ├── echo_agent.py          # Simple echo agent (no LLM)
│   └── foundry_proxy_agent.py # Foundry proxy (streams Foundry SSE → unified-ui SSE)
├── api/v1/
│   ├── health.py              # Health endpoint
│   ├── conversations.py       # Conversation creation endpoints
│   └── agent.py               # Agent invoke endpoints (SSE streaming)
├── middleware/
│   └── auth.py                # Auth dependencies (anonymous, basic, API key, Entra ID)
├── session/
│   └── store.py               # In-memory session store
└── tools/
    └── sample_tools.py        # Sample tools: get_weather, calculate, get_current_time
```

## How to Build Your Own

1. **Install the SDK**: `uv add unifiedui-sdk`
2. **Create your tools** using `@langchain_core.tools.tool`
3. **Build your agent** — use `create_react_agent()` or your own LangGraph builder
4. **Wrap it with an adapter** — pass your agent to `LangchainStreamAdapter(agent=...)` or `LanggraphStreamAdapter(graph=...)`
4. **Expose endpoints** — a POST invoke endpoint returning `EventSourceResponse` with SSE events
5. **Optionally add conversations** — a POST endpoint returning `CreateConversationResponse`
6. **Configure in unified-ui** — add a Chat Agent with type "REST API", set your invoke URL and auth type

See the [SDK Integrations documentation](https://github.com/unified-ui/unifiedui-sdk#integrations--build-rest-api-agents-for-unified-ui) for full details.

## License

MIT
