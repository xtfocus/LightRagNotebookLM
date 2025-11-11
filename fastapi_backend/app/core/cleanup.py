"""
Cleanup utilities for handling orphaned files and data consistency.
"""
import asyncio
from typing import List, Dict, Any, Tuple
from sqlmodel import select
from loguru import logger
from minio.error import S3Error
import uuid
from minio import Minio
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import setup_minio_client, async_session_maker
from app.models import Document, User
from app.core.retry_utils import minio_retry, db_retry


async def find_orphaned_minio_files() -> List[Dict[str, Any]]:
    """
    Find files in MinIO that don't have corresponding database records.
    
    Returns:
        List of orphaned file information
    """
    minio_client, bucket = setup_minio_client()
    orphaned_files = []
    
    try:
        # Get all objects in MinIO
        objects = minio_client.list_objects(bucket, recursive=True)
        
        async with async_session_maker() as session:
            for obj in objects:
                object_key = obj.object_name
                
                # Check if database record exists
                result = await session.execute(
                    select(Document).where(Document.object_key == object_key)
                )
                document = result.scalars().first()
                
                if not document:
                    orphaned_files.append({
                        "object_key": object_key,
                        "size": obj.size,
                        "last_modified": obj.last_modified,
                        "bucket": bucket
                    })
                    logger.warning(f"Found orphaned MinIO file: {object_key}")
    
    except Exception as e:
        logger.error(f"Error scanning for orphaned MinIO files: {e}")
    
    return orphaned_files


async def find_orphaned_database_records() -> List[Dict[str, Any]]:
    """
    Find database records that don't have corresponding MinIO files.
    
    Returns:
        List of orphaned database records
    """
    minio_client, bucket = setup_minio_client()
    orphaned_records = []
    
    try:
        async with async_session_maker() as session:
            # Get all documents from database
            result = await session.execute(select(Document))
            documents = result.scalars().all()
            
            for document in documents:
                try:
                    # Check if MinIO file exists
                    minio_client.stat_object(bucket, document.object_key)
                except S3Error as e:
                    if e.code == "NoSuchKey":
                        orphaned_records.append({
                            "document_id": str(document.id),
                            "object_key": document.object_key,
                            "filename": document.filename,
                            "owner_id": str(document.owner_id),
                            "created_at": document.created_at.isoformat()
                        })
                        logger.warning(f"Found orphaned database record: {document.id} -> {document.object_key}")
                    else:
                        logger.error(f"Error checking MinIO file {document.object_key}: {e}")
    
    except Exception as e:
        logger.error(f"Error scanning for orphaned database records: {e}")
    
    return orphaned_records


@minio_retry
async def _remove_minio_object(minio_client: Minio, bucket: str, object_key: str):
    """Remove object from MinIO with retry logic."""
    minio_client.remove_object(bucket, object_key)


async def cleanup_orphaned_minio_files(dry_run: bool = True) -> Dict[str, Any]:
    """
    Clean up orphaned MinIO files.
    
    Args:
        dry_run: If True, only report what would be deleted without actually deleting
        
    Returns:
        Summary of cleanup operation
    """
    orphaned_files = await find_orphaned_minio_files()
    
    if not orphaned_files:
        return {
            "message": "No orphaned MinIO files found",
            "deleted_count": 0,
            "total_size": 0
        }
    
    if dry_run:
        total_size = sum(f["size"] for f in orphaned_files)
        return {
            "message": f"Would delete {len(orphaned_files)} orphaned files",
            "deleted_count": 0,
            "total_size": total_size,
            "orphaned_files": orphaned_files
        }
    
    # Actually delete the files
    minio_client, bucket = setup_minio_client()
    deleted_count = 0
    total_size = 0
    failed_deletions = []
    
    for file_info in orphaned_files:
        try:
            await _remove_minio_object(minio_client, bucket, file_info["object_key"])
            deleted_count += 1
            total_size += file_info["size"]
            logger.info(f"Deleted orphaned file: {file_info['object_key']}")
        except Exception as e:
            failed_deletions.append({
                "object_key": file_info["object_key"],
                "error": str(e)
            })
            logger.error(f"Failed to delete orphaned file {file_info['object_key']}: {e}")
    
    return {
        "message": f"Deleted {deleted_count} orphaned files",
        "deleted_count": deleted_count,
        "total_size": total_size,
        "failed_deletions": failed_deletions
    }


@db_retry
async def _commit_cleanup_transaction(session: AsyncSession):
    """Commit cleanup transaction with retry logic."""
    await session.commit()

@db_retry
async def _delete_document_record(session: AsyncSession, document: Document):
    """Delete document record with retry logic."""
    await session.delete(document)
    await session.commit()


async def cleanup_orphaned_database_records(dry_run: bool = True) -> Dict[str, Any]:
    """
    Clean up orphaned database records.
    
    Args:
        dry_run: If True, only report what would be deleted without actually deleting
        
    Returns:
        Summary of cleanup operation
    """
    orphaned_records = await find_orphaned_database_records()
    
    if not orphaned_records:
        return {
            "message": "No orphaned database records found",
            "deleted_count": 0
        }
    
    if dry_run:
        return {
            "message": f"Would delete {len(orphaned_records)} orphaned records",
            "deleted_count": 0,
            "orphaned_records": orphaned_records
        }
    
    # Actually delete the records
    async with async_session_maker() as session:
        deleted_count = 0
        failed_deletions = []
        
        for record_info in orphaned_records:
            try:
                # Convert string document_id to UUID
                document_uuid = uuid.UUID(record_info["document_id"])
                
                result = await session.execute(
                    select(Document).where(Document.id == document_uuid)
                )
                document = result.scalars().first()
                
                if document:
                    await _delete_document_record(session, document)
                    deleted_count += 1
                    logger.info(f"Deleted orphaned database record: {record_info['document_id']}")
                
            except ValueError as e:
                failed_deletions.append({
                    "document_id": record_info["document_id"],
                    "error": f"Invalid UUID format: {e}"
                })
                logger.error(f"Invalid UUID format for document {record_info['document_id']}: {e}")
            except Exception as e:
                failed_deletions.append({
                    "document_id": record_info["document_id"],
                    "error": str(e)
                })
                logger.error(f"Failed to delete orphaned record {record_info['document_id']}: {e}")
        
        await _commit_cleanup_transaction(session)
    
    return {
        "message": f"Deleted {deleted_count} orphaned records",
        "deleted_count": deleted_count,
        "failed_deletions": failed_deletions
    }


async def verify_data_consistency() -> Dict[str, Any]:
    """
    Verify data consistency between MinIO and PostgreSQL.
    
    Returns:
        Consistency report
    """
    orphaned_files = await find_orphaned_minio_files()
    orphaned_records = await find_orphaned_database_records()
    
    total_files = len(orphaned_files)
    total_records = len(orphaned_records)
    
    is_consistent = total_files == 0 and total_records == 0
    
    return {
        "is_consistent": is_consistent,
        "orphaned_minio_files": total_files,
        "orphaned_database_records": total_records,
        "details": {
            "orphaned_files": orphaned_files,
            "orphaned_records": orphaned_records
        }
    }


async def run_full_cleanup(dry_run: bool = True) -> Dict[str, Any]:
    """
    Run a full cleanup operation.
    
    Args:
        dry_run: If True, only report what would be cleaned without actually cleaning
        
    Returns:
        Complete cleanup report
    """
    logger.info(f"Starting full cleanup (dry_run={dry_run})")
    
    # Verify consistency first
    consistency_report = await verify_data_consistency()
    
    # Clean up orphaned files
    minio_cleanup = await cleanup_orphaned_minio_files(dry_run)
    
    # Clean up orphaned records
    db_cleanup = await cleanup_orphaned_database_records(dry_run)
    
    return {
        "consistency_report": consistency_report,
        "minio_cleanup": minio_cleanup,
        "database_cleanup": db_cleanup,
        "dry_run": dry_run
    } 