"""
Text Processing Package

This package provides a factory pattern implementation for processing different types
of sources (documents, URLs) into machine-readable text format.

Classes:
    TextProcessor: Abstract base class for all text processors
    TextProcessorFactory: Factory for creating appropriate processors
    PDFProcessor: Handles PDF files
    DOCXProcessor: Handles DOCX files
    TXTProcessor: Handles plain text files
    URLProcessor: Handles URL processing using markitdown
"""

from .base import TextProcessor
from .factory import TextProcessorFactory
from .pdf_processor import PDFProcessor
from .docx_processor import DOCXProcessor
from .txt_processor import TXTProcessor
from .url_processor import URLProcessor

__all__ = [
    "TextProcessor",
    "TextProcessorFactory", 
    "PDFProcessor",
    "DOCXProcessor",
    "TXTProcessor",
    "URLProcessor",
] 