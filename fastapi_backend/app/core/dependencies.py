from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from fastapi import Depends

from app.core.config import settings
from app.core.db import async_session_maker
from app.services.rate_limiting import RateLimiterInterface, SimpleRateLimiter


def get_session_maker() -> async_sessionmaker[AsyncSession]:
    """Get the async session maker for dependency injection."""
    return async_session_maker


async def get_rate_limiter(
    session_maker: async_sessionmaker[AsyncSession] = Depends(get_session_maker)
) -> RateLimiterInterface:
    """
    Get rate limiter instance based on environment.
    
    For demo app: returns SimpleRateLimiter
    For production: could return EnterpriseRateLimiter with Redis
    """
    if settings.ENVIRONMENT == "production":
        # Future: return EnterpriseRateLimiter(redis_client, session_maker)
        return SimpleRateLimiter(session_maker)
    else:
        return SimpleRateLimiter(session_maker) 