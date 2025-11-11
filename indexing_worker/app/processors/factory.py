"""
Text Processor Factory

This module provides a factory pattern for creating appropriate text processors
based on source type and MIME type.
"""

from typing import Dict, Type, Optional
from loguru import logger

from .base import TextProcessor
from .pdf_processor import PDFProcessor
from .docx_processor import DOCXProcessor
from .txt_processor import TXTProcessor
from .url_processor import URLProcessor


class TextProcessorFactory:
    """Factory for creating text processors based on source type."""
    
    _processors: Dict[str, Type[TextProcessor]] = {
        "pdf": PDFProcessor,
        "docx": DOCXProcessor,
        "txt": TXTProcessor,
        "url": URLProcessor,
    }
    
    @classmethod
    def create_processor(cls, source_type: str, mime_type: str = None) -> TextProcessor:
        """
        Create a processor for the given source type.
        
        Args:
            source_type: Type of source (pdf, docx, txt, url)
            mime_type: MIME type for document sources (optional)
            
        Returns:
            Appropriate text processor instance
            
        Raises:
            ValueError: If source type is not supported
        """
        # Map MIME types to processor types for backward compatibility
        if source_type == "document" and mime_type:
            source_type = cls._map_mime_type_to_processor(mime_type)
        
        processor_class = cls._processors.get(source_type)
        if not processor_class:
            supported_types = list(cls._processors.keys())
            raise ValueError(f"Unsupported source type: {source_type}. Supported types: {supported_types}")
        
        processor = processor_class()
        
        # Validate that the processor can handle the source type and MIME type
        if not processor.can_handle("document", mime_type) and not processor.can_handle(source_type, mime_type):
            raise ValueError(f"Processor {processor.__class__.__name__} cannot handle source type '{source_type}' with MIME type '{mime_type}'")
        
        logger.debug(f"Created processor {processor.__class__.__name__} for source type '{source_type}'")
        return processor
    
    @classmethod
    def _map_mime_type_to_processor(cls, mime_type: str) -> str:
        """
        Map MIME type to processor type.
        
        Args:
            mime_type: MIME type string
            
        Returns:
            Processor type string
        """
        mime_type_mapping = {
            "application/pdf": "pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
            "application/msword": "docx",
            "text/plain": "txt",
        }
        
        return mime_type_mapping.get(mime_type, "txt")  # Default to txt for unknown types
    
    @classmethod
    def register_processor(cls, source_type: str, processor_class: Type[TextProcessor]):
        """
        Register a new processor type.
        
        Args:
            source_type: Source type identifier
            processor_class: Processor class to register
        """
        if not issubclass(processor_class, TextProcessor):
            raise ValueError(f"Processor class must inherit from TextProcessor")
        
        cls._processors[source_type] = processor_class
        logger.info(f"Registered processor {processor_class.__name__} for source type '{source_type}'")
    
    @classmethod
    def unregister_processor(cls, source_type: str):
        """
        Unregister a processor type.
        
        Args:
            source_type: Source type to unregister
        """
        if source_type in cls._processors:
            processor_class = cls._processors.pop(source_type)
            logger.info(f"Unregistered processor {processor_class.__name__} for source type '{source_type}'")
        else:
            logger.warning(f"Attempted to unregister non-existent processor for source type '{source_type}'")
    
    @classmethod
    def get_supported_source_types(cls) -> list[str]:
        """
        Get list of supported source types.
        
        Returns:
            List of supported source type identifiers
        """
        return list(cls._processors.keys())
    
    @classmethod
    def get_supported_mime_types(cls) -> list[str]:
        """
        Get list of supported MIME types.
        
        Returns:
            List of supported MIME types
        """
        return [
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword",
            "text/plain",
        ]
    
    @classmethod
    def can_handle_source_type(cls, source_type: str, mime_type: str = None) -> bool:
        """
        Check if the factory can handle a given source type.
        
        Args:
            source_type: Source type to check
            mime_type: MIME type for document sources (optional)
            
        Returns:
            True if the source type is supported
        """
        try:
            processor = cls.create_processor(source_type, mime_type)
            return processor.can_handle("document", mime_type) or processor.can_handle(source_type, mime_type)
        except (ValueError, Exception):
            return False 