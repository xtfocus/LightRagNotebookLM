from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from ag_ui.core import RunAgentInput
from ...agents import get_agent
from ...agents.notebook_agent import notebook_state_builder
from ...protocols.agui_utils import AGUIStreamingHandler

router = APIRouter(prefix="/notebook-chat", tags=["notebook-chat"])

@router.post("/")
async def notebook_chat_endpoint(input_data: RunAgentInput, request: Request):
    """
    AG-UI protocol endpoint for notebook chat using the NotebookAgent.
    Provides conversation with internet search capabilities for notebook interactions.
    """
    agent = get_agent("notebook")
    handler = AGUIStreamingHandler(
        agent=agent,
        input_data=input_data,
        request=request,
        state_builder=notebook_state_builder,
    )
    return StreamingResponse(handler.stream(), media_type=handler.encoder.get_content_type()) 