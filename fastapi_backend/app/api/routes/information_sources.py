"""
Source Management API Routes

This module provides comprehensive source management functionality with robust
error handling, validation, and transactional safety.

Key Features:
- Create sources of different types (document, URL, video, image, text)
- List user sources with filtering by type
- Update source metadata and descriptions
- Delete sources (with cascade handling)
- Source validation and type-specific processing
- Comprehensive error handling and logging

Architecture:
- PostgreSQL: Source metadata storage with ACID compliance
- User ownership verification for all operations
- Input validation and type-specific requirements
- Cascade delete handling for related records

Error Handling:
- Source validation errors with detailed messages
- Ownership verification for all operations
- Duplicate detection and conflict handling
- Comprehensive logging for debugging

Security:
- User ownership verification for all operations
- Input validation preventing invalid data
- Type-specific metadata validation
"""

import uuid
import json
from typing import Any, List, Optional, Dict

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlmodel import col, delete, func, select
from loguru import logger
from pydantic import ValidationError

from app.api.deps import CurrentUser, AsyncSessionDep
from app.models import (
    Source,
    SourceCreate,
    SourcePublic,
    SourcesPublic,
    SourceUpdate,
    SourceType,
    ProcessingStatus,
    Document,
)
from app.models import NotebookSource
from app.core.kafka import kafka_publisher
from app.core.qdrant import QdrantManager
from app.core.db import setup_minio_client
from app.api.routes.files import FileDeleteService

router = APIRouter(prefix="/sources", tags=["sources"])


class SourceValidationError(Exception):
    """Raised when source validation fails."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class SourceNotExistError(Exception):
    """Raised when source is not found."""
    def __init__(self, message: str = "Source not found"):
        self.message = message
        super().__init__(self.message)


class SourceConflictError(Exception):
    """Raised when there's a conflict in source operations."""
    def __init__(self, message: str = "Source operation conflict"):
        self.message = message
        super().__init__(self.message)


class SourceService:
    """Service class for source operations with validation and error handling."""
    
    @staticmethod
    def validate_source_metadata(source_type: SourceType, metadata: Dict[str, Any]) -> None:
        """
        Validate source metadata based on source type.
        
        Args:
            source_type: Type of source being created
            metadata: Source metadata to validate
            
        Raises:
            SourceValidationError: If validation fails
        """
        if source_type == SourceType.DOCUMENT:
            if "document_id" not in metadata:
                raise SourceValidationError("Document sources must include document_id in metadata")
        
        elif source_type == SourceType.URL:
            if "url" not in metadata:
                raise SourceValidationError("URL sources must include url in metadata")
        
        elif source_type == SourceType.TEXT:
            if "content" not in metadata:
                raise SourceValidationError("Text sources must include content in metadata")
    
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
            SourceNotExistError: If source not found or not owned by user
        """
        logger.info(f"🔍 Verifying ownership for source {source_id} - user {current_user.id}")
        
        result = await session.execute(
            select(Source).where(
                Source.id == source_id,
                Source.owner_id == current_user.id
            )
        )
        source = result.scalars().first()
        
        if not source:
            logger.warning(f"❌ Source {source_id} not found or access denied for user {current_user.id}")
            raise SourceNotExistError(f"Source {source_id} not found or access denied")
        
        logger.info(f"✅ Ownership verified for source {source_id} - user {current_user.id}")
        return source
    
    @staticmethod
    async def get_source_with_notebook_count(
        session: AsyncSessionDep,
        source: Source
    ) -> Dict[str, Any]:
        """
        Get source data with notebook count for API responses.
        
        Args:
            session: Database session
            source: Source object to enrich with notebook count
            
        Returns:
            Dictionary containing source data with notebook count
        """
        # Count notebooks linked to this source
        notebook_count_query = select(func.count(NotebookSource.id)).where(
            NotebookSource.source_id == source.id
        )
        result = await session.execute(notebook_count_query)
        notebook_count = result.scalar() or 0
        
        # Convert source to dict and add notebook count
        source_dict = {
            "id": source.id,
            "title": source.title,
            "description": source.description,
            "source_type": source.source_type,
            "source_metadata": source.source_metadata,
            "status": source.status,
            "owner_id": source.owner_id,
            "created_at": source.created_at,
            "updated_at": source.updated_at,
            "notebook_count": notebook_count
        }
        
        return source_dict


class SourceDeleteService:
    """Service class for comprehensive source deletion with storage cleanup."""
    
    def __init__(self):
        self.qdrant_manager = QdrantManager()
        minio_client, bucket = setup_minio_client()
        self.file_delete_service = FileDeleteService(minio_client, bucket)
    
    async def delete_source_transactional(
        self,
        session: AsyncSessionDep,
        current_user: CurrentUser,
        source_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Delete a source with comprehensive cleanup including storage.
        
        This method implements a robust deletion process that:
        1. Verifies source exists and user owns it
        2. Handles storage cleanup based on source type
        3. Deletes from Qdrant for document sources
        4. Deletes from MinIO for document sources
        5. Deletes database record with proper transaction handling
        
        Args:
            session: Database session for transaction management
            current_user: Authenticated user performing the deletion
            source_id: UUID of the source to delete
            
        Returns:
            Dict containing success message and source_id
            
        Raises:
            SourceNotExistError: Source not found or not owned by user
            HTTPException: Storage deletion failure or database error
        """
        # Get source and verify ownership
        source = await SourceService.get_source_with_ownership(session, current_user, source_id)
        
        logger.info(f"Starting comprehensive deletion for source {source_id}")
        logger.info(f"Source details: title='{source.title}', type='{source.source_type}', metadata={source.source_metadata}")
        
        try:
            # Handle storage cleanup based on source type
            await self._cleanup_source_storage(source, current_user)
            
            # Delete source (cascade will handle related records)
            await session.delete(source)
            await session.commit()
            
            logger.info(f"✅ Successfully deleted source {source_id} for user {current_user.id}")
            return {
                "message": "Source deleted successfully", 
                "source_id": str(source_id)
            }
            
        except Exception as e:
            # Database or other errors - rollback transaction
            await session.rollback()
            logger.error(f"❌ Failed to delete source {source_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to delete source: {e}")
    
    async def _cleanup_source_storage(self, source: Source, current_user: CurrentUser):
        """Clean up storage resources based on source type."""
        if source.source_type == SourceType.DOCUMENT:
            await self._cleanup_document_source_storage(source, current_user)
        elif source.source_type == SourceType.URL:
            await self._cleanup_url_source_storage(source)
        # TEXT, VIDEO, IMAGE sources don't require storage cleanup
    
    async def _cleanup_document_source_storage(self, source: Source, current_user: CurrentUser):
        """Clean up storage for document-type sources."""
        try:
            # Extract document_id from source metadata
            document_id_str = source.source_metadata.get("document_id")
            if not document_id_str:
                logger.warning(f"No document_id found in source metadata for source {source.id}")
                return
            
            document_id = uuid.UUID(document_id_str)
            logger.info(f"Cleaning up storage for document {document_id}")
            
            # Step 1: Delete from Qdrant
            qdrant_success = self.qdrant_manager.delete_document_chunks(str(document_id))
            if qdrant_success:
                logger.info(f"✅ Successfully deleted Qdrant chunks for document {document_id}")
            else:
                logger.warning(f"⚠️ Failed to delete Qdrant chunks for document {document_id}")
            
            # Step 2: Delete from MinIO using existing FileDeleteService
            # We need to get the document record to access object_key
            from app.api.deps import get_session
            async with get_session() as doc_session:
                result = await doc_session.execute(
                    select(Document).where(
                        Document.id == document_id,
                        Document.owner_id == current_user.id
                    )
                )
                document = result.scalars().first()
                
                if document:
                    # Use FileDeleteService to handle MinIO cleanup
                    minio_success = await self._delete_from_minio_safe(document.object_key)
                    if minio_success:
                        logger.info(f"✅ Successfully deleted MinIO file for document {document_id}")
                    else:
                        logger.warning(f"⚠️ Failed to delete MinIO file for document {document_id}")
                else:
                    logger.warning(f"Document {document_id} not found for MinIO cleanup")
                    
        except Exception as e:
            logger.error(f"❌ Error during document source storage cleanup: {e}")
            # Don't raise - we want to continue with database deletion even if storage cleanup fails
    
    async def _cleanup_url_source_storage(self, source: Source):
        """Clean up storage for URL-type sources."""
        try:
            # For URL sources, we need to delete from Qdrant using source_id
            # URL content is stored with source_id as the document_id in Qdrant
            qdrant_success = self.qdrant_manager.delete_document_chunks(str(source.id))
            if qdrant_success:
                logger.info(f"✅ Successfully deleted Qdrant chunks for URL source {source.id}")
            else:
                logger.warning(f"⚠️ Failed to delete Qdrant chunks for URL source {source.id}")
                
        except Exception as e:
            logger.error(f"❌ Error during URL source storage cleanup: {e}")
            # Don't raise - we want to continue with database deletion even if storage cleanup fails
    
    async def _delete_from_minio_safe(self, object_key: str) -> bool:
        """Safely delete from MinIO with error handling."""
        try:
            minio_client, bucket = setup_minio_client()
            minio_client.remove_object(bucket, object_key)
            return True
        except Exception as e:
            logger.error(f"Failed to delete MinIO object {object_key}: {e}")
            return False


@router.get("/", response_model=SourcesPublic)
async def list_sources(
    session: AsyncSessionDep,
    current_user: CurrentUser,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    source_type: Optional[SourceType] = Query(None, description="Filter by source type"),
) -> Any:
    """
    List user's sources with optional filtering by type.
    Includes notebook count for each source to show usage impact.
    """
    try:
        # Build query with filters
        query = select(Source).where(Source.owner_id == current_user.id)
        
        if source_type:
            query = query.where(Source.source_type == source_type)
        
        # Get count
        count_query = select(func.count()).select_from(query.subquery())
        result = await session.execute(count_query)
        count = result.scalar()
        
        # Get paginated results
        query = query.offset(skip).limit(limit).order_by(Source.created_at.desc())
        result = await session.execute(query)
        sources = result.scalars().all()
        
        # Enrich sources with notebook count
        enriched_sources = []
        for source in sources:
            source_with_count = await SourceService.get_source_with_notebook_count(session, source)
            enriched_sources.append(source_with_count)
        
        logger.info(f"Listed {len(sources)} sources for user {current_user.id}")
        return SourcesPublic(data=enriched_sources, count=count)
        
    except Exception as e:
        logger.error(f"Error listing sources for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to list sources")


@router.post("/", response_model=SourcePublic)
async def create_source(
    session: AsyncSessionDep,
    current_user: CurrentUser,
    source_in: SourceCreate,
) -> Any:
    """
    Create a new source with validation and error handling.
    """
    try:
        # Log incoming request data for debugging
        logger.info(f"Creating source for user {current_user.id}")
        logger.info(f"Source data: title='{source_in.title}', type='{source_in.source_type}', metadata={source_in.source_metadata}")
        
        # Validate source metadata
        SourceService.validate_source_metadata(source_in.source_type, source_in.source_metadata)
        
        # Create source
        source = Source(
            title=source_in.title,
            description=source_in.description,
            source_type=source_in.source_type,
            source_metadata=source_in.source_metadata,
            status=ProcessingStatus.PENDING,  # Set initial status
            owner_id=current_user.id,
        )
        
        session.add(source)
        await session.commit()
        await session.refresh(source)
        
        # Publish Kafka event for URL sources to trigger processing
        if source.source_type == SourceType.URL:
            logger.info(f"Attempting to publish Kafka event for URL source {source.id}")
            logger.debug(f"Source metadata: {source.source_metadata}")
            
            try:
                event = kafka_publisher.create_url_source_event(
                    source_id=str(source.id),
                    operation="c",  # Create operation
                    metadata=source.source_metadata,
                    owner_id=str(current_user.id),
                    version=1
                )
                
                logger.debug(f"Created URL source event: {event.model_dump()}")
                
                success = kafka_publisher.publish_url_source_event(event)
                if success:
                    logger.info(f"✅ Successfully published URL source event for source {source.id}")
                else:
                    logger.warning(f"❌ Failed to publish URL source event for source {source.id}")
                    
            except Exception as e:
                logger.error(f"❌ Error publishing URL source event for source {source.id}: {e}")
                logger.error(f"Exception type: {type(e).__name__}")
                # Don't fail the source creation if event publishing fails
                # The source is still created and can be processed later
        
        logger.info(f"Created source {source.id} of type {source.source_type} for user {current_user.id}")
        return source
        
    except SourceValidationError as e:
        logger.warning(f"Source validation failed for user {current_user.id}: {e.message}")
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
        logger.error(f"Error creating source for user {current_user.id}: {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Exception details: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create source")


@router.get("/{source_id}", response_model=SourcePublic)
async def get_source(
    session: AsyncSessionDep,
    current_user: CurrentUser,
    source_id: uuid.UUID,
) -> Any:
    """
    Get a specific source by ID with ownership verification.
    Includes notebook count to show usage impact.
    """
    try:
        source = await SourceService.get_source_with_ownership(session, current_user, source_id)
        
        # Enrich source with notebook count
        source_with_count = await SourceService.get_source_with_notebook_count(session, source)
        
        logger.info(f"Retrieved source {source_id} for user {current_user.id}")
        return source_with_count
        
    except SourceNotExistError as e:
        logger.warning(f"Source not found: {e.message}")
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        logger.error(f"Error retrieving source {source_id} for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve source")


@router.put("/{source_id}", response_model=SourcePublic)
async def update_source(
    session: AsyncSessionDep,
    current_user: CurrentUser,
    source_id: uuid.UUID,
    source_in: SourceUpdate,
) -> Any:
    """
    Update a source with ownership verification and validation.
    """
    try:
        source = await SourceService.get_source_with_ownership(session, current_user, source_id)
        
        # Update fields if provided
        if source_in.title is not None:
            source.title = source_in.title
        if source_in.description is not None:
            source.description = source_in.description
        if source_in.source_metadata is not None:
            # Validate metadata if source type is known
            if source.source_type:
                SourceService.validate_source_metadata(source.source_type, source_in.source_metadata)
            source.source_metadata = source_in.source_metadata
        
        await session.commit()
        await session.refresh(source)
        
        logger.info(f"Updated source {source_id} for user {current_user.id}")
        return source
        
    except SourceNotExistError as e:
        logger.warning(f"Source not found for update: {e.message}")
        raise HTTPException(status_code=404, detail=e.message)
    except SourceValidationError as e:
        logger.warning(f"Source validation failed for update: {e.message}")
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"Error updating source {source_id} for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update source")


@router.delete("/{source_id}")
async def delete_source(
    session: AsyncSessionDep,
    current_user: CurrentUser,
    source_id: uuid.UUID,
) -> Any:
    """
    Delete a source with comprehensive cleanup including storage.
    
    This endpoint now handles:
    - Database deletion with cascade handling
    - Qdrant cleanup for document and URL sources
    - MinIO cleanup for document sources
    - Proper error handling and rollback
    """
    try:
        logger.info(f"DELETE /sources/{source_id} - Request received from user {current_user.id}")
        
        # Use the new comprehensive deletion service
        delete_service = SourceDeleteService()
        result = await delete_service.delete_source_transactional(session, current_user, source_id)
        
        logger.info(f"✅ Comprehensive source deletion completed for source {source_id}")
        return result
        
    except SourceNotExistError as e:
        logger.warning(f"❌ Source not found for deletion: {e.message}")
        raise HTTPException(status_code=404, detail=e.message)
    except HTTPException:
        # Re-raise HTTP exceptions from the service
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error deleting source {source_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete source") 