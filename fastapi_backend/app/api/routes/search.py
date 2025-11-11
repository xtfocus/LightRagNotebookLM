from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
import openai

from app.api.deps import get_current_user
from app.models import User, SearchResults, SearchResult
from app.core.config import settings
from app.core.qdrant import qdrant_manager

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/documents")
async def search_documents(
    query: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    score_threshold: float = Query(0.7, ge=0.0, le=1.0, description="Minimum similarity score"),
    current_user: User = Depends(get_current_user)
) -> SearchResults:
    """Search documents using vector similarity."""
    
    if not settings.OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
    
    try:
        # Create embedding for the query
        openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        response = openai_client.embeddings.create(
            model=settings.OPENAI_MODEL,
            input=[query]
        )
        query_embedding = response.data[0].embedding
        
        # Search in Qdrant
        search_results = qdrant_manager.search_similar(
            query_embedding=query_embedding,
            limit=limit,
            score_threshold=score_threshold,
            owner_id=str(current_user.id)
        )
        
        # Convert to SearchResult objects
        results = []
        for result in search_results:
            payload = result["payload"]
            search_result = SearchResult(
                document_id=payload["document_id"],
                filename=payload["filename"],
                score=result["score"],
                chunk_text=payload["chunk_text"],
                chunk_index=payload["chunk_index"],
                doc_metadata=payload["metadata"]
            )
            results.append(search_result)
        
        return SearchResults(
            results=results,
            total=len(results),
            query=query
        )
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail="Search failed")


@router.get("/health")
async def search_health() -> dict:
    """Check search service health."""
    try:
        # Check Qdrant connection
        collection_info = qdrant_manager.get_collection_info()
        
        # Check OpenAI connection
        openai_available = bool(settings.OPENAI_API_KEY)
        
        return {
            "status": "healthy",
            "qdrant": {
                "connected": collection_info is not None,
                "collection_info": collection_info
            },
            "openai": {
                "available": openai_available,
                "model": settings.OPENAI_MODEL
            }
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        } 