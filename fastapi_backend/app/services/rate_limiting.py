from abc import ABC, abstractmethod
from uuid import UUID
from sqlalchemy import select, func

from app.models import NotebookSource, Document, ProcessingStatus
from app.core.config import settings


class RateLimiterInterface(ABC):
    """Abstract interface for rate limiting services."""
    
    @abstractmethod
    async def check_processing_limit(self, user_id: UUID, notebook_id: UUID = None) -> bool:
        """Check if user can process more files across all their notebooks."""
        pass
    
    @abstractmethod
    async def check_upload_rate_limit(self, user_id: UUID) -> bool:
        """Check if user can upload more files per minute."""
        pass
    
    @abstractmethod
    async def check_daily_quota(self, user_id: UUID) -> bool:
        """Check if user has exceeded daily upload quota."""
        pass
    
    @abstractmethod
    async def record_upload(self, user_id: UUID, notebook_id: UUID, file_size: int):
        """Record an upload for rate limiting purposes."""
        pass


class SimpleRateLimiter(RateLimiterInterface):
    """Simple rate limiter implementation for demo app using your son's logic."""
    
    def __init__(self, session_maker):
        self.session_maker = session_maker
        # Concurrent processing limit (only PROCESSING status - your son's logic)
        self.max_concurrent_processing = getattr(settings, 'MAX_CONCURRENT_PROCESSING_PER_USER', 5)
    
    async def check_processing_limit(self, user_id: UUID, notebook_id: UUID = None) -> bool:
        """
        Check if user can process more files across all their notebooks.
        
        Uses your son's brilliant logic: only count sources that are currently being processed.
        This prevents abuse by limiting per user, not per notebook.
        
        Args:
            user_id: The user ID to check limits for
            notebook_id: Optional notebook ID (not used for per-user limits)
        """
        async with self.session_maker() as session:
            # Count only sources that are currently being processed across ALL user's notebooks
            result = await session.execute(
                select(func.count()).select_from(NotebookSource)
                .join(Document, NotebookSource.document_id == Document.id)
                .where(
                    Document.owner_id == user_id,  # Check across all user's notebooks
                    Document.status == ProcessingStatus.PROCESSING
                )
            )
            processing_count = result.scalar() or 0
            
            # Allow upload if processing count is less than limit
            return processing_count < self.max_concurrent_processing
    
    async def check_upload_rate_limit(self, user_id: UUID) -> bool:
        """
        Check if user can upload more files per minute.
        
        For demo app: no rate limiting implemented.
        Future: implement token bucket algorithm with Redis.
        """
        # No rate limiting for demo app
        return True
    
    async def check_daily_quota(self, user_id: UUID) -> bool:
        """
        Check if user has exceeded daily upload quota.
        
        For demo app: no daily quota implemented.
        Future: implement daily quota with rollover logic.
        """
        # No daily quota for demo app
        return True
    
    async def record_upload(self, user_id: UUID, notebook_id: UUID, file_size: int):
        """
        Record an upload for rate limiting purposes.
        
        For demo app: no recording implemented.
        Future: record for analytics and quota tracking.
        """
        # No recording for demo app
        pass


class MockRateLimiter(RateLimiterInterface):
    """Mock rate limiter for testing."""
    
    def __init__(self, should_allow: bool = True):
        self.should_allow = should_allow
        self.recorded_uploads = []
    
    async def check_processing_limit(self, user_id: UUID, notebook_id: UUID = None) -> bool:
        return self.should_allow
    
    async def check_upload_rate_limit(self, user_id: UUID) -> bool:
        return self.should_allow
    
    async def check_daily_quota(self, user_id: UUID) -> bool:
        return self.should_allow
    
    async def record_upload(self, user_id: UUID, notebook_id: UUID, file_size: int):
        self.recorded_uploads.append({
            'user_id': user_id,
            'notebook_id': notebook_id,
            'file_size': file_size
        }) 