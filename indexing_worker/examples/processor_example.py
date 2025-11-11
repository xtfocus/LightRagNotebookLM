"""
Example usage of the Text Processor Factory

This script demonstrates how to use the new processor factory pattern
for processing different types of sources.
"""

import asyncio
import sys
import os

# Add the app directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.processors import TextProcessorFactory


async def main():
    """Demonstrate the processor factory usage."""
    
    print("🔧 Text Processor Factory Example")
    print("=" * 50)
    
    # Show supported source types
    supported_types = TextProcessorFactory.get_supported_source_types()
    print(f"Supported source types: {supported_types}")
    
    supported_mime_types = TextProcessorFactory.get_supported_mime_types()
    print(f"Supported MIME types: {supported_mime_types}")
    print()
    
    # Example 1: Process a PDF document
    print("📄 Example 1: PDF Processing")
    print("-" * 30)
    
    # Create a simple PDF-like content for demonstration
    pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"
    
    try:
        processor = TextProcessorFactory.create_processor("pdf")
        print(f"Created processor: {processor.__class__.__name__}")
        
        # This will likely fail since it's not a real PDF, but demonstrates the structure
        try:
            text = await processor.process(pdf_content)
            print(f"Extracted text: {text[:100]}...")
        except ValueError as e:
            print(f"Expected error (not a real PDF): {e}")
    except Exception as e:
        print(f"Error creating PDF processor: {e}")
    
    print()
    
    # Example 2: Process a DOCX document
    print("📝 Example 2: DOCX Processing")
    print("-" * 30)
    
    # Create a simple DOCX-like content for demonstration
    docx_content = b"PK\x03\x04\x14\x00\x00\x00\x08\x00"
    
    try:
        processor = TextProcessorFactory.create_processor("docx")
        print(f"Created processor: {processor.__class__.__name__}")
        
        # This will likely fail since it's not a real DOCX, but demonstrates the structure
        try:
            text = await processor.process(docx_content)
            print(f"Extracted text: {text[:100]}...")
        except ValueError as e:
            print(f"Expected error (not a real DOCX): {e}")
    except Exception as e:
        print(f"Error creating DOCX processor: {e}")
    
    print()
    
    # Example 3: Process a TXT document
    print("📄 Example 3: TXT Processing")
    print("-" * 30)
    
    txt_content = b"  This is some test text with   extra whitespace.  \n\n  And multiple lines.  "
    
    try:
        processor = TextProcessorFactory.create_processor("txt")
        print(f"Created processor: {processor.__class__.__name__}")
        
        text = await processor.process(txt_content)
        print(f"Original content: {repr(txt_content)}")
        print(f"Processed text: {repr(text)}")
    except Exception as e:
        print(f"Error processing TXT: {e}")
    
    print()
    
    # Example 4: Process a URL
    print("🌐 Example 4: URL Processing")
    print("-" * 30)
    
    test_url = "https://example.com"
    
    try:
        processor = TextProcessorFactory.create_processor("url")
        print(f"Created processor: {processor.__class__.__name__}")
        
        # Test URL validation
        try:
            text = await processor.process(test_url)
            print(f"Extracted text: {text[:100]}...")
        except ValueError as e:
            print(f"URL processing error: {e}")
    except Exception as e:
        print(f"Error creating URL processor: {e}")
    
    print()
    
    # Example 5: MIME type mapping
    print("🔗 Example 5: MIME Type Mapping")
    print("-" * 30)
    
    mime_type_examples = [
        ("application/pdf", "PDF file"),
        ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", "DOCX file"),
        ("text/plain", "TXT file"),
    ]
    
    for mime_type, description in mime_type_examples:
        try:
            processor = TextProcessorFactory.create_processor("document", mime_type)
            print(f"✅ {description} ({mime_type}) -> {processor.__class__.__name__}")
        except Exception as e:
            print(f"❌ {description} ({mime_type}) -> Error: {e}")
    
    print()
    
    # Example 6: Factory validation
    print("✅ Example 6: Factory Validation")
    print("-" * 30)
    
    test_cases = [
        ("pdf", None, True),
        ("docx", None, True),
        ("txt", None, True),
        ("url", None, True),
        ("document", "application/pdf", True),
        ("document", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", True),
        ("document", "text/plain", True),
        ("unsupported", None, False),
    ]
    
    for source_type, mime_type, expected in test_cases:
        can_handle = TextProcessorFactory.can_handle_source_type(source_type, mime_type)
        status = "✅" if can_handle == expected else "❌"
        mime_info = f" (mime: {mime_type})" if mime_type else ""
        print(f"{status} {source_type}{mime_info}: {can_handle}")
    
    print()
    print("🎉 Example completed!")


if __name__ == "__main__":
    asyncio.run(main()) 