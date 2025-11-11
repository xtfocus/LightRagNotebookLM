"""
Tests for Custom Error Handling and Decorators

This module tests the custom exceptions and decorators to ensure they
work correctly and provide the expected HTTP responses.
"""

import pytest
from fastapi import HTTPException
from unittest.mock import MagicMock

from app.core.file_errors import (
    FileOperationError,
    FilePermissionError,
    FileNotExistError,
    FileConflictError,
    FileValidationError,
    handle_file_errors,
    require_superuser
)


class TestCustomExceptions:
    """Test custom exception classes."""
    
    def test_file_operation_error(self):
        """Test base FileOperationError."""
        error = FileOperationError("Test error", 500)
        assert error.message == "Test error"
        assert error.status_code == 500
        assert str(error) == "Test error"
    
    def test_file_permission_error(self):
        """Test FilePermissionError."""
        error = FilePermissionError("Access denied")
        assert error.message == "Access denied"
        assert error.status_code == 403
    
    def test_file_not_exist_error(self):
        """Test FileNotExistError."""
        error = FileNotExistError("Document not found")
        assert error.message == "Document not found"
        assert error.status_code == 404


class TestErrorHandlingDecorator:
    """Test the handle_file_errors decorator."""
    
    @pytest.mark.asyncio
    async def test_handle_file_permission_error(self):
        """Test that FilePermissionError is converted to HTTP 403."""
        @handle_file_errors
        async def test_function():
            raise FilePermissionError("Access denied")
        
        with pytest.raises(HTTPException) as exc_info:
            await test_function()
        
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "Access denied"
    
    @pytest.mark.asyncio
    async def test_handle_file_not_exist_error(self):
        """Test that FileNotExistError is converted to HTTP 404."""
        @handle_file_errors
        async def test_function():
            raise FileNotExistError("Document not found")
        
        with pytest.raises(HTTPException) as exc_info:
            await test_function()
        
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Document not found"
    
    @pytest.mark.asyncio
    async def test_handle_success(self):
        """Test that successful operations are not affected."""
        @handle_file_errors
        async def test_function():
            return {"message": "Success"}
        
        result = await test_function()
        assert result == {"message": "Success"}


class TestSuperuserDecorator:
    """Test the require_superuser decorator."""
    
    @pytest.mark.asyncio
    async def test_require_superuser_success(self):
        """Test that superusers can access protected endpoints."""
        @require_superuser
        async def test_function(current_user):
            return {"message": "Success"}
        
        # Create a mock superuser
        superuser = MagicMock()
        superuser.is_superuser = True
        
        result = await test_function(superuser)
        assert result == {"message": "Success"}
    
    @pytest.mark.asyncio
    async def test_require_superuser_failure(self):
        """Test that non-superusers are denied access."""
        @require_superuser
        async def test_function(current_user):
            return {"message": "Success"}
        
        # Create a mock non-superuser
        regular_user = MagicMock()
        regular_user.is_superuser = False
        
        with pytest.raises(FilePermissionError) as exc_info:
            await test_function(regular_user)
        
        assert exc_info.value.message == "Only superusers can perform this operation"
        assert exc_info.value.status_code == 403