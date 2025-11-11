## Tool State Injection in NotebookAgent (Brief Guide)

This agent uses LangGraph's InjectedState to pass graph state into tool functions without exposing it to the LLM tool schema.

### What we needed
- Tools must access `selected_sources` chosen in the UI.
- We must NOT ask the LLM to include `selected_sources` in tool args (to avoid hallucination and leakage).
- We must avoid globals and race conditions.

### Solution
We annotate a trailing `state` parameter with `InjectedState` and decorate the function with `@tool`:

```python
from typing import Annotated
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

@tool
def look_up_sources(
    query: str,
    top_k: int = 5,
    state: Annotated[dict, InjectedState] | None = None,
) -> str:
    if state is None:
        return "Internal error: state not provided. Please try again."
    selected_sources = state.get("selected_sources", [])
    # ... use selected_sources in vector search ...
```

Key points:
- `@tool` generates the LLM-visible schema from positional args (`query`, optional `top_k`).
- `state: Annotated[dict, InjectedState]` is hidden from the schema and is injected by ToolNode at runtime.
- The LLM now reliably sends `{ query: "..." }`, while the backend injects `state` (with `selected_sources`).

### Why this is safe and correct
- No globals, no cross-request contamination, no race conditions.
- The LLM cannot fabricate or tamper with `selected_sources`.
- Works with standard `ToolNode`; no custom wrapper required.

### Where it is used
- File: `fastapi_agent/app/agents/notebook_agent.py`
- Function: `look_up_sources`
- State provider: `notebook_state_builder` builds a dict with `messages` and `selected_sources` and feeds the graph.

### Troubleshooting
- If logs show "state not provided", ensure your LangGraph version supports `InjectedState` and that the tool is decorated with `@tool`.
- Verify the tool is bound via `model.bind_tools([look_up_sources, ...])` and executed through `ToolNode`.

