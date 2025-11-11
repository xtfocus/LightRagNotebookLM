import os
from typing import Any, Callable, List, Literal

from langchain_core.messages import AIMessage, AnyMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.types import Command
from typing_extensions import Annotated, TypedDict

from .base import BaseAgent, BaseAgentState

try:
    from tavily import TavilyClient
except ImportError:
    TavilyClient = None

import logging

logger = logging.getLogger(__name__)


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


TOOLS: List[Callable] = [get_father, browsing_internet]


async def chat_node(
    state: BaseAgentState, config
) -> Command[Literal["tool_node", "__end__"]]:
    """
    Standard chat node based on the ReAct design pattern. It handles:
    - The model to use
    - The system prompt
    - Getting a response from the model
    - Handling tool calls
    """
    model = ChatOpenAI(model="gpt-4o")
    model_with_tools = model.bind_tools(
        [
            *TOOLS,
        ],
        parallel_tool_calls=False,
    )
    system_message = SystemMessage(
        content=f"You are a helpful assistant. Talk in {state.get('language', 'english')}."
    )
    response = await model_with_tools.ainvoke(
        [
            system_message,
            *state["messages"],
        ],
        config,
    )
    if isinstance(response, AIMessage) and response.tool_calls:
        return Command(goto="tool_node", update={"messages": response})
    return Command(goto="__end__", update={"messages": response})


class ChatAgent(BaseAgent):
    """
    ChatAgent: A concrete agent for chat-based workflows.
    Use .build() to get a fresh, uncompiled workflow.
    """

    name = "chat_agent"
    description = "A minimal chat agent using LangGraph."
    tools = TOOLS

    def build(self) -> StateGraph:
        workflow = StateGraph(self.state_class)
        workflow.add_node("chat_node", chat_node)
        workflow.add_node("tool_node", ToolNode(tools=self.tools))
        workflow.add_edge("tool_node", "chat_node")
        workflow.set_entry_point("chat_node")
        return workflow

    async def run(self, state, config=None) -> Any:
        """
        Run the agent's workflow asynchronously.
        """
        return await self.workflow.ainvoke(state, config or {})


# Example registration (in __init__.py):
# from .chat_agent import ChatAgent
# register_agent(ChatAgent())
