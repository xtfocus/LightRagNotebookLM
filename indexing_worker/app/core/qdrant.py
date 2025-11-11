from typing import List, Dict, Any, Optional
from loguru import logger
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, 
    Filter, FieldCondition, MatchValue,
    CreateCollection, UpdateStatus
)

from app.core.config import settings


class QdrantManager:
    """Qdrant vector database manager."""
    
    def __init__(self):
        self.client = None
        self._connect()
    
    def _connect(self):
        """Connect to Qdrant."""
        try:
            self.client = QdrantClient(
                host=settings.QDRANT_HOST,
                port=settings.QDRANT_PORT
            )
            logger.info(f"Connected to Qdrant at {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
            self._ensure_collection_exists()
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            self.client = None
    
    def _ensure_collection_exists(self):
        """Ensure the documents collection exists."""
        if not self.client:
            return
        
        try:
            # Check if collection exists
            collections = self.client.get_collections()
            collection_names = [c.name for c in collections.collections]
            
            if settings.QDRANT_COLLECTION_NAME not in collection_names:
                # Create collection
                self.client.create_collection(
                    collection_name=settings.QDRANT_COLLECTION_NAME,
                    vectors_config=VectorParams(
                        size=settings.OPENAI_EMBEDDING_DIMENSION,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created collection: {settings.QDRANT_COLLECTION_NAME}")
            else:
                logger.info(f"Collection {settings.QDRANT_COLLECTION_NAME} already exists")
                
        except Exception as e:
            logger.error(f"Failed to ensure collection exists: {e}")
    
    def upsert_chunks(
        self,
        document_id: str,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]]
    ) -> bool:
        """Upsert document chunks with embeddings."""
        logger.info(f"💾 Starting Qdrant upsert for document {document_id}")
        logger.info(f"📊 Chunks: {len(chunks)}, Embeddings: {len(embeddings)}")
        
        if not self.client:
            logger.error("❌ Qdrant client not connected")
            return False
        
        try:
            points = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                logger.debug(f"📝 Creating point {i} for document {document_id}")
                # Use hash of document_id + chunk index to generate unique integer ID
                point_id = hash(f"{document_id}_{i}") & 0x7fffffffffffffff  # Ensure positive 64-bit integer
                point = PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "document_id": document_id,
                        "chunk_index": i,
                        "chunk_text": chunk["text"],
                        "filename": chunk.get("filename", ""),
                        "metadata": chunk.get("metadata", {}),
                        "owner_id": chunk["owner_id"]
                    }
                )
                points.append(point)
            
            logger.info(f"📦 Prepared {len(points)} points for upsert")
            
            # Upsert points
            logger.info(f"🚀 Upserting points to Qdrant collection: {settings.QDRANT_COLLECTION_NAME}")
            self.client.upsert(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                points=points
            )
            
            logger.info(f"✅ Successfully upserted {len(points)} chunks for document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to upsert chunks for document {document_id}: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            return False
    
    def delete_document_chunks(self, document_id: str) -> bool:
        """Delete all chunks for a document."""
        if not self.client:
            logger.error("Qdrant client not connected")
            return False
        
        try:
            # Create filter to match document_id
            filter_condition = Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id)
                    )
                ]
            )
            
            # Delete points
            self.client.delete(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                points_selector=filter_condition
            )
            
            logger.info(f"Deleted chunks for document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete chunks for document {document_id}: {e}")
            return False
    
    def search_similar(
        self,
        query_embedding: List[float],
        limit: int = 10,
        score_threshold: float = 0.7,
        owner_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        if not self.client:
            logger.error("Qdrant client not connected")
            return []
        
        try:
            # Build filter
            filter_condition = None
            if owner_id:
                filter_condition = Filter(
                    must=[
                        FieldCondition(
                            key="owner_id",
                            match=MatchValue(value=owner_id)
                        )
                    ]
                )
            
            # Search
            search_result = self.client.search(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                query_vector=query_embedding,
                query_filter=filter_condition,
                limit=limit,
                score_threshold=score_threshold
            )
            
            # Convert to list of dicts
            results = []
            for result in search_result:
                results.append({
                    "id": result.id,
                    "score": result.score,
                    "payload": result.payload
                })
            
            logger.info(f"Found {len(results)} similar documents")
            return results
            
        except Exception as e:
            logger.error(f"Failed to search similar documents: {e}")
            return []
    
    def get_collection_info(self) -> Optional[Dict[str, Any]]:
        """Get collection information."""
        if not self.client:
            return None
        
        try:
            info = self.client.get_collection(settings.QDRANT_COLLECTION_NAME)
            return {
                "name": info.name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status
            }
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return None


# Global instance
qdrant_manager = QdrantManager() 