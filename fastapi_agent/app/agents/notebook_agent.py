import os
from typing import Any, Literal, List, Dict, Optional, Annotated

from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.types import Command

from .base import BaseAgent, BaseAgentState

try:
    from tavily import TavilyClient
except ImportError:
    TavilyClient = None

import json
import requests
from loguru import logger


class NotebookAgentState(BaseAgentState):
    """Notebook agent state that includes selected sources for RAG functionality."""
    selected_sources: List[str]


# Example tool functions (replace with real tools)
async def get_father() -> str:
    """Answer the question: Who created this chatbot?"""
    return "a fullstack data scientist who loves eating fish very much"


def browsing_internet(query: str):
    """
    Search the internet for up-to-date information using Tavily.
    """
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        return "Tavily API key not set. Please set TAVILY_API_KEY environment variable."
    if TavilyClient is None:
        return "TavilyClient is not installed. Please install the 'tavily' package."
    tavily_client = TavilyClient(api_key=api_key)
    try:
        response = tavily_client.search(query)
        logger.info(f"Tavily search response: {response}")
        return response
    except Exception as e:
        logger.error(f"Tavily search failed: {str(e)}")
        return f"Tavily search failed: {str(e)}"


TOOLS = [get_father, browsing_internet]


def _create_embedding(query: str, model: str, api_key: str) -> List[float]:
    """Create an embedding using OpenAI v1 client."""
    try:
        from openai import OpenAI  # type: ignore
        client = OpenAI(api_key=api_key)
        resp = client.embeddings.create(model=model, input=[query])
        return resp.data[0].embedding
    except ImportError as e:
        logger.error(f"[RAG-TOOL] OpenAI client import failed - error: {e}, model: {model}")
        raise RuntimeError("OpenAI client not available. Please install: pip install openai") from e
    except Exception as e:
        logger.error(f"[RAG-TOOL] Embedding creation failed - error: {e}, model: {model}, query_length: {len(query)}")
        raise RuntimeError(f"Failed to create embedding: {e}") from e


def _qdrant_search_with_filter(
    query_embedding: List[float],
    selected_ids: List[str],
    limit: int = 5,
    score_threshold: float = 0.5,
    host: Optional[str] = None,
    collection: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Search Qdrant using REST and filter by selected document/source ids."""
    host = host or os.getenv("QDRANT_HTTP", "http://qdrant:6333")
    collection = collection or os.getenv("QDRANT_COLLECTION", "documents")
    url = f"{host}/collections/{collection}/points/search"

    logger.info(f"[RAG-QDRANT] Starting Qdrant search with filter - host: {host}, collection: {collection}, selected_ids: {len(selected_ids)}, limit: {limit}")
    logger.debug(f"[RAG-QDRANT] URL: {url}, embedding_dim: {len(query_embedding) if query_embedding else 0}")

    # Build OR filter over document_id or source_id matching any selected id
    should_terms = []
    for sid in selected_ids:
        should_terms.append({"key": "document_id", "match": {"value": sid}})
        should_terms.append({"key": "source_id", "match": {"value": sid}})

    q_filter: Dict[str, Any] = {"should": should_terms} if should_terms else {}

    logger.info(f"[RAG-QDRANT] Qdrant filter constructed - should_terms: {len(should_terms)}, has_filter: {bool(should_terms)}")
    logger.debug(f"[RAG-QDRANT] Filter terms: {should_terms}")

    payload = {
        "vector": query_embedding,
        "limit": limit,
        "score_threshold": score_threshold,
        "with_payload": True,
        **({"filter": q_filter} if should_terms else {}),
    }

    logger.info(f"[RAG-QDRANT] Sending request to Qdrant - payload_keys: {list(payload.keys())}")

    try:
        r = requests.post(url, json=payload, timeout=15)
        
        logger.info(f"[RAG-QDRANT] Received response from Qdrant - status: {r.status_code}, size: {len(r.content) if r.content else 0}")
        
        r.raise_for_status()
        results = r.json().get("result", [])
        
        logger.info(f"[RAG-QDRANT] Parsed Qdrant response - result_count: {len(results)}")
        
        out: List[Dict[str, Any]] = []
        for i, res in enumerate(results):
            payload_data = res.get("payload", {})
            out.append({
                "id": res.get("id"),
                "score": res.get("score"),
                "payload": payload_data,
            })
            
            # Log individual result details
            logger.debug(f"[RAG-QDRANT] Result {i+1} - id: {res.get('id')}, score: {res.get('score')}, doc_id: {payload_data.get('document_id')}")
        
        logger.info(f"[RAG-QDRANT] Qdrant search completed successfully - total_results: {len(out)}")
        logger.debug(f"[RAG-QDRANT] Scores: {[res.get('score') for res in out]}")
        
        return out
        
    except Exception as e:
        logger.error(f"[RAG-QDRANT] Qdrant search failed - error: {e}, type: {type(e).__name__}, host: {host}, collection: {collection}")
        raise


@tool
def look_up_sources(query: str, top_k: int = 5, state: Annotated[dict, InjectedState] | None = None) -> str:
    """
    Search for relevant information in the user's selected sources using vector search.
    
    Use this tool when the user asks a question that could be answered from their selected sources.
    Pass the user's question as the 'query' parameter. The tool will automatically search only
    the sources that are currently selected in the notebook.

    Args:
        query: The user's question or search query (required)
        top_k: Number of chunks to return (optional, default: 5)
        state: The current agent state dict containing selected_sources (injected by LangGraph)

    Returns:
        A formatted string with top chunks as context, or an error/explanation.
    """
    # Log tool invocation with detailed state information
    logger.debug(f"[RAG-TOOL] ===== look_up_sources tool invoked =====")
    logger.debug(f"[RAG-TOOL] Query: {query}")
    logger.debug(f"[RAG-TOOL] Top_k: {top_k}")
    if state is None:
        logger.warning("[RAG-TOOL] State was not injected; cannot access selected_sources")
        return "Internal error: state not provided. Please try again."
    logger.debug(f"[RAG-TOOL] State keys: {list(state.keys()) if isinstance(state, dict) else 'Not a dict'}")
    
    # Get selected sources from the state (LangGraph passes state as dict)
    selected_sources = state.get('selected_sources', [])
    
    logger.info(f"[RAG-TOOL] Selected sources - count: {len(selected_sources)}")
    logger.debug(f"[RAG-TOOL] Selected sources detail: {selected_sources}")
    
    if not selected_sources:
        logger.warning(f"[RAG-TOOL] No sources selected - returning early for query: {query}")
        return "No sources selected. Please select at least one source and try again."

    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "text-embedding-3-small")
    if not api_key:
        logger.error(f"[RAG-TOOL] OPENAI_API_KEY not configured for model: {model}")
        return "OPENAI_API_KEY not configured on the agent."

    try:
        logger.info(f"[RAG-TOOL] Creating embedding - model: {model}, query_len: {len(query)}")
        embedding = _create_embedding(query, model, api_key)
        logger.debug(f"[RAG-TOOL] Embedding dimension: {len(embedding) if embedding else 0}")
    except Exception as e:
        logger.error(f"[RAG-TOOL] Embedding creation failed - error: {e}, query: {query}")
        return f"Failed to create embedding for the query. {e}"

    try:
        logger.info(f"[RAG-TOOL] Qdrant search - sources: {len(selected_sources)}, limit: {top_k}")
        results = _qdrant_search_with_filter(
            query_embedding=embedding,
            selected_ids=selected_sources,
            limit=top_k,
            score_threshold=0.2,
        )
        logger.info(f"[RAG-TOOL] Qdrant results: {len(results) if results else 0}")
    except Exception as e:
        logger.error(f"[RAG-TOOL] Qdrant search failed - error: {e}, sources: {selected_sources}")
        return f"Failed to search sources. {e}"

    if not results:
        logger.warning(f"[RAG-TOOL] No results found in Qdrant search - sources: {selected_sources}, query: {query}")
        return "No relevant information found in the selected sources. Try different sources or rephrase your query."

    # Log detailed results
    logger.debug(f"[RAG-TOOL] Results summary: {[{'score': res.get('score'), 'doc_id': res.get('payload', {}).get('document_id')} for res in results]}")

    # Build context string
    lines: List[str] = [f"Top {len(results)} chunks:"]
    for i, res in enumerate(results, 1):
        payload = res.get("payload", {})
        text = payload.get("chunk_text") or payload.get("text") or payload.get("chunk") or ""
        url = payload.get("metadata", {}).get("url") or payload.get("url")
        prefix = (text[:300] + "…") if len(text) > 300 else text
        lines.append(f"{i}. score={res.get('score'):.3f} ref={payload.get('document_id')}")
        if url:
            lines.append(f"   url={url}")
        lines.append(f"   {prefix}")

    final_response = "\n".join(lines)
    
    logger.info(f"[RAG-TOOL] Completed - results: {len(results)}, response_len: {len(final_response)}")
    logger.debug(f"[RAG-TOOL] Top scores: {[res.get('score') for res in results[:3]] if results else []}")

    return final_response



# Register the tool
TOOLS.append(look_up_sources)


async def notebook_chat_node(
    state: dict, config
) -> Command[Literal["tool_node", "__end__"]]:
    """
    Notebook chat node with internet search capabilities.
    Handles:
    - The model to use
    - The system prompt
    - Getting a response from the model
    - Tool calls for internet search when needed
    """
    # Log the state being passed to the chat node
    logger.debug(f"[RAG-CHAT-NODE] Chat node called with state type: {type(state)}")
    logger.debug(f"[RAG-CHAT-NODE] State selected_sources: {state.get('selected_sources', 'NOT_FOUND')}")
    logger.debug(f"[RAG-CHAT-NODE] State messages count: {len(state.get('messages', []))}")
    model = ChatOpenAI(model="gpt-4o")
    model_with_tools = model.bind_tools(
        [
            *TOOLS,
        ],
        parallel_tool_calls=False,
    )
    
    system_content = """You are a helpful AI assistant for a notebook-based LLM interface.

Your role is to:
- Help users understand and work with their uploaded documents and sources
- Provide clear, helpful responses about their content
- Be conversational and engaging
- Ask clarifying questions when needed
- Stay focused on the user's sources and questions
- Proactively decide when to use tools based on the question and available context (do not wait for explicit requests)
- Use source lookup when you need information from their selected sources
- Use internet search when you need current information not available in their sources
- Answer questions about who created this chatbot when asked

You have access to:
1. The user's uploaded sources and documents (via look_up_sources tool)
2. Internet search for current information
3. Information about who created this chatbot

When to use source lookup (decide autonomously):
- When the user asks questions about their uploaded documents or sources
- When you need specific information from their selected sources
- When the user references content from their sources
- ALWAYS use this tool when sources are selected and the question relates to their content
- IMPORTANT: Always pass the user's question as the 'query' parameter to look_up_sources

When to use internet search (decide autonomously):
- When asked about current events or recent information
- When you need to verify facts or get updated information
- When the user's sources don't contain the information they're asking about
- When asked about topics outside their uploaded content

Decision guidance:
- Think about whether the answer likely exists in the user's selected sources. If yes, call look_up_sources first.
- If the answer requires up-to-date or external knowledge, call internet search.
- If neither tool is needed, answer directly.

Keep responses concise but informative. If the user hasn't uploaded any sources yet, you can still help with general questions using internet search."""
    
    system_message = SystemMessage(content=system_content)
    
    response = await model_with_tools.ainvoke(
        [
            system_message,
            *state["messages"],
        ],
        config,
    )
    
    if hasattr(response, 'tool_calls') and response.tool_calls:
        logger.debug(f"[RAG-CHAT-NODE] Tool calls detected: {len(response.tool_calls)}")
        for i, tool_call in enumerate(response.tool_calls):
            # Handle both dict and object tool calls
            if isinstance(tool_call, dict):
                tool_name = tool_call.get('name', 'unknown')
                tool_args = tool_call.get('args', {})
            else:
                tool_name = getattr(tool_call, 'name', 'unknown')
                tool_args = getattr(tool_call, 'args', {})
            logger.debug(f"[RAG-CHAT-NODE] Tool call {i}: {tool_name} with args: {tool_args}")
            logger.debug(f"[RAG-CHAT-NODE] Tool call type: {type(tool_call)}")
            logger.debug(f"[RAG-CHAT-NODE] Tool call full object: {tool_call}")
        logger.debug(f"[RAG-CHAT-NODE] Passing state to tool_node with selected_sources: {state.get('selected_sources', 'NOT_FOUND')}")
        return Command(goto="tool_node", update={"messages": response})
    
    return Command(goto="__end__", update={"messages": response})


# No need for StatefulToolNode - LangGraph's ToolNode automatically passes state to tools


class NotebookAgent(BaseAgent):
    """
    NotebookAgent: A chat agent for notebook conversations with internet search capabilities.
    Use .build() to get a fresh, uncompiled workflow.
    """
    name = "notebook"
    description = "A chat agent for notebook conversations with internet search capabilities."
    state_class = NotebookAgentState
    tools = TOOLS
    
    def build(self) -> StateGraph:
        workflow = StateGraph(self.state_class)
        workflow.add_node("chat_node", notebook_chat_node)
        workflow.add_node("tool_node", ToolNode(tools=self.tools))
        workflow.add_edge("tool_node", "chat_node")
        workflow.set_entry_point("chat_node")
        return workflow
    
    async def run(self, state, config=None) -> Any:
        return await self.workflow.ainvoke(state, config or {})


def notebook_state_builder(input_data) -> NotebookAgentState:
    """Custom state builder that extracts selected sources from CopilotKit shared state."""
    
    # Convert AG-UI messages to agent state messages
    converted_messages = []
    selected_sources = []
    
    # Extract selected sources from system message content
    # CopilotKit embeds the selected sources in the system message content
    for msg in input_data.messages:
        if hasattr(msg, 'role') and msg.role == 'system':
            content = getattr(msg, 'content', '')
            logger.debug(f"[RAG-STATE-BUILDER] System message content length: {len(content)}")
            
            # Look for the selected sources in the system message content
            import re
            # Pattern to match: "List of currently selected source IDs for RAG retrieval: [...]"
            pattern = r'List of currently selected source IDs for RAG retrieval:\s*\[(.*?)\]'
            match = re.search(pattern, content, re.DOTALL)
            
            if match:
                sources_str = match.group(1)
                logger.debug(f"[RAG-STATE-BUILDER] Found sources string: {sources_str}")
                
                # Handle empty array case
                if sources_str.strip() == '':
                    selected_sources = []
                    logger.info("[RAG-STATE-BUILDER] Found empty sources array in system message")
                    break
                
                # Parse the JSON array
                try:
                    import json
                    # Clean up the string and parse as JSON
                    sources_str = sources_str.strip().replace('"', '"').replace('"', '"')
                    selected_sources = json.loads(f'[{sources_str}]')
                    logger.info(f"[RAG-STATE-BUILDER] Successfully extracted selected sources from system message - count: {len(selected_sources)}")
                    logger.debug(f"[RAG-STATE-BUILDER] Selected sources: {selected_sources}")
                    break
                except json.JSONDecodeError as e:
                    logger.error(f"[RAG-STATE-BUILDER] Failed to parse sources JSON: {e}")
                    logger.debug(f"[RAG-STATE-BUILDER] Raw sources string: {sources_str}")
            else:
                logger.debug("[RAG-STATE-BUILDER] No sources pattern found in system message")
    
    if not selected_sources:
        logger.warning("[RAG-STATE-BUILDER] No selected sources found in system message content")
    
    for msg in input_data.messages:
        role = getattr(msg, "role", None)
        content = getattr(msg, "content", "")
        
        if role == "user":
            from langchain_core.messages import HumanMessage
            converted_messages.append(HumanMessage(content=content))
            # Log user message for context
            logger.info(f"[RAG-STATE-BUILDER] Processing user message - length: {len(content)}, has_sources: {len(selected_sources) > 0}")
            logger.debug(f"[RAG-STATE-BUILDER] Selected sources: {selected_sources}")
        elif role == "assistant":
            from langchain_core.messages import AIMessage
            converted_messages.append(AIMessage(content=content))
    
    # Create the state as a dict first (LangGraph expects dict-like state)
    state_dict = {
        "messages": converted_messages,
        "selected_sources": selected_sources,
        "current_tool": None
    }
    
    logger.info(f"[RAG-STATE-BUILDER] State builder completed - sources: {len(selected_sources)}, messages: {len(converted_messages)}")
    logger.debug(f"[RAG-STATE-BUILDER] Final selected sources: {selected_sources}")
    logger.debug(f"[RAG-STATE-BUILDER] Final state type: {type(state_dict)}")
    logger.debug(f"[RAG-STATE-BUILDER] Final state keys: {list(state_dict.keys())}")
    logger.debug(f"[RAG-STATE-BUILDER] Final state selected_sources: {state_dict.get('selected_sources', 'NOT_FOUND')}")
    
    return state_dict 