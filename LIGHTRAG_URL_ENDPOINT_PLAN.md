# LightRAG URL Endpoint Implementation Plan

## Overview

Add a new `/documents/url` endpoint to LightRAG that handles URL content extraction and indexing, similar to the existing `/documents/text` endpoint but with automatic URL content fetching.

## Key Findings

### 1. Qdrant Sharing ✅
- **LightRAG connects to external Qdrant** via `QDRANT_URL` environment variable
- **Does NOT run its own Qdrant** - it's a client, not a server
- **We can share the same Qdrant instance** that's already in docker-compose
- **Configuration**: Set `QDRANT_URL=http://qdrant:6333` in LightRAG service

### 2. URL Endpoint Design
- **Endpoint**: `POST /documents/url`
- **Request Model**: `InsertURLRequest` (similar to `InsertTextRequest`)
- **Processing Flow**:
  1. Receive URL in request
  2. Extract content using markitdown (like our current URLProcessor)
  3. Call `pipeline_index_texts` with extracted content
  4. Return track_id for status monitoring

## Implementation Steps

### Step 1: Add URL Request Model

Add to `LightRAG/lightrag/api/routers/document_routes.py`:

```python
class InsertURLRequest(BaseModel):
    """Request model for inserting a URL document
    
    Attributes:
        url: The URL to fetch and index
        file_source: Optional custom source identifier (defaults to URL)
    """
    
    url: str = Field(
        min_length=1,
        description="The URL to fetch and index",
    )
    file_source: str = Field(
        default=None, 
        min_length=0, 
        description="Optional custom source identifier. If not provided, uses the URL."
    )
    
    @field_validator("url", mode="after")
    @classmethod
    def validate_url(cls, url: str) -> str:
        """Validate and normalize URL"""
        url = url.strip()
        
        # Add protocol if missing
        if not url.startswith(("http://", "https://")):
            if url.startswith("www."):
                url = "https://" + url
            else:
                url = "https://" + url
        
        # Basic URL validation
        from urllib.parse import urlparse
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("Invalid URL format")
        
        return url
```

### Step 2: Add URL Extraction Function

Add helper function to extract URL content:

```python
async def extract_url_content(url: str, timeout: int = 25) -> str:
    """
    Extract text content from URL using markitdown.
    
    Args:
        url: URL to extract content from
        timeout: Timeout in seconds (default: 25)
        
    Returns:
        Extracted text content as markdown string
        
    Raises:
        ValueError: If URL extraction fails or times out
    """
    import asyncio
    from markitdown import MarkItDown
    
    async def _convert() -> str:
        def _run():
            logger.info(f"🔄 Extracting content from URL: {url}")
            instance = MarkItDown()
            conversion_result = instance.convert(url)
            return conversion_result.text_content
        
        return await asyncio.to_thread(_run)
    
    try:
        text_content = await asyncio.wait_for(_convert(), timeout=timeout)
        
        if not text_content or not text_content.strip():
            logger.warning(f"⚠️ No content extracted from URL: {url}")
            return ""
        
        logger.info(f"✅ Successfully extracted {len(text_content)} characters from URL")
        return text_content.strip()
        
    except asyncio.TimeoutError:
        logger.error(f"❌ URL extraction timed out: {url}")
        raise ValueError(f"URL extraction timed out after {timeout} seconds")
    except ImportError:
        logger.error("❌ markitdown library not available")
        raise ValueError("URL processing library (markitdown) not available")
    except Exception as e:
        logger.error(f"❌ URL extraction failed for {url}: {e}")
        raise ValueError(f"URL extraction failed: {str(e)}")
```

### Step 3: Add URL Endpoint

Add new endpoint to router:

```python
@router.post(
    "/url", 
    response_model=InsertResponse, 
    dependencies=[Depends(combined_auth)]
)
async def insert_url(
    request: InsertURLRequest, 
    background_tasks: BackgroundTasks
):
    """
    Insert URL content into the RAG system.
    
    This endpoint fetches content from a URL, extracts text, and indexes it
    into the RAG system for later retrieval.
    
    Args:
        request (InsertURLRequest): The request body containing the URL to fetch.
        background_tasks: FastAPI BackgroundTasks for async processing
        
    Returns:
        InsertResponse: A response object containing the status of the operation.
        
    Raises:
        HTTPException: If an error occurs during URL processing (500).
    """
    try:
        # Use URL as file_source if not provided
        file_source = request.file_source or request.url
        
        # Check if URL already exists in doc_status storage
        if file_source and file_source.strip() and file_source != "unknown_source":
            existing_doc_data = await rag.doc_status.get_doc_by_file_path(file_source)
            if existing_doc_data:
                status = existing_doc_data.get("status", "unknown")
                return InsertResponse(
                    status="duplicated",
                    message=f"URL '{file_source}' already exists in document storage (Status: {status}).",
                    track_id="",
                )
        
        # Generate track_id for URL insertion
        track_id = generate_track_id("url")
        
        # Extract URL content in background
        async def process_url():
            try:
                # Extract content from URL
                text_content = await extract_url_content(request.url)
                
                if not text_content:
                    # Enqueue as error document
                    error_files = [{
                        "file_path": file_source,
                        "error_description": "[URL Extraction]No content extracted from URL",
                        "original_error": "URL returned empty content",
                        "file_size": 0,
                    }]
                    await rag.apipeline_enqueue_error_documents(error_files, track_id)
                    return
                
                # Index the extracted text
                await pipeline_index_texts(
                    rag,
                    [text_content],
                    file_sources=[file_source],
                    track_id=track_id,
                )
            except Exception as e:
                logger.error(f"Error processing URL {request.url}: {str(e)}")
                # Enqueue as error document
                error_files = [{
                    "file_path": file_source,
                    "error_description": f"[URL Extraction]{str(e)}",
                    "original_error": str(e),
                    "file_size": 0,
                }]
                await rag.apipeline_enqueue_error_documents(error_files, track_id)
        
        background_tasks.add_task(process_url)
        
        return InsertResponse(
            status="success",
            message=f"URL '{request.url}' successfully received. Content extraction and processing will continue in background.",
            track_id=track_id,
        )
    except ValueError as e:
        # Validation errors (invalid URL format, etc.)
        logger.error(f"URL validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error /documents/url: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
```

### Step 4: Update Dependencies

Ensure `markitdown` is available in LightRAG's dependencies:

- Check if `markitdown` is in `LightRAG/pyproject.toml`
- If not, add it as an optional dependency or install it

### Step 5: Update Docker Compose

Update LightRAG service to use shared Qdrant:

```yaml
lightrag:
  # ... existing config ...
  environment:
    # ... other env vars ...
    - QDRANT_URL=http://qdrant:6333  # Use shared Qdrant instance
    - QDRANT_API_KEY=${QDRANT_API_KEY:-}  # Optional API key
  depends_on:
    - qdrant  # Ensure Qdrant starts first
    - db
```

## Benefits

1. **Unified API**: URL handling becomes part of LightRAG's API
2. **Shared Infrastructure**: One Qdrant instance for both systems
3. **Consistent Processing**: URLs go through same pipeline as other documents
4. **Better Status Tracking**: Uses LightRAG's track_id system
5. **Error Handling**: Integrated with LightRAG's error document system

## Testing

1. Test URL endpoint with various URLs:
   - Standard web pages
   - PDFs hosted online
   - Articles with complex HTML
   - Invalid URLs (should return 400)
   - Duplicate URLs (should return duplicated status)

2. Verify Qdrant sharing:
   - Check that LightRAG and our backend use same Qdrant instance
   - Verify workspace isolation works correctly
   - Test that both systems can query the same collections

## Migration Path

1. **Phase 1**: Add URL endpoint to LightRAG (this implementation)
2. **Phase 2**: Update our backend to call LightRAG `/documents/url` instead of custom processor
3. **Phase 3**: Remove custom URLProcessor from indexing_worker
4. **Phase 4**: Remove indexing_worker entirely (after full migration)

## Notes

- URL extraction is async and happens in background
- Uses same error handling as file uploads
- Supports duplicate detection via file_source
- Timeout is configurable (default: 25 seconds)
- Returns track_id for status monitoring

