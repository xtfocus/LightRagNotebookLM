"""
PDF Processor

This module handles text extraction from PDF files.
"""

import io
from typing import Any
from loguru import logger
import PyPDF2

from .base import TextProcessor
from app.core.config import settings


class PDFProcessor(TextProcessor):
    """Handles PDF document processing."""
    
    def can_handle(self, source_type: str, mime_type: str = None) -> bool:
        """Check if this processor can handle the given source type and MIME type."""
        if source_type != "document":
            return False
        
        if mime_type is None:
            return True
        
        return mime_type == "application/pdf"
    
    async def extract_text(self, file_data: bytes) -> str:
        """
        Extract text from PDF file data.
        
        Args:
            file_data: Raw PDF file data as bytes
            
        Returns:
            Extracted text as string
            
        Raises:
            ValueError: If text extraction fails
        """
        if not isinstance(file_data, bytes):
            raise ValueError("File data must be bytes")
        
        # Validate PDF signature
        if not self._is_valid_pdf(file_data):
            raise ValueError("Invalid PDF file format")
        
        try:
            return await self._extract_text_from_pdf(file_data)
        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {e}")
            raise ValueError(f"PDF text extraction failed: {str(e)}")
    
    def _is_valid_pdf(self, file_data: bytes) -> bool:
        """
        Check if the file data represents a valid PDF.
        
        Args:
            file_data: Raw file data
            
        Returns:
            True if the file is a valid PDF
        """
        return file_data.startswith(b'%PDF')
    
    async def _extract_text_from_pdf(self, file_data: bytes) -> str:
        """Extract text from PDF file."""
        try:
            pdf_file = io.BytesIO(file_data)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text = ""
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                    else:
                        logger.warning(f"No text extracted from page {page_num + 1}")
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {page_num + 1}: {e}")
                    continue
            
            if not text.strip():
                logger.warning("No text extracted from PDF - file may be image-based or corrupted")
                return ""
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {e}")
            raise ValueError(f"PDF text extraction failed: {str(e)}")
    
    def validate_input(self, data: Any) -> None:
        """
        Validate PDF input data.
        
        Args:
            data: PDF file data to validate
            
        Raises:
            ValueError: If data is invalid
        """
        super().validate_input(data)
        
        if not isinstance(data, bytes):
            raise ValueError("PDF data must be bytes")
        
        # Check for minimum PDF size (very small files are likely invalid)
        if len(data) < settings.MIN_FILE_SIZE_BYTES:
            raise ValueError(f"PDF file appears to be too small (min {settings.MIN_FILE_SIZE_BYTES} bytes)")
        
        # Check for maximum PDF size (configurable limit)
        if len(data) > settings.MAX_PDF_SIZE_BYTES:
            max_size_mb = settings.MAX_PDF_SIZE_BYTES / (1024 * 1024)
            raise ValueError(f"PDF file is too large (max {max_size_mb:.0f}MB)") 