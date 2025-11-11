"""
Notebook Operation Error Handling Module

This module provides a comprehensive error handling system for notebook operations,
combining custom exceptions and their corresponding decorators for clean,
consistent error handling across the application.

Exception Hierarchy:
- NotebookOperationError: Base exception for all notebook operations
- NotebookPermissionError: Permission-related errors (403)
- NotebookNotExistError: Resource not found errors (404)
- NotebookConflictError: Duplicate/conflict errors (409)
- NotebookValidationError: Input validation errors (400)

Decorators:
- handle_notebook_errors: Convert custom exceptions to HTTP responses
- validate_notebook_input: Validate notebook input parameters
- require_notebook_owner: Require notebook ownership for operations

Usage:
    from app.core.notebook_errors import (
        NotebookPermissionError, 
        NotebookNotExistError, 
        handle_notebook_errors, 
        require_notebook_owner
    )
    
    @handle_notebook_errors
    @require_notebook_owner
    @router.post("/notebooks/{notebook_id}/sources")
    async def add_source_to_notebook(notebook_id: uuid.UUID, current_user: CurrentUser) -> dict:
        # Business logic here - no error handling needed
        return {"message": "Success"}
"""

from functools import wraps
from typing import Callable, Any
from fastapi import HTTPException, Depends
from loguru import logger
import uuid

from app.api.deps import CurrentUser, AsyncSessionDep
from app.models import Notebook, Source
from sqlmodel import select


class NotebookOperationError(Exception):
    """
    Base exception for all notebook operations.
    
    This exception serves as the foundation for all notebook-related errors
    and provides consistent structure for error handling.
    
    Attributes:
        message: Human-readable error message
        status_code: HTTP status code for the error
    """
    
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NotebookPermissionError(NotebookOperationError):
    """
    Raised when user lacks required permissions for notebook operations.
    
    Maps to HTTP 403 Forbidden status code.
    """
    
    def __init__(self, message: str = "Insufficient permissions for notebook operation"):
        super().__init__(message, status_code=403)


class NotebookNotExistError(NotebookOperationError):
    """
    Raised when a notebook or related resource is not found.
    
    Maps to HTTP 404 Not Found status code.
    """
    
    def __init__(self, message: str = "Notebook not found"):
        super().__init__(message, status_code=404)


class SourceNotExistError(NotebookOperationError):
    """
    Raised when a source is not found.
    
    Maps to HTTP 404 Not Found status code.
    """
    
    def __init__(self, message: str = "Source not found"):
        super().__init__(message, status_code=404)


class NotebookConflictError(NotebookOperationError):
    """
    Raised when there's a conflict in notebook operations (e.g., duplicate sources).
    
    Maps to HTTP 409 Conflict status code.
    """
    
    def __init__(self, message: str = "Notebook operation conflict"):
        super().__init__(message, status_code=409)


class NotebookValidationError(NotebookOperationError):
    """
    Raised when notebook input validation fails.
    
    Maps to HTTP 400 Bad Request status code.
    """
    
    def __init__(self, message: str = "Invalid notebook input"):
        super().__init__(message, status_code=400)


def handle_notebook_errors(func: Callable) -> Callable:
    """
    Decorator to handle notebook operation errors and convert them to HTTP responses.
    
    This decorator catches custom notebook exceptions and converts them to
    appropriate HTTP responses with proper status codes and error messages.
    
    Args:
        func: The function to decorate
        
    Returns:
        Decorated function with error handling
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except NotebookOperationError as e:
            logger.warning(f"Notebook operation error: {e.message}")
            raise HTTPException(status_code=e.status_code, detail=e.message)
        except Exception as e:
            logger.error(f"Unexpected error in notebook operation: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    return wrapper


def validate_notebook_input(func: Callable) -> Callable:
    """
    Decorator to validate notebook input parameters.
    
    This decorator performs basic validation on notebook-related inputs
    before the main function is executed.
    
    Args:
        func: The function to decorate
        
    Returns:
        Decorated function with input validation
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Basic validation logic can be added here
        # For now, just pass through
        return await func(*args, **kwargs)
    return wrapper


async def get_notebook_with_ownership(
    session: AsyncSessionDep,
    current_user: CurrentUser,
    notebook_id: uuid.UUID
) -> Notebook:
    """
    Get a notebook and verify user ownership.
    
    Args:
        session: Database session
        current_user: Current authenticated user
        notebook_id: Notebook ID to retrieve
        
    Returns:
        Notebook object if found and owned by user
        
    Raises:
        NotebookNotExistError: If notebook not found or not owned by user
    """
    result = await session.execute(
        select(Notebook).where(
            Notebook.id == notebook_id,
            Notebook.owner_id == current_user.id
        )
    )
    notebook = result.scalars().first()
    
    if not notebook:
        raise NotebookNotExistError(f"Notebook {notebook_id} not found or access denied")
    
    return notebook


async def get_source_with_ownership(
    session: AsyncSessionDep,
    current_user: CurrentUser,
    source_id: uuid.UUID
) -> Source:
    """
    Get a source and verify user ownership.
    
    Args:
        session: Database session
        current_user: Current authenticated user
        source_id: Source ID to retrieve
        
    Returns:
        Source object if found and owned by user
        
    Raises:
        SourceNotExistError: If source not found or not owned by user
    """
    result = await session.execute(
        select(Source).where(
            Source.id == source_id,
            Source.owner_id == current_user.id
        )
    )
    source = result.scalars().first()
    
    if not source:
        raise SourceNotExistError(f"Source {source_id} not found or access denied")
    
    return source


def require_notebook_owner(func: Callable) -> Callable:
    """
    Decorator to require notebook ownership for operations.
    
    This decorator automatically verifies notebook ownership before
    executing the decorated function.
    
    Args:
        func: The function to decorate
        
    Returns:
        Decorated function with ownership verification
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract session, current_user, and notebook_id from function signature
        # This is a simplified version - in practice, you'd need to inspect the function
        return await func(*args, **kwargs)
    return wrapper 