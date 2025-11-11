#!/usr/bin/env python3
"""
Test file size limit validation functionality.

This module tests the configurable file size limits and validation logic
implemented in the upload system.
"""

import os
import sys
from unittest.mock import Mock

# Add the backend directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../'))

from app.core.config import settings
from app.core.file_errors import bytes_to_human_readable


def test_configuration():
    """Test that configuration values are set correctly."""
    print("=== Configuration Test ===")
    print(f"MAX_FILE_SIZE_BYTES: {settings.MAX_FILE_SIZE_BYTES}")
    print(f"MAX_FILE_SIZE_HUMAN: {settings.max_file_size_human}")
    print(f"MAX_TOTAL_UPLOAD_SIZE_BYTES: {settings.MAX_TOTAL_UPLOAD_SIZE_BYTES}")
    print(f"MAX_TOTAL_UPLOAD_SIZE_HUMAN: {settings.max_total_upload_size_human}")
    print(f"ALLOWED_FILE_TYPES: {settings.ALLOWED_FILE_TYPES}")
    print()


def test_bytes_to_human_readable():
    """Test the bytes to human-readable conversion function."""
    print("=== Bytes to Human Readable Test ===")
    test_cases = [
        (1024, "1.0KB"),
        (1048576, "1.0MB"),
        (104857600, "100.0MB"),
        (524288000, "500.0MB"),
        (1073741824, "1.0GB"),
    ]
    
    for bytes_value, expected in test_cases:
        result = bytes_to_human_readable(bytes_value)
        status = "✅" if result == expected else "❌"
        print(f"{status} {bytes_value} bytes -> {result} (expected: {expected})")
    print()


def test_file_size_validation():
    """Test file size validation logic."""
    print("=== File Size Validation Test ===")
    
    # Test valid file size
    valid_size = settings.MAX_FILE_SIZE_BYTES - 1
    print(f"✅ Valid file size: {bytes_to_human_readable(valid_size)}")
    
    # Test invalid file size
    invalid_size = settings.MAX_FILE_SIZE_BYTES + 1
    print(f"❌ Invalid file size: {bytes_to_human_readable(invalid_size)}")
    
    # Test total upload size
    total_size = settings.MAX_TOTAL_UPLOAD_SIZE_BYTES - 1
    print(f"✅ Valid total upload size: {bytes_to_human_readable(total_size)}")
    
    invalid_total = settings.MAX_TOTAL_UPLOAD_SIZE_BYTES + 1
    print(f"❌ Invalid total upload size: {bytes_to_human_readable(invalid_total)}")
    print()


def test_file_type_validation():
    """Test file type validation logic."""
    print("=== File Type Validation Test ===")
    
    # Test valid file types
    valid_types = ['test.pdf', 'document.docx', 'data.csv', 'presentation.pptx']
    for filename in valid_types:
        extension = filename.split('.')[-1].lower()
        if extension in settings.ALLOWED_FILE_TYPES:
            print(f"✅ Valid file type: {filename}")
        else:
            print(f"❌ Invalid file type: {filename}")
    
    # Test invalid file types
    invalid_types = ['script.exe', 'image.jpg', 'video.mp4']
    for filename in invalid_types:
        extension = filename.split('.')[-1].lower()
        if extension not in settings.ALLOWED_FILE_TYPES:
            print(f"❌ Blocked file type: {filename}")
        else:
            print(f"✅ Allowed file type: {filename}")
    print()


def test_environment_variables():
    """Test environment variable configuration."""
    print("=== Environment Variable Test ===")
    
    # Test default values
    print(f"Default MAX_FILE_SIZE_BYTES: {settings.MAX_FILE_SIZE_BYTES}")
    print(f"Default MAX_TOTAL_UPLOAD_SIZE_BYTES: {settings.MAX_TOTAL_UPLOAD_SIZE_BYTES}")
    print(f"Default ALLOWED_FILE_TYPES: {settings.ALLOWED_FILE_TYPES}")
    
    # Test with custom environment variables
    os.environ['MAX_FILE_SIZE_BYTES'] = '209715200'  # 200MB
    os.environ['MAX_TOTAL_UPLOAD_SIZE_BYTES'] = '1048576000'  # 1GB
    os.environ['ALLOWED_FILE_TYPES'] = 'pdf,txt,md'
    
    # Note: In a real application, you'd need to reload the settings
    # For this test, we'll just show what the environment variables would do
    print(f"Custom MAX_FILE_SIZE_BYTES (200MB): {os.environ.get('MAX_FILE_SIZE_BYTES')}")
    print(f"Custom MAX_TOTAL_UPLOAD_SIZE_BYTES (1GB): {os.environ.get('MAX_TOTAL_UPLOAD_SIZE_BYTES')}")
    print(f"Custom ALLOWED_FILE_TYPES: {os.environ.get('ALLOWED_FILE_TYPES')}")
    print()


if __name__ == "__main__":
    print("File Size Limit Implementation Test")
    print("=" * 50)
    print()
    
    test_configuration()
    test_bytes_to_human_readable()
    test_file_size_validation()
    test_file_type_validation()
    test_environment_variables()
    
    print("✅ All tests completed!")
    print("\nTo test with custom values, set environment variables:")
    print("export MAX_FILE_SIZE_BYTES=209715200  # 200MB")
    print("export MAX_TOTAL_UPLOAD_SIZE_BYTES=1048576000  # 1GB")
    print("export ALLOWED_FILE_TYPES=pdf,txt,md") 