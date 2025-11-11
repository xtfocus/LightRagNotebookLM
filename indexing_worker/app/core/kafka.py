import json
import time
from typing import Dict, Any
from loguru import logger
from kafka import KafkaProducer
from kafka.errors import KafkaError

from app.core.config import settings
from app.models import DocumentEvent


class KafkaEventPublisher:
    """Kafka event publisher for document events."""
    
    def __init__(self):
        self.producer = None
        self._connect()
    
    def _connect(self):
        """Connect to Kafka broker."""
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
    
    def publish_document_event(self, event: DocumentEvent) -> bool:
        """Publish a document event to Kafka."""
        if not self.producer:
            logger.error("Kafka producer not connected")
            return False
        
        try:
            # Convert event to dict
            event_dict = event.model_dump()
            
            # Use document_id as key for partitioning
            key = str(event.document_id)
            
            future = self.producer.send(
                settings.KAFKA_TOPIC_SOURCE_CHANGES,
                key=key,
                value=event_dict
            )
            
            # Wait for the send to complete
            record_metadata = future.get(timeout=10)
            
            logger.info(
                f"Published event {event.op} for document {event.document_id} "
                f"to topic {record_metadata.topic} partition {record_metadata.partition} "
                f"offset {record_metadata.offset}"
            )
            return True
            
        except KafkaError as e:
            logger.error(f"Failed to publish event to Kafka: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error publishing event: {e}")
            return False
    
    def _create_event(
        self,
        document_id: str,
        operation: str,
        metadata: Dict[str, Any],
        owner_id: str,
        version: int = 1
    ) -> DocumentEvent:
        """Create a document event."""
        return DocumentEvent(
            op=operation,
            ts_ms=int(time.time() * 1000),
            document_id=document_id,
            version=version,
            doc_metadata=metadata,
            owner_id=owner_id
        )
    
    def close(self):
        """Close the Kafka producer."""
        if self.producer:
            self.producer.close()
            logger.info("Kafka producer closed")


# Global instance
kafka_publisher = KafkaEventPublisher() 