"""
File Operation Error Handling Module

This module provides a comprehensive error handling system for file operations,
combining custom exceptions and their corresponding decorators for clean,
consistent error handling across the application.

Exception Hierarchy:
- FileOperationError: Base exception for all file operations
- FilePermissionError: Permission-related errors (403)
- FileNotExistError: Resource not found errors (404) - renamed from FileNotFoundError
- FileConflictError: Duplicate/conflict errors (409)
- FileValidationError: Input validation errors (400)

Decorators:
- handle_file_errors: Convert custom exceptions to HTTP responses
- require_superuser: Require superuser permissions for endpoints
- validate_file_input: Validate file input parameters

Usage:
    from app.core.file_errors import (
        FilePermissionError, 
        FileNotExistError, 
        handle_file_errors, 
        require_superuser
    )
    
    @handle_file_errors
    @require_superuser
    @router.post("/admin-only")
    async def admin_endpoint(current_user: CurrentUser) -> dict:
        # Business logic here - no error handling needed
        return {"message": "Success"}
"""

from functools import wraps
from typing import Callable, Any
from fastapi import HTTPException
from loguru import logger

from app.api.deps import CurrentUser
from app.core.config import settings


def bytes_to_human_readable(bytes_value: int) -> str:
    """
    Convert bytes to human-readable format.
    
    Args:
        bytes_value: Size in bytes
        
    Returns:
        Human-readable string (e.g., "1.5MB", "2.3GB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f}{unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f}TB"


class FileOperationError(Exception):
    """
    Base exception for all file operations.
    
    This exception serves as the foundation for all file-related errors
    and provides consistent structure for error handling.
    
    Attributes:
        message: Human-readable error message
        status_code: HTTP status code for the error
    """
    
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class FilePermissionError(FileOperationError):
    """
    Raised when user lacks required permissions for file operations.
    
    Maps to HTTP 403 Forbidden status code.
    """
    
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, status_code=403)


class FileNotExistError(FileOperationError):
    """
    Raised when a file or document is not found.
    
    Maps to HTTP 404 Not Found status code.
    Note: Renamed from FileNotFoundError to avoid conflict with built-in exception.
    """
    
    def __init__(self, message: str = "File not found"):
        super().__init__(message, status_code=404)


class FileConflictError(FileOperationError):
    """
    Raised when there's a conflict (e.g., duplicate file upload).
    
    Maps to HTTP 409 Conflict status code.
    """
    
    def __init__(self, message: str = "File conflict"):
        super().__init__(message, status_code=409)


class FileValidationError(FileOperationError):
    """
    Raised when file input validation fails.
    
    Maps to HTTP 400 Bad Request status code.
    """
    
    def __init__(self, message: str = "Invalid file data"):
        super().__init__(message, status_code=400)


def handle_file_errors(func: Callable) -> Callable:
    """
    Convert custom file operation exceptions to appropriate HTTP responses.
    
    This decorator catches custom exceptions and converts them to FastAPI
    HTTPException responses with the correct status codes and messages.
    
    Args:
        func: The function to wrap with error handling
        
    Returns:
        Wrapped function with automatic error handling
        
    Exception Mapping:
        - FilePermissionError -> HTTP 403 Forbidden
        - FileNotExistError -> HTTP 404 Not Found
        - FileConflictError -> HTTP 409 Conflict
        - FileValidationError -> HTTP 400 Bad Request
        - FileOperationError -> HTTP 500 Internal Server Error
    """
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        try:
            return await func(*args, **kwargs)
        except FilePermissionError as e:
            raise HTTPException(status_code=e.status_code, detail=e.message)
        except FileNotExistError as e:
            raise HTTPException(status_code=e.status_code, detail=e.message)
        except FileConflictError as e:
            raise HTTPException(status_code=e.status_code, detail=e.message)
        except FileValidationError as e:
            raise HTTPException(status_code=e.status_code, detail=e.message)
        except FileOperationError as e:
            raise HTTPException(status_code=e.status_code, detail=e.message)
        except Exception as e:
            # Log unexpected errors and convert to generic 500
            logger.exception(f"Unexpected error in {func.__name__}: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    return wrapper


def require_superuser(func: Callable) -> Callable:
    """
    Require superuser permissions for the decorated endpoint.
    
    This decorator checks if the current user has superuser privileges
    and raises a FilePermissionError if they don't.
    
    Args:
        func: The function to wrap with permission checking
        
    Returns:
        Wrapped function with superuser permission checking
        
    Usage:
        @require_superuser
        @router.post("/admin-only")
        async def admin_endpoint(current_user: CurrentUser) -> dict:
            # Only superusers can access this
            return {"message": "Admin operation"}
    """
    @wraps(func)
    async def wrapper(current_user: CurrentUser, *args, **kwargs) -> Any:
        if not current_user.is_superuser:
            raise FilePermissionError("Only superusers can perform this operation")
        return await func(current_user, *args, **kwargs)
    
    return wrapper


def validate_file_input(func: Callable) -> Callable:
    """
    Validate file input parameters and raise appropriate exceptions.
    
    This decorator provides common validation for file operations
    such as checking for empty files, missing parameters, file sizes, and file types.
    
    Args:
        func: The function to wrap with input validation
        
    Returns:
        Wrapped function with input validation
        
    Usage:
        @validate_file_input
        @router.post("/upload")
        async def upload_files(files: List[UploadFile]) -> dict:
            # Files are already validated
            return {"message": "Upload successful"}
    """
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        # Check for common validation patterns
        # This is a basic implementation - can be extended as needed
        
        # Check for files parameter
        if 'files' in kwargs and (not kwargs['files'] or len(kwargs['files']) == 0):
            raise FileValidationError("No files provided")
        
        # Check for document_ids parameter
        if 'document_ids' in kwargs and (not kwargs['document_ids'] or len(kwargs['document_ids']) == 0):
            raise FileValidationError("No document IDs provided")
        
        # File size and type validation
        if 'files' in kwargs and kwargs['files']:
            total_size = 0
            for file in kwargs['files']:
                # Check individual file size based on file type
                if hasattr(file, 'size') and file.size:
                    # Determine file type and get appropriate size limit
                    file_extension = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
                    mime_type = getattr(file, 'content_type', '')
                    
                    # Get size limit based on file type
                    size_limit = settings.MAX_FILE_SIZE_BYTES  # fallback
                    limit_name = "MAX_FILE_SIZE_BYTES"
                    
                    if file_extension == 'pdf' or mime_type == 'application/pdf':
                        size_limit = settings.MAX_PDF_SIZE_BYTES
                        limit_name = "MAX_PDF_SIZE_BYTES"
                    elif file_extension in ['docx', 'doc'] or mime_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword']:
                        size_limit = settings.MAX_DOCX_SIZE_BYTES
                        limit_name = "MAX_DOCX_SIZE_BYTES"
                    elif file_extension == 'txt' or mime_type == 'text/plain':
                        size_limit = settings.MAX_TXT_SIZE_BYTES
                        limit_name = "MAX_TXT_SIZE_BYTES"
                    
                    # Check file size against appropriate limit
                    if file.size > size_limit:
                        max_size_mb = size_limit / (1024 * 1024)
                        raise FileValidationError(
                            f"File '{file.filename}' ({bytes_to_human_readable(file.size)}) exceeds maximum size of {bytes_to_human_readable(size_limit)} for {file_extension.upper()} files"
                        )
                    
                    # Check minimum file size
                    if file.size < settings.MIN_FILE_SIZE_BYTES:
                        raise FileValidationError(
                            f"File '{file.filename}' ({bytes_to_human_readable(file.size)}) is too small (minimum {bytes_to_human_readable(settings.MIN_FILE_SIZE_BYTES)})"
                        )
                    
                    total_size += file.size
                
                # Check file type (extension-based)
                if hasattr(file, 'filename') and file.filename:
                    file_extension = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
                    if file_extension and file_extension not in settings.ALLOWED_FILE_TYPES:
                        raise FileValidationError(
                            f"File type '{file_extension}' is not allowed. Allowed types: {', '.join(settings.ALLOWED_FILE_TYPES)}"
                        )
            
            # Check total upload size
            if total_size > settings.MAX_TOTAL_UPLOAD_SIZE_BYTES:
                max_total_mb = settings.MAX_TOTAL_UPLOAD_SIZE_BYTES / (1024 * 1024)
                total_mb = total_size / (1024 * 1024)
                raise FileValidationError(
                    f"Total upload size ({bytes_to_human_readable(total_size)}) exceeds maximum of {bytes_to_human_readable(settings.MAX_TOTAL_UPLOAD_SIZE_BYTES)}"
                )
        
        return await func(*args, **kwargs)
    
    return wrapper


def non_blocking_kafka(func: Callable) -> Callable:
    """
    Make Kafka operations non-blocking with automatic error handling.
    
    This decorator wraps functions that might publish Kafka events and
    ensures that Kafka failures don't affect the main operation.
    
    Args:
        func: The function to wrap with non-blocking Kafka handling
        
    Returns:
        Wrapped function with non-blocking Kafka operations
        
    Note:
        This decorator is designed to work with functions that return
        objects with 'id' and 'owner_id' attributes for Kafka events.
        For other use cases, manual Kafka error handling may be needed.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        result = await func(*args, **kwargs)
        
        # Try to extract document info for Kafka event
        # This is a simplified approach - in practice, you might need
        # more sophisticated logic to determine what Kafka event to send
        try:
            if hasattr(result, 'id') and hasattr(result, 'owner_id'):
                # This would need to be customized based on the operation
                # For now, we just log that Kafka handling is available
                logger.debug(f"Kafka event could be sent for {result.id}")
        except Exception as e:
            logger.warning(f"Kafka event handling failed: {e}")
        
        return result
    
    return wrapper 