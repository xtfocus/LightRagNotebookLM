import pytest
import json
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.models import Document, ProcessingStatus, DocumentEvent
from app.core.kafka import KafkaEventPublisher
from app.core.qdrant import QdrantManager


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_kafka_publisher():
    with patch('app.core.kafka.KafkaEventPublisher') as mock:
        mock.return_value.publish_document_event.return_value = True
        yield mock


@pytest.fixture
def mock_qdrant_manager():
    with patch('app.core.qdrant.QdrantManager') as mock:
        mock.return_value.search_similar.return_value = []
        mock.return_value.get_collection_info.return_value = {
            "name": "documents",
            "vectors_count": 0,
            "points_count": 0,
            "status": "green"
        }
        yield mock


def test_document_model():
    """Test Document model creation."""
    document = Document(
        filename="test.pdf",
        mime_type="application/pdf",
        size=1024,
        bucket="app-docs",
        object_key="user_123/test.pdf",
        document_metadata=json.dumps({"test": "data"}),
        status=ProcessingStatus.PENDING,
        version=1,
        owner_id="123e4567-e89b-12d3-a456-426614174000"
    )
    
    assert document.filename == "test.pdf"
    assert document.status == ProcessingStatus.PENDING
    assert json.loads(document.document_metadata) == {"test": "data"}


def test_document_event_model():
    """Test DocumentEvent model creation."""
    event = DocumentEvent(
        op="c",
        ts_ms=1234567890,
        document_id="123e4567-e89b-12d3-a456-426614174000",
        version=1,
        doc_metadata={"filename": "test.pdf"},
        owner_id="123e4567-e89b-12d3-a456-426614174000"
    )
    
    assert event.op == "c"
    assert event.document_id == "123e4567-e89b-12d3-a456-426614174000"
    assert event.doc_metadata["filename"] == "test.pdf"


def test_kafka_event_publisher():
    """Test Kafka event publisher."""
    publisher = KafkaEventPublisher()
    
    # Test event creation
    event = publisher.create_document_event(
        document_id="test-doc",
        operation="c",
        metadata={"filename": "test.pdf"},
        owner_id="test-user",
        version=1
    )
    
    assert event.op == "c"
    assert event.document_id == "test-doc"
    assert event.metadata["filename"] == "test.pdf"


def test_qdrant_manager():
    """Test Qdrant manager."""
    manager = QdrantManager()
    
    # Test search similar (should return empty list when not connected)
    results = manager.search_similar(
        query_embedding=[0.1, 0.2, 0.3],
        limit=10,
        score_threshold=0.7
    )
    
    assert isinstance(results, list)


def test_search_health_endpoint(client, mock_qdrant_manager):
    """Test search health endpoint."""
    response = client.get("/api/v1/search/health")
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert "qdrant" in data
    assert "openai" in data


def test_search_documents_endpoint_requires_auth(client):
    """Test search documents endpoint requires authentication."""
    response = client.get("/api/v1/search/documents?query=test")
    assert response.status_code == 401  # Unauthorized


def test_upload_files_endpoint_requires_auth(client):
    """Test upload files endpoint requires authentication."""
    response = client.post("/api/v1/uploads/files")
    assert response.status_code == 401  # Unauthorized


def test_list_documents_endpoint_requires_auth(client):
    """Test list documents endpoint requires authentication."""
    response = client.get("/api/v1/uploads/documents")
    assert response.status_code == 401  # Unauthorized


def test_get_document_endpoint_requires_auth(client):
    """Test get document endpoint requires authentication."""
    response = client.get("/api/v1/uploads/documents/123e4567-e89b-12d3-a456-426614174000")
    assert response.status_code == 401  # Unauthorized


def test_delete_document_endpoint_requires_auth(client):
    """Test delete document endpoint requires authentication."""
    response = client.delete("/api/v1/uploads/documents/123e4567-e89b-12d3-a456-426614174000")
    assert response.status_code == 401  # Unauthorized


def test_delete_documents_endpoint_requires_auth(client):
    """Test delete documents endpoint requires authentication."""
    response = client.delete("/api/v1/uploads/documents")
    assert response.status_code == 401  # Unauthorized


@pytest.mark.asyncio
async def test_document_status_enum():
    """Test ProcessingStatus enum values."""
    assert ProcessingStatus.PENDING == "pending"
    assert ProcessingStatus.PROCESSING == "processing"
    assert ProcessingStatus.INDEXED == "indexed"
    assert ProcessingStatus.FAILED == "failed"


def test_document_metadata_json_handling():
    """Test JSON handling in document metadata."""
    metadata = {"filename": "test.pdf", "size": 1024}
    metadata_json = json.dumps(metadata)
    
    # Test serialization
    assert metadata_json == '{"filename": "test.pdf", "size": 1024}'
    
    # Test deserialization
    parsed_metadata = json.loads(metadata_json)
    assert parsed_metadata == metadata


def test_kafka_event_serialization():
    """Test Kafka event serialization."""
    event = DocumentEvent(
        op="c",
        ts_ms=1234567890,
        document_id="test-doc",
        version=1,
        doc_metadata={"filename": "test.pdf"},
        owner_id="test-user"
    )
    
    # Test model serialization
    event_dict = event.model_dump()
    assert event_dict["op"] == "c"
    assert event_dict["document_id"] == "test-doc"
    assert event_dict["metadata"]["filename"] == "test.pdf"


if __name__ == "__main__":
    pytest.main([__file__]) 