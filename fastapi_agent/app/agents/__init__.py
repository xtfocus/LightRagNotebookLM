from typing import Dict, List
from .base import BaseAgent

# Global agent registry (name -> agent instance)
_agent_registry: Dict[str, BaseAgent] = {}

def register_agent(agent: BaseAgent) -> None:
    """
    Register an agent instance in the global registry.
    """
    _agent_registry[agent.name] = agent

def get_agent(name: str) -> BaseAgent:
    """
    Retrieve an agent by name. Raises KeyError if not found.
    """
    return _agent_registry[name]

def list_agents() -> List[str]:
    """
    List all registered agent names.
    """
    return list(_agent_registry.keys())

# Example usage (register agents explicitly in app startup):
# from .chat_agent import ChatAgent
# register_agent(ChatAgent())
