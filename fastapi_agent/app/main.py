from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from .agents import register_agent
from .agents.chat_agent import ChatAgent
from .agents.notebook_agent import NotebookAgent
from .api.main import api_router
from .core.config import config


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup persistent DB pool and LangGraph checkpointer
    DB_URI = config.LANGGRAPHDB_URI
    async with AsyncConnectionPool(
        conninfo=DB_URI,
        max_size=20,
        kwargs={  # Required https://github.com/langchain-ai/langgraph/tree/main/libs/checkpoint-postgres
            "autocommit": True,
            "row_factory": dict_row,
        },
    ) as pool:
        checkpointer = AsyncPostgresSaver(pool)
        await checkpointer.setup()
        app.state.checkpointer = (
            checkpointer  # Store checkpointer for use in agents/protocols
        )

        # Register the original chat agent
        chat_agent_second = ChatAgent()
        chat_agent_second.name = "agui"
        chat_agent_second.workflow = chat_agent_second.build().compile(
            checkpointer=checkpointer
        )
        register_agent(chat_agent_second)

        # Register the notebook agent for notebooks
        notebook_agent = NotebookAgent()
        notebook_agent.workflow = notebook_agent.build().compile(
            checkpointer=checkpointer
        )
        register_agent(notebook_agent)

        yield
    # Cleanup handled by context manager


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=config.AGENT_API_PREFIX)


@app.get("/health")
def health():
    return {"status": "ok"}
