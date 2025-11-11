"""
Notebook Management API Routes

This module provides comprehensive notebook management functionality with robust
error handling, validation, and transactional safety.

Key Features:
- Create and manage notebooks with ownership verification
- Update notebook metadata and descriptions
- Delete notebooks with cascade handling
- Comprehensive error handling and logging
- Input validation and security checks

Architecture:
- PostgreSQL: Notebook metadata storage with ACID compliance
- User ownership verification for all operations
- Input validation and security checks
- Cascade delete handling for related records

Error Handling:
- Notebook validation errors with detailed messages
- Ownership verification for all operations
- Conflict detection and handling
- Comprehensive logging for debugging

Security:
- User ownership verification for all operations
- Input validation preventing invalid data
- Secure deletion with cascade handling
"""

import uuid
from typing import Any, List, Optional, Dict

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlmodel import col, delete, func, select
from loguru import logger
from pydantic import ValidationError

from app.api.deps import CurrentUser, AsyncSessionDep
from app.models import (
    Notebook,
    NotebookCreate,
    NotebookPublic,
    NotebooksPublic,
    NotebookUpdate,
    NotebookSource,
    NotebookSourceCreate,
    NotebookSourcePublic,
    NotebookSourcesPublic,
    NotebookMessage,
    NotebookMessageCreate,
    NotebookMessagePublic,
    NotebookMessagesPublic,
    Source,
)
from app.api.routes.information_sources import SourceDeleteService

router = APIRouter(prefix="/notebooks", tags=["notebooks"])


class NotebookValidationError(Exception):
    """Raised when notebook validation fails."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class NotebookNotExistError(Exception):
    """Raised when notebook is not found."""
    def __init__(self, message: str = "Notebook not found"):
        self.message = message
        super().__init__(self.message)


class NotebookConflictError(Exception):
    """Raised when there's a conflict in notebook operations."""
    def __init__(self, message: str = "Notebook operation conflict"):
        self.message = message
        super().__init__(self.message)


class NotebookService:
    """Service class for notebook operations with validation and error handling."""
    
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
    
    @staticmethod
    async def get_notebook_with_source_count(
        session: AsyncSessionDep,
        notebook: Notebook
    ) -> Dict[str, Any]:
        """
        Get notebook data with source count for API responses.
        
        Args:
            session: Database session
            notebook: Notebook object to enrich with source count
            
        Returns:
            Dictionary containing notebook data with source count
        """
        # Count sources linked to this notebook
        source_count_query = select(func.count(NotebookSource.id)).where(
            NotebookSource.notebook_id == notebook.id
        )
        result = await session.execute(source_count_query)
        source_count = result.scalar() or 0
        
        # Convert notebook to dict and add source count
        notebook_dict = {
            "id": notebook.id,
            "title": notebook.title,
            "description": notebook.description,
            "owner_id": notebook.owner_id,
            "created_at": notebook.created_at,
            "updated_at": notebook.updated_at,
            "source_count": source_count
        }
        
        return notebook_dict


class NotebookDeleteService:
    """Service class for comprehensive notebook deletion with orphaned source handling."""
    
    def __init__(self):
        self.source_delete_service = SourceDeleteService()
    
    async def delete_notebook_transactional(
        self,
        session: AsyncSessionDep,
        current_user: CurrentUser,
        notebook_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Delete a notebook with comprehensive cleanup including orphaned source handling.
        
        This method implements a robust deletion process that:
        1. Verifies notebook exists and user owns it
        2. Identifies sources that will become orphaned (not used by other notebooks)
        3. Deletes orphaned sources with full storage cleanup
        4. Deletes notebook (cascade will handle related records)
        5. Proper error handling and rollback
        
        Args:
            session: Database session for transaction management
            current_user: Authenticated user performing the deletion
            notebook_id: UUID of the notebook to delete
            
        Returns:
            Dict containing success message, notebook_id, and cleanup summary
            
        Raises:
            NotebookNotExistError: Notebook not found or not owned by user
            HTTPException: Deletion failure or database error
        """
        # Get notebook and verify ownership
        notebook = await NotebookService.get_notebook_with_ownership(session, current_user, notebook_id)
        
        logger.info(f"Starting comprehensive deletion for notebook {notebook_id}")
        logger.info(f"Notebook details: title='{notebook.title}', owner={current_user.id}")
        
        try:
            # Step 1: Identify and handle orphaned sources
            orphaned_sources = await self._identify_orphaned_sources(session, notebook_id, current_user.id)
            cleanup_summary = await self._cleanup_orphaned_sources(session, orphaned_sources, current_user)
            
            # Step 2: Delete notebook (cascade will handle related records)
            await session.delete(notebook)
            await session.commit()
            
            logger.info(f"✅ Successfully deleted notebook {notebook_id} for user {current_user.id}")
            logger.info(f"✅ Cleanup summary: {cleanup_summary}")
            
            return {
                "message": "Notebook deleted successfully",
                "notebook_id": str(notebook_id),
                "cleanup_summary": cleanup_summary
            }
            
        except Exception as e:
            # Database or other errors - rollback transaction
            await session.rollback()
            logger.error(f"❌ Failed to delete notebook {notebook_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to delete notebook: {e}")
    
    async def _identify_orphaned_sources(
        self, 
        session: AsyncSessionDep, 
        notebook_id: uuid.UUID, 
        owner_id: uuid.UUID
    ) -> List[Source]:
        """
        Identify sources that will become orphaned when the notebook is deleted.
        
        A source becomes orphaned if:
        1. It's currently linked to the notebook being deleted
        2. It's not linked to any other notebooks owned by the same user
        """
        # Get all sources linked to this notebook
        notebook_sources_query = select(NotebookSource).where(
            NotebookSource.notebook_id == notebook_id
        )
        notebook_sources_result = await session.execute(notebook_sources_query)
        notebook_sources = notebook_sources_result.scalars().all()
        
        orphaned_sources = []
        
        for notebook_source in notebook_sources:
            source_id = notebook_source.source_id
            
            # Check if this source is used by any other notebooks owned by the same user
            other_notebooks_query = select(NotebookSource).join(Notebook).where(
                NotebookSource.source_id == source_id,
                NotebookSource.notebook_id != notebook_id,
                Notebook.owner_id == owner_id
            )
            other_notebooks_result = await session.execute(other_notebooks_query)
            other_notebooks = other_notebooks_result.scalars().all()
            
            if not other_notebooks:
                # This source will become orphaned - get the full source object
                source_query = select(Source).where(Source.id == source_id)
                source_result = await session.execute(source_query)
                source = source_result.scalars().first()
                
                if source:
                    orphaned_sources.append(source)
                    logger.info(f"Source {source_id} will become orphaned after notebook deletion")
        
        logger.info(f"Identified {len(orphaned_sources)} orphaned sources for notebook {notebook_id}")
        return orphaned_sources
    
    async def _cleanup_orphaned_sources(
        self, 
        session: AsyncSessionDep, 
        orphaned_sources: List[Source], 
        current_user: CurrentUser
    ) -> Dict[str, Any]:
        """
        Clean up orphaned sources with comprehensive storage deletion.
        """
        cleanup_summary = {
            "total_orphaned": len(orphaned_sources),
            "successfully_deleted": 0,
            "failed_deletions": [],
            "deleted_source_ids": []
        }
        
        for source in orphaned_sources:
            try:
                logger.info(f"Deleting orphaned source {source.id} (title: '{source.title}')")
                
                # Use the comprehensive source deletion service
                result = await self.source_delete_service.delete_source_transactional(
                    session, current_user, source.id
                )
                
                cleanup_summary["successfully_deleted"] += 1
                cleanup_summary["deleted_source_ids"].append(str(source.id))
                logger.info(f"✅ Successfully deleted orphaned source {source.id}")
                
            except Exception as e:
                logger.error(f"❌ Failed to delete orphaned source {source.id}: {e}")
                cleanup_summary["failed_deletions"].append({
                    "source_id": str(source.id),
                    "title": source.title,
                    "error": str(e)
                })
        
        return cleanup_summary


@router.get("/", response_model=NotebooksPublic)
async def list_notebooks(
    session: AsyncSessionDep,
    current_user: CurrentUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> Any:
    """List user's notebooks with pagination and error handling."""
    try:
        count_query = select(func.count()).select_from(Notebook).where(Notebook.owner_id == current_user.id)
        result = await session.execute(count_query)
        count = result.scalar()
        
        query = (
            select(Notebook)
            .where(Notebook.owner_id == current_user.id)
            .offset(skip)
            .limit(limit)
            .order_by(Notebook.updated_at.desc())
        )
        result = await session.execute(query)
        notebooks = result.scalars().all()
        
        # Enrich notebooks with source count
        enriched_notebooks = []
        for notebook in notebooks:
            notebook_with_count = await NotebookService.get_notebook_with_source_count(session, notebook)
            enriched_notebooks.append(notebook_with_count)
        
        logger.info(f"Listed {len(notebooks)} notebooks for user {current_user.id}")
        return NotebooksPublic(data=enriched_notebooks, count=count)
        
    except Exception as e:
        logger.error(f"Error listing notebooks for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to list notebooks")


@router.post("/", response_model=NotebookPublic)
async def create_notebook(
    session: AsyncSessionDep,
    current_user: CurrentUser,
    notebook_in: NotebookCreate,
) -> Any:
    """Create a new notebook with validation and error handling."""
    try:
        # Log incoming request data for debugging
        logger.info(f"Creating notebook for user {current_user.id}")
        logger.info(f"Notebook data: title='{notebook_in.title}', description='{notebook_in.description}'")
        
        # Basic validation
        if not notebook_in.title or not notebook_in.title.strip():
            raise NotebookValidationError("Notebook title is required")
        
        notebook = Notebook(
            title=notebook_in.title.strip(),
            description=notebook_in.description,
            owner_id=current_user.id,
        )
        
        session.add(notebook)
        await session.commit()
        await session.refresh(notebook)
        
        logger.info(f"Created notebook {notebook.id} for user {current_user.id}")
        return notebook
        
    except NotebookValidationError as e:
        logger.warning(f"Notebook validation failed for user {current_user.id}: {e.message}")
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
        logger.error(f"Error creating notebook for user {current_user.id}: {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Exception details: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create notebook")


@router.get("/{notebook_id}", response_model=NotebookPublic)
async def get_notebook(
    session: AsyncSessionDep,
    current_user: CurrentUser,
    notebook_id: uuid.UUID,
) -> Any:
    """Get a specific notebook by ID with ownership verification."""
    try:
        notebook = await NotebookService.get_notebook_with_ownership(session, current_user, notebook_id)
        
        # Enrich notebook with source count
        notebook_with_count = await NotebookService.get_notebook_with_source_count(session, notebook)
        
        logger.info(f"Retrieved notebook {notebook_id} for user {current_user.id}")
        return notebook_with_count
        
    except NotebookNotExistError as e:
        logger.warning(f"Notebook not found: {e.message}")
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        logger.error(f"Error retrieving notebook {notebook_id} for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve notebook")


@router.put("/{notebook_id}", response_model=NotebookPublic)
async def update_notebook(
    session: AsyncSessionDep,
    current_user: CurrentUser,
    notebook_id: uuid.UUID,
    notebook_in: NotebookUpdate,
) -> Any:
    """Update a notebook with ownership verification and validation."""
    try:
        notebook = await NotebookService.get_notebook_with_ownership(session, current_user, notebook_id)
        
        # Update fields if provided
        if notebook_in.title is not None:
            if not notebook_in.title.strip():
                raise NotebookValidationError("Notebook title cannot be empty")
            notebook.title = notebook_in.title.strip()
        if notebook_in.description is not None:
            notebook.description = notebook_in.description
        
        await session.commit()
        await session.refresh(notebook)
        
        logger.info(f"Updated notebook {notebook_id} for user {current_user.id}")
        return notebook
        
    except NotebookNotExistError as e:
        logger.warning(f"Notebook not found for update: {e.message}")
        raise HTTPException(status_code=404, detail=e.message)
    except NotebookValidationError as e:
        logger.warning(f"Notebook validation failed for update: {e.message}")
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"Error updating notebook {notebook_id} for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update notebook")


@router.delete("/{notebook_id}")
async def delete_notebook(
    session: AsyncSessionDep,
    current_user: CurrentUser,
    notebook_id: uuid.UUID,
) -> Any:
    """
    Delete a notebook with comprehensive cleanup including orphaned source handling.
    
    This endpoint now handles:
    - Database deletion with cascade handling
    - Identification of orphaned sources (not used by other notebooks)
    - Comprehensive deletion of orphaned sources (Qdrant + MinIO cleanup)
    - Proper error handling and rollback
    """
    try:
        logger.info(f"DELETE /notebooks/{notebook_id} - Request received from user {current_user.id}")
        
        # Use the new comprehensive deletion service
        delete_service = NotebookDeleteService()
        result = await delete_service.delete_notebook_transactional(session, current_user, notebook_id)
        
        logger.info(f"✅ Comprehensive notebook deletion completed for notebook {notebook_id}")
        return result
        
    except NotebookNotExistError as e:
        logger.warning(f"❌ Notebook not found for deletion: {e.message}")
        raise HTTPException(status_code=404, detail=e.message)
    except HTTPException:
        # Re-raise HTTP exceptions from the service
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error deleting notebook {notebook_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete notebook") 