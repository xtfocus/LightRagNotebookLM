from abc import ABC, abstractmethod
from typing import Any, Callable, List, Type

from langchain_core.messages import AnyMessage
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, TypedDict


class BaseAgentState(TypedDict):
    current_tool: str | None
    messages: Annotated[list[AnyMessage], add_messages]


class BaseAgent(ABC):
    """
    Abstract base class for all LangGraph-based agents.
    Subclasses should define name, description, state_class, tools, and workflow logic.
    Use .build() to get a fresh, uncompiled workflow, and .compile(checkpointer=...) to make it persistent.
    """

    name: str
    description: str
    state_class = BaseAgentState
    tools: List[Callable]

    def __init__(self):
        self.workflow = self.build()

    @abstractmethod
    def build(self) -> StateGraph:
        """
        Build and return the LangGraph StateGraph for this agent.
        Should define nodes, edges, and entry point.
        Returns a fresh, uncompiled workflow.
        """
        pass

    @abstractmethod
    async def run(self, *args, **kwargs) -> Any:
        """
        Run the agent's main logic. Signature can be adapted for protocol adapters.
        """
        pass


# Example usage:
#
# class MyAgent(BaseAgent):
#     name = "my_agent"
#     description = "An example agent."
#     state_class = MyAgentState
#     tools = [my_tool]
#
#     def build(self) -> StateGraph:
#         workflow = StateGraph(self.state_class)
#         # Add nodes, edges, entry point...
#         return workflow
#
#     async def run(self, state, config):
#         # Implement agent logic
#         pass
