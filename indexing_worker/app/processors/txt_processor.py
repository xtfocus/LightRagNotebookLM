"""
TXT Processor

This module handles text extraction from plain text files.
"""

from typing import Any
from loguru import logger

from .base import TextProcessor
from app.core.config import settings


class TXTProcessor(TextProcessor):
    """Handles plain text file processing."""
    
    def can_handle(self, source_type: str, mime_type: str = None) -> bool:
        """Check if this processor can handle the given source type and MIME type."""
        if source_type != "document":
            return False
        
        if mime_type is None:
            return True
        
        return mime_type == "text/plain"
    
    async def extract_text(self, file_data: bytes) -> str:
        """
        Extract text from plain text file data.
        
        Args:
            file_data: Raw text file data as bytes
            
        Returns:
            Extracted text as string
            
        Raises:
            ValueError: If text extraction fails
        """
        if not isinstance(file_data, bytes):
            raise ValueError("File data must be bytes")
        
        try:
            return await self._extract_text_from_txt(file_data)
        except Exception as e:
            logger.error(f"Failed to extract text from TXT file: {e}")
            raise ValueError(f"TXT text extraction failed: {str(e)}")
    
    async def _extract_text_from_txt(self, file_data: bytes) -> str:
        """Extract text from plain text file."""
        try:
            # Try UTF-8 first
            try:
                text = file_data.decode('utf-8')
            except UnicodeDecodeError:
                # Try other common encodings
                for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                    try:
                        text = file_data.decode(encoding)
                        logger.info(f"Successfully decoded text file using {encoding} encoding")
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    raise ValueError("Unable to decode text file with any supported encoding")
            
            # Clean up the text
            cleaned_text = self._clean_text(text)
            
            if not cleaned_text.strip():
                logger.warning("No content in text file after cleaning")
                return ""
            
            return cleaned_text.strip()
            
        except Exception as e:
            logger.error(f"Failed to extract text from TXT file: {e}")
            raise ValueError(f"TXT text extraction failed: {str(e)}")
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text content.
        
        Args:
            text: Raw text content
            
        Returns:
            Cleaned text
        """
        # Remove null bytes and other control characters
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
        
        # Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove excessive whitespace
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Remove leading/trailing whitespace
            cleaned_line = line.strip()
            
            # Skip empty lines
            if cleaned_line:
                cleaned_lines.append(cleaned_line)
        
        # Join lines with single newlines
        return '\n'.join(cleaned_lines)
    
    def validate_input(self, data: Any) -> None:
        """
        Validate TXT input data.
        
        Args:
            data: TXT file data to validate
            
        Raises:
            ValueError: If data is invalid
        """
        super().validate_input(data)
        
        if not isinstance(data, bytes):
            raise ValueError("TXT data must be bytes")
        
        # Check for minimum file size
        if len(data) < 1:
            raise ValueError("TXT file cannot be empty")
        
        # Check for maximum file size (configurable limit)
        if len(data) > settings.MAX_TXT_SIZE_BYTES:
            max_size_mb = settings.MAX_TXT_SIZE_BYTES / (1024 * 1024)
            raise ValueError(f"TXT file is too large (max {max_size_mb:.0f}MB)")
        
        # Check if it's likely a text file (not binary)
        # Look for null bytes or excessive control characters
        null_count = data.count(b'\x00')
        if null_count > len(data) * settings.MAX_BINARY_NULL_RATIO:
            raise ValueError("File appears to be binary, not text") 