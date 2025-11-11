"""
Retry utilities using tenacity library.

This module provides configurable retry decorators for different types of operations
including MinIO, Kafka, and database operations.
"""

import logging
from typing import Callable, Any, TypeVar
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_log,
    after_log,
)

from app.core.config import settings

# Configure logger
logger = logging.getLogger(__name__)

# Type variable for generic functions
F = TypeVar('F', bound=Callable[..., Any])


def minio_retry(func: F) -> F:
    """Retry decorator for MinIO operations."""
    return retry(
        stop=stop_after_attempt(settings.MINIO_RETRY_MAX_ATTEMPTS),
        wait=wait_exponential(
            multiplier=settings.MINIO_RETRY_MULTIPLIER,
            min=settings.MINIO_RETRY_BASE_DELAY,
            max=settings.MINIO_RETRY_MAX_DELAY
        ),
        retry=retry_if_exception_type((
            ConnectionError,
            TimeoutError,
            OSError,
            Exception
        )),
        before=before_log(logger, logging.INFO),
        after=after_log(logger, logging.WARN),
    )(func)


def kafka_retry(func: F) -> F:
    """Retry decorator for Kafka operations."""
    return retry(
        stop=stop_after_attempt(settings.KAFKA_RETRY_MAX_ATTEMPTS),
        wait=wait_exponential(
            multiplier=settings.KAFKA_RETRY_MULTIPLIER,
            min=settings.KAFKA_RETRY_BASE_DELAY,
            max=settings.KAFKA_RETRY_MAX_DELAY
        ),
        retry=retry_if_exception_type((
            ConnectionError,
            TimeoutError,
            Exception
        )),
        before=before_log(logger, logging.INFO),
        after=after_log(logger, logging.WARN),
    )(func)


def db_retry(func: F) -> F:
    """Retry decorator for database operations."""
    return retry(
        stop=stop_after_attempt(settings.DB_RETRY_MAX_ATTEMPTS),
        wait=wait_exponential(
            multiplier=settings.DB_RETRY_MULTIPLIER,
            min=settings.DB_RETRY_BASE_DELAY,
            max=settings.DB_RETRY_MAX_DELAY
        ),
        retry=retry_if_exception_type((
            ConnectionError,
            TimeoutError,
            Exception
        )),
        before=before_log(logger, logging.INFO),
        after=after_log(logger, logging.WARN),
    )(func) 