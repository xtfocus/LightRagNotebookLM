import sentry_sdk
from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware

from app.api.main import api_router
from app.core.config import settings
from app.core.scheduler import start_cleanup_scheduler, stop_cleanup_scheduler
from app.core.exception_handlers import register_exception_handlers
from app.core.middleware import setup_request_logging


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.BACKEND_API_PREFIX}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
)

# Set all CORS enabled origins
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.BACKEND_API_PREFIX)

# Register global exception handlers
register_exception_handlers(app)

# Set up request logging middleware
setup_request_logging(app, log_request_body=True)


@app.on_event("startup")
async def startup_event():
    """Startup event handler."""
    # Start the cleanup scheduler
    await start_cleanup_scheduler()


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler."""
    # Stop the cleanup scheduler
    await stop_cleanup_scheduler()
