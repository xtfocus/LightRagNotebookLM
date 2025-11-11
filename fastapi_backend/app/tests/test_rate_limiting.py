"""
Tests for rate limiting service.

Tests the SimpleRateLimiter implementation using your son's logic.
"""

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy import select, func

from app.services.rate_limiting import SimpleRateLimiter, MockRateLimiter
from app.models import ProcessingStatus


class TestSimpleRateLimiter:
    """Test the SimpleRateLimiter implementation."""
    
    @pytest.fixture
    def mock_session_maker(self):
        """Create a mock session maker."""
        mock_session = AsyncMock()
        mock_session_maker = AsyncMock()
        mock_session_maker.return_value.__aenter__.return_value = mock_session
        return mock_session_maker, mock_session
    
    @pytest.fixture
    def rate_limiter(self, mock_session_maker):
        """Create a rate limiter instance."""
        session_maker, _ = mock_session_maker
        return SimpleRateLimiter(session_maker)
    
    @pytest.fixture
    def user_id(self):
        """Create a test user ID."""
        return uuid4()
    
    @pytest.fixture
    def notebook_id(self):
        """Create a test notebook ID."""
        return uuid4()
    
    async def test_check_processing_limit_under_limit(self, rate_limiter, mock_session_maker, user_id, notebook_id):
        """Test that processing limit allows uploads when under limit."""
        session_maker, mock_session = mock_session_maker
        
        # Mock the query result - only 3 files processing (under limit of 5)
        mock_result = MagicMock()
        mock_result.scalar.return_value = 3
        mock_session.execute.return_value = mock_result
        
        # Test the rate limiter
        result = await rate_limiter.check_processing_limit(user_id, notebook_id)
        
        # Should allow upload (3 < 5)
        assert result is True
        
        # Verify the query was executed correctly
        mock_session.execute.assert_called_once()
        call_args = mock_session.execute.call_args[0][0]
        assert "PROCESSING" in str(call_args)
        assert "owner_id" in str(call_args)  # Should check per-user, not per-notebook
    
    async def test_check_processing_limit_at_limit(self, rate_limiter, mock_session_maker, user_id, notebook_id):
        """Test that processing limit blocks uploads when at limit."""
        session_maker, mock_session = mock_session_maker
        
        # Mock the query result - 5 files processing (at limit)
        mock_result = MagicMock()
        mock_result.scalar.return_value = 5
        mock_session.execute.return_value = mock_result
        
        # Test the rate limiter
        result = await rate_limiter.check_processing_limit(user_id, notebook_id)
        
        # Should block upload (5 >= 5)
        assert result is False
    
    async def test_check_processing_limit_over_limit(self, rate_limiter, mock_session_maker, user_id, notebook_id):
        """Test that processing limit blocks uploads when over limit."""
        session_maker, mock_session = mock_session_maker
        
        # Mock the query result - 6 files processing (over limit)
        mock_result = MagicMock()
        mock_result.scalar.return_value = 6
        mock_session.execute.return_value = mock_result
        
        # Test the rate limiter
        result = await rate_limiter.check_processing_limit(user_id, notebook_id)
        
        # Should block upload (6 >= 5)
        assert result is False
    
    async def test_check_processing_limit_zero_processing(self, rate_limiter, mock_session_maker, user_id, notebook_id):
        """Test that processing limit allows uploads when no files are processing."""
        session_maker, mock_session = mock_session_maker
        
        # Mock the query result - 0 files processing
        mock_result = MagicMock()
        mock_result.scalar.return_value = 0
        mock_session.execute.return_value = mock_result
        
        # Test the rate limiter
        result = await rate_limiter.check_processing_limit(user_id, notebook_id)
        
        # Should allow upload (0 < 5)
        assert result is True
    
    async def test_check_processing_limit_without_notebook_id(self, rate_limiter, mock_session_maker, user_id):
        """Test that processing limit works without notebook_id (per-user limit)."""
        session_maker, mock_session = mock_session_maker
        
        # Mock the query result - 3 files processing
        mock_result = MagicMock()
        mock_result.scalar.return_value = 3
        mock_session.execute.return_value = mock_result
        
        # Test the rate limiter without notebook_id
        result = await rate_limiter.check_processing_limit(user_id, None)
        
        # Should allow upload (3 < 5)
        assert result is True
        
        # Verify the query was executed correctly (per-user, not per-notebook)
        mock_session.execute.assert_called_once()
        call_args = mock_session.execute.call_args[0][0]
        assert "owner_id" in str(call_args)
        assert "notebook_id" not in str(call_args)  # Should not filter by notebook
    
    async def test_check_upload_rate_limit_always_true(self, rate_limiter, user_id):
        """Test that upload rate limit always returns True for demo."""
        result = await rate_limiter.check_upload_rate_limit(user_id)
        assert result is True
    
    async def test_check_daily_quota_always_true(self, rate_limiter, user_id):
        """Test that daily quota always returns True for demo."""
        result = await rate_limiter.check_daily_quota(user_id)
        assert result is True
    
    async def test_record_upload_no_op(self, rate_limiter, user_id, notebook_id):
        """Test that record_upload does nothing for demo."""
        # Should not raise any exception
        await rate_limiter.record_upload(user_id, notebook_id, 1024)


class TestMockRateLimiter:
    """Test the MockRateLimiter for testing."""
    
    @pytest.fixture
    def user_id(self):
        """Create a test user ID."""
        return uuid4()
    
    @pytest.fixture
    def notebook_id(self):
        """Create a test notebook ID."""
        return uuid4()
    
    async def test_mock_rate_limiter_allow(self, user_id, notebook_id):
        """Test that mock rate limiter allows when configured to allow."""
        rate_limiter = MockRateLimiter(should_allow=True)
        
        assert await rate_limiter.check_processing_limit(user_id, notebook_id) is True
        assert await rate_limiter.check_processing_limit(user_id, None) is True  # Test without notebook_id
        assert await rate_limiter.check_upload_rate_limit(user_id) is True
        assert await rate_limiter.check_daily_quota(user_id) is True
    
    async def test_mock_rate_limiter_block(self, user_id, notebook_id):
        """Test that mock rate limiter blocks when configured to block."""
        rate_limiter = MockRateLimiter(should_allow=False)
        
        assert await rate_limiter.check_processing_limit(user_id, notebook_id) is False
        assert await rate_limiter.check_processing_limit(user_id, None) is False  # Test without notebook_id
        assert await rate_limiter.check_upload_rate_limit(user_id) is False
        assert await rate_limiter.check_daily_quota(user_id) is False
    
    async def test_mock_rate_limiter_record_upload(self, user_id, notebook_id):
        """Test that mock rate limiter records uploads."""
        rate_limiter = MockRateLimiter()
        
        # Record an upload
        await rate_limiter.record_upload(user_id, notebook_id, 1024)
        
        # Check that it was recorded
        assert len(rate_limiter.recorded_uploads) == 1
        assert rate_limiter.recorded_uploads[0]['user_id'] == user_id
        assert rate_limiter.recorded_uploads[0]['notebook_id'] == notebook_id
        assert rate_limiter.recorded_uploads[0]['file_size'] == 1024 