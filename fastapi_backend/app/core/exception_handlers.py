"""
Global Exception Handlers

This module provides comprehensive exception handling for the FastAPI application
with detailed logging and user-friendly error messages.

Key Features:
- Pydantic validation error handling with detailed field-level errors
- SQLAlchemy integrity error handling
- Custom application error handling
- Comprehensive logging for debugging
- User-friendly error messages
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError
from pydantic import ValidationError
from loguru import logger
from typing import Dict, Any


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle Pydantic validation errors with detailed logging and user-friendly messages.
    
    Args:
        request: FastAPI request object
        exc: Validation error exception
        
    Returns:
        JSONResponse with detailed validation error information
    """
    # Log detailed validation errors
    logger.error(f"Validation error in {request.method} {request.url}")
    logger.error(f"Validation errors: {exc.errors()}")
    
    # Extract user information if available
    user_info = "unknown"
    if hasattr(request.state, 'user') and request.state.user:
        user_info = str(request.state.user.id)
    
    logger.error(f"User: {user_info}")
    
    # Build detailed error response
    error_details = []
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        error_details.append(f"{field_path}: {error['msg']}")
    
    error_message = f"Validation error: {'; '.join(error_details)}"
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": error_message,
            "validation_errors": exc.errors(),
            "field_errors": error_details
        }
    )


async def pydantic_validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """
    Handle Pydantic model validation errors.
    
    Args:
        request: FastAPI request object
        exc: Pydantic validation error
        
    Returns:
        JSONResponse with validation error details
    """
    logger.error(f"Pydantic validation error in {request.method} {request.url}")
    logger.error(f"Validation errors: {exc.errors()}")
    
    # Extract user information if available
    user_info = "unknown"
    if hasattr(request.state, 'user') and request.state.user:
        user_info = str(request.state.user.id)
    
    logger.error(f"User: {user_info}")
    
    # Build detailed error response
    error_details = []
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        error_details.append(f"{field_path}: {error['msg']}")
    
    error_message = f"Validation error: {'; '.join(error_details)}"
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": error_message,
            "validation_errors": exc.errors(),
            "field_errors": error_details
        }
    )


async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    """
    Handle SQLAlchemy integrity errors with detailed logging.
    
    Args:
        request: FastAPI request object
        exc: SQLAlchemy integrity error
        
    Returns:
        JSONResponse with integrity error details
    """
    logger.error(f"Integrity error in {request.method} {request.url}")
    logger.error(f"Integrity error details: {exc}")
    logger.error(f"Integrity error params: {exc.params}")
    
    # Extract user information if available
    user_info = "unknown"
    if hasattr(request.state, 'user') and request.state.user:
        user_info = str(request.state.user.id)
    
    logger.error(f"User: {user_info}")
    
    # Determine the type of integrity error
    error_message = "Database integrity constraint violation"
    if "unique" in str(exc).lower():
        error_message = "Duplicate entry - this record already exists"
    elif "foreign key" in str(exc).lower():
        error_message = "Referenced record does not exist"
    elif "not null" in str(exc).lower():
        error_message = "Required field is missing"
    
    return JSONResponse(
        status_code=409,
        content={
            "detail": error_message,
            "error_type": "integrity_error",
            "constraint": str(exc)
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle HTTP exceptions with enhanced logging.
    
    Args:
        request: FastAPI request object
        exc: HTTP exception
        
    Returns:
        JSONResponse with HTTP error details
    """
    # Log HTTP exceptions with context
    logger.warning(f"HTTP {exc.status_code} error in {request.method} {request.url}")
    logger.warning(f"Error detail: {exc.detail}")
    
    # Extract user information if available
    user_info = "unknown"
    if hasattr(request.state, 'user') and request.state.user:
        user_info = str(request.state.user.id)
    
    logger.warning(f"User: {user_info}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "error_type": "http_error"
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle general exceptions with comprehensive logging.
    
    Args:
        request: FastAPI request object
        exc: General exception
        
    Returns:
        JSONResponse with general error details
    """
    # Log comprehensive error information
    logger.error(f"Unhandled exception in {request.method} {request.url}")
    logger.error(f"Exception type: {type(exc).__name__}")
    logger.error(f"Exception message: {str(exc)}")
    
    # Extract user information if available
    user_info = "unknown"
    if hasattr(request.state, 'user') and request.state.user:
        user_info = str(request.state.user.id)
    
    logger.error(f"User: {user_info}")
    
    # Log request details for debugging
    logger.error(f"Request headers: {dict(request.headers)}")
    logger.error(f"Request query params: {dict(request.query_params)}")
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_type": "internal_error"
        }
    )


def register_exception_handlers(app) -> None:
    """
    Register all exception handlers with the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, pydantic_validation_exception_handler)
    app.add_exception_handler(IntegrityError, integrity_error_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler) 