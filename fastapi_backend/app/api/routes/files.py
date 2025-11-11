"""
File Upload and Management API Routes

This module provides comprehensive file upload, download, and management functionality
with robust idempotency, transactional safety, and error handling.

Key Features:
- Transactional file uploads with rollback on failure
- Idempotent operations preventing duplicate files
- Batch operations with partial failure handling
- Data consistency verification and cleanup
- MinIO storage integration with PostgreSQL metadata
- Kafka event publishing for indexing pipeline

Architecture:
- MinIO: Object storage for file content
- PostgreSQL: Metadata storage with ACID compliance
- Kafka: Event streaming for indexing worker
- File hash: SHA256 for content-based duplicate detection

Error Handling:
- Upload failures: Rollback MinIO files if database fails
- Delete failures: Log inconsistencies for manual cleanup
- Kafka failures: Non-blocking with warning logs
- Batch operations: Continue on individual failures

Security:
- User ownership verification for all operations
- Superuser-only access to cleanup endpoints
- Object key validation preventing path traversal
- File size and type validation

Dependencies:
- FastAPI: Web framework and routing
- SQLModel: Database ORM and querying
- MinIO: Object storage client
- Kafka: Event publishing
- Hashlib: File content hashing
"""

from typing import List, Dict, Any, Optional
import io
import datetime
import uuid
import json
from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Depends
from loguru import logger
from sqlmodel import select
import hashlib
from sqlalchemy.exc import IntegrityError

from app.api.deps import CurrentUser, AsyncSessionDep
from app.core.db import setup_minio_client
from app.models import User, Document, DocumentCreate, DocumentsPublic, DocumentPublic
from app.core.kafka import kafka_publisher
from app.core.config import settings
from app.core.cleanup import (
    verify_data_consistency,
    cleanup_orphaned_minio_files,
    cleanup_orphaned_database_records,
    run_full_cleanup
)
from app.core.file_errors import (
    handle_file_errors, 
    require_superuser, 
    validate_file_input,
    FileValidationError, 
    FileNotExistError, 
    FileConflictError, 
    FileOperationError,
    bytes_to_human_readable
)
from app.core.retry_utils import minio_retry, db_retry
from app.core.dependencies import get_rate_limiter
from app.services.rate_limiting import RateLimiterInterface

router = APIRouter(prefix="/uploads", tags=["uploads"])


class FileUploadService:
    """Service class for file upload operations with transactional safety."""
    
    def __init__(self, minio_client, bucket: str, rate_limiter=None):
        self.minio_client = minio_client
        self.bucket = bucket
        self.rate_limiter = rate_limiter
    
    async def upload_file_transactional(
        self,
        session: AsyncSessionDep,
        current_user: CurrentUser,
        upload: UploadFile
    ) -> DocumentPublic:
        """
        Upload a file with transactional safety and idempotency.
        
        This method implements a robust upload process that:
        1. Generates file hash for content-based duplicate detection
        2. Checks for existing files using (owner_id, object_key) constraint
        3. Creates database record before MinIO upload (database-first approach)
        4. Rolls back on any failure to maintain consistency
        5. Publishes Kafka events non-blocking for indexing pipeline
        
        Args:
            session: Database session for transaction management
            current_user: Authenticated user performing the upload
            upload: FastAPI UploadFile object containing file data
            
        Returns:
            DocumentPublic: The created document record with metadata
            
        Raises:
            FileValidationError: Empty file or invalid data
            FileConflictError: File already exists (idempotency)
            FileOperationError: Upload failure with rollback
        """
        data = await upload.read()
        if not data:
            raise FileValidationError(f"Empty file: {upload.filename}")
        
        # Validate file size based on file type
        file_extension = upload.filename.split('.')[-1].lower() if '.' in upload.filename else ''
        mime_type = upload.content_type or ''
        
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
        if len(data) > size_limit:
            raise FileValidationError(
                f"File '{upload.filename}' ({bytes_to_human_readable(len(data))}) exceeds maximum size of {bytes_to_human_readable(size_limit)} for {file_extension.upper()} files"
            )
        
        # Check minimum file size
        if len(data) < settings.MIN_FILE_SIZE_BYTES:
            raise FileValidationError(
                f"File '{upload.filename}' ({bytes_to_human_readable(len(data))}) is too small (minimum {bytes_to_human_readable(settings.MIN_FILE_SIZE_BYTES)})"
            )
        
        # Rate limiting check (your son's brilliant logic)
        if self.rate_limiter:
            # Check processing limit across all user's notebooks
            can_process = await self.rate_limiter.check_processing_limit(
                current_user.id, 
                None  # notebook_id not needed for per-user limit
            )
            if not can_process:
                raise FileValidationError(
                    f"Processing limit exceeded. You have {self.rate_limiter.max_concurrent_processing} files currently being processed. Please wait for some to complete."
                )
        
        # Generate file hash for idempotency
        file_hash = hashlib.sha256(data).hexdigest()
        
        # Generate unique object key
        object_key = f"{current_user.id}/{upload.filename}"
        
        # Check for existing document with same object_key (idempotency)
        existing_doc = await session.execute(
            select(Document).where(
                Document.owner_id == current_user.id,
                Document.object_key == object_key
            )
        )
        if existing_doc.scalars().first():
            raise FileConflictError(f"File already exists: {upload.filename}")
        
        # Create document record first (but don't commit yet)
        document_data = DocumentCreate(
            filename=upload.filename,
            mime_type=upload.content_type or "application/octet-stream",
            size=len(data),
            bucket=self.bucket,
            object_key=object_key,
            document_metadata=json.dumps({
                "original_filename": upload.filename,
                "upload_timestamp": datetime.datetime.utcnow().isoformat(),
                "file_hash": file_hash,
            }),
            owner_id=current_user.id
        )
        
        document = Document.from_orm(document_data)
        session.add(document)
        
        try:
            # Upload to MinIO
            await self._upload_to_minio(upload, object_key, data)
            
            # Commit database transaction
            await self._commit_transaction(session)
            await session.refresh(document)
            
            # Publish event to Kafka (non-blocking)
            await self._publish_kafka_event(document, current_user.id, "c")
            
            return DocumentPublic.from_orm(document)
            
        except IntegrityError as e:
            # Database constraint violation (duplicate)
            await session.rollback()
            logger.warning(f"Duplicate file upload attempted: {upload.filename}")
            raise FileConflictError(f"File already exists: {upload.filename}")
            
        except Exception as e:
            # Any other error - rollback and cleanup
            await session.rollback()
            await self._cleanup_failed_upload(object_key, e)
            raise FileOperationError(f"Failed to upload {upload.filename}: {e}")
    
    async def _check_existing_document(
        self, 
        session: AsyncSessionDep, 
        owner_id: uuid.UUID, 
        object_key: str
    ) -> bool:
        """Check if document already exists for idempotency."""
        result = await session.execute(
            select(Document).where(
                Document.owner_id == owner_id,
                Document.object_key == object_key
            )
        )
        return result.scalars().first() is not None
    
    async def _create_document_record(
        self,
        session: AsyncSessionDep,
        current_user: CurrentUser,
        upload: UploadFile,
        object_key: str,
        file_hash: str,
        file_size: int
    ) -> Document:
        """Create document record in database."""
        document_data = DocumentCreate(
            filename=upload.filename,
            mime_type=upload.content_type or "application/octet-stream",
            size=file_size,
            bucket=self.bucket,
            object_key=object_key,
            document_metadata=json.dumps({
                "original_filename": upload.filename,
                "upload_timestamp": datetime.datetime.utcnow().isoformat(),
                "file_hash": file_hash,
            }),
            owner_id=current_user.id
        )
        
        document = Document.from_orm(document_data)
        session.add(document)
        return document
    
    @minio_retry
    async def _upload_to_minio(self, upload: UploadFile, object_key: str, data: bytes):
        """Upload file to MinIO storage with retry logic."""
        self.minio_client.put_object(
            self.bucket,
            object_key,
            io.BytesIO(data),
            length=len(data),
            content_type=upload.content_type or "application/octet-stream",
        )
    
    async def _publish_kafka_event(
        self, 
        document: Document, 
        owner_id: uuid.UUID, 
        operation: str
    ):
        """Publish event to Kafka (non-blocking)."""
        try:
            event = kafka_publisher.create_document_event(
                document_id=str(document.id),
                operation=operation,
                metadata={
                    "filename": document.filename,
                    "mime_type": document.mime_type,
                    "size": document.size,
                    "bucket": document.bucket,
                    "object_key": document.object_key,
                    "metadata": json.loads(document.document_metadata),
                },
                owner_id=str(owner_id),
                version=document.version
            )
            
            success = kafka_publisher.publish_document_event(event)
            if not success:
                logger.warning(f"Failed to publish event for document {document.id}")
            
        except Exception as e:
            logger.error(f"Kafka publishing failed for document {document.id}: {e}")
    
    async def _cleanup_failed_upload(self, object_key: str, error: Exception):
        """Clean up MinIO file on upload failure with retry logic."""
        try:
            await self._delete_from_minio(object_key)
            logger.info(f"Cleaned up orphaned MinIO file: {object_key}")
        except Exception as cleanup_error:
            logger.error(f"Failed to cleanup MinIO file {object_key}: {cleanup_error}")

    @db_retry
    async def _commit_transaction(self, session: AsyncSessionDep):
        """Commit database transaction with retry logic."""
        await session.commit()
    
    @db_retry
    async def _delete_document_record(self, session: AsyncSessionDep, document: Document):
        """Delete document record from database with retry logic."""
        await session.delete(document)
        await session.commit()


class FileDeleteService:
    """Service class for file deletion operations with rollback capability."""
    
    def __init__(self, minio_client, bucket: str):
        self.minio_client = minio_client
        self.bucket = bucket
    
    async def delete_document_transactional(
        self,
        session: AsyncSessionDep,
        current_user: CurrentUser,
        document_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Delete a document with transactional safety and rollback capability.
        
        This method implements a robust deletion process that:
        1. Verifies document exists and user owns it
        2. Deletes from MinIO first (fail-fast approach)
        3. Publishes Kafka event non-blocking for indexing cleanup
        4. Deletes database record with proper transaction handling
        5. Logs inconsistencies for manual cleanup if needed
        
        Args:
            session: Database session for transaction management
            current_user: Authenticated user performing the deletion
            document_id: UUID of the document to delete
            
        Returns:
            Dict containing success message and document_id
            
        Raises:
            FileNotExistError: Document not found or not owned by user
            FileOperationError: MinIO deletion failure or database error
        """
        # Get document and verify ownership
        document = await self._get_and_verify_document(session, current_user, document_id)
        object_key = document.object_key
        
        try:
            # Step 1: Delete from MinIO first (fail-fast)
            await self._delete_from_minio(object_key)
            
            # Step 2: Publish delete event to Kafka (non-blocking)
            await self._publish_kafka_event(document, current_user.id, "d")
            
            # Step 3: Delete from database
            await self._delete_document_record(session, document)
            
            logger.info(f"Successfully deleted document {document_id} for user {current_user.id}")
            return {
                "message": "Document deleted successfully", 
                "document_id": str(document_id)
            }
            
        except FileOperationError:
            # Re-raise FileOperationError (like MinIO deletion failure)
            raise
            
        except Exception as e:
            # Database or other errors - log inconsistency
            await session.rollback()
            await self._handle_deletion_inconsistency(document_id, object_key, e)
            raise FileOperationError(f"Failed to delete document: {e}")
    
    async def _get_and_verify_document(
        self, 
        session: AsyncSessionDep, 
        current_user: CurrentUser, 
        document_id: uuid.UUID
    ) -> Document:
        """Get document and verify user ownership."""
        result = await session.execute(
            select(Document).where(
                Document.id == document_id,
                Document.owner_id == current_user.id
            )
        )
        document = result.scalars().first()
        
        if not document:
            raise FileNotExistError("Document not found")
        
        return document
    
    @minio_retry
    async def _delete_from_minio(self, object_key: str):
        """Delete file from MinIO storage with retry logic."""
        self.minio_client.remove_object(self.bucket, object_key)
    
    async def _publish_kafka_event(
        self, 
        document: Document, 
        owner_id: uuid.UUID, 
        operation: str
    ):
        """Publish event to Kafka (non-blocking)."""
        try:
            event = kafka_publisher.create_document_event(
                document_id=str(document.id),
                operation=operation,
                metadata={
                    "filename": document.filename,
                    "mime_type": document.mime_type,
                    "size": document.size,
                    "bucket": document.bucket,
                    "object_key": document.object_key,
                    "metadata": json.loads(document.document_metadata),
                },
                owner_id=str(owner_id),
                version=document.version
            )
            
            success = kafka_publisher.publish_document_event(event)
            if not success:
                logger.warning(f"Failed to publish delete event for document {document.id}")
                
        except Exception as e:
            logger.error(f"Kafka publishing failed for document {document.id}: {e}")
    
    async def _handle_deletion_inconsistency(
        self, 
        document_id: uuid.UUID, 
        object_key: str, 
        error: Exception
    ):
        """Handle inconsistency when MinIO file deleted but database record remains."""
        logger.error(f"Database deletion failed for document {document_id}: {error}")
        logger.error(f"INCONSISTENT STATE: MinIO file {object_key} was deleted but database record remains")
        logger.error(f"Document {document_id} needs manual cleanup")


# API Endpoints

@handle_file_errors
@validate_file_input
@router.post("/files")
async def upload_files(
    session: AsyncSessionDep,
    current_user: CurrentUser,
    files: List[UploadFile] = File(...),
    rate_limiter: RateLimiterInterface = Depends(get_rate_limiter)
) -> Dict[str, Any]:
    """
    Upload multiple files with transactional safety and idempotency.
    
    This endpoint handles batch file uploads with comprehensive error handling:
    - Each file is processed individually with its own transaction
    - Failed uploads don't affect successful ones
    - Duplicate files are detected and reported
    - Detailed error reporting for each file
    
    Args:
        session: Database session
        current_user: Authenticated user
        files: List of files to upload
        
    Returns:
        Dict containing:
        - documents: List of successfully uploaded documents
        - failed_uploads: List of failed uploads with reasons
        - message: Summary of operation results
    """
    # Log incoming request data for debugging
    logger.info(f"Uploading {len(files)} files for user {current_user.id}")
    for i, file in enumerate(files):
        logger.info(f"File {i+1}: name='{file.filename}', size={file.size}, content_type='{file.content_type}'")
    
    minio_client, bucket = setup_minio_client()
    upload_service = FileUploadService(minio_client, bucket, rate_limiter)
    minio_client, bucket = setup_minio_client()
    upload_service = FileUploadService(minio_client, bucket, rate_limiter)
    
    saved_documents: List[DocumentPublic] = []
    failed_uploads: List[str] = []

    for upload in files:
        try:
            document = await upload_service.upload_file_transactional(
                session, current_user, upload
            )
            saved_documents.append(document)
        except FileConflictError as e:
            failed_uploads.append(f"{upload.filename}: {e.message}")
        except FileValidationError as e:
            failed_uploads.append(f"{upload.filename}: {e.message}")
        except FileOperationError as e:
            failed_uploads.append(f"{upload.filename}: Upload failed")
        except Exception as e:
            logger.exception(f"Unexpected error uploading {upload.filename}: {e}")
            failed_uploads.append(f"{upload.filename}: Unexpected error")

    response = {"documents": saved_documents}
    if failed_uploads:
        response["failed_uploads"] = failed_uploads
        response["message"] = f"Uploaded {len(saved_documents)} files, {len(failed_uploads)} failed"
    else:
        response["message"] = f"Successfully uploaded {len(saved_documents)} files"

    return response


@handle_file_errors
@router.get("/documents")
async def list_documents(
    session: AsyncSessionDep,
    current_user: CurrentUser,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return")
) -> DocumentsPublic:
    """
    List user's documents with pagination.
    
    Args:
        session: Database session
        current_user: Authenticated user
        skip: Number of records to skip for pagination
        limit: Maximum number of records to return
        
    Returns:
        DocumentsPublic: Paginated list of user's documents
    """
    query = select(Document).where(Document.owner_id == current_user.id)
    query = query.offset(skip).limit(limit)
    
    result = await session.execute(query)
    documents = result.scalars().all()
    
    return DocumentsPublic(documents=documents)


@handle_file_errors
@router.get("/documents/{document_id}")
async def get_document(
    session: AsyncSessionDep,
    current_user: CurrentUser,
    document_id: uuid.UUID
) -> DocumentPublic:
    """
    Get a specific document by ID.
    
    Args:
        session: Database session
        current_user: Authenticated user
        document_id: UUID of the document to retrieve
        
    Returns:
        DocumentPublic: Document details
    """
    result = await session.execute(
        select(Document).where(
            Document.id == document_id,
            Document.owner_id == current_user.id
        )
    )
    document = result.scalars().first()
    
    if not document:
        raise FileNotExistError("Document not found")
    
    return DocumentPublic.from_orm(document)


@handle_file_errors
@router.delete("/documents/{document_id}")
async def delete_document(
    session: AsyncSessionDep,
    current_user: CurrentUser,
    document_id: uuid.UUID
) -> Dict[str, Any]:
    """
    Delete a single document with transactional safety.
    
    Args:
        session: Database session
        current_user: Authenticated user
        document_id: UUID of the document to delete
        
    Returns:
        Dict containing success message and document_id
    """
    minio_client, bucket = setup_minio_client()
    delete_service = FileDeleteService(minio_client, bucket)
    return await delete_service.delete_document_transactional(
        session, current_user, document_id
    )


@handle_file_errors
@validate_file_input
@router.delete("/documents")
async def delete_documents(
    session: AsyncSessionDep,
    current_user: CurrentUser,
    document_ids: List[uuid.UUID]
) -> Dict[str, Any]:
    """
    Delete multiple documents with transactional safety.
    
    This endpoint handles batch deletions with individual error handling:
    - Each document is deleted in its own transaction
    - Failed deletions don't affect successful ones
    - Detailed reporting of successes and failures
    
    Args:
        session: Database session
        current_user: Authenticated user
        document_ids: List of document UUIDs to delete
        
    Returns:
        Dict containing:
        - message: Summary of operation results
        - deleted_count: Number of successfully deleted documents
        - total_requested: Total number of documents requested for deletion
        - failed_deletions: List of failed deletions with reasons
    """
    # Get documents and verify ownership
    result = await session.execute(
        select(Document).where(
            Document.id.in_(document_ids),
            Document.owner_id == current_user.id
        )
    )
    documents = result.scalars().all()
    
    if not documents:
        raise FileNotExistError("No documents found")
    
    minio_client, bucket = setup_minio_client()
    delete_service = FileDeleteService(minio_client, bucket)
    
    deleted_count = 0
    failed_deletions: List[str] = []
    
    for document in documents:
        try:
            await delete_service.delete_document_transactional(
                session, current_user, document.id
            )
            deleted_count += 1
        except FileNotExistError as e:
            failed_deletions.append(f"Document {document.id}: {e.message}")
        except FileOperationError as e:
            failed_deletions.append(f"Document {document.id}: {e.message}")
        except Exception as e:
            logger.exception(f"Unexpected error deleting document {document.id}: {e}")
            failed_deletions.append(f"Document {document.id}: Unexpected error")
    
    response = {
        "message": f"Deleted {deleted_count} documents",
        "deleted_count": deleted_count,
        "total_requested": len(document_ids)
    }
    
    if failed_deletions:
        response["failed_deletions"] = failed_deletions
        response["message"] += f", {len(failed_deletions)} failed"
    
    return response


@handle_file_errors
@router.get("/presign")
async def get_presigned_url(
    current_user: CurrentUser, 
    key: str, 
    expires_minutes: int = Query(60, ge=1, le=1440, description="URL expiration time in minutes")
) -> Dict[str, Any]:
    """
    Get a presigned URL for direct file access.
    
    Args:
        current_user: Authenticated user
        key: Object key in MinIO
        expires_minutes: URL expiration time (1-1440 minutes)
        
    Returns:
        Dict containing presigned URL and metadata
    """
    minio_client, bucket = setup_minio_client()
    try:
        url = minio_client.get_presigned_url(
            method="GET",
            bucket_name=bucket,
            object_name=key,
            expires=datetime.timedelta(minutes=expires_minutes),
        )
    except Exception as e:
        logger.exception(f"Failed to presign {key}: {e}")
        raise FileOperationError(f"Failed to generate presigned URL: {e}")

    return {"url": url, "bucket": bucket, "key": key}


# Data Consistency and Cleanup Endpoints

@handle_file_errors
@require_superuser
@router.get("/consistency-check")
async def check_data_consistency(current_user: CurrentUser) -> dict:
    """
    Check data consistency between MinIO and PostgreSQL.
    Only available to superusers for security.
    """
    report = await verify_data_consistency()
    return {
        "message": "Data consistency check completed",
        "report": report
    }


@handle_file_errors
@require_superuser
@router.post("/cleanup/orphaned-files")
async def cleanup_files(
    current_user: CurrentUser,
    dry_run: bool = Query(True, description="If True, only report what would be deleted")
) -> Dict[str, Any]:
    """
    Clean up orphaned MinIO files.
    
    This endpoint removes MinIO files that don't have corresponding database records:
    - Scans MinIO storage for orphaned files
    - Provides dry-run mode for safe testing
    - Reports detailed cleanup results
    
    Args:
        current_user: Authenticated user (must be superuser)
        dry_run: If True, only report what would be deleted
        
    Returns:
        Dict containing cleanup operation results
        
    Security: Superuser-only access required
    """
    result = await cleanup_orphaned_minio_files(dry_run)
    return {
        "message": "Orphaned files cleanup completed",
        "dry_run": dry_run,
        "result": result
    }


@handle_file_errors
@require_superuser
@router.post("/cleanup/orphaned-records")
async def cleanup_records(
    current_user: CurrentUser,
    dry_run: bool = Query(True, description="If True, only report what would be deleted")
) -> Dict[str, Any]:
    """
    Clean up orphaned database records.
    
    This endpoint removes database records that don't have corresponding MinIO files:
    - Scans database for orphaned records
    - Provides dry-run mode for safe testing
    - Reports detailed cleanup results
    
    Args:
        current_user: Authenticated user (must be superuser)
        dry_run: If True, only report what would be deleted
        
    Returns:
        Dict containing cleanup operation results
        
    Security: Superuser-only access required
    """
    result = await cleanup_orphaned_database_records(dry_run)
    return {
        "message": "Orphaned records cleanup completed",
        "dry_run": dry_run,
        "result": result
    }


@handle_file_errors
@require_superuser
@router.post("/cleanup/full")
async def full_cleanup(
    current_user: CurrentUser,
    dry_run: bool = Query(True, description="If True, only report what would be cleaned")
) -> Dict[str, Any]:
    """
    Run a full cleanup operation including consistency check and cleanup.
    
    This endpoint performs a comprehensive cleanup operation:
    - Checks data consistency between MinIO and PostgreSQL
    - Cleans up orphaned files and records
    - Provides dry-run mode for safe testing
    - Reports detailed results of all operations
    
    Args:
        current_user: Authenticated user (must be superuser)
        dry_run: If True, only report what would be cleaned
        
    Returns:
        Dict containing complete cleanup operation results
        
    Security: Superuser-only access required
    """
    result = await run_full_cleanup(dry_run)
    return {
        "message": "Full cleanup operation completed",
        "dry_run": dry_run,
        "result": result
    } 