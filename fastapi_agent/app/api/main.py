from fastapi import APIRouter

from .routes.chat_agui import router as chat_agui_router
from .routes.notebook_chat import router as notebook_chat_router

api_router = APIRouter()
api_router.include_router(chat_agui_router)
api_router.include_router(notebook_chat_router)
