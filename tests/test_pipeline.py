"""
Pipeline functionality tests for TSS Converter
Tests the core processing pipeline and error handling
"""

import unittest
import tempfile
import shutil
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from streamlit_pipeline import StreamlitTSSPipeline, ProgressCallback, ResourceManager, with_retry
from common.exceptions import TSConverterError


class TestResourceManager(unittest.TestCase):
    """Test resource management and cleanup"""
    
    def test_resource_manager_temp_file_cleanup(self):
        """Test that temporary files are cleaned up"""
        test_dir = Path(tempfile.mkdtemp())
        temp_file = test_dir / "temp.txt"
        
        try:
            # Create temp file
            temp_file.write_text("test content")
            self.assertTrue(temp_file.exists())
            
            # Use resource manager
            with ResourceManager() as rm:
                rm.add_temp_file(temp_file)
                self.assertTrue(temp_file.exists())  # Should exist during context
            
            # File should be cleaned up after context
            self.assertFalse(temp_file.exists())
        
        finally:
            shutil.rmtree(test_dir, ignore_errors=True)
    
    def test_resource_manager_exception_handling(self):
        """Test resource cleanup happens even with exceptions"""
        test_dir = Path(tempfile.mkdtemp())
        temp_file = test_dir / "temp.txt"
        
        try:
            temp_file.write_text("test content")
            
            with self.assertRaises(ValueError):
                with ResourceManager() as rm:
                    rm.add_temp_file(temp_file)
                    raise ValueError("Test exception")
            
            # File should still be cleaned up
            self.assertFalse(temp_file.exists())
        
        finally:
            shutil.rmtree(test_dir, ignore_errors=True)


class TestRetryDecorator(unittest.TestCase):
    """Test automatic retry functionality"""
    
    def test_retry_on_failure(self):
        """Test that functions are retried on failure"""
        call_count = 0
        
        @with_retry(max_retries=2, backoff_factor=0.001)  # Fast for testing
        def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise OSError("Temporary failure")
            return "success"
        
        result = failing_function()
        self.assertEqual(result, "success")
        self.assertEqual(call_count, 3)  # 1 initial + 2 retries
    
    def test_retry_exhaustion(self):
        """Test that retries are exhausted and final exception is raised"""
        call_count = 0
        
        @with_retry(max_retries=2, backoff_factor=0.001)
        def always_failing_function():
            nonlocal call_count
            call_count += 1
            raise OSError("Persistent failure")
        
        with self.assertRaises(OSError) as ctx:
            always_failing_function()
        
        self.assertIn("Persistent failure", str(ctx.exception))
        self.assertEqual(call_count, 3)  # 1 initial + 2 retries
    
    def test_retry_with_specific_exceptions(self):
        """Test that only specified exceptions trigger retries"""
        call_count = 0
        
        @with_retry(max_retries=2, exceptions=(OSError,))
        def function_with_different_error():
            nonlocal call_count
            call_count += 1
            raise ValueError("This should not be retried")
        
        with self.assertRaises(ValueError):
            function_with_different_error()
        
        self.assertEqual(call_count, 1)  # No retries for ValueError


class TestProgressCallback(unittest.TestCase):
    """Test progress tracking functionality"""
    
    def test_progress_callback_updates(self):
        """Test that progress callback properly tracks steps"""
        updates = []
        
        def mock_update(data):
            updates.append(data.copy())
        
        callback = ProgressCallback(mock_update)
        
        # Test step progression
        callback.start_step(1, "Test Step")
        self.assertEqual(len(updates), 1)
        self.assertEqual(updates[0]["current_step"], 1)
        self.assertEqual(updates[0]["step_status"]["step1"], "running")
        
        callback.complete_step(1, "Test Step")
        self.assertEqual(len(updates), 2)
        self.assertEqual(updates[1]["step_status"]["step1"], "completed")
        
        callback.error_step(2, "Test error")
        self.assertEqual(len(updates), 3)
        self.assertEqual(updates[2]["step_status"]["step2"], "error")
        self.assertTrue(updates[2]["error"])


class TestPipelineValidation(unittest.TestCase):
    """Test pipeline input validation"""
    
    def setUp(self):
        self.pipeline = StreamlitTSSPipeline()
        self.test_dir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_validate_nonexistent_file(self):
        """Test validation of non-existent files"""
        fake_file = self.test_dir / "nonexistent.xlsx"
        
        is_valid, message = self.pipeline.validate_input_file(fake_file)
        
        self.assertFalse(is_valid)
        self.assertIn("does not exist", message.lower())
    
    def test_validate_wrong_extension(self):
        """Test validation of files with wrong extensions"""
        txt_file = self.test_dir / "test.txt"
        txt_file.write_text("not an excel file")
        
        is_valid, message = self.pipeline.validate_input_file(txt_file)
        
        self.assertFalse(is_valid)
        self.assertIn("format", message.lower())
    
    @patch('openpyxl.load_workbook')
    def test_validate_corrupted_excel(self, mock_load):
        """Test validation of corrupted Excel files"""
        # Mock openpyxl to raise exception for corrupted file
        mock_load.side_effect = Exception("Invalid file format")
        
        excel_file = self.test_dir / "corrupted.xlsx"
        # Create file with Excel signature but invalid content
        with open(excel_file, 'wb') as f:
            f.write(b'PK\x03\x04' + b'corrupted content')
        
        is_valid, message = self.pipeline.validate_input_file(excel_file)
        
        self.assertFalse(is_valid)


class TestPipelineIntegration(unittest.TestCase):
    """Integration tests for complete pipeline"""
    
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.pipeline = StreamlitTSSPipeline()
    
    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)
        if self.pipeline.current_session_id:
            self.pipeline.cleanup_session()
    
    def test_session_directory_creation(self):
        """Test that session directories are created properly"""
        session_dir = self.pipeline.create_session_directory()
        
        self.assertTrue(session_dir.exists())
        self.assertTrue((session_dir / "input").exists())
        self.assertTrue((session_dir / "output").exists())
        
        # Cleanup
        self.pipeline.cleanup_session()
        self.assertFalse(session_dir.exists())
    
    def test_file_upload_and_save(self):
        """Test file upload and saving to session directory"""
        test_content = b"test file content"
        filename = "test.xlsx"
        
        saved_path = self.pipeline.save_uploaded_file(test_content, filename)
        
        self.assertTrue(saved_path.exists())
        self.assertEqual(saved_path.read_bytes(), test_content)
        self.assertEqual(saved_path.name, filename)


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)