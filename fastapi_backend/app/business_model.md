## Business Abstraction Summary

This codebase implements a **notebook-based LLM interface** where users can upload files, create notebooks, and chat with an AI assistant using their uploaded documents as context. Here are the key business abstractions:

### 1. **Source** - The Core Information Abstraction

**Source** is the primary abstraction that represents any type of information that can be used as context for AI interactions:

- **Purpose**: Generic container for different types of information sources
- **Types**: Supports 5 source types via `SourceType` enum:
  - `DOCUMENT` - Links to existing Document (files like PDF, DOCX, TXT)
  - `URL` - Web pages and articles
  - `VIDEO` - Video files or YouTube links (planned)
  - `IMAGE` - Image files (planned)
  - `TEXT` - Direct text input

- **Key Properties**:
  - `title` - Human-readable name
  - `description` - Optional description
  - `source_type` - One of the enum values above
  - `source_metadata` - JSON field containing type-specific data
  - `owner_id` - User who owns the source

### 2. **Document** - File Storage Abstraction

**Document** represents uploaded files in the system:

- **Purpose**: Handles file uploads, storage, and processing status
- **Properties**:
  - File metadata (filename, mime_type, size, bucket, object_key)
  - Processing status (PENDING, PROCESSING, INDEXED, FAILED)
  - Version tracking
  - **New**: `source_id` field linking to a Source record

- **Relationship**: One-to-one relationship with Source via `source_id`

### 3. **Notebook** - Workspace Abstraction

**Notebook** represents a user's workspace for AI interactions:

- **Purpose**: Container for organizing sources and chat conversations
- **Properties**:
  - `title` and `description`
  - `owner_id` - User who owns the notebook
  - Relationships to sources and messages

### 4. **NotebookSource** - Junction Abstraction

**NotebookSource** manages the many-to-many relationship between notebooks and sources:

- **Purpose**: Links sources to notebooks with ordering and metadata
- **Key Features**:
  - `position` field for ordering sources within a notebook
  - `added_at` timestamp for when source was added
  - Unique constraint preventing duplicate sources in the same notebook
  - Idempotent operations (prevents duplicate additions)

### 5. **URL** - Web Content Abstraction

**URL** sources represent web content:

- **Purpose**: Extract and process web pages/articles
- **Metadata Structure**:
  ```json
  {
    "url": "https://example.com/article",
    "title": "Article Title", 
    "content": "extracted text content",
    "last_fetched": "2024-01-01T00:00:00Z"
  }
  ```

### 6. **Source Metadata** - Type-Specific Data Storage

Each source type has specific metadata requirements:

- **Document Sources**:
  ```json
  {
    "document_id": "uuid",
    "filename": "document.pdf",
    "mime_type": "application/pdf", 
    "size": 1024000,
    "status": "indexed"
  }
  ```

- **Text Sources**:
  ```json
  {
    "content": "user provided text",
    "word_count": 150
  }
  ```

### 7. **Text Processing Architecture**

The system uses a **Factory Pattern** for processing different source types:

- **TextProcessor** abstract base class
- **TextProcessorFactory** for creating appropriate processors
- Dedicated processors: `PDFProcessor`, `DOCXProcessor`, `TXTProcessor`, `URLProcessor`
- MIME type mapping for automatic processor selection

### Key Business Relationships

1. **User** → **Sources** (one-to-many)
2. **User** → **Notebooks** (one-to-many) 
3. **Document** → **Source** (one-to-one via `source_id`)
4. **Notebook** ↔ **Source** (many-to-many via **NotebookSource**)
5. **Notebook** → **NotebookMessage** (one-to-many for chat history)

### Business Workflow

1. **File Upload**: Files become Documents, which are linked to Sources
2. **Source Creation**: Users can create Sources from Documents, URLs, or direct text
3. **Notebook Creation**: Users create notebooks to organize their work
4. **Source Addition**: Sources are added to notebooks with ordering
5. **AI Interaction**: Chat with AI using notebook sources as context

This architecture provides a flexible, extensible system for managing different types of information sources while maintaining clear separation of concerns between file storage (Document), information abstraction (Source), and workspace organization (Notebook).
