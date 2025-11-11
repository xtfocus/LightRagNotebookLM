import logging
import asyncio
import os

from sqlalchemy import Engine
from sqlmodel import select
from tenacity import after_log, before_log, retry, stop_after_attempt, wait_fixed

# Early diagnostics for environment values that have caused issues
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Prestart env snapshot: ALLOWED_FILE_TYPES=%r", os.getenv("ALLOWED_FILE_TYPES"))
logger.info("Prestart env snapshot: BACKEND_CORS_ORIGINS=%r", os.getenv("BACKEND_CORS_ORIGINS"))

from app.core.db import async_engine

max_tries = 60 * 5  # 5 minutes
wait_seconds = 1


@retry(
    stop=stop_after_attempt(max_tries),
    wait=wait_fixed(wait_seconds),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.WARN),
)
async def init() -> None:
    try:
        async with async_engine.begin() as conn:
            # Try to create session to check if DB is awake
            await conn.execute(select(1))
    except Exception as e:
        logger.error(e)
        raise e


def main() -> None:
    logger.info("Initializing service")
    asyncio.run(init())
    logger.info("Service finished initializing")


if __name__ == "__main__":
    main()
