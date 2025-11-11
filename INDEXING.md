# High-Level Design: File Processing Pipeline with Kafka & Qdrant

## **Architecture Overview**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   MinIO         │
│   (Next.js)     │───▶│   (FastAPI)     │───▶│   (Storage)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   PostgreSQL    │
                       │   (Metadata)    │
                       └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Kafka         │
                       │   (Events)      │
                       └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Indexing      │
                       │   Worker        │
                       └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Qdrant        │
                       │   (Vector DB)   │
                       └─────────────────┘
```

## **1. Infrastructure Components**

### **1.1 New Services to Add**
- **Kafka** (KRaft mode): Event streaming platform
- **Qdrant**: Vector database for embeddings
- **Indexing Worker**: Separate service for CPU-intensive processing
- **Kafka UI**: Monitoring interface

### **1.2 Existing Services**
- **FastAPI Backend**: API endpoints
- **PostgreSQL**: Document metadata storage
- **MinIO**: File storage
- **Next.js Frontend**: User interface

## **2. Data Flow**

### **2.1 Upload Flow**
```
User Upload → FastAPI → MinIO Storage → PostgreSQL Metadata → Kafka Event → Indexing Worker → Qdrant
```

### **2.2 Search Flow**
```
User Query → FastAPI → OpenAI Embedding → Qdrant Search → Results
```

## **3. Event Schema (CDC-Compatible)**

### **3.1 Event Structure**
```json
{
  "op": "c",                    // "c"=create, "u"=update, "d"=delete
  "ts_ms": 1733721624000,       // timestamp in ms
  "document_id": "doc_123",
  "version": 1,
  "metadata": {
    "filename": "invoice.pdf",
    "mime_type": "application/pdf",
    "size": 123456,
    "bucket": "app-docs",
    "object_key": "user_123/invoice.pdf"
  },
  "owner_id": "user_123"
}
```

### **3.2 Kafka Topics**
- `source_changes`: Permanent topic for document events

## **4. Database Schema**

### **4.1 Document Model**
```python
class Document:
    id: UUID (primary key)
    filename: str
    mime_type: str
    size: int
    bucket: str
    object_key: str
    metadata: JSON
    status: enum (pending, processing, indexed, failed)
    version: int
    owner_id: UUID (foreign key to User)
    created_at: datetime
    updated_at: datetime
```

## **5. Service Responsibilities**

### **5.1 FastAPI Backend**
- **File Upload**: Store files in MinIO
- **Metadata Storage**: Save document info to PostgreSQL
- **Event Publishing**: Send events to Kafka after DB commit
- **Search API**: Vector search endpoint
- **Document Management**: CRUD operations

### **5.2 Indexing Worker**
- **Event Consumption**: Read from Kafka topic
- **Text Extraction**: Extract text from various file formats
- **Text Chunking**: Split text into semantic chunks
- **Embedding Generation**: Create vectors using OpenAI
- **Vector Storage**: Store embeddings in Qdrant
- **Status Updates**: Update document processing status

### **5.3 Kafka**
- **Event Streaming**: Reliable message delivery
- **Topic Management**: Persistent storage of events
- **Consumer Groups**: Enable multiple worker instances

### **5.4 Qdrant**
- **Vector Storage**: Store document embeddings
- **Similarity Search**: Fast vector similarity queries
- **Metadata Storage**: Store chunk metadata

## **6. Key Design Principles**

### **6.1 CDC Compatibility**
- Events follow Debezium format
- Stable topic names (`source_changes`)
- Isolated event publishing module
- Future CDC migration without worker changes

### **6.2 Idempotency**
- Workers use UPSERT operations
- Document ID + chunk ID as unique keys
- Handle duplicate events gracefully

### **6.3 CPU Isolation**
- Separate indexing worker container
- Process pool for CPU-intensive tasks
- Resource limits to prevent hogging
- Async processing for I/O operations

### **6.4 Fault Tolerance**
- Event replay capability
- Failed processing doesn't block uploads
- Graceful error handling
- Health checks and monitoring

## **7. Configuration**

### **7.1 Environment Variables**
```bash
# Kafka
KAFKA_BOOTSTRAP_SERVERS=broker:9092
KAFKA_EXTERNAL_BOOTSTRAP_SERVERS=localhost:9094

# Qdrant
QDRANT_HOST=qdrant
QDRANT_PORT=6333

# OpenAI
OPENAI_API_KEY=<key>

# Worker
INDEXING_WORKER_BATCH_SIZE=10
INDEXING_WORKER_POLL_INTERVAL=5
```

### **7.2 Resource Limits**
```yaml
# Indexing Worker
cpus: '2.0'      # Max 2 CPU cores
memory: 2G       # Max 2GB RAM
```

## **8. API Endpoints**

### **8.1 Upload Endpoints**
- `POST /uploads/files`: Upload files with event publishing
- `GET /uploads/documents`: List user documents

### **8.2 Search Endpoints**
- `GET /search/documents`: Vector similarity search

### **8.3 Management Endpoints**
- `GET /health`: Service health check
- `POST /documents/{id}/reindex`: Manual reindexing

## **9. Monitoring & Observability**

### **9.1 Health Checks**
- Kafka connectivity
- Qdrant availability
- Worker processing status
- Database connectivity

### **9.2 Metrics**
- Documents processed per minute
- Embedding generation time
- Search response time
- Error rates

### **9.3 Logging**
- Event publishing logs
- Processing status updates
- Error tracking
- Performance metrics

## **10. Future CDC Migration**

### **10.1 Migration Steps**
1. **Remove Event Publishing**: Delete Kafka publishing from FastAPI
2. **Configure Debezium**: Set up CDC connector for PostgreSQL
3. **Update Topic**: Debezium will populate `source_changes` topic
4. **No Worker Changes**: Workers continue processing same events

### **10.2 Benefits**
- **Consistency**: All database changes captured
- **Reliability**: Database-level event capture
- **Performance**: Reduced application complexity
- **Scalability**: Better event ordering and delivery

This design provides a robust, scalable foundation that can evolve from application-level events to CDC while maintaining the same processing capabilities and search functionality.
