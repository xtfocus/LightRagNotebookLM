"""
Base Text Processor

This module defines the abstract base class for all text extraction processors.
"""

from abc import ABC, abstractmethod
from typing import Any
from loguru import logger


class TextProcessor(ABC):
    """Abstract base class for text extraction processors."""
    
    @abstractmethod
    async def extract_text(self, data: Any) -> str:
        """
        Extract text from the given data.
        
        Args:
            data: The data to extract text from (bytes for files, str for URLs/text)
            
        Returns:
            Extracted text as string
            
        Raises:
            ValueError: If text extraction fails
        """
        pass
    
    @abstractmethod
    def can_handle(self, source_type: str, mime_type: str = None) -> bool:
        """
        Check if this processor can handle the given source type.
        
        Args:
            source_type: Type of source (document, url, text, etc.)
            mime_type: MIME type for document sources (optional)
            
        Returns:
            True if this processor can handle the source type
        """
        pass
    
    def validate_input(self, data: Any) -> None:
        """
        Validate input data before processing.
        
        Args:
            data: Data to validate
            
        Raises:
            ValueError: If data is invalid
        """
        if data is None:
            raise ValueError("Input data cannot be None")
        
        if isinstance(data, str) and not data.strip():
            raise ValueError("Input data cannot be empty")
        
        if isinstance(data, bytes) and len(data) == 0:
            raise ValueError("Input data cannot be empty")
    
    async def process(self, data: Any) -> str:
        """
        Process the data and extract text.
        
        Args:
            data: Data to process
            
        Returns:
            Extracted text
            
        Raises:
            ValueError: If processing fails
        """
        try:
            self.validate_input(data)
            return await self.extract_text(data)
        except Exception as e:
            logger.error(f"Processing failed in {self.__class__.__name__}: {e}")
            raise ValueError(f"Text extraction failed: {str(e)}") 