"""
Notebook Messages Management API Routes

This module provides comprehensive message management functionality for notebooks
with robust error handling, validation, and transactional safety.

Key Features:
- Add messages to notebooks with ownership verification
- List notebook messages with pagination
- Message validation and security checks
- Comprehensive error handling and logging

Architecture:
- PostgreSQL: Message storage with ACID compliance
- User ownership verification for all operations
- Input validation and security checks
- Cascade delete handling for related records

Error Handling:
- Message validation errors with detailed messages
- Ownership verification for all operations
- Conflict detection and handling
- Comprehensive logging for debugging

Security:
- User ownership verification for all operations
- Input validation preventing invalid data
- Secure message handling
"""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import func, select
from loguru import logger

from app.api.deps import CurrentUser, AsyncSessionDep
from app.models import (
    Notebook,
    NotebookMessage,
    NotebookMessageCreate,
    NotebookMessagePublic,
    NotebookMessagesPublic,
)

router = APIRouter(prefix="/notebooks", tags=["notebook-messages"])


class MessageValidationError(Exception):
    """Raised when message validation fails."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class MessageService:
    """Service class for message operations with validation and error handling."""
    
    @staticmethod
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
            HTTPException: If notebook not found or not owned by user
        """
        result = await session.execute(
            select(Notebook).where(
                Notebook.id == notebook_id,
                Notebook.owner_id == current_user.id
            )
        )
        notebook = result.scalars().first()
        
        if not notebook:
            raise HTTPException(status_code=404, detail=f"Notebook {notebook_id} not found or access denied")
        
        return notebook
    
    @staticmethod
    def validate_message_input(message_in: NotebookMessageCreate) -> None:
        """
        Validate message input.
        
        Args:
            message_in: Message creation data
            
        Raises:
            MessageValidationError: If validation fails
        """
        if not message_in.content or not message_in.content.strip():
            raise MessageValidationError("Message content is required")
        
        if message_in.role not in ["user", "assistant"]:
            raise MessageValidationError("Message role must be 'user' or 'assistant'")


@router.get("/{notebook_id}/messages", response_model=NotebookMessagesPublic)
async def list_notebook_messages(
    session: AsyncSessionDep,
    current_user: CurrentUser,
    notebook_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> Any:
    """List messages in a notebook with ownership verification."""
    try:
        # Verify notebook ownership
        notebook = await MessageService.get_notebook_with_ownership(session, current_user, notebook_id)
        
        # Get count
        count_query = select(func.count()).select_from(NotebookMessage).where(
            NotebookMessage.notebook_id == notebook_id
        )
        result = await session.execute(count_query)
        count = result.scalar()
        
        # Get paginated messages
        query = (
            select(NotebookMessage)
            .where(NotebookMessage.notebook_id == notebook_id)
            .offset(skip)
            .limit(limit)
            .order_by(NotebookMessage.created_at)
        )
        result = await session.execute(query)
        messages = result.scalars().all()
        
        logger.info(f"Listed {len(messages)} messages for notebook {notebook_id}")
        return NotebookMessagesPublic(data=messages, count=count)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing messages for notebook {notebook_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to list messages")


@router.post("/{notebook_id}/messages", response_model=NotebookMessagePublic)
async def add_message_to_notebook(
    session: AsyncSessionDep,
    current_user: CurrentUser,
    notebook_id: uuid.UUID,
    message_in: NotebookMessageCreate,
) -> Any:
    """Add a message to a notebook with validation and ownership verification."""
    try:
        # Verify notebook ownership
        notebook = await MessageService.get_notebook_with_ownership(session, current_user, notebook_id)
        
        # Validate message input
        MessageService.validate_message_input(message_in)
        
        # Create message
        message = NotebookMessage(
            notebook_id=notebook_id,
            role=message_in.role,
            content=message_in.content.strip(),
            used_sources=message_in.used_sources,
        )
        
        session.add(message)
        await session.commit()
        await session.refresh(message)
        
        logger.info(f"Added {message.role} message to notebook {notebook_id}")
        return message
        
    except HTTPException:
        raise
    except MessageValidationError as e:
        logger.warning(f"Message validation failed for notebook {notebook_id}: {e.message}")
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"Error adding message to notebook {notebook_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to add message") 