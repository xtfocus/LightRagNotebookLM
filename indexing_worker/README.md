# Indexing Worker

A standalone service for processing document events and creating vector embeddings for the file processing pipeline.

## Architecture

The indexing worker is designed as a separate service from the FastAPI backend to:

- **Reduce coupling**: Independent deployment and scaling
- **Optimize resources**: Only includes dependencies it needs
- **Improve performance**: Smaller container size and faster startup
- **Enable scaling**: Can be scaled independently of the API

## Features

- **Event-driven processing**: Consumes Kafka events for document changes
- **Text extraction**: Supports PDF, DOCX, TXT files, URLs, and direct text input
- **Vector embeddings**: Creates embeddings using OpenAI
- **Vector storage**: Stores embeddings in Qdrant
- **Status tracking**: Updates document processing status
- **Fault tolerance**: Handles failures gracefully
- **Extensible processing**: Factory pattern for adding new source types
- **Configurable limits**: All file size limits and timeouts are configurable

## Text Processing Architecture

The worker uses a **Factory Pattern** for processing different types of sources:

### Supported Source Types

1. **Document Sources** (`document`)
   - PDF files (`application/pdf`)
   - DOCX files (`application/vnd.openxmlformats-officedocument.wordprocessingml.document`)
   - Plain text files (`text/plain`)

2. **URL Sources** (`url`)
   - Web pages and articles
   - Uses `markitdown` library for conversion to markdown

### Processor Classes

```python
from app.processors import TextProcessorFactory

# Create appropriate processor
processor = TextProcessorFactory.create_processor("document", "application/pdf")
processor = TextProcessorFactory.create_processor("url")
processor = TextProcessorFactory.create_processor("text")

# Process content
text = await processor.process(data)
```

### Adding New Processors

To add support for new source types (e.g., images, videos):

1. Create a new processor class inheriting from `TextProcessor`
2. Implement the required methods
3. Register with the factory

```python
class ImageProcessor(TextProcessor):
    def can_handle(self, source_type: str, mime_type: str = None) -> bool:
        return source_type == "image"
    
    async def extract_text(self, image_data: bytes) -> str:
        # OCR processing logic
        pass

# Register new processor
TextProcessorFactory.register_processor("image", ImageProcessor)
```

## Dependencies

### Core
- `loguru`: Logging
- `pydantic`: Data validation
- `sqlmodel`: Database ORM

### Processing
- `kafka-python`: Event consumption
- `openai`: Embedding generation
- `qdrant-client`: Vector storage
- `langchain`: Text processing
- `PyPDF2`: PDF text extraction
- `python-docx`: DOCX text extraction
- `markitdown[all]`: URL to markdown conversion
- `aiohttp`: Async HTTP requests

### Storage
- `psycopg`: PostgreSQL connection
- `minio`: File storage access

## Configuration

The worker uses the same environment variables as the main application:

```bash
# Kafka
KAFKA_BOOTSTRAP_SERVERS=kafka:9092

# Qdrant
QDRANT_HOST=qdrant
QDRANT_PORT=6333

# OpenAI
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=text-embedding-3-small

# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_SERVER=langgraphdb
POSTGRES_DB=langgraph

# Worker settings
INDEXING_WORKER_BATCH_SIZE=10
INDEXING_WORKER_POLL_INTERVAL=5
INDEXING_WORKER_CHUNK_SIZE=1000
INDEXING_WORKER_CHUNK_OVERLAP=200

# File Processing Limits
MAX_PDF_SIZE_BYTES=104857600      # 100MB default
MAX_DOCX_SIZE_BYTES=52428800       # 50MB default
MAX_TXT_SIZE_BYTES=10485760        # 10MB default
MIN_FILE_SIZE_BYTES=100            # 100 bytes minimum

# URL Processing Configuration
URL_PROCESSING_TIMEOUT_SECONDS=25  # 25 seconds default

# Text Processing Configuration
MAX_BINARY_NULL_RATIO=0.1          # 10% null bytes threshold
```

### File Size Limits

All file size limits are configurable via environment variables:

- **PDF files**: `MAX_PDF_SIZE_BYTES` (default: 100MB)
- **DOCX files**: `MAX_DOCX_SIZE_BYTES` (default: 50MB)
- **TXT files**: `MAX_TXT_SIZE_BYTES` (default: 10MB)
- **Minimum file size**: `MIN_FILE_SIZE_BYTES` (default: 100 bytes)

### URL Processing

- **Timeout**: `URL_PROCESSING_TIMEOUT_SECONDS` (default: 25 seconds)
- **Binary detection**: `MAX_BINARY_NULL_RATIO` (default: 10% null bytes)

## Development

### Local Development
```bash
cd indexing_worker
uv sync
python -m app.workers.indexing_worker
```

### Running Tests
```bash
cd indexing_worker
uv sync
pytest tests/
```

### Example Usage
```bash
cd indexing_worker
python examples/processor_example.py
```

### Docker Build
```bash
docker build -t app-worker .
```

### Docker Compose
The worker is included in the main docker-compose.yml and will start automatically with the other services.

## API Usage

### Processing Sources

```python
from app.processors import TextProcessorFactory

# Process a document
processor = TextProcessorFactory.create_processor("document", "application/pdf")
text = await processor.process(file_data)

# Process a URL
processor = TextProcessorFactory.create_processor("url")
text = await processor.process("https://example.com")

# Process direct text
processor = TextProcessorFactory.create_processor("text")
text = await processor.process("Some text content")
```

### Factory Methods

```python
# Get supported source types
types = TextProcessorFactory.get_supported_source_types()

# Check if source type is supported
can_handle = TextProcessorFactory.can_handle_source_type("document", "application/pdf")

# Register custom processor
TextProcessorFactory.register_processor("custom", CustomProcessor)
```

## Error Handling

All processors include comprehensive error handling:

- **Input validation**: Validates data before processing
- **Timeout handling**: URL processing has configurable timeout
- **Graceful degradation**: Failed processing doesn't crash the worker
- **Detailed logging**: All errors are logged with context
- **Configurable limits**: All size and timeout limits are configurable

## Performance Considerations

- **Async processing**: All text extraction is asynchronous
- **Thread pool**: CPU-intensive operations use thread pool
- **Timeout limits**: URL processing has configurable timeouts
- **Memory management**: Large files are processed in chunks
- **Error recovery**: Failed processing is retried with exponential backoff
- **Configurable limits**: All processing limits can be tuned for your environment

## Monitoring

The worker provides comprehensive logging for monitoring:

- Processing start/completion events
- Error details with context
- Performance metrics (processing time, text length)
- Source type statistics
- File size validation results

## Future Enhancements

- **Image processing**: OCR for image files
- **Video processing**: Speech-to-text for video files
- **Audio processing**: Speech-to-text for audio files
- **Batch processing**: Process multiple sources in parallel
- **Caching**: Cache processed content to avoid reprocessing
- **Dynamic limits**: Adjust limits based on system resources 