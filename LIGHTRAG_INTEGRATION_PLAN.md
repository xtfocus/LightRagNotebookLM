# LightRAG Integration Plan & Architecture Analysis

## Executive Summary

LightRAG is a comprehensive RAG backend server that can replace several components in our current architecture:
- ✅ **Document Processing & Indexing** → LightRAG handles this natively
- ✅ **Vector Search** → LightRAG uses Qdrant (we already have this)
- ✅ **File Storage** → LightRAG has built-in document management
- ✅ **Web UI** → LightRAG includes a Web UI
- ⚠️ **Langfuse** → Need to verify if included (likely separate)
- ❌ **Kafka** → Can be removed (LightRAG uses direct API calls)
- ❌ **Indexing Worker** → Can be removed (LightRAG handles indexing)

---

## LightRAG API Capabilities

### 1. Document Management APIs (`/documents`)

#### File Upload & Indexing
- `POST /documents/upload` - Upload single file
- `POST /documents/upload-multiple` - Upload multiple files
- `POST /documents/insert-text` - Insert text directly
- `POST /documents/insert-texts` - Insert multiple texts
- `GET /documents/list` - List all documents
- `GET /documents/{filename}` - Get document details
- `DELETE /documents/{filename}` - Delete document

#### Document Processing
- `POST /documents/scan` - Scan directory for new files
- `POST /documents/reprocess` - Reprocess failed documents
- `POST /documents/cancel-pipeline` - Cancel ongoing processing
- `GET /documents/status/{filename}` - Get processing status
- `GET /documents/status` - Get all document statuses

#### Features:
- ✅ **Raw File Storage**: Files stored in `input_dir` (configurable)
- ✅ **Automatic Indexing**: Background pipeline processes files
- ✅ **Status Tracking**: Tracks processing status (pending, processing, processed, failed)
- ✅ **Multiple Formats**: Supports PDF, DOCX, TXT, Markdown, etc.
- ✅ **Text Extraction**: Built-in text extraction from files
- ✅ **Chunking**: Automatic text chunking with configurable size/overlap

### 2. Query APIs (`/query`)

#### Query Endpoints
- `POST /query` - Standard query (returns full response)
- `POST /query/stream` - Streaming query
- `POST /query/data` - Query with structured data response

#### Query Features:
- ✅ **Multiple Modes**: local, global, hybrid, naive, mix, bypass
- ✅ **Vector Search**: Uses configured vector DB (Qdrant in our case)
- ✅ **Reranking**: Optional reranking support
- ✅ **Conversation History**: Supports multi-turn conversations
- ✅ **Token Control**: Configurable token budgets
- ✅ **References**: Returns source references with chunks
- ✅ **Streaming**: Real-time streaming responses

### 3. Graph APIs (`/graph`)

- `GET /graph/entities` - Get knowledge graph entities
- `GET /graph/relations` - Get relationships
- `GET /graph/visualize` - Graph visualization data

### 4. Storage Configuration

LightRAG supports multiple storage backends:
- **Vector Storage**: Qdrant, Milvus, FAISS, Chroma, etc.
- **Graph Storage**: PostgreSQL, Neo4j, MongoDB, Redis, NetworkX
- **KV Storage**: PostgreSQL, Redis, MongoDB, JSON
- **Doc Status Storage**: PostgreSQL, JSON, MongoDB

**Current Setup**: We use Qdrant (already compatible!)

---

## Current Architecture Components

### Components to REPLACE

#### 1. **Kafka** ❌ REMOVE
**Current Usage:**
- Event-driven document processing
- Publishes document events (create, update, delete)
- Indexing worker consumes events

**Replacement:**
- LightRAG uses **direct API calls** instead of event streaming
- Upload → LightRAG processes immediately or in background
- No need for Kafka message queue

**Migration:**
- Replace `kafka_publisher.publish_document_event()` calls
- Use LightRAG `/documents/upload` API directly
- Remove Kafka dependency from `docker-compose.yml`

#### 2. **Indexing Worker** ❌ REMOVE
**Current Functionality:**
- Consumes Kafka events
- Extracts text from files (PDF, DOCX, TXT, URLs)
- Creates embeddings using OpenAI
- Stores embeddings in Qdrant
- Updates document status in database

**Replacement:**
- LightRAG handles all of this:
  - File upload → automatic text extraction
  - Automatic chunking
  - Embedding generation
  - Vector storage in Qdrant
  - Status tracking

**Migration:**
- Remove `indexing_worker/` directory
- Remove Kafka consumer logic
- Use LightRAG document APIs instead

#### 3. **Document Processors** ⚠️ PARTIAL REPLACE
**Current Functionality:**
- `PDFProcessor`, `DOCXProcessor`, `TXTProcessor`, `URLProcessor`
- Text extraction from various formats

**Replacement:**
- LightRAG has built-in processors
- May need to verify URL processing (LightRAG may handle this differently)

**Migration:**
- Remove custom processors if LightRAG covers all formats
- Keep URL processor if LightRAG doesn't handle URLs well

### Components to KEEP & WRAP

#### 1. **Source Management** ✅ KEEP AS WRAPPER
**Current Functionality:**
- User-facing source abstraction
- Source types: DOCUMENT, URL, VIDEO, IMAGE, TEXT
- Ownership and permissions
- Notebook-source relationships
- Metadata management

**Integration Strategy:**
- Keep Source model in PostgreSQL (business logic layer)
- Map Source → LightRAG document operations:
  - `Source` (DOCUMENT) → LightRAG `/documents/upload`
  - `Source` (URL) → LightRAG `/documents/insert-text` (after URL extraction)
  - `Source` (TEXT) → LightRAG `/documents/insert-text`
- Store LightRAG document reference in `source_metadata`
- Keep Source Management API as wrapper around LightRAG APIs

**Example Flow:**
```
User creates Source → Backend creates Source record → 
Call LightRAG API → Store LightRAG doc_id in source_metadata →
Return Source to user
```

#### 2. **MinIO File Storage** ⚠️ EVALUATE
**Current Usage:**
- Stores raw uploaded files
- Accessed by indexing worker

**Decision Needed:**
- Option A: Keep MinIO for raw file storage, LightRAG for indexing
- Option B: Let LightRAG handle file storage (uses filesystem)
- **Recommendation**: Keep MinIO for now, sync files to LightRAG input_dir

#### 3. **Qdrant** ✅ SHARE INSTANCE
- **LightRAG connects to external Qdrant** (does NOT run its own)
- **We can share the same Qdrant instance** that's already in docker-compose
- **Configuration**: Set `QDRANT_URL=http://qdrant:6333` in LightRAG service
- **Benefits**: 
  - Single Qdrant instance for both systems
  - Reduced resource usage
  - Easier management
- **Workspace Isolation**: LightRAG uses workspace parameter to isolate data within same Qdrant instance

#### 4. **PostgreSQL** ✅ KEEP
- Still needed for:
  - User management
  - Source metadata (business layer)
  - Notebook management
  - Notebook-source relationships
  - Authentication/authorization

---

## Integration Architecture

### New Architecture Flow

```
┌─────────────┐
│   Frontend  │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│   FastAPI Backend (Wrapper Layer)   │
│  ┌───────────────────────────────┐  │
│  │  Source Management API        │  │
│  │  - CRUD operations            │  │
│  │  - Ownership checks           │  │
│  │  - Notebook relationships      │  │
│  └───────────┬───────────────────┘  │
│              │                       │
│  ┌───────────▼───────────────────┐  │
│  │  LightRAG Client             │  │
│  │  - Document operations        │  │
│  │  - Query operations            │  │
│  │  - Status tracking             │  │
│  └───────────┬───────────────────┘  │
└──────────────┼───────────────────────┘
               │
       ┌───────┴────────┐
       │                │
       ▼                ▼
┌─────────────┐  ┌──────────────┐
│  LightRAG   │  │  PostgreSQL  │
│  Server     │  │  (Metadata)   │
└──────┬──────┘  └──────────────┘
       │
       ▼
┌─────────────┐
│   Qdrant    │
│  (Vectors)   │
└─────────────┘
```

### Source Management Wrapper Pattern

```python
# Example: Create Source with LightRAG integration
async def create_source(source_data: SourceCreate):
    # 1. Create Source record in PostgreSQL
    source = Source(
        title=source_data.title,
        source_type=source_data.source_type,
        owner_id=current_user.id
    )
    session.add(source)
    await session.commit()
    
    # 2. Process based on source type
    if source_data.source_type == SourceType.DOCUMENT:
        # Upload to LightRAG
        lightrag_response = await lightrag_client.upload_document(
            file_path=document.file_path,
            track_id=str(source.id)
        )
        # Store LightRAG doc_id in metadata
        source.source_metadata = {
            "lightrag_doc_id": lightrag_response["doc_id"],
            "lightrag_filename": lightrag_response["filename"],
            "status": "processing"
        }
    
    elif source_data.source_type == SourceType.URL:
        # Extract URL content, then insert to LightRAG
        content = await extract_url_content(source_data.url)
        lightrag_response = await lightrag_client.insert_text(
            text=content,
            file_source=source_data.url,
            track_id=str(source.id)
        )
        source.source_metadata = {
            "lightrag_doc_id": lightrag_response["doc_id"],
            "status": "processed"
        }
    
    elif source_data.source_type == SourceType.TEXT:
        # Direct text insertion
        lightrag_response = await lightrag_client.insert_text(
            text=source_data.text,
            track_id=str(source.id)
        )
        source.source_metadata = {
            "lightrag_doc_id": lightrag_response["doc_id"],
            "status": "processed"
        }
    
    await session.commit()
    return source
```

---

## Migration Steps

### Phase 1: Setup LightRAG Server
1. ✅ Add LightRAG server to `docker-compose.yml`
2. ✅ Configure LightRAG to use existing Qdrant instance
3. ✅ Set up LightRAG input directory (for file storage)
4. ✅ Configure LightRAG with OpenAI embeddings (same as current)

### Phase 2: Create LightRAG Client
1. Create `fastapi_backend/app/core/lightrag_client.py`
2. Implement wrapper functions:
   - `upload_document(file_path, track_id)`
   - `insert_text(text, file_source, track_id)`
   - `get_document_status(filename)`
   - `delete_document(filename)`
   - `query(query, mode, ...)`

### Phase 3: Integrate with Source Management
1. Update `create_source()` to call LightRAG APIs
2. Update `delete_source()` to delete from LightRAG
3. Add status sync: Poll LightRAG status → update Source status
4. Store LightRAG document references in `source_metadata`

### Phase 4: Remove Old Components
1. ❌ Remove Kafka from `docker-compose.yml`
2. ❌ Remove indexing-worker service
3. ❌ Remove Kafka publisher code
4. ❌ Remove document processor code (if LightRAG covers all)
5. ⚠️ Keep MinIO (or migrate to LightRAG file storage)

### Phase 5: Update Query Flow
1. Replace direct Qdrant queries with LightRAG `/query` API
2. Update agent to use LightRAG query endpoints
3. Map LightRAG query responses to current response format

---

## LightRAG Configuration

### Required Environment Variables

```bash
# LightRAG Server Configuration
LIGHTRAG_WORKING_DIR=/app/lightrag_working
LIGHTRAG_INPUT_DIR=/app/lightrag_input
LIGHTRAG_WORKSPACE=default  # Or per-user workspaces

# LLM Configuration (same as current)
OPENAI_API_KEY=...
OPENAI_MODEL=text-embedding-3-small
OPENAI_EMBEDDING_DIMENSION=1536

# Storage Configuration
LIGHTRAG_VECTOR_STORAGE=qdrant
LIGHTRAG_GRAPH_STORAGE=postgres  # Or networkx for simpler
LIGHTRAG_KV_STORAGE=postgres
LIGHTRAG_DOC_STATUS_STORAGE=postgres

# Qdrant Connection (use existing)
QDRANT_HOST=qdrant
QDRANT_PORT=6333

# PostgreSQL Connection (for graph/KV storage)
POSTGRES_SERVER=db
POSTGRES_PORT=5432
POSTGRES_DB=lightrag
POSTGRES_USER=...
POSTGRES_PASSWORD=...
```

### Docker Compose Service

```yaml
lightrag:
  image: lightrag:latest  # Or build from LightRAG repo
  ports:
    - "8001:8000"  # Different port from backend
  environment:
    - LIGHTRAG_WORKING_DIR=/app/working
    - LIGHTRAG_INPUT_DIR=/app/input
    - OPENAI_API_KEY=${OPENAI_API_KEY}
    - QDRANT_URL=http://qdrant:6333  # Use shared Qdrant instance
    - QDRANT_API_KEY=${QDRANT_API_KEY:-}  # Optional API key
    - LIGHTRAG_VECTOR_STORAGE=QdrantVectorDBStorage
    # ... other storage configs ...
  volumes:
    - lightrag_working:/app/working
    - lightrag_input:/app/input
    - ./uploads:/app/uploads  # If syncing from MinIO
  networks:
    - my_network
  depends_on:
    qdrant:
      condition: service_healthy  # Use existing Qdrant service
    db:
      condition: service_healthy  # If using PostgreSQL for graph storage
```

---

## Open Questions & Decisions Needed - VERIFIED ✅

### 1. File Storage Strategy ✅ VERIFIED
- **Question**: Should we keep MinIO or use LightRAG's file storage?
- **Answer**: LightRAG uses filesystem-based storage via `input_dir` parameter
- **LightRAG Implementation**: 
  - Files stored in `input_dir` directory (configurable)
  - `DocumentManager` class manages file scanning and storage
  - Supports many file formats: PDF, DOCX, TXT, MD, HTML, CSV, JSON, code files, etc.
- **Recommendation**: 
  - **Option A (Recommended)**: Keep MinIO for raw file storage, sync files to LightRAG `input_dir`
    - Maintains existing file management
    - LightRAG processes from `input_dir`
    - Easier migration path
  - **Option B**: Use LightRAG's filesystem storage directly
    - Simpler architecture
    - Requires migrating from MinIO

### 2. Workspace Isolation ✅ VERIFIED
- **Question**: How to handle per-user document isolation?
- **Answer**: LightRAG has built-in workspace support
- **LightRAG Implementation**:
  - `workspace` parameter in LightRAG initialization (defaults to empty string)
  - All storage backends (KV, Vector, Graph, DocStatus) use workspace for isolation
  - Workspace passed to all storage namespaces
  - Can be set via `WORKSPACE` environment variable
- **Recommendation**: **Use LightRAG workspaces (one per user)**
  - Set `workspace=str(user_id)` when initializing LightRAG per user
  - Provides complete data isolation at storage level
  - Better than filtering by metadata

### 3. Langfuse Integration ✅ VERIFIED
- **Question**: Does LightRAG include Langfuse or do we need separate setup?
- **Answer**: LightRAG has optional Langfuse integration
- **LightRAG Implementation**:
  - Langfuse is an **optional dependency** (`pip install lightrag-hku[observability]`)
  - Automatically enabled if environment variables are set:
    - `LANGFUSE_SECRET_KEY`
    - `LANGFUSE_PUBLIC_KEY`
    - `LANGFUSE_HOST` (defaults to https://cloud.langfuse.com)
  - Only works with **OpenAI-compatible APIs** (not Ollama, Azure, Bedrock)
  - Provides drop-in replacement for OpenAI client
  - Features: Tracing, Analytics, Debugging, Evaluation, Monitoring
- **Recommendation**: 
  - **Enable Langfuse** if using OpenAI embeddings/LLM
  - Set environment variables in LightRAG server configuration
  - No separate Langfuse server needed (use cloud.langfuse.com or self-hosted)
  - **Note**: If using Ollama/Azure, Langfuse won't work (limitation)

### 4. URL Processing ✅ SOLUTION: ADD TO LIGHTRAG
- **Question**: Does LightRAG handle URL extraction well?
- **Answer**: LightRAG does NOT have built-in URL extraction, but we can add it
- **Solution**: **Add `/documents/url` endpoint to LightRAG**
  - Create new endpoint that accepts URL
  - Use markitdown to extract content (like our current URLProcessor)
  - Call `pipeline_index_texts` with extracted content
  - Returns track_id for status monitoring
- **Implementation**: See `LIGHTRAG_URL_ENDPOINT_PLAN.md` for detailed implementation
- **Benefits**:
  - Unified API for all document types
  - Consistent error handling
  - Better status tracking
  - No need for custom URL processor

### 5. Status Synchronization ✅ VERIFIED
- **Question**: How to sync LightRAG processing status with Source status?
- **Answer**: LightRAG provides comprehensive status tracking APIs
- **LightRAG Implementation**:
  - Status tracking via `DocStatusStorage` (supports PostgreSQL, JSON, MongoDB)
  - Status values: `PENDING`, `PREPROCESSED`, `PROCESSED`, `FAILED`
  - APIs available:
    - `GET /documents/status/{filename}` - Get single document status
    - `GET /documents/status` - Get all document statuses
    - `GET /track_status/{track_id}` - Get status by track_id
  - Status includes: `content_summary`, `content_length`, `status`, `created_at`, `updated_at`, `track_id`, `chunks_count`, `error_msg`, `metadata`
- **Recommendation**: 
  - **Option A (Recommended)**: Poll LightRAG status API periodically
    - Use `track_id` returned from upload/insert operations
    - Poll `/track_status/{track_id}` every 2-5 seconds for active sources
    - Update Source status in PostgreSQL when LightRAG status changes
  - **Option B**: Background task that monitors LightRAG status
    - Periodic sync job that checks all pending/processing sources
    - More efficient for bulk operations
  - **Implementation**: Create sync service that maps LightRAG status → Source status

### 6. Query Integration ✅ VERIFIED
- **Question**: Replace direct Qdrant queries with LightRAG queries?
- **Answer**: Yes, LightRAG query API provides better context retrieval
- **LightRAG Implementation**:
  - Query endpoint: `POST /query` with multiple modes:
    - `local`: Context-dependent information
    - `global`: Global knowledge
    - `hybrid`: Combines local and global
    - `naive`: Basic search
    - `mix`: Integrates knowledge graph + vector retrieval (recommended)
    - `bypass`: Direct query without RAG
  - Features:
    - Knowledge graph integration
    - Reranking support
    - Token budget control
    - Conversation history
    - Streaming support
    - Reference citations
- **Recommendation**: **Yes, replace direct Qdrant queries**
  - Use LightRAG `/query` API instead of direct Qdrant queries
  - Better context retrieval with knowledge graph
  - Automatic reranking and token management
  - Returns structured references for citations

---

## Benefits of Migration

### Simplified Architecture
- ✅ Remove Kafka complexity
- ✅ Remove indexing worker service
- ✅ Single RAG backend instead of multiple components

### Better Features
- ✅ Built-in Web UI for document management
- ✅ Advanced query modes (local, global, hybrid)
- ✅ Knowledge graph support
- ✅ Better chunking and embedding strategies

### Reduced Maintenance
- ✅ One less service to maintain (indexing worker)
- ✅ One less infrastructure component (Kafka)
- ✅ LightRAG handles updates and improvements

### Performance
- ✅ Optimized RAG pipeline
- ✅ Better caching strategies
- ✅ Efficient vector search

---

## Risks & Mitigation

### Risk 1: LightRAG API Changes
- **Mitigation**: Use wrapper layer (Source Management) to abstract LightRAG
- **Impact**: Low - changes isolated to wrapper layer

### Risk 2: Data Migration
- **Mitigation**: 
  - Keep existing data in PostgreSQL
  - Re-index documents through LightRAG
  - Gradual migration with dual-write period

### Risk 3: Feature Gaps
- **Mitigation**: 
  - Test LightRAG thoroughly before migration
  - Keep custom processors if needed
  - Extend LightRAG with custom code if necessary

---

## Next Steps

1. **Research Phase** ✅ COMPLETED
   - [x] Verify LightRAG URL processing capabilities → **No built-in URL extraction, keep custom processor**
   - [x] Check Langfuse integration status → **Optional, works with OpenAI-compatible APIs**
   - [x] Review LightRAG workspace isolation → **Built-in workspace support per user**
   - [ ] Test LightRAG with our document types (PDF, DOCX, TXT) → **Next: Run test uploads**

2. **Prototype Phase** (3-5 days)
   - [ ] Set up LightRAG server in docker-compose
   - [ ] Create LightRAG client wrapper
   - [ ] Implement Source → LightRAG integration for one source type
   - [ ] Test end-to-end flow

3. **Migration Phase** (1-2 weeks)
   - [ ] Migrate all source types to LightRAG
   - [ ] Update query flow to use LightRAG
   - [ ] Remove Kafka and indexing worker
   - [ ] Update documentation

4. **Testing & Validation** (1 week)
   - [ ] End-to-end testing
   - [ ] Performance testing
   - [ ] User acceptance testing
   - [ ] Data validation

---

## References

- LightRAG GitHub: https://github.com/Distillative-AI/LightRAG
- LightRAG API Documentation: Check `/docs` endpoint when server is running
- Current Architecture: See `FILE_PROCESSING_PIPELINE.md` and `INDEXING.md`

