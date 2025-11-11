# FastAPI Agent – Protocol & Agent Integration Guide

## Overview

This backend is built with FastAPI and supports integration with agent protocols such as AGUI. The architecture is modular, allowing you to add new agent-backed endpoints or protocols with minimal duplication and maximum flexibility.

---

## Key Concepts

- **Agent**: A class implementing a chat or workflow logic, registered globally by name.
- **Protocol**: An API contract (e.g., AGUI) for interacting with agents.
- **Adapters/Handlers**: Protocol-specific classes that adapt agent logic to the protocol (e.g., `AGUIStreamingHandler`).

---

## Key Files & Structure

- `app/agents/` – Agent classes and registration logic.
- `app/protocols/` – Protocol adapters/handlers (e.g., AGUI).
- `app/api/routes/` – API endpoints for each protocol.
- `app/main.py` – App startup, agent registration, and protocol endpoint setup.
- `app/core/config.py` – Centralized configuration (API prefix, CORS, DB, etc.).

---

## How to Add a New Agent

### 1. **Create Your Agent**

- Subclass `BaseAgent` in `app/agents/base.py`.
- Implement required properties and methods (`name`, `description`, `state_class`, `tools`, `build()`, `run()`).
- Example (see `chat_agent.py` for a full example):

```python
from .base import BaseAgent

class MyAgent(BaseAgent):
    name = "my_agent"
    description = "A custom agent."
    state_class = MyAgentState
    tools = [my_tool]

    def build(self):
        # Build and return a StateGraph
        ...

    async def run(self, state, config=None):
        # Implement agent logic
        ...
```

### 2. **Register Your Agent**

- In `app/main.py`, register your agent in the `lifespan` function after instantiating and compiling its workflow:

```python
from .agents import register_agent
from .agents.my_agent import MyAgent

my_agent = MyAgent()
my_agent.workflow = my_agent.build().compile(checkpointer=checkpointer)
register_agent(my_agent)
```

---

## How to Add a New Protocol Endpoint

### **A. AGUI Protocol**

1. **Create a Route File** (e.g., `app/api/routes/chat_myagui.py`):

```python
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from ...agents import get_agent
from ...protocols.agui_utils import AGUIStreamingHandler

router = APIRouter(prefix="/chat-myagui", tags=["myagui"])

@router.post("/")
async def agentic_chat_endpoint(input_data: RunAgentInput, request: Request):
    agent = get_agent("my_agent")
    handler = AGUIStreamingHandler(agent=agent, input_data=input_data, request=request)
    return StreamingResponse(handler.stream(), media_type=handler.encoder.get_content_type())
```

2. **Include the Route in `app/api/main.py`:**

```python
from .routes.chat_myagui import router as chat_myagui_router
api_router.include_router(chat_myagui_router)
```

---

## Configuration

- **API Prefix**: Set via `AGENT_API_PREFIX` in your environment or `core/config.py` (default: `/api/v1`).
- **CORS**: Controlled by `BACKEND_CORS_ORIGINS` in your environment or config.
- **Database**: Set `LANGGRAPHDB_URI` or use the default Postgres config in `core/config.py`.

---

## Best Practices

- **Always register agents in `main.py`** after compiling their workflows.
- **Use the agent registry** (`register_agent`, `get_agent`) for all protocol handlers.
- **Keep protocol adapters generic** (see `AGUIStreamingHandler` for a reusable pattern).
- **Document new agents and protocols** in this README and in code comments.
- **Test endpoints** with real requests (e.g., using curl or Postman).

---

## Troubleshooting

- **Agent Not Found**: Ensure your agent is registered with the correct name before protocol endpoints are initialized.
- **Protocol Errors**: Check that your protocol handler matches the expected input/output for the frontend.
- **Database/Checkpointer Issues**: Ensure your Postgres DB is running and accessible.

## ⚠️ Important: Agent Name Consistency

**CRITICAL**: The agent name used in the frontend CopilotRuntime configuration MUST exactly match the agent name registered in the backend.

### ✅ Correct Example:
```python
# Backend (main.py)
register_agent(notebook_agent)  # agent.name = "notebook"
```

```typescript
// Frontend (route.ts)
const runtime = new CopilotRuntime({
  agents: {
    "notebook": notebookChatAgent,  // ✅ Matches backend name
  },
});
```

### ❌ Common Mistake:
```typescript
// Frontend (route.ts) - WRONG!
const runtime = new CopilotRuntime({
  agents: {
    "notebook-chat": notebookChatAgent,  // ❌ Doesn't match backend "notebook"
  },
});
```

### 🔍 Debugging Agent Name Issues:
1. Check backend agent registration in `main.py` - verify the agent name
2. Verify frontend agent name in `CopilotRuntime` configuration
3. Ensure names match exactly (case-sensitive)
4. Check `agentConfig.ts` for consistency across the frontend
5. Restart both backend and frontend services after name changes

---

## Example: Adding a New AGUI Agent and Endpoint

1. **Create your agent** in `app/agents/my_agent.py`.
2. **Register it** in `main.py` after compiling its workflow.
3. **Create a new AGUI route** in `app/api/routes/chat_myagui.py` (see above).
4. **Include the route** in `app/api/main.py`.
5. **Test** the endpoint at `/api/v1/chat-myagui/`.

---

## Contribution Guidelines

- **Add new agents/protocols** following the patterns above.
- **Document your changes** in this README and in code.
- **Test your integration** before submitting PRs.

---

## Support

For questions or issues, contact the project maintainer or open an issue in the repository. 