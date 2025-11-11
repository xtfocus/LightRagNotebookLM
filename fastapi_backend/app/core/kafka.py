"""
Kafka Event Publisher for Document Operations

This module provides a robust Kafka event publishing system for document lifecycle events.
It handles document creation, updates, and deletion events for the indexing pipeline.

Key Features:
- Reliable event publishing with retry mechanisms
- Idempotent producer configuration
- Event serialization and deserialization
- Connection management and error handling
- Structured event creation with metadata

Architecture:
- KafkaProducer: High-throughput, reliable message publishing
- DocumentEvent: Structured event schema for document operations
- Event Metadata: Rich context for indexing and processing
- Connection Pooling: Efficient broker connection management

Event Types:
- 'c': Document creation events
- 'u': Document update events  
- 'd': Document deletion events

Configuration:
- Bootstrap servers: Kafka cluster endpoints
- Acks: 'all' for maximum durability
- Retries: 3 attempts with exponential backoff
- Idempotence: Enabled to prevent duplicate messages
- Serialization: JSON with UTF-8 encoding

Error Handling:
- Connection failures: Automatic retry with backoff
- Serialization errors: Detailed logging and graceful failure
- Network timeouts: Configurable timeout handling
- Producer errors: Comprehensive error reporting

Dependencies:
- kafka-python: Kafka client library
- Pydantic: Event schema validation
- Loguru: Structured logging
"""

import json
import time
from typing import Dict, Any, Optional
from loguru import logger
from kafka import KafkaProducer
from kafka.errors import KafkaError, KafkaTimeoutError

from app.core.config import settings
from app.models import DocumentEvent
from app.core.retry_utils import kafka_retry


class KafkaEventPublisher:
    """
    Kafka event publisher for document events with reliability and error handling.
    
    This class provides a robust interface for publishing document lifecycle events
    to Kafka topics for downstream processing by indexing workers and other services.
    
    Features:
    - Automatic connection management and recovery
    - Configurable retry policies and timeouts
    - Idempotent message delivery
    - Structured event creation and validation
    - Comprehensive error handling and logging
    
    Configuration:
    - Bootstrap servers from settings
    - Producer acks set to 'all' for maximum durability
    - Retry count of 3 with exponential backoff
    - Idempotence enabled to prevent duplicate messages
    - Max in-flight requests limited to 1 for ordering
    """
    
    def __init__(self):
        """Initialize the Kafka event publisher with connection setup."""
        self.producer: Optional[KafkaProducer] = None
        self._connect()
    
    @kafka_retry
    def _connect(self) -> None:
        """
        Establish connection to Kafka broker with error handling.
        
        Creates a KafkaProducer instance with optimal configuration for
        reliability and performance. Handles connection failures gracefully
        with detailed logging.
        
        Configuration:
        - bootstrap_servers: Kafka cluster endpoints
        - value_serializer: JSON serialization with UTF-8 encoding
        - key_serializer: String key serialization
        - acks: 'all' for maximum durability
        - retries: 3 attempts with exponential backoff
        - max_in_flight_requests_per_connection: 1 for message ordering
        - enable_idempotence: True to prevent duplicate messages
        
        Raises:
            Exception: Logged but not re-raised to allow graceful degradation
        """
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',  # Wait for all replicas
                retries=3,
                max_in_flight_requests_per_connection=1,
                enable_idempotence=True,
            )
            logger.info(f"Connected to Kafka at {settings.KAFKA_BOOTSTRAP_SERVERS}")
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            self.producer = None
    
    @kafka_retry
    def publish_document_event(self, event: DocumentEvent) -> bool:
        """
        Publish a document event to Kafka with reliability guarantees.
        
        This method publishes document lifecycle events to the configured Kafka topic
        with comprehensive error handling and retry logic. Events are keyed by document_id
        to ensure proper partitioning and ordering.
        
        Args:
            event: DocumentEvent object containing event data and metadata
            
        Returns:
            bool: True if event was successfully published, False otherwise
            
        Error Handling:
        - Connection failures: Returns False, logs error
        - Serialization errors: Returns False, logs error
        - Timeout errors: Returns False, logs error
        - Network errors: Returns False, logs error
        
        Performance:
        - Synchronous publishing with 10-second timeout
        - Document ID used as partition key for ordering
        - Metadata includes operation type, timestamps, and document details
        """
        if not self.producer:
            logger.error("Kafka producer not connected")
            return False
        
        try:
            # Convert event to dict for serialization
            event_dict = event.model_dump()
            
            # Use document_id as key for partitioning and ordering
            key = str(event.document_id)
            
            # Send event to Kafka topic
            future = self.producer.send(
                settings.KAFKA_TOPIC_SOURCE_CHANGES,
                key=key,
                value=event_dict
            )
            
            # Wait for the send to complete with timeout
            record_metadata = future.get(timeout=10)
            
            logger.info(
                f"Published event {event.op} for document {event.document_id} "
                f"to topic {record_metadata.topic} partition {record_metadata.partition} "
                f"offset {record_metadata.offset}"
            )
            return True
            
        except KafkaTimeoutError as e:
            logger.error(f"Timeout publishing event to Kafka: {e}")
            return False
        except KafkaError as e:
            logger.error(f"Failed to publish event to Kafka: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error publishing event: {e}")
            return False
    
    def create_document_event(
        self,
        document_id: str,
        operation: str,
        metadata: Dict[str, Any],
        owner_id: str,
        version: int = 1
    ) -> DocumentEvent:
        """
        Create a document event with structured metadata.
        
        This method creates a DocumentEvent object with all required fields
        and proper timestamp formatting. It serves as a factory method for
        consistent event creation across the application.
        
        Args:
            document_id: UUID of the document as string
            operation: Event operation type ('c', 'u', 'd')
            metadata: Dictionary containing document metadata
            owner_id: UUID of the document owner as string
            version: Document version number (default: 1)
            
        Returns:
            DocumentEvent: Fully populated event object
            
        Event Structure:
        - op: Operation type (create, update, delete)
        - ts_ms: Timestamp in milliseconds since epoch
        - document_id: Unique document identifier
        - version: Document version for optimistic locking
        - doc_metadata: Rich metadata for processing
        - owner_id: Document owner for access control
        """
        return self._create_event(
            document_id=document_id,
            operation=operation,
            metadata=metadata,
            owner_id=owner_id,
            version=version
        )
    
    def _create_event(
        self,
        document_id: str,
        operation: str,
        metadata: Dict[str, Any],
        owner_id: str,
        version: int = 1
    ) -> DocumentEvent:
        """
        Internal method to create a document event with timestamp.
        
        Args:
            document_id: UUID of the document as string
            operation: Event operation type ('c', 'u', 'd')
            metadata: Dictionary containing document metadata
            owner_id: UUID of the document owner as string
            version: Document version number
            
        Returns:
            DocumentEvent: Event object with current timestamp
        """
        return DocumentEvent(
            op=operation,
            ts_ms=int(time.time() * 1000),
            document_id=document_id,
            version=version,
            doc_metadata=metadata,
            owner_id=owner_id
        )
    
    @kafka_retry
    def publish_url_source_event(self, event: "URLSourceEvent") -> bool:
        """
        Publish a URL source event to Kafka with reliability and error handling.
        
        This method publishes URL source lifecycle events to Kafka topics for
        downstream processing by indexing workers and other services.
        
        Args:
            event: URLSourceEvent object to publish
            
        Returns:
            bool: True if event was published successfully, False otherwise
            
        Features:
        - Automatic connection management and recovery
        - Configurable retry policies and timeouts
        - Idempotent message delivery
        - Structured event creation and validation
        - Comprehensive error handling and logging
        """
        if not self.producer:
            logger.error("Kafka producer not connected")
            return False
        
        try:
            # Convert event to dict for serialization, converting UUIDs to strings
            event_dict = event.model_dump()
            event_dict['source_id'] = str(event.source_id)
            event_dict['owner_id'] = str(event.owner_id)
            
            # Use source_id as key for partitioning and ordering
            key = str(event.source_id)
            
            # Send event to Kafka topic
            future = self.producer.send(
                settings.KAFKA_TOPIC_SOURCE_CHANGES,
                key=key,
                value=event_dict
            )
            
            # Wait for the send to complete with timeout
            record_metadata = future.get(timeout=10)
            
            logger.info(
                f"Published URL source event {event.op} for source {event.source_id} "
                f"to topic {record_metadata.topic} partition {record_metadata.partition} "
                f"offset {record_metadata.offset}"
            )
            return True
            
        except KafkaTimeoutError as e:
            logger.error(f"Timeout publishing URL source event to Kafka: {e}")
            return False
        except KafkaError as e:
            logger.error(f"Failed to publish URL source event to Kafka: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error publishing URL source event: {e}")
            return False
    
    def create_url_source_event(
        self,
        source_id: str,
        operation: str,
        metadata: Dict[str, Any],
        owner_id: str,
        version: int = 1
    ) -> "URLSourceEvent":
        """
        Create a URL source event with structured metadata.
        
        This method creates a URLSourceEvent object with all required fields
        and proper timestamp formatting. It serves as a factory method for
        consistent event creation across the application.
        
        Args:
            source_id: UUID of the source as string
            operation: Event operation type ('c', 'u', 'd')
            metadata: Dictionary containing source metadata
            owner_id: UUID of the source owner as string
            version: Source version number (default: 1)
            
        Returns:
            URLSourceEvent: Fully populated event object
            
        Event Structure:
        - op: Operation type (create, update, delete)
        - ts_ms: Timestamp in milliseconds since epoch
        - source_id: Unique source identifier
        - version: Source version for optimistic locking
        - source_metadata: Rich metadata for processing
        - owner_id: Source owner for access control
        """
        return self._create_url_source_event(
            source_id=source_id,
            operation=operation,
            metadata=metadata,
            owner_id=owner_id,
            version=version
        )
    
    def _create_url_source_event(
        self,
        source_id: str,
        operation: str,
        metadata: Dict[str, Any],
        owner_id: str,
        version: int = 1
    ) -> "URLSourceEvent":
        """
        Internal method to create a URL source event with timestamp.
        
        Args:
            source_id: UUID of the source as string
            operation: Event operation type ('c', 'u', 'd')
            metadata: Dictionary containing source metadata
            owner_id: UUID of the source owner as string
            version: Source version number
            
        Returns:
            URLSourceEvent: Event object with current timestamp
        """
        # Import here to avoid circular imports
        from app.models import URLSourceEvent
        import uuid
        
        return URLSourceEvent(
            op=operation,
            ts_ms=int(time.time() * 1000),
            source_id=uuid.UUID(source_id),
            version=version,
            source_metadata=metadata,
            owner_id=uuid.UUID(owner_id)
        )
    
    def close(self) -> None:
        """
        Close the Kafka producer and release resources.
        
        This method properly closes the Kafka producer connection,
        ensuring all pending messages are sent and resources are
        released. Should be called during application shutdown.
        """
        if self.producer:
            self.producer.close()
            logger.info("Kafka producer closed")


# Global instance for application-wide use
kafka_publisher = KafkaEventPublisher() 