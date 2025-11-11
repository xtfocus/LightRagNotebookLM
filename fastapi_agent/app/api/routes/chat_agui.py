from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from ag_ui.core import RunAgentInput
from ...agents import get_agent
from ...protocols.agui_utils import AGUIStreamingHandler

router = APIRouter(prefix="/chat-agui", tags=["agui"])

@router.post("/")
async def agentic_chat_endpoint(input_data: RunAgentInput, request: Request):
    """
    AG-UI protocol endpoint using the ChatAgent and AGUIStreamingHandler.
    Converts AG-UI input to agent state, runs the agent, and streams AG-UI events.
    The event structure and streaming logic match the original implementation.
    """
    agent = get_agent("agui")
    handler = AGUIStreamingHandler(
        agent=agent,
        input_data=input_data,
        request=request,
    )
    return StreamingResponse(handler.stream(), media_type=handler.encoder.get_content_type())
