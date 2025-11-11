"""
Notebook Sources Management API Routes

This module provides comprehensive notebook-source relationship management with
robust error handling, validation, and idempotent operations.

Key Features:
- Add sources to notebooks with idempotency (prevents duplicates)
- Remove sources from notebooks
- List notebook sources with pagination
- Reorder sources in notebooks
- Comprehensive error handling and logging

Architecture:
- PostgreSQL: Junction table with unique constraint (notebook_id, source_id)
- User ownership verification for all operations
- Idempotent operations preventing duplicate sources
- Cascade delete handling for related records

Error Handling:
- Source validation errors with detailed messages
- Ownership verification for all operations
- Duplicate detection and conflict handling
- Comprehensive logging for debugging

Security:
- User ownership verification for all operations
- Input validation preventing invalid data
- Secure relationship management

Idempotency:
- Unique constraint 'uq_notebook_source' prevents duplicate sources
- Graceful handling of duplicate attempts (return existing instead of error)
- Maintains data consistency across retries
"""

import uuid
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlmodel import func, select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from loguru import logger
from pydantic import ValidationError

from app.api.deps import CurrentUser, AsyncSessionDep
from app.models import (
    Notebook,
    Source,
    NotebookSource,
    NotebookSourceCreate,
    NotebookSourcePublic,
    NotebookSourcesPublic,
    NotebookSourceUpdate,
)

router = APIRouter(prefix="/notebooks", tags=["notebook-sources"])


class NotebookSourceValidationError(Exception):
    """Raised when notebook source validation fails."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class NotebookSourceNotExistError(Exception):
    """Raised when notebook source relationship is not found."""
    def __init__(self, message: str = "Notebook source relationship not found"):
        self.message = message
        super().__init__(self.message)


class NotebookSourceConflictError(Exception):
    """Raised when there's a conflict in notebook source operations."""
    def __init__(self, message: str = "Notebook source operation conflict"):
        self.message = message
        super().__init__(self.message)


class NotebookSourceService:
    """Service class for notebook source operations with validation and error handling."""
    
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
            HTTPException: If source not found or not owned by user
        """
        result = await session.execute(
            select(Source).where(
                Source.id == source_id,
                Source.owner_id == current_user.id
            )
        )
        source = result.scalars().first()
        
        if not source:
            raise HTTPException(status_code=404, detail=f"Source {source_id} not found or access denied")
        
        return source
    
    @staticmethod
    async def get_notebook_source_relationship(
        session: AsyncSessionDep,
        notebook_id: uuid.UUID,
        source_id: uuid.UUID
    ) -> Optional[NotebookSource]:
        """
        Get notebook source relationship if it exists.
        
        Args:
            session: Database session
            notebook_id: Notebook ID
            source_id: Source ID
            
        Returns:
            NotebookSource object if found, None otherwise
        """
        result = await session.execute(
            select(NotebookSource).where(
                NotebookSource.notebook_id == notebook_id,
                NotebookSource.source_id == source_id
            )
        )
        return result.scalars().first()
    
    @staticmethod
    def validate_notebook_source_input(notebook_source_in: NotebookSourceCreate) -> None:
        """
        Validate notebook source input.
        
        Args:
            notebook_source_in: Notebook source creation data
            
        Raises:
            NotebookSourceValidationError: If validation fails
        """
        if not notebook_source_in.source_id:
            raise NotebookSourceValidationError("Source ID is required")
        
        if notebook_source_in.position is not None and notebook_source_in.position < 0:
            raise NotebookSourceValidationError("Position must be non-negative")


@router.get("/{notebook_id}/sources", response_model=NotebookSourcesPublic)
async def list_notebook_sources(
    session: AsyncSessionDep,
    current_user: CurrentUser,
    notebook_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> Any:
    """List sources in a notebook with ownership verification."""
    try:
        # Verify notebook ownership
        notebook = await NotebookSourceService.get_notebook_with_ownership(session, current_user, notebook_id)
        
        # Get count
        count_query = select(func.count()).select_from(NotebookSource).where(
            NotebookSource.notebook_id == notebook_id
        )
        result = await session.execute(count_query)
        count = result.scalar()
        
        # Get paginated notebook sources with source details
        query = (
            select(NotebookSource)
            .options(selectinload(NotebookSource.source))
            .where(NotebookSource.notebook_id == notebook_id)
            .offset(skip)
            .limit(limit)
            .order_by(NotebookSource.position, NotebookSource.added_at)
        )
        result = await session.execute(query)
        notebook_sources = result.scalars().all()
        
        logger.info(f"Listed {len(notebook_sources)} sources for notebook {notebook_id}")
        return NotebookSourcesPublic(data=notebook_sources, count=count)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing sources for notebook {notebook_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to list notebook sources")


@router.post("/{notebook_id}/sources", response_model=NotebookSourcePublic)
async def add_source_to_notebook(
    session: AsyncSessionDep,
    current_user: CurrentUser,
    notebook_id: uuid.UUID,
    notebook_source_in: NotebookSourceCreate,
) -> Any:
    """Add a source to a notebook with idempotency and ownership verification."""
    try:
        # Log incoming request data for debugging
        logger.info(f"Adding source to notebook for user {current_user.id}")
        logger.info(f"Notebook ID: {notebook_id}, Source ID: {notebook_source_in.source_id}, Position: {notebook_source_in.position}")
        
        # Verify notebook ownership
        notebook = await NotebookSourceService.get_notebook_with_ownership(session, current_user, notebook_id)
        
        # Verify source ownership
        source = await NotebookSourceService.get_source_with_ownership(session, current_user, notebook_source_in.source_id)
        
        # Validate input
        NotebookSourceService.validate_notebook_source_input(notebook_source_in)
        
        # Check for existing relationship (idempotency)
        existing_relationship = await NotebookSourceService.get_notebook_source_relationship(
            session, notebook_id, notebook_source_in.source_id
        )
        
        if existing_relationship:
            logger.info(f"Source {notebook_source_in.source_id} already exists in notebook {notebook_id}")
            return existing_relationship
        
        # Get next position if not specified
        if notebook_source_in.position is None:
            max_position_query = select(func.max(NotebookSource.position)).where(
                NotebookSource.notebook_id == notebook_id
            )
            result = await session.execute(max_position_query)
            max_position = result.scalar()
            position = (max_position or -1) + 1
        else:
            position = notebook_source_in.position
        
        # Create notebook source relationship
        notebook_source = NotebookSource(
            notebook_id=notebook_id,
            source_id=notebook_source_in.source_id,
            position=position,
        )
        
        session.add(notebook_source)
        await session.commit()
        await session.refresh(notebook_source)
        
        # Load the source details for the response
        await session.refresh(notebook_source, ['source'])
        
        logger.info(f"Added source {notebook_source_in.source_id} to notebook {notebook_id} at position {position}")
        return notebook_source
        
    except HTTPException:
        raise
    except IntegrityError as e:
        await session.rollback()
        logger.warning(f"Integrity error adding source to notebook: {e}")
        raise HTTPException(status_code=409, detail="Source already exists in notebook")
    except NotebookSourceValidationError as e:
        logger.warning(f"Notebook source validation failed: {e.message}")
        raise HTTPException(status_code=400, detail=e.message)
    except ValidationError as e:
        logger.error(f"Pydantic validation error for user {current_user.id}: {e}")
        logger.error(f"Validation errors: {e.errors()}")
        # Return detailed validation errors
        error_details = []
        for error in e.errors():
            field = " -> ".join(str(loc) for loc in error["loc"])
            error_details.append(f"{field}: {error['msg']}")
        raise HTTPException(status_code=422, detail=f"Validation error: {'; '.join(error_details)}")
    except Exception as e:
        logger.error(f"Error adding source to notebook {notebook_id}: {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Exception details: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to add source to notebook")


@router.delete("/{notebook_id}/sources/{source_id}")
async def remove_source_from_notebook(
    session: AsyncSessionDep,
    current_user: CurrentUser,
    notebook_id: uuid.UUID,
    source_id: uuid.UUID,
) -> Any:
    """Remove a source from a notebook with ownership verification."""
    try:
        # Verify notebook ownership
        notebook = await NotebookSourceService.get_notebook_with_ownership(session, current_user, notebook_id)
        
        # Verify source ownership
        source = await NotebookSourceService.get_source_with_ownership(session, current_user, source_id)
        
        # Find the relationship
        relationship = await NotebookSourceService.get_notebook_source_relationship(session, notebook_id, source_id)
        
        if not relationship:
            raise HTTPException(status_code=404, detail="Source not found in notebook")
        
        # Delete the relationship
        await session.delete(relationship)
        await session.commit()
        
        logger.info(f"Removed source {source_id} from notebook {notebook_id}")
        return {"message": "Source removed from notebook successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing source {source_id} from notebook {notebook_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove source from notebook")


@router.put("/{notebook_id}/sources/{source_id}", response_model=NotebookSourcePublic)
async def update_notebook_source(
    session: AsyncSessionDep,
    current_user: CurrentUser,
    notebook_id: uuid.UUID,
    source_id: uuid.UUID,
    notebook_source_in: NotebookSourceUpdate,
) -> Any:
    """Update a notebook source relationship (e.g., change position)."""
    try:
        # Verify notebook ownership
        notebook = await NotebookSourceService.get_notebook_with_ownership(session, current_user, notebook_id)
        
        # Verify source ownership
        source = await NotebookSourceService.get_source_with_ownership(session, current_user, source_id)
        
        # Find the relationship
        relationship = await NotebookSourceService.get_notebook_source_relationship(session, notebook_id, source_id)
        
        if not relationship:
            raise HTTPException(status_code=404, detail="Source not found in notebook")
        
        # Update position if provided
        if notebook_source_in.position is not None:
            if notebook_source_in.position < 0:
                raise HTTPException(status_code=400, detail="Position must be non-negative")
            relationship.position = notebook_source_in.position
        
        await session.commit()
        await session.refresh(relationship)
        
        logger.info(f"Updated source {source_id} in notebook {notebook_id}")
        return relationship
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating source {source_id} in notebook {notebook_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update notebook source") 