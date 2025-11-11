from fastapi import APIRouter, Request, Response, status, Depends
from fastapi.responses import StreamingResponse
import httpx
import os
from app.api.deps import get_current_user

router = APIRouter(tags=["agent"])

# AGENT_SERVICE_URL can be set via env or default to Docker service name
AGENT_SERVICE_URL = os.getenv("AGENT_SERVICE_URL", "http://agent:8000")

@router.post("/agent/chat", dependencies=[Depends(get_current_user)])
async def agent_chat_proxy(request: Request):
    # Optionally, add authentication here (Depends(get_current_user))
    agent_url = f"{AGENT_SERVICE_URL}/chat"
    try:
        async with httpx.AsyncClient(timeout=None) as client:
            # Stream request body to agent
            req_body = await request.body()
            async with client.stream(
                "POST",
                agent_url,
                content=req_body,
                headers={"content-type": request.headers.get("content-type", "application/json")},
            ) as agent_response:
                return StreamingResponse(
                    agent_response.aiter_raw(),
                    status_code=agent_response.status_code,
                    media_type=agent_response.headers.get("content-type", "text/event-stream"),
                )
    except httpx.RequestError as e:
        return Response(
            content=f"Agent service unavailable: {e}",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        ) 