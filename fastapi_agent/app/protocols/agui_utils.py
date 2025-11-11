"""
AGUIStreamingHandler for AG-UI protocol streaming in FastAPI.
Handles incremental and snapshot state updates, tool call progress logging, and event encoding.
"""

import uuid
from typing import (Any, AsyncGenerator, Awaitable, Callable, Dict, List,
                    Optional, Union)

from ag_ui.core import (EventType, RunAgentInput, RunErrorEvent,
                        RunFinishedEvent, RunStartedEvent,
                        TextMessageContentEvent, TextMessageEndEvent,
                        TextMessageStartEvent)
from ag_ui.encoder import EventEncoder
from langchain_core.messages import AIMessage, HumanMessage
from loguru import logger

from app.agents.base import BaseAgent

from .events import StateDeltaEvent, StateSnapshotEvent


class AGUIStreamingHandler:
    """
    Generic AG-UI event streaming handler for any agent.
    Handles:
      - State snapshot and delta event construction
      - Tool call progress logging
      - Streaming of encoded events for FastAPI
    """

    def __init__(
        self,
        agent: BaseAgent,
        input_data: RunAgentInput,
        request: Any,
        tool_node_names: Union[str, List[str]] = "tool_node",
        state_builder: Optional[Callable[[RunAgentInput], Any]] = None,
        message_chunk_extractors: Optional[Dict[str, Callable[[Any], Any]]] = None,
        on_tool_call: Optional[Callable[[Any, Dict[str, Any]], Any]] = None,
        on_llm_output: Optional[Callable[[Any, List[bool]], List[bytes]]] = None,
        build_snapshot: Optional[Callable[[RunAgentInput], StateSnapshotEvent]] = None,
        build_delta: Optional[Callable[[str], StateDeltaEvent]] = None,
        on_error: Optional[Callable[[Exception], bytes]] = None,
    ) -> None:
        """
        Initialize the AGUIStreamingHandler.
        See class docstring for parameter details.
        """
        self.agent = agent
        self.input_data = input_data
        self.request = request
        self.tool_node_names = (
            [tool_node_names] if isinstance(tool_node_names, str) else tool_node_names
        )
        self.state_builder = state_builder or self.default_state_builder
        self.message_chunk_extractors = message_chunk_extractors or {
            "content": lambda chunk: getattr(chunk, "content", None),
            "name": lambda chunk: getattr(chunk, "name", None),
        }
        self.on_tool_call = on_tool_call or self.default_tool_call
        self.on_llm_output = on_llm_output or self.default_llm_output
        self.build_snapshot = build_snapshot or self.default_snapshot
        self.build_delta = build_delta or self.default_delta
        self.on_error = on_error or self.default_error
        self.encoder = EventEncoder(accept=request.headers.get("accept"))
        self.assistant_message_id = str(uuid.uuid4())
        self.progress_logs: List[Dict[str, Any]] = []

    # --- Progress Log Helpers ---
    def progress_log_message(self, tool_name: str) -> str:
        """Return the standard progress log message for a tool call."""
        return f"Executing tool: {tool_name}"

    def should_add_progress_log(self, tool_name: str) -> bool:
        """Return True if a progress log for this tool should be added (not already present)."""
        msg = self.progress_log_message(tool_name)
        return not self.progress_logs or self.progress_logs[-1]["message"] != msg

    @staticmethod
    def extract_tool_name(tool_call: dict) -> Optional[str]:
        """Extract the tool name from a tool_call dict (OpenAI or generic format)."""
        if "function" in tool_call and tool_call["function"]:
            return tool_call["function"].get("name")
        return tool_call.get("name")

    def emit_progress_log_events(self, tool_name: str, log_prefix: str = "") -> Any:
        """Emit delta and snapshot events for a tool progress log."""
        self.add_progress_log(tool_name)
        delta_event = self.encoder.encode(self.build_delta(tool_name))
        snapshot_event = self.encoder.encode(self.build_snapshot(self.input_data))
        logger.debug(f"{log_prefix}Yielding ToolCallEvent: {delta_event}")
        logger.debug(
            f"{log_prefix}Yielding StateSnapshotEvent (with updated logs): {snapshot_event}"
        )
        yield delta_event
        yield snapshot_event

    def add_progress_log(self, tool_name: str) -> None:
        """Append a new progress log entry for a tool call."""
        self.progress_logs.append(
            {"message": self.progress_log_message(tool_name), "done": False}
        )

    def mark_last_log_done(self) -> None:
        """Mark the last progress log entry as done."""
        if self.progress_logs:
            self.progress_logs[-1]["done"] = True

    # --- Event Builders ---
    def agui_messages_to_agentstate(self, messages: List[Any]) -> List[Any]:
        """
        Convert AG-UI protocol messages to agent state messages.
        Args:
            messages: List of AG-UI message objects.
        Returns:
            List of HumanMessage or AIMessage objects for the agent state.
        """
        converted = []
        for msg in messages:
            role = getattr(msg, "role", None)
            content = getattr(msg, "content", "")
            if role == "user":
                converted.append(HumanMessage(content=content))
            elif role == "assistant":
                converted.append(AIMessage(content=content))
        return converted

    def default_state_builder(self, input_data: RunAgentInput) -> Any:
        """
        Default function to build the agent state from AG-UI input.
        Args:
            input_data: AG-UI RunAgentInput.
        Returns:
            An instance of the agent's state_class.
        """
        return self.agent.state_class(
            messages=self.agui_messages_to_agentstate(input_data.messages)
        )

    def default_snapshot(self, input_data: RunAgentInput) -> StateSnapshotEvent:
        """
        Build the default state snapshot event for AG-UI.
        Args:
            input_data: AG-UI RunAgentInput.
        Returns:
            StateSnapshotEvent instance.
        """
        return StateSnapshotEvent(
            type=EventType.STATE_SNAPSHOT,
            message_id=self.assistant_message_id,
            snapshot={
                "status": {"phase": "initialized", "error": None},
                "processing": {
                    "progress": 0,
                    "completed": False,
                    "inProgress": False,
                },
                "ui": {"showProgress": True, "activeTab": "chat"},
                "logs": self.progress_logs,
            },
        )

    def default_delta(self, tool_name: str) -> StateDeltaEvent:
        """
        Build the default state delta event for a tool call.
        Args:
            tool_name: Name of the tool being called.
        Returns:
            StateDeltaEvent instance.
        """
        return StateDeltaEvent(
            message_id=self.assistant_message_id,
            delta=[
                {
                    "op": "replace",
                    "path": "/status/phase",
                    "value": f"calling {tool_name}",
                }
            ],
        )

    def default_tool_call(
        self, message_chunk: Any, metadata: Dict[str, Any]
    ) -> List[bytes]:
        """
        Default handler for tool call events.
        Appends a new log entry and returns both a delta and a snapshot event.
        Args:
            message_chunk: The message chunk from the agent workflow.
            metadata: Metadata dict from the workflow.
        Returns:
            List of encoded events (delta and snapshot), or empty if already logged.
        """
        tool_name = self.message_chunk_extractors["name"](message_chunk) or "tool"
        if self.should_add_progress_log(tool_name):
            return list(self.emit_progress_log_events(tool_name))
        return []

    def default_llm_output(
        self, message_chunk: Any, started: List[bool]
    ) -> List[bytes]:
        """
        Default handler for LLM output events.
        Args:
            message_chunk: The message chunk from the agent workflow.
            started: List with a single boolean indicating if streaming has started.
        Returns:
            List of encoded AG-UI events (TextMessageStartEvent, TextMessageContentEvent).
        """
        events: List[bytes] = []
        content = self.message_chunk_extractors["content"](message_chunk)
        if content:
            if not started[0]:
                started[0] = True
                events.append(
                    self.encoder.encode(
                        TextMessageStartEvent(
                            type=EventType.TEXT_MESSAGE_START,
                            message_id=self.assistant_message_id,
                            role="assistant",
                        )
                    )
                )
            events.append(
                self.encoder.encode(
                    TextMessageContentEvent(
                        type=EventType.TEXT_MESSAGE_CONTENT,
                        message_id=self.assistant_message_id,
                        delta=content,
                    )
                )
            )
        return events

    def default_error(self, error: Exception) -> bytes:
        """
        Default handler for errors during streaming.
        Args:
            error: The exception raised.
        Returns:
            Encoded RunErrorEvent.
        """
        return self.encoder.encode(
            RunErrorEvent(
                type=EventType.RUN_ERROR, message="Got an error: " + str(error)
            )
        )

    # --- Streaming Loop ---
    async def stream(self) -> AsyncGenerator[bytes, None]:
        """
        Main streaming generator for AG-UI events.
        Yields encoded AG-UI events as bytes for FastAPI StreamingResponse.
        """
        try:
            async for event in self._emit_run_started():
                yield event
            async for event in self._emit_initial_snapshot():
                yield event

            config = {"configurable": {"thread_id": self.input_data.thread_id}}
            started = [False]
            initial_state = self.state_builder(self.input_data)

            async for message_chunk, metadata in self.agent.workflow.astream(
                initial_state, config, stream_mode="messages"
            ):
                logger.debug(f"MESSAGE_CHUNK: {message_chunk}\n METADATA: {metadata}")
                async for event in self._route_message_chunk(
                    message_chunk, metadata, started
                ):
                    yield event

            if started[0]:
                async for event in self._emit_end_event():
                    yield event
            async for event in self._emit_finish_event():
                yield event
        except Exception as error:
            async for event in self._emit_error_event(error):
                yield event
            raise

    async def _emit_run_started(self) -> AsyncGenerator[bytes, None]:
        """Emit the RunStartedEvent."""
        event = self.encoder.encode(
            RunStartedEvent(
                type=EventType.RUN_STARTED,
                thread_id=self.input_data.thread_id,
                run_id=self.input_data.run_id,
            )
        )
        logger.debug(f"Yielding RunStartedEvent: {event}")
        yield event

    async def _emit_initial_snapshot(self) -> AsyncGenerator[bytes, None]:
        """Emit the initial StateSnapshotEvent."""
        snapshot_event = self.encoder.encode(self.build_snapshot(self.input_data))
        logger.debug(f"Yielding StateSnapshotEvent: {snapshot_event}")
        yield snapshot_event

    async def _emit_end_event(self) -> AsyncGenerator[bytes, None]:
        """Emit the TextMessageEndEvent."""
        end_event = self.encoder.encode(
            TextMessageEndEvent(
                type=EventType.TEXT_MESSAGE_END,
                message_id=self.assistant_message_id,
            )
        )
        logger.debug(f"Yielding TextMessageEndEvent: {end_event}")
        yield end_event

    async def _emit_finish_event(self) -> AsyncGenerator[bytes, None]:
        """Emit the RunFinishedEvent."""
        finish_event = self.encoder.encode(
            RunFinishedEvent(
                type=EventType.RUN_FINISHED,
                thread_id=self.input_data.thread_id,
                run_id=self.input_data.run_id,
            )
        )
        logger.debug(f"Yielding RunFinishedEvent: {finish_event}")
        yield finish_event

    async def _emit_error_event(self, error: Exception) -> AsyncGenerator[bytes, None]:
        """Emit the RunErrorEvent for an exception."""
        error_event = self.on_error(error)
        logger.error(f"Yielding ErrorEvent: {error_event}")
        yield error_event

    async def _route_message_chunk(
        self, message_chunk: Any, metadata: Dict[str, Any], started: List[bool]
    ) -> AsyncGenerator[bytes, None]:
        """
        Route a message chunk to the appropriate handler (tool node or LLM output).
        """
        node = metadata.get("langgraph_node")
        if node in self.tool_node_names:
            async for event in self._handle_tool_node(message_chunk, metadata):
                yield event
        else:
            async for event in self._handle_llm_output(message_chunk, started):
                yield event

    async def _handle_tool_node(
        self, message_chunk: Any, metadata: Dict[str, Any]
    ) -> AsyncGenerator[bytes, None]:
        """
        Handle tool node events: yield tool call events, mark log done, yield done snapshot.
        """
        tool_events = self.on_tool_call(message_chunk, metadata)
        if isinstance(tool_events, list):
            for tool_event in tool_events:
                logger.debug(
                    f"Yielding ToolCallEvent or StateSnapshotEvent: {tool_event}"
                )
                yield tool_event
        else:
            logger.debug(f"Yielding ToolCallEvent: {tool_events}")
            yield tool_events
        self.mark_last_log_done()
        done_snapshot_event = self.encoder.encode(self.build_snapshot(self.input_data))
        logger.debug(
            f"Yielding StateSnapshotEvent (log marked done): {done_snapshot_event}"
        )
        yield done_snapshot_event

    async def _handle_llm_output(
        self, message_chunk: Any, started: List[bool]
    ) -> AsyncGenerator[bytes, None]:
        """
        Handle LLM output events: yield all LLM output events.
        Also, if a tool call is detected in the message chunk, emit a progress log event immediately.
        """
        additional_kwargs = getattr(message_chunk, "additional_kwargs", {})
        tool_calls = additional_kwargs.get("tool_calls", [])
        for tool_call in tool_calls:
            tool_name = self.extract_tool_name(tool_call)
            if tool_name and self.should_add_progress_log(tool_name):
                async for event in self._emit_progress_log_events_async(
                    tool_name, log_prefix="[EARLY TOOL CALL] "
                ):
                    yield event
        for event in self.on_llm_output(message_chunk, started):
            logger.debug(f"Yielding LLMOutputEvent: {event}")
            yield event

    async def _emit_progress_log_events_async(
        self, tool_name: str, log_prefix: str = ""
    ) -> AsyncGenerator[bytes, None]:
        """
        Async generator version of emit_progress_log_events for use in async contexts.
        """
        for event in self.emit_progress_log_events(tool_name, log_prefix=log_prefix):
            yield event
