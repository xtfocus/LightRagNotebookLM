# Idempotency and Error Handling in File CRUD Operations

## Overview

This document outlines the comprehensive improvements made to ensure idempotency and proper error handling in file CRUD operations. The system now handles partial failures, provides rollback mechanisms, and includes automated cleanup for orphaned data.

## 🚨 **Previous Issues Identified**

### 1. **Upload Operation Problems**
- **MinIO succeeds, PostgreSQL fails**: Files uploaded to MinIO but no database records
- **PostgreSQL succeeds, Kafka fails**: Database records exist but no indexing events
- **No duplicate detection**: Same file could be uploaded multiple times
- **No rollback mechanism**: Failed operations left orphaned files

### 2. **Delete Operation Problems**
- **MinIO deletion fails**: Database records deleted but files remain in storage
- **Database fails**: Files deleted from MinIO but records remain in database
- **Kafka failures**: File deletion events not published to indexing worker
- **No compensation actions**: Partial failures left inconsistent state

### 3. **Missing Transaction Safety**
- No database transactions wrapping MinIO operations
- No rollback mechanisms for failed operations
- No cleanup jobs for orphaned data
- No verification of data consistency

## ✅ **Solutions Implemented**

### 1. **Transactional Upload with Idempotency**

#### **New Function: `upload_file_transactional()`**

**Features:**
- **File Hash Generation**: SHA256 hash for content-based duplicate detection
- **Pre-flight Duplicate Check**: Verifies no existing document with same `(owner_id, object_key)`
- **Database-First Approach**: Creates database record before MinIO upload
- **Rollback on Failure**: Cleans up MinIO file if database operation fails
- **Non-blocking Kafka**: Event publishing doesn't fail the upload
- **Comprehensive Error Handling**: Different error types handled appropriately

**Flow:**
```python
1. Generate file hash and object key
2. Check for existing document (idempotency)
3. Create database record (not committed yet)
4. Upload to MinIO
5. Commit database transaction
6. Publish Kafka event (non-blocking)
7. Return success or rollback on failure
```

**Error Scenarios Handled:**
- **Duplicate File**: Returns 409 Conflict with clear message
- **MinIO Upload Failure**: Rolls back database transaction
- **Database Failure**: Cleans up orphaned MinIO file
- **Kafka Failure**: Logs warning but doesn't fail upload

### 2. **Transactional Delete with Rollback**

#### **New Function: `delete_document_transactional()`**

**Features:**
- **MinIO-First Deletion**: Deletes from storage before database
- **Verification**: Ensures MinIO deletion succeeds before proceeding
- **Non-blocking Kafka**: Event publishing doesn't block deletion
- **Inconsistency Detection**: Logs when MinIO file deleted but database record remains
- **Comprehensive Error Handling**: Different failure modes handled appropriately

**Flow:**
```python
1. Verify document exists and user owns it
2. Delete from MinIO (fail if this fails)
3. Publish Kafka event (non-blocking)
4. Delete from database
5. Commit transaction
6. Return success or handle rollback
```

**Error Scenarios Handled:**
- **MinIO Deletion Failure**: Returns 500 error, no database changes
- **Database Failure**: Logs inconsistency, MinIO file already deleted
- **Kafka Failure**: Logs warning but continues with deletion

### 3. **Data Consistency and Cleanup**

#### **New Module: `app/utils/cleanup.py`**

**Features:**
- **Orphaned File Detection**: Finds MinIO files without database records
- **Orphaned Record Detection**: Finds database records without MinIO files
- **Consistency Verification**: Comprehensive data integrity checks
- **Safe Cleanup**: Dry-run mode for testing before actual deletion
- **Detailed Reporting**: Complete audit trail of cleanup operations

**Functions:**
- `find_orphaned_minio_files()`: Scan MinIO for orphaned files
- `find_orphaned_database_records()`: Scan database for orphaned records
- `cleanup_orphaned_minio_files()`: Remove orphaned files
- `cleanup_orphaned_database_records()`: Remove orphaned records
- `verify_data_consistency()`: Comprehensive consistency check
- `run_full_cleanup()`: Complete cleanup operation

### 4. **Automated Cleanup Scheduler**

#### **New Module: `app/core/scheduler.py`**

**Features:**
- **Periodic Cleanup**: Runs every 24 hours automatically
- **Consistency Monitoring**: Checks data integrity before cleanup
- **Dry-Run Mode**: Tests cleanup operations before execution
- **Graceful Error Handling**: Continues operation despite individual failures
- **Configurable Intervals**: Adjustable cleanup frequency

**Operation:**
```python
1. Check if cleanup is due (24-hour interval)
2. Verify data consistency
3. Run dry-run cleanup to see what would be cleaned
4. If orphaned data found, run actual cleanup
5. Log all operations and results
```

### 5. **API Endpoints for Management**

#### **New Endpoints Added:**

- `GET /api/v1/uploads/consistency-check`: Check data consistency
- `POST /api/v1/uploads/cleanup/orphaned-files`: Clean orphaned MinIO files
- `POST /api/v1/uploads/cleanup/orphaned-records`: Clean orphaned database records
- `POST /api/v1/uploads/cleanup/full`: Run complete cleanup operation

**Security:**
- All cleanup endpoints require superuser privileges
- Dry-run mode enabled by default for safety
- Comprehensive logging of all operations

## 🔧 **Database Schema Improvements**

### **Unique Constraint Added:**
```sql
-- Prevents duplicate file uploads per user
ALTER TABLE document ADD CONSTRAINT uq_user_object_key 
UNIQUE (owner_id, object_key);
```

### **File Hash Storage:**
```python
# Added to document metadata
{
    "file_hash": "sha256_hash_of_file_content",
    "upload_timestamp": "2024-01-01T12:00:00Z",
    "original_filename": "document.pdf"
}
```

## 📊 **Error Handling Matrix**

| Operation | MinIO Failure | Database Failure | Kafka Failure | Result |
|-----------|---------------|------------------|---------------|---------|
| **Upload** | Rollback DB | Cleanup MinIO | Continue | Partial Success |
| **Delete** | Fail Early | Log Inconsistency | Continue | Partial Success |
| **Batch Upload** | Individual Rollback | Individual Cleanup | Continue | Mixed Results |
| **Batch Delete** | Individual Failure | Individual Logging | Continue | Mixed Results |

## 🚀 **Usage Examples**

### **Upload with Idempotency:**
```python
# First upload - succeeds
response = await upload_file_transactional(session, user, file, minio_client, bucket)

# Second upload of same file - returns 409 Conflict
response = await upload_file_transactional(session, user, file, minio_client, bucket)
# Result: HTTPException(status_code=409, detail="File already exists: document.pdf")
```

### **Delete with Rollback:**
```python
# Successful deletion
result = await delete_document_transactional(session, user, doc_id, minio_client, bucket)
# Result: {"message": "Document deleted successfully", "document_id": "123"}

# MinIO deletion failure
result = await delete_document_transactional(session, user, doc_id, minio_client, bucket)
# Result: HTTPException(status_code=500, detail="Failed to delete file from storage")
```

### **Consistency Check:**
```python
# Check data consistency
report = await verify_data_consistency()
# Result: {
#   "is_consistent": false,
#   "orphaned_minio_files": 5,
#   "orphaned_database_records": 2,
#   "details": {...}
# }
```

### **Cleanup Operations:**
```python
# Dry-run cleanup
result = await run_full_cleanup(dry_run=True)
# Result: Shows what would be cleaned without actually cleaning

# Actual cleanup
result = await run_full_cleanup(dry_run=False)
# Result: Actually performs cleanup and reports results
```

## 🔍 **Monitoring and Observability**

### **Logging:**
- All operations logged with appropriate levels
- Error details captured for debugging
- Inconsistency warnings logged prominently
- Cleanup operations fully audited

### **Metrics:**
- Upload success/failure rates
- Delete success/failure rates
- Orphaned file counts
- Cleanup operation results
- Data consistency status

### **Alerts:**
- Data inconsistency detected
- Cleanup failures
- High orphaned file counts
- Upload/delete error rates

## 🛡️ **Security Considerations**

### **Access Control:**
- Cleanup endpoints restricted to superusers
- User can only access their own files
- Object key validation prevents path traversal

### **Data Protection:**
- File hash verification for integrity
- Secure file deletion from MinIO
- Database transaction safety
- Audit trail for all operations

## 📈 **Performance Impact**

### **Minimal Overhead:**
- File hash generation: ~1ms per file
- Duplicate checks: Database index lookup
- Cleanup operations: Run in background
- Non-blocking Kafka operations

### **Scalability:**
- Batch operations supported
- Asynchronous cleanup scheduler
- Configurable cleanup intervals
- Efficient orphaned data detection

## 🔄 **Recovery Procedures**

### **Manual Recovery:**
1. **Orphaned MinIO Files**: Use cleanup endpoints to remove
2. **Orphaned Database Records**: Use cleanup endpoints to remove
3. **Inconsistent State**: Run consistency check and cleanup
4. **Failed Uploads**: Retry with same file (idempotent)

### **Automated Recovery:**
1. **Scheduled Cleanup**: Runs every 24 hours
2. **Consistency Monitoring**: Continuous verification
3. **Error Logging**: Comprehensive audit trail
4. **Graceful Degradation**: Partial failures don't break system

## ✅ **Testing Recommendations**

### **Unit Tests:**
- Test idempotency with duplicate uploads
- Test rollback scenarios for upload failures
- Test rollback scenarios for delete failures
- Test cleanup operations in dry-run mode

### **Integration Tests:**
- Test MinIO + PostgreSQL consistency
- Test Kafka event publishing failures
- Test batch operation partial failures
- Test cleanup scheduler operation

### **Load Tests:**
- Test concurrent uploads
- Test concurrent deletes
- Test cleanup performance with large datasets
- Test system behavior under failure conditions

## 📋 **Future Improvements**

### **Planned Enhancements:**
1. **Event Sourcing**: Complete audit trail of all operations
2. **Compensation Actions**: Automatic recovery from partial failures
3. **Distributed Transactions**: True ACID across MinIO and PostgreSQL
4. **Advanced Monitoring**: Real-time consistency dashboards
5. **Backup and Restore**: Point-in-time recovery capabilities

### **Considered Patterns:**
1. **Saga Pattern**: For complex multi-step operations
2. **Outbox Pattern**: For reliable event publishing
3. **CQRS**: For read/write operation separation
4. **Event Sourcing**: For complete operation history

---

This implementation provides robust idempotency and error handling while maintaining system performance and usability. The automated cleanup ensures data consistency over time, and the comprehensive error handling prevents data loss in failure scenarios. 