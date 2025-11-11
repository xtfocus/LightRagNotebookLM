import json
import time
import asyncio
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
from loguru import logger
from kafka import KafkaConsumer
from kafka.errors import KafkaError
import openai
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sqlmodel import create_engine, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.core.config import settings
from app.core.qdrant import qdrant_manager
from app.models import DocumentEvent, URLSourceEvent, ProcessingStatus, Document, Source
from app.processors import TextProcessorFactory

# Configuration constants
POLLING_INTERVAL_SECONDS = 1
KAFKA_RETRY_DELAY_SECONDS = 5
THREAD_POOL_MAX_WORKERS = 4
TASK_TIMEOUT_SECONDS = 300  # 5 minutes timeout for task processing


class IndexingWorker:
    """
    Worker for processing document and URL source events and creating embeddings.
    
    This worker consumes Kafka events for document and URL source processing,
    extracts text content, creates embeddings, and stores them in Qdrant.
    
    Features:
    - Async processing of multiple source types (documents, URLs)
    - Real-time status updates to database
    - Comprehensive error handling and logging
    - Resource cleanup on shutdown
    """
    
    def __init__(self):
        self.consumer = None
        self.openai_client = None
        self.text_splitter = None
        self.executor = ThreadPoolExecutor(max_workers=THREAD_POOL_MAX_WORKERS)
        self.async_engine = None
        self.async_session_maker = None
        self.processor_factory = TextProcessorFactory()
        self._setup()
    
    def _setup(self):
        """Setup Kafka consumer, OpenAI client, and text splitter."""
        # Setup OpenAI client
        if settings.OPENAI_API_KEY:
            self.openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            logger.info("OpenAI client initialized")
        else:
            logger.error("OPENAI_API_KEY not set")
        
        # Setup text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.INDEXING_WORKER_CHUNK_SIZE,
            chunk_overlap=settings.INDEXING_WORKER_CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Setup async database
        self.async_engine = create_async_engine(
            str(settings.SQLALCHEMY_DATABASE_URI).replace("+psycopg", "+asyncpg"),
            echo=False,
            future=True
        )
        self.async_session_maker = async_sessionmaker(
            self.async_engine, 
            expire_on_commit=False, 
            class_=AsyncSession
        )
        
        # Setup Kafka consumer
        self._setup_consumer()
    
    def _setup_consumer(self):
        """Setup Kafka consumer."""
        try:
            self.consumer = KafkaConsumer(
                settings.KAFKA_TOPIC_SOURCE_CHANGES,
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                group_id='indexing-worker-group',
                consumer_timeout_ms=1000
            )
            logger.info(f"Connected to Kafka topic: {settings.KAFKA_TOPIC_SOURCE_CHANGES}")
        except Exception as e:
            logger.error(f"Failed to setup Kafka consumer: {e}")
            self.consumer = None
    
    async def process_source(self, source_id: str, source_type: str, data: Any, mime_type: str = None) -> str:
        """
        Process a source using the appropriate processor.
        
        Args:
            source_id: ID of the source being processed
            source_type: Type of source (document, url, text)
            data: Data to process (bytes for files, str for URLs/text)
            mime_type: MIME type for document sources (optional)
            
        Returns:
            Extracted text as string
            
        Raises:
            ValueError: If processing fails
        """
        try:
            logger.info(f"🔧 Creating processor for source type: {source_type}")
            processor = self.processor_factory.create_processor(source_type, mime_type)
            logger.info(f"✅ Using processor: {processor.__class__.__name__}")
            
            logger.info(f"🔄 Starting text extraction for source {source_id}")
            text = await processor.process(data)
            
            if not text or not text.strip():
                logger.warning(f"⚠️ No text extracted from source {source_id}")
                return ""
    
            logger.info(f"✅ Successfully extracted {len(text)} characters from source {source_id}")
            logger.debug(f"📄 First 200 characters: {text[:200]}...")
            return text
            
        except Exception as e:
            logger.error(f"❌ Failed to process source {source_id}: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            raise ValueError(f"Source processing failed: {str(e)}")
    
    def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings for text chunks."""
        if not self.openai_client:
            logger.error("❌ OpenAI client not available")
            return []
        
        try:
            logger.info(f"🧠 Creating embeddings for {len(texts)} text chunks")
            logger.debug(f"Using model: {settings.OPENAI_MODEL}")
            
            response = self.openai_client.embeddings.create(
                model=settings.OPENAI_MODEL,
                input=texts
            )
            
            embeddings = [embedding.embedding for embedding in response.data]
            logger.info(f"✅ Successfully created {len(embeddings)} embeddings")
            logger.debug(f"First embedding dimension: {len(embeddings[0]) if embeddings else 0}")
            
            return embeddings
        except Exception as e:
            logger.error(f"❌ Failed to create embeddings: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            return []
    
    def _get_file_data(self, bucket: str, object_key: str) -> bytes:
        """Get file data from MinIO."""
        try:
            from app.core.db import setup_minio_client
            minio_client, _ = setup_minio_client()
            response = minio_client.get_object(bucket, object_key)
            logger.debug(f"📁 Retrieved file from MinIO: {bucket}/{object_key}")
            return response.read()
        except Exception as e:
            logger.error(f"❌ Failed to get file data from MinIO: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            return b""
    
    async def _update_entity_status(self, entity_id: str, status: ProcessingStatus, entity_type: str = "entity"):
        """Update entity status in database (unified method for documents and sources)."""
        try:
            async with self.async_session_maker() as session:
                if entity_type == "document":
                    result = await session.execute(
                        select(Document).where(Document.id == entity_id)
                    )
                    entity = result.scalars().first()
                else:  # source
                    result = await session.execute(
                        select(Source).where(Source.id == entity_id)
                    )
                    entity = result.scalars().first()
                
                if entity:
                    entity.status = status
                    await session.commit()
                    logger.info(f"✅ Updated {entity_type} {entity_id} status to {status}")
                else:
                    logger.warning(f"⚠️ {entity_type.capitalize()} {entity_id} not found for status update")
        except Exception as e:
            logger.error(f"❌ Failed to update {entity_type} status: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
    
    async def _update_document_status(self, document_id: str, status: ProcessingStatus):
        """Update document status in database."""
        await self._update_entity_status(document_id, status, "document")
    
    async def _update_source_status(self, source_id: str, status: ProcessingStatus):
        """Update source status in database."""
        await self._update_entity_status(source_id, status, "source")
    
    async def process_document(self, document_id: str, owner_id: str, filename: str, metadata: Dict[str, Any]) -> bool:
        """Process a single document."""
        try:
            logger.info(f"🚀 Starting document processing for document {document_id}")
            
            # Update document status to processing
            await self._update_document_status(document_id, ProcessingStatus.PROCESSING)
            
            # Get file from MinIO
            file_data = self._get_file_data(metadata.get("bucket"), metadata.get("object_key"))
            if not file_data:
                logger.error(f"❌ Failed to get file data for document {document_id}")
                await self._update_document_status(document_id, ProcessingStatus.FAILED)
                return False
            
            # Extract text
            text = await self.process_source(document_id, "document", file_data, metadata.get("mime_type", ""))
            if not text:
                logger.error(f"❌ No text extracted from document {document_id}")
                await self._update_document_status(document_id, ProcessingStatus.FAILED)
                return False
            
            # Split text into chunks
            chunks = self.text_splitter.split_text(text)
            logger.info(f"📄 Split document into {len(chunks)} chunks")
            
            # Create embeddings
            embeddings = self.create_embeddings(chunks)
            if not embeddings or len(embeddings) != len(chunks):
                logger.error(f"❌ Failed to create embeddings for document {document_id}")
                await self._update_document_status(document_id, ProcessingStatus.FAILED)
                return False
            
            # Prepare chunks for Qdrant
            qdrant_chunks = []
            for i, chunk in enumerate(chunks):
                qdrant_chunks.append({
                    "text": chunk,
                    "filename": filename,
                    "owner_id": owner_id,
                    "metadata": metadata
                })
            
            # Store in Qdrant
            success = qdrant_manager.upsert_chunks(document_id, qdrant_chunks, embeddings)
            if not success:
                logger.error(f"❌ Failed to store chunks in Qdrant for document {document_id}")
                await self._update_document_status(document_id, ProcessingStatus.FAILED)
                return False
            
            # Update document status to indexed
            await self._update_document_status(document_id, ProcessingStatus.INDEXED)
            logger.info(f"🎉 Successfully processed document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to process document {document_id}: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            await self._update_document_status(document_id, ProcessingStatus.FAILED)
            return False
    
    async def process_url_source(self, source_id: str, owner_id: str, metadata: Dict[str, Any]) -> bool:
        """Process a URL source."""
        logger.info(f"🚀 Starting URL source processing for source {source_id}")
        logger.debug(f"Owner ID: {owner_id}")
        logger.debug(f"Metadata: {metadata}")
        
        try:
            # Update source status to processing
            logger.info(f"📝 Updating source {source_id} status to PROCESSING")
            await self._update_source_status(source_id, ProcessingStatus.PROCESSING)
            
            # Extract URL from metadata
            url = metadata.get("url")
            if not url:
                logger.error(f"❌ No URL found in metadata for source {source_id}")
                logger.error(f"Available metadata keys: {list(metadata.keys())}")
                await self._update_source_status(source_id, ProcessingStatus.FAILED)
                return False
            
            logger.info(f"🌐 Processing URL source {source_id}: {url}")
            
            # Extract text from URL using URLProcessor
            logger.info(f"📄 Extracting text from URL: {url}")
            text = await self.process_source(source_id, "url", url)
            if not text:
                logger.error(f"❌ No text extracted from URL source {source_id}")
                await self._update_source_status(source_id, ProcessingStatus.FAILED)
                return False
            
            logger.info(f"✅ Successfully extracted {len(text)} characters from URL")
            
            # Split text into chunks
            logger.info(f"✂️ Splitting text into chunks")
            chunks = self.text_splitter.split_text(text)
            logger.info(f"📊 Created {len(chunks)} chunks from text")
            
            # Create embeddings
            logger.info(f"🧠 Creating embeddings for {len(chunks)} chunks")
            embeddings = self.create_embeddings(chunks)
            if not embeddings or len(embeddings) != len(chunks):
                logger.error(f"❌ Failed to create embeddings for URL source {source_id}")
                logger.error(f"Expected {len(chunks)} embeddings, got {len(embeddings) if embeddings else 0}")
                await self._update_source_status(source_id, ProcessingStatus.FAILED)
                return False
            
            logger.info(f"✅ Successfully created {len(embeddings)} embeddings")
            
            # Prepare chunks for Qdrant
            logger.info(f"📦 Preparing chunks for Qdrant storage")
            qdrant_chunks = []
            for i, chunk in enumerate(chunks):
                qdrant_chunks.append({
                    "text": chunk,
                    "source_id": source_id,
                    "source_type": "url",
                    "url": url,
                    "owner_id": owner_id,
                    "metadata": metadata
                })
            
            logger.info(f"💾 Storing {len(qdrant_chunks)} chunks in Qdrant")
            # Store in Qdrant using source_id as document identifier
            success = qdrant_manager.upsert_chunks(source_id, qdrant_chunks, embeddings)
            if not success:
                logger.error(f"❌ Failed to store chunks in Qdrant for URL source {source_id}")
                await self._update_source_status(source_id, ProcessingStatus.FAILED)
                return False
            
            logger.info(f"✅ Successfully stored chunks in Qdrant")
            
            # Update source status to indexed
            logger.info(f"📝 Updating source {source_id} status to INDEXED")
            await self._update_source_status(source_id, ProcessingStatus.INDEXED)
            logger.info(f"🎉 Successfully processed URL source {source_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to process URL source {source_id}: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            await self._update_source_status(source_id, ProcessingStatus.FAILED)
            return False
    
    async def process_event(self, event_data: Dict[str, Any]):
        """Process a single event asynchronously."""
        try:
            logger.info(f"🔍 Received event: {event_data}")
            
            # Try to determine event type based on the data structure
            if "document_id" in event_data:
                # This is a DocumentEvent
                logger.info(f"📄 Processing DocumentEvent for document {event_data.get('document_id')}")
                event = DocumentEvent(**event_data)
                await self._process_document_event(event)
            elif "source_id" in event_data:
                # This is a URLSourceEvent
                logger.info(f"🌐 Processing URLSourceEvent for source {event_data.get('source_id')}")
                event = URLSourceEvent(**event_data)
                await self._process_url_source_event(event)
            else:
                logger.error(f"❌ Unknown event type: {event_data}")
                
        except Exception as e:
            logger.error(f"❌ Failed to process event: {e}")
            logger.error(f"Event data: {event_data}")
            logger.error(f"Exception type: {type(e).__name__}")
            # Re-raise to allow proper error handling upstream
            raise
    
    async def _process_document_event(self, event: DocumentEvent):
        """Process a document event asynchronously."""
        if event.op == "c":  # Create
            logger.info(f"🆕 Processing create event for document {event.document_id}")
            await self.process_document(
                str(event.document_id),
                str(event.owner_id),
                event.doc_metadata.get("filename", ""),
                event.doc_metadata
            )
                
        elif event.op == "d":  # Delete
            logger.info(f"🗑️ Processing delete event for document {event.document_id}")
            success = qdrant_manager.delete_document_chunks(str(event.document_id))
            if not success:
                logger.error(f"❌ Failed to delete chunks for document {event.document_id}")
                
        elif event.op == "u":  # Update
            logger.info(f"🔄 Processing update event for document {event.document_id}")
            # For updates, we reprocess the entire document
            await self.process_document(
                str(event.document_id),
                str(event.owner_id),
                event.doc_metadata.get("filename", ""),
                event.doc_metadata
            )
    
    async def _process_url_source_event(self, event: URLSourceEvent):
        """Process a URL source event."""
        logger.info(f"🌐 Processing URL source event: op={event.op}, source_id={event.source_id}")
        logger.debug(f"Event details: {event.model_dump()}")
        
        if event.op == "c":  # Create
            logger.info(f"🆕 Processing create event for URL source {event.source_id}")
            logger.info(f"Owner ID: {event.owner_id}")
            logger.debug(f"Source metadata: {event.source_metadata}")
            
            # Process the URL source
            await self.process_url_source(
                str(event.source_id),
                str(event.owner_id),
                event.source_metadata
            )
                
        elif event.op == "d":  # Delete
            logger.info(f"🗑️ Processing delete event for URL source {event.source_id}")
            success = qdrant_manager.delete_document_chunks(str(event.source_id))
            if not success:
                logger.error(f"❌ Failed to delete chunks for URL source {event.source_id}")
                
        elif event.op == "u":  # Update
            logger.info(f"🔄 Processing update event for URL source {event.source_id}")
            # For updates, we reprocess the entire URL source
            await self.process_url_source(
                str(event.source_id),
                str(event.owner_id),
                event.source_metadata
            )
    
    async def run(self):
        """Main worker loop."""
        logger.info("🚀 Starting indexing worker...")
        
        while True:
            try:
                if not self.consumer:
                    logger.error("❌ Kafka consumer not available, retrying...")
                    await asyncio.sleep(KAFKA_RETRY_DELAY_SECONDS)
                    self._setup_consumer()
                    continue
                
                # Poll for messages
                messages = self.consumer.poll(timeout_ms=1000, max_records=settings.INDEXING_WORKER_BATCH_SIZE)
                
                if messages:
                    logger.info(f"📨 Received {sum(len(msgs) for msgs in messages.values())} messages from Kafka")
                
                # Collect all messages to process concurrently
                tasks = []
                for topic_partition, partition_messages in messages.items():
                    logger.info(f"📬 Processing messages from topic: {topic_partition.topic}, partition: {topic_partition.partition}")
                    for message in partition_messages:
                        try:
                            logger.info(f"📋 Processing message: offset={message.offset}, key={message.key}")
                            # Create async task for each message
                            task = asyncio.create_task(self.process_event(message.value))
                            tasks.append((task, message))
                        except Exception as e:
                            logger.error(f"❌ Failed to create task for message: {e}")
                            logger.error(f"Message offset: {message.offset}")
                            logger.error(f"Exception type: {type(e).__name__}")
                
                # Wait for all tasks to complete (with timeout)
                if tasks:
                    logger.info(f"🚀 Processing {len(tasks)} events concurrently")
                    try:
                        # Wait for all tasks with a reasonable timeout
                        await asyncio.wait_for(
                            asyncio.gather(*[task for task, _ in tasks], return_exceptions=True),
                            timeout=TASK_TIMEOUT_SECONDS
                        )
                        
                        # Check results and handle any exceptions
                        for i, (task, message) in enumerate(tasks):
                            if task.done():
                                try:
                                    result = task.result()
                                    logger.debug(f"✅ Task {i} completed successfully")
                                except Exception as e:
                                    logger.error(f"❌ Task {i} failed: {e}")
                                    logger.error(f"Message offset: {message.offset}")
                            else:
                                logger.warning(f"⚠️ Task {i} did not complete within timeout")
                                task.cancel()
                            
                    except asyncio.TimeoutError:
                        logger.error(f"❌ Timeout waiting for {len(tasks)} tasks to complete")
                        # Cancel all tasks
                        for task, _ in tasks:
                            task.cancel()
                    except Exception as e:
                        logger.error(f"❌ Error in concurrent processing: {e}")
                        # Cancel all tasks
                        for task, _ in tasks:
                            task.cancel()
                
                # Small delay to prevent busy waiting
                await asyncio.sleep(POLLING_INTERVAL_SECONDS)
                
            except KafkaError as e:
                logger.error(f"❌ Kafka error: {e}")
                await asyncio.sleep(KAFKA_RETRY_DELAY_SECONDS)
            except Exception as e:
                logger.error(f"❌ Unexpected error in worker loop: {e}")
                logger.error(f"Exception type: {type(e).__name__}")
                await asyncio.sleep(KAFKA_RETRY_DELAY_SECONDS)


    async def cleanup(self):
        """Clean up resources asynchronously."""
        logger.info("🧹 Cleaning up indexing worker resources...")
        
        if self.consumer:
            self.consumer.close()
            logger.info("✅ Kafka consumer closed")
        
        if self.executor:
            self.executor.shutdown(wait=True)
            logger.info("✅ Thread pool executor shutdown")
        
        if self.async_engine:
            await self.async_engine.dispose()
            logger.info("✅ Async engine disposed")
    
    def cleanup_sync(self):
        """Synchronous cleanup for use in main function."""
        logger.info("🧹 Cleaning up indexing worker resources...")
        
        if self.consumer:
            self.consumer.close()
            logger.info("✅ Kafka consumer closed")
        
        if self.executor:
            self.executor.shutdown(wait=True)
            logger.info("✅ Thread pool executor shutdown")
        
        if self.async_engine:
            # Note: async_engine.dispose() is async, but this is sync context
            logger.info("✅ Async engine cleanup noted (dispose in async context)")
    
    def is_healthy(self) -> bool:
        """
        Check if the worker is in a healthy state.
        
        Returns:
            True if all components are properly initialized, False otherwise
        """
        return (
            self.consumer is not None and
            self.openai_client is not None and
            self.async_engine is not None
        )

async def main_async():
    """Async main entry point for the indexing worker."""
    worker = IndexingWorker()
    try:
        await worker.run()
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down indexing worker...")
    finally:
        await worker.cleanup()

def main():
    """Main entry point for the indexing worker."""
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down indexing worker...")
    except Exception as e:
        logger.error(f"❌ Unexpected error in main: {e}")
        logger.error(f"Exception type: {type(e).__name__}")


if __name__ == "__main__":
    main() 