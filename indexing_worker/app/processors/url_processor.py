"""
URL Processor

This module handles text extraction from URLs using markitdown library.
"""

import asyncio
from typing import Any
from loguru import logger
from urllib.parse import urlparse

from .base import TextProcessor
from app.core.config import settings


class URLProcessor(TextProcessor):
    """Handles URL processing using markitdown."""
    
    def can_handle(self, source_type: str, mime_type: str = None) -> bool:
        """Check if this processor can handle the given source type."""
        return source_type == "url"
    
    async def extract_text(self, url: str) -> str:
        """
        Extract text from URL using markitdown.
        
        Args:
            url: URL to extract text from
            
        Returns:
            Extracted text as markdown string
            
        Raises:
            ValueError: If text extraction fails
        """
        logger.info(f"🌐 Starting URL text extraction for: {url}")
        
        if not isinstance(url, str):
            raise ValueError("URL must be a string")
        
        # Validate and normalize URL
        normalized_url = self._normalize_url(url)
        logger.info(f"🔗 Normalized URL: {normalized_url}")
        
        try:
            async def _convert() -> str:
                def _run():
                    logger.info(f"🔄 Running markitdown conversion for: {normalized_url}")
                    from markitdown import MarkItDown, UnsupportedFormatException, FileConversionException
                    
                    instance = MarkItDown()
                    logger.info(f"📄 Converting URL with markitdown...")
                    conversion_result = instance.convert(normalized_url)
                    logger.info(f"✅ Markitdown conversion completed")
                    return conversion_result.text_content
                
                return await asyncio.to_thread(_run)
            
            logger.info(f"⏱️ Starting conversion with timeout: {settings.URL_PROCESSING_TIMEOUT_SECONDS}s")
            text_content = await asyncio.wait_for(_convert(), timeout=settings.URL_PROCESSING_TIMEOUT_SECONDS)
            
            if not text_content or not text_content.strip():
                logger.warning(f"⚠️ No content extracted from URL: {normalized_url}")
                return ""
            
            logger.info(f"✅ Successfully extracted {len(text_content)} characters from URL")
            logger.debug(f"📄 First 200 characters: {text_content[:200]}...")
            
            return text_content.strip()
            
        except asyncio.TimeoutError:
            logger.error(f"❌ URL conversion timed out: {normalized_url}")
            raise ValueError(f"URL conversion timed out after {settings.URL_PROCESSING_TIMEOUT_SECONDS} seconds")
        except ImportError as e:
            logger.error(f"❌ markitdown library not available: {e}")
            raise ValueError("URL processing library not available")
        except Exception as e:
            logger.error(f"❌ URL processing failed for {normalized_url}: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            raise ValueError(f"URL processing failed: {str(e)}")
    
    def _normalize_url(self, url: str) -> str:
        """
        Normalize and validate URL.
        
        Args:
            url: Raw URL string
            
        Returns:
            Normalized URL
            
        Raises:
            ValueError: If URL is invalid
        """
        url = url.strip()
        
        # Add protocol if missing
        if not url.startswith(("http://", "https://")):
            if url.startswith("www."):
                url = "https://" + url
            else:
                url = "https://www." + url
        
        # Validate URL format
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError("Invalid URL format")
        except Exception as e:
            raise ValueError(f"Invalid URL format: {str(e)}")
        
        return url
    
    def validate_input(self, data: Any) -> None:
        """
        Validate URL input data.
        
        Args:
            data: URL string to validate
            
        Raises:
            ValueError: If URL is invalid
        """
        super().validate_input(data)
        
        if not isinstance(data, str):
            raise ValueError("URL must be a string")
        
        # Basic URL validation
        if len(data.strip()) < 10:  # Minimum reasonable URL length
            raise ValueError("URL appears to be too short")
        
        # Check for basic URL patterns
        if not any(char in data for char in ['.', '/']):
            raise ValueError("URL must contain domain separator") 