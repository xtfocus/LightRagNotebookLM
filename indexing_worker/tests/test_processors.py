"""
Tests for text processors and factory.

This module tests the processor factory pattern and individual processors.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch

from app.processors import (
    TextProcessorFactory, 
    PDFProcessor, 
    DOCXProcessor, 
    TXTProcessor, 
    URLProcessor
)


class TestTextProcessorFactory:
    """Test the TextProcessorFactory class."""
    
    def test_create_pdf_processor(self):
        """Test creating a PDF processor."""
        processor = TextProcessorFactory.create_processor("pdf")
        assert isinstance(processor, PDFProcessor)
    
    def test_create_docx_processor(self):
        """Test creating a DOCX processor."""
        processor = TextProcessorFactory.create_processor("docx")
        assert isinstance(processor, DOCXProcessor)
    
    def test_create_txt_processor(self):
        """Test creating a TXT processor."""
        processor = TextProcessorFactory.create_processor("txt")
        assert isinstance(processor, TXTProcessor)
    
    def test_create_url_processor(self):
        """Test creating a URL processor."""
        processor = TextProcessorFactory.create_processor("url")
        assert isinstance(processor, URLProcessor)
    
    def test_create_processor_with_mime_type(self):
        """Test creating processors with MIME type mapping."""
        # Test PDF
        processor = TextProcessorFactory.create_processor("document", "application/pdf")
        assert isinstance(processor, PDFProcessor)
        
        # Test DOCX
        processor = TextProcessorFactory.create_processor("document", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        assert isinstance(processor, DOCXProcessor)
        
        # Test TXT
        processor = TextProcessorFactory.create_processor("document", "text/plain")
        assert isinstance(processor, TXTProcessor)
    
    def test_unsupported_source_type(self):
        """Test creating processor for unsupported source type."""
        with pytest.raises(ValueError, match="Unsupported source type"):
            TextProcessorFactory.create_processor("unsupported")
    
    def test_get_supported_source_types(self):
        """Test getting supported source types."""
        types = TextProcessorFactory.get_supported_source_types()
        assert "pdf" in types
        assert "docx" in types
        assert "txt" in types
        assert "url" in types
    
    def test_get_supported_mime_types(self):
        """Test getting supported MIME types."""
        mime_types = TextProcessorFactory.get_supported_mime_types()
        assert "application/pdf" in mime_types
        assert "application/vnd.openxmlformats-officedocument.wordprocessingml.document" in mime_types
        assert "text/plain" in mime_types
    
    def test_can_handle_source_type(self):
        """Test checking if factory can handle source types."""
        assert TextProcessorFactory.can_handle_source_type("pdf")
        assert TextProcessorFactory.can_handle_source_type("docx")
        assert TextProcessorFactory.can_handle_source_type("txt")
        assert TextProcessorFactory.can_handle_source_type("url")
        assert not TextProcessorFactory.can_handle_source_type("unsupported")


class TestPDFProcessor:
    """Test the PDFProcessor class."""
    
    def test_can_handle_pdf(self):
        """Test PDF processor can handle PDF sources."""
        processor = PDFProcessor()
        assert processor.can_handle("document", "application/pdf")
        assert not processor.can_handle("document", "text/plain")
        assert not processor.can_handle("url")
    
    def test_is_valid_pdf(self):
        """Test PDF validation."""
        processor = PDFProcessor()
        
        # Valid PDF signature
        valid_pdf = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"
        assert processor._is_valid_pdf(valid_pdf)
        
        # Invalid PDF signature
        invalid_pdf = b"Not a PDF file"
        assert not processor._is_valid_pdf(invalid_pdf)
    
    @pytest.mark.asyncio
    async def test_extract_text_from_pdf(self):
        """Test PDF text extraction."""
        processor = PDFProcessor()
        
        # Create a simple PDF-like content (this is a minimal test)
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"
        
        # This will likely fail since it's not a real PDF, but we can test the structure
        with pytest.raises(ValueError):
            await processor.extract_text(pdf_content)
    
    def test_validate_input(self):
        """Test input validation."""
        processor = PDFProcessor()
        
        # Valid input
        processor.validate_input(b"test data")
        
        # Invalid inputs
        with pytest.raises(ValueError):
            processor.validate_input(None)
        
        with pytest.raises(ValueError):
            processor.validate_input(b"")
        
        with pytest.raises(ValueError):
            processor.validate_input(b"a" * 50)  # Too small


class TestDOCXProcessor:
    """Test the DOCXProcessor class."""
    
    def test_can_handle_docx(self):
        """Test DOCX processor can handle DOCX sources."""
        processor = DOCXProcessor()
        assert processor.can_handle("document", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        assert processor.can_handle("document", "application/msword")
        assert not processor.can_handle("document", "application/pdf")
        assert not processor.can_handle("url")
    
    def test_is_valid_docx(self):
        """Test DOCX validation."""
        processor = DOCXProcessor()
        
        # Valid DOCX signature (ZIP file)
        valid_docx = b"PK\x03\x04\x14\x00\x00\x00\x08\x00"
        assert processor._is_valid_docx(valid_docx)
        
        # Invalid DOCX signature
        invalid_docx = b"Not a DOCX file"
        assert not processor._is_valid_docx(invalid_docx)
    
    def test_validate_input(self):
        """Test input validation."""
        processor = DOCXProcessor()
        
        # Valid input
        processor.validate_input(b"test data")
        
        # Invalid inputs
        with pytest.raises(ValueError):
            processor.validate_input(None)
        
        with pytest.raises(ValueError):
            processor.validate_input(b"")
        
        with pytest.raises(ValueError):
            processor.validate_input(b"a" * 50)  # Too small


class TestTXTProcessor:
    """Test the TXTProcessor class."""
    
    def test_can_handle_txt(self):
        """Test TXT processor can handle TXT sources."""
        processor = TXTProcessor()
        assert processor.can_handle("document", "text/plain")
        assert not processor.can_handle("document", "application/pdf")
        assert not processor.can_handle("url")
    
    @pytest.mark.asyncio
    async def test_extract_text(self):
        """Test TXT text extraction."""
        processor = TXTProcessor()
        
        # Test normal text
        result = await processor.extract_text(b"Hello, world!")
        assert result == "Hello, world!"
        
        # Test text with extra whitespace
        result = await processor.extract_text(b"  Hello,   world!  ")
        assert result == "Hello, world!"
        
        # Test empty text
        with pytest.raises(ValueError):
            await processor.extract_text(b"")
    
    def test_clean_text(self):
        """Test text cleaning."""
        processor = TXTProcessor()
        
        # Test removing excessive whitespace
        text = "  Line 1  \n\n  Line 2  \n  "
        cleaned = processor._clean_text(text)
        assert cleaned == "Line 1\nLine 2"
        
        # Test null byte removal
        text_with_nulls = "Hello\x00World"
        cleaned = processor._clean_text(text_with_nulls)
        assert cleaned == "HelloWorld"
    
    def test_validate_input(self):
        """Test text input validation."""
        processor = TXTProcessor()
        
        # Valid input
        processor.validate_input(b"test text")
        
        # Invalid inputs
        with pytest.raises(ValueError):
            processor.validate_input(None)
        
        with pytest.raises(ValueError):
            processor.validate_input(b"")
        
        # Test binary file detection
        binary_data = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        with pytest.raises(ValueError):
            processor.validate_input(binary_data)


class TestURLProcessor:
    """Test the URLProcessor class."""
    
    def test_can_handle_url(self):
        """Test URL processor can handle URL sources."""
        processor = URLProcessor()
        assert processor.can_handle("url")
        assert not processor.can_handle("document")
    
    def test_normalize_url(self):
        """Test URL normalization."""
        processor = URLProcessor()
        
        # Test adding protocol
        assert processor._normalize_url("example.com").startswith("https://")
        assert processor._normalize_url("www.example.com").startswith("https://")
        
        # Test already has protocol
        assert processor._normalize_url("https://example.com") == "https://example.com"
        
        # Test invalid URL
        with pytest.raises(ValueError):
            processor._normalize_url("")
    
    def test_validate_input(self):
        """Test URL input validation."""
        processor = URLProcessor()
        
        # Valid input
        processor.validate_input("https://example.com")
        
        # Invalid inputs
        with pytest.raises(ValueError):
            processor.validate_input(None)
        
        with pytest.raises(ValueError):
            processor.validate_input("")
        
        with pytest.raises(ValueError):
            processor.validate_input("short")


if __name__ == "__main__":
    pytest.main([__file__]) 