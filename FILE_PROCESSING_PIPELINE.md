# File Processing Pipeline with Kafka & Qdrant

This document describes the implementation of a robust file processing pipeline that uses Kafka for event streaming and Qdrant for vector search capabilities.

## Architecture Overview

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

## Services

### New Services Added

1. **Kafka** (KRaft mode): Event streaming platform
2. **Qdrant**: Vector database for embeddings
3. **Indexing Worker**: Separate service for CPU-intensive processing
4. **Kafka UI**: Monitoring interface

### Existing Services Enhanced

1. **FastAPI Backend**: Enhanced with document management and search APIs
2. **PostgreSQL**: Enhanced with Document table
3. **MinIO**: File storage (unchanged)
4. **Next.js Frontend**: User interface (unchanged)

## Data Flow

### Upload Flow
```
User Upload → FastAPI → MinIO Storage → PostgreSQL Metadata → Kafka Event → Indexing Worker → Qdrant
```

### Search Flow
```
User Query → FastAPI → OpenAI Embedding → Qdrant Search → Results
```

## Database Schema

### Document Model
```python
class Document:
    id: UUID (primary key)
    filename: str
    mime_type: str
    size: int
    bucket: str
    object_key: str
    document_metadata: str (JSON string)
    status: enum (pending, processing, indexed, failed)
    version: int
    owner_id: UUID (foreign key to User)
    created_at: datetime
    updated_at: datetime
```

## API Endpoints

### Upload Endpoints
- `POST /api/v1/uploads/files`: Upload files with event publishing
- `GET /api/v1/uploads/documents`: List user documents
- `GET /api/v1/uploads/documents/{document_id}`: Get a single document by ID
- `DELETE /api/v1/uploads/documents/{document_id}`: Delete a single document
- `DELETE /api/v1/uploads/documents`: Delete multiple documents (bulk delete)
- `GET /api/v1/uploads/presign`: Get presigned URL for file access

### Search Endpoints
- `GET /api/v1/search/documents`: Vector similarity search
- `GET /api/v1/search/health`: Search service health check

### Management Endpoints
- `GET /api/v1/utils/health-check/`: Service health check

## Event Schema (CDC-Compatible)

### Event Structure
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

### Kafka Topics
- `source_changes`: Permanent topic for document events

## Configuration

### Environment Variables
```bash
# Kafka
KAFKA_BOOTSTRAP_SERVERS=broker:9092
KAFKA_EXTERNAL_BOOTSTRAP_SERVERS=localhost:9094

# Qdrant
QDRANT_HOST=qdrant
QDRANT_PORT=6333

# OpenAI
OPENAI_API_KEY=<key>
OPENAI_MODEL=text-embedding-3-small
OPENAI_EMBEDDING_DIMENSION=1536

# Worker
INDEXING_WORKER_BATCH_SIZE=10
INDEXING_WORKER_POLL_INTERVAL=5
INDEXING_WORKER_CHUNK_SIZE=1000
INDEXING_WORKER_CHUNK_OVERLAP=200
```

### Resource Limits
```yaml
# Indexing Worker
cpus: '2.0'      # Max 2 CPU cores
memory: 2G       # Max 2GB RAM
```

## Service Responsibilities

### FastAPI Backend
- **File Upload**: Store files in MinIO
- **Metadata Storage**: Save document info to PostgreSQL
- **Event Publishing**: Send events to Kafka after DB commit
- **Search API**: Vector search endpoint
- **Document Management**: CRUD operations

### Indexing Worker
- **Event Consumption**: Read from Kafka topic
- **Text Extraction**: Extract text from various file formats (PDF, DOCX, TXT)
- **Text Chunking**: Split text into semantic chunks
- **Embedding Generation**: Create vectors using OpenAI
- **Vector Storage**: Store embeddings in Qdrant
- **Status Updates**: Update document processing status

### Kafka
- **Event Streaming**: Reliable message delivery
- **Topic Management**: Persistent storage of events
- **Consumer Groups**: Enable multiple worker instances

### Qdrant
- **Vector Storage**: Store document embeddings
- **Similarity Search**: Fast vector similarity queries
- **Metadata Storage**: Store chunk metadata

## Key Design Principles

### CDC Compatibility
- Events follow Debezium format
- Stable topic names (`source_changes`)
- Isolated event publishing module
- Future CDC migration without worker changes

### Idempotency
- Workers use UPSERT operations
- Document ID + chunk ID as unique keys
- Handle duplicate events gracefully

### CPU Isolation
- Separate indexing worker container
- Process pool for CPU-intensive tasks
- Resource limits to prevent hogging
- Async processing for I/O operations

### Fault Tolerance
- Event replay capability
- Failed processing doesn't block uploads
- Graceful error handling
- Health checks and monitoring

## Monitoring & Observability

### Health Checks
- Kafka connectivity
- Qdrant availability
- Worker processing status
- Database connectivity

### Metrics
- Documents processed per minute
- Embedding generation time
- Search response time
- Error rates

### Logging
- Event publishing logs
- Processing status updates
- Error tracking
- Performance metrics

## Future CDC Migration

### Migration Steps
1. **Remove Event Publishing**: Delete Kafka publishing from FastAPI
2. **Configure Debezium**: Set up CDC connector for PostgreSQL
3. **Update Topic**: Debezium will populate `source_changes` topic
4. **No Worker Changes**: Workers continue processing same events

### Benefits
- **Consistency**: All database changes captured
- **Reliability**: Database-level event capture
- **Performance**: Reduced application complexity
- **Scalability**: Better event ordering and delivery

## Getting Started

### 1. Environment Setup
```bash
# Copy environment template
cp env.example .env

# Edit .env file with your API keys
# - OPENAI_API_KEY
# - TAVILY_API_KEY (for agent)
```

### 2. Start Services
```bash
# Start all services
docker-compose up -d

# Check service health
docker-compose ps
```

### 3. Run Database Migrations
```bash
# Apply migrations
docker-compose exec backend alembic upgrade head
```

### 4. Access Services
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/api/v1
- **Kafka UI**: http://localhost:8080
- **MinIO Console**: http://localhost:9001
- **MailHog**: http://localhost:8025

## Development

### Adding New File Types
1. Update `extract_text_from_file()` in `app/workers/indexing_worker.py`
2. Add new MIME type handling
3. Install required dependencies

### Customizing Embeddings
1. Update `OPENAI_MODEL` in environment
2. Adjust `OPENAI_EMBEDDING_DIMENSION` if needed
3. Update Qdrant collection configuration

### Scaling Workers
1. Increase `INDEXING_WORKER_BATCH_SIZE`
2. Add more worker instances
3. Adjust resource limits

## Troubleshooting

### Common Issues

1. **Kafka Connection Failed**
   - Check `KAFKA_BOOTSTRAP_SERVERS` configuration
   - Verify Kafka service is running
   - Check network connectivity

2. **Qdrant Connection Failed**
   - Check `QDRANT_HOST` and `QDRANT_PORT`
   - Verify Qdrant service is running
   - Check collection exists

3. **OpenAI API Errors**
   - Verify `OPENAI_API_KEY` is set
   - Check API key validity
   - Monitor rate limits

4. **Worker Not Processing**
   - Check Kafka consumer group
   - Verify topic exists
   - Check worker logs

### Logs
```bash
# View worker logs
docker-compose logs indexing-worker

# View Kafka logs
docker-compose logs kafka

# View Qdrant logs
docker-compose logs qdrant
```

This implementation provides a robust, scalable foundation that can evolve from application-level events to CDC while maintaining the same processing capabilities and search functionality. 