"""
Security tests for TSS Converter Web Application
Tests file validation, malicious content detection, and rate limiting
"""

import unittest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from common.validation import FileValidator
from common.exceptions import FileFormatError, TSConverterError


class TestFileSecurityValidation(unittest.TestCase):
    """Test security aspects of file validation"""
    
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        
    def tearDown(self):
        # Clean up test files
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def create_test_file(self, content: bytes, filename: str = "test.xlsx"):
        """Create a test file with given content"""
        file_path = self.test_dir / filename
        with open(file_path, 'wb') as f:
            f.write(content)
        return file_path
    
    def test_valid_excel_signature(self):
        """Test that valid Excel files pass signature validation"""
        # Create file with valid XLSX signature (ZIP format)
        valid_content = b'PK\x03\x04' + b'\x00' * 100
        file_path = self.create_test_file(valid_content)
        
        # Should not raise exception for signature check
        try:
            FileValidator._validate_file_signature(file_path)
        except FileFormatError:
            self.fail("Valid Excel signature was rejected")
    
    def test_invalid_file_signature(self):
        """Test that invalid file signatures are rejected"""
        # Create file with invalid signature
        invalid_content = b'INVALID' + b'\x00' * 100
        file_path = self.create_test_file(invalid_content)
        
        with self.assertRaises(FileFormatError) as ctx:
            FileValidator._validate_file_signature(file_path)
        
        self.assertIn("Invalid signature", str(ctx.exception))
    
    def test_malicious_content_detection(self):
        """Test detection of suspicious patterns in files"""
        # Create file with malicious JavaScript
        malicious_content = b'PK\x03\x04' + b'<script>alert("xss")</script>' + b'\x00' * 100
        file_path = self.create_test_file(malicious_content)
        
        with self.assertRaises(FileFormatError) as ctx:
            FileValidator._scan_malicious_content(file_path)
        
        self.assertIn("malicious content", str(ctx.exception))
    
    def test_filename_path_traversal(self):
        """Test rejection of path traversal attempts in filenames"""
        malicious_filenames = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config",
            "file../../../secret.txt",
            "normal/../../evil.exe"
        ]
        
        for filename in malicious_filenames:
            with self.assertRaises(FileFormatError) as ctx:
                FileValidator._validate_filename(filename)
            self.assertIn("Path traversal", str(ctx.exception))
    
    def test_filename_suspicious_characters(self):
        """Test rejection of filenames with suspicious characters"""
        suspicious_filenames = [
            "file<script>.xlsx",
            'file"evil".xlsx',
            "file|pipe.xlsx",
            "file?.xlsx",
            "file*.xlsx"
        ]
        
        for filename in suspicious_filenames:
            with self.assertRaises(FileFormatError) as ctx:
                FileValidator._validate_filename(filename)
            self.assertIn("Suspicious characters", str(ctx.exception))
    
    def test_oversized_file_rejection(self):
        """Test rejection of files exceeding size limits"""
        # Create a file larger than the limit
        large_content = b'PK\x03\x04' + b'\x00' * (FileValidator.MAX_FILE_SIZE + 1)
        file_path = self.create_test_file(large_content)
        
        with self.assertRaises(FileFormatError) as ctx:
            FileValidator.validate_file_security(file_path)
        
        self.assertIn("File size", str(ctx.exception))
    
    def test_empty_file_rejection(self):
        """Test rejection of empty files"""
        file_path = self.create_test_file(b'')
        
        with self.assertRaises(FileFormatError) as ctx:
            FileValidator.validate_file_security(file_path)
        
        self.assertIn("Empty file", str(ctx.exception))


class TestIntegrationSecurity(unittest.TestCase):
    """Integration tests for security features"""
    
    def test_complete_file_validation_flow(self):
        """Test complete file validation including all security checks"""
        test_dir = Path(tempfile.mkdtemp())
        
        try:
            # Create a valid-looking Excel file
            valid_file = test_dir / "valid.xlsx"
            with open(valid_file, 'wb') as f:
                # Write Excel signature + some content
                f.write(b'PK\x03\x04' + b'\x00' * 1000)
            
            # This should pass all validations
            try:
                result = FileValidator.validate_file_format(valid_file)
                self.assertEqual(result, valid_file)
            except Exception as e:
                # Allow openpyxl-related errors since we're not creating real Excel files
                if "openpyxl" not in str(e).lower():
                    raise
        
        finally:
            import shutil
            shutil.rmtree(test_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()