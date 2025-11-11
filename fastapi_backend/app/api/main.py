from fastapi import APIRouter

from app.api.routes import items, login, private, users, utils, agent, files, search, information_sources, notebooks, notebook_messages, notebook_sources
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(items.router)
api_router.include_router(agent.router)
api_router.include_router(files.router)
api_router.include_router(search.router)
api_router.include_router(information_sources.router)
api_router.include_router(notebooks.router)
api_router.include_router(notebook_messages.router)
api_router.include_router(notebook_sources.router)

if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
