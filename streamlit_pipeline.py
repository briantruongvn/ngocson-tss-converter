"""
Streamlit Pipeline Integration for TSS Converter
Wraps the existing 5-step pipeline with progress tracking and error handling.
"""

import os
import sys
import tempfile
import shutil
import time
import random
from pathlib import Path
from typing import Dict, Any, Optional, Callable, Tuple
import logging
import traceback
from functools import wraps

# Import existing pipeline modules (they use function-based approach)
import step1_template_creation
import step2_data_extraction
import step3_data_mapping
import step4_data_fill
import step5_filter_deduplicate
from common.exceptions import TSConverterError
from common.validation import FileValidator
from common.quality_reporter import get_global_reporter, reset_global_reporter
from config_streamlit import get_temp_directory, STREAMLIT_CONFIG

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def with_retry(max_retries: int = 3, backoff_factor: float = 1.0, 
               exceptions: tuple = (Exception,)):
    """
    Decorator for automatic retry with exponential backoff
    
    Args:
        max_retries: Maximum number of retry attempts
        backoff_factor: Multiplier for delay between retries
        exceptions: Tuple of exception types to catch and retry
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(f"Function {func.__name__} failed after {max_retries} retries")
                        raise last_exception
                    
                    # Calculate delay with jitter
                    delay = backoff_factor * (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}, retrying in {delay:.2f}s: {str(e)}")
                    time.sleep(delay)
                    
            return None  # Should never reach here
        return wrapper
    return decorator

class ResourceManager:
    """Context manager for safe resource handling"""
    
    def __init__(self):
        self.resources = []
        self.temp_files = []
        
    def add_resource(self, resource, cleanup_func=None):
        """Add a resource to be cleaned up"""
        self.resources.append((resource, cleanup_func))
        
    def add_temp_file(self, file_path: Path):
        """Add a temporary file to be cleaned up"""
        self.temp_files.append(file_path)
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up all resources"""
        # Clean up temp files
        for temp_file in self.temp_files:
            try:
                if temp_file.exists():
                    temp_file.unlink()
                    logger.debug(f"Cleaned up temp file: {temp_file}")
            except Exception as e:
                logger.warning(f"Failed to clean up temp file {temp_file}: {e}")
        
        # Clean up other resources
        for resource, cleanup_func in self.resources:
            try:
                if cleanup_func:
                    cleanup_func(resource)
                elif hasattr(resource, 'close'):
                    resource.close()
                logger.debug(f"Cleaned up resource: {resource}")
            except Exception as e:
                logger.warning(f"Failed to clean up resource {resource}: {e}")

class ProgressCallback:
    """Callback class for tracking pipeline progress"""
    
    def __init__(self, update_func: Optional[Callable] = None):
        self.update_func = update_func
        self.current_step = 0
        self.step_status = {f"step{i}": "pending" for i in range(1, 6)}
        self.start_time = time.time()
        
    def start_step(self, step_num: int, step_name: str):
        """Mark step as started"""
        self.current_step = step_num
        self.step_status[f"step{step_num}"] = "running"
        
        if self.update_func:
            self.update_func({
                "current_step": step_num,
                "step_status": self.step_status.copy(),
                "message": f"Running {step_name}..."
            })
    
    def complete_step(self, step_num: int, step_name: str):
        """Mark step as completed"""
        self.step_status[f"step{step_num}"] = "completed"
        
        if self.update_func:
            self.update_func({
                "current_step": step_num,
                "step_status": self.step_status.copy(),
                "message": f"Completed {step_name}"
            })
    
    def error_step(self, step_num: int, error_message: str):
        """Mark step as error"""
        self.step_status[f"step{step_num}"] = "error"
        
        if self.update_func:
            self.update_func({
                "current_step": step_num,
                "step_status": self.step_status.copy(),
                "message": f"Error: {error_message}",
                "error": True
            })

class StreamlitTSSPipeline:
    """
    Streamlit wrapper for TSS Converter pipeline
    Provides progress tracking, file management, and error handling for web interface
    """
    
    def __init__(self, temp_dir: Optional[Path] = None):
        self.temp_dir = temp_dir or get_temp_directory()
        self.current_session_id = None
        self.processing_stats = {}
        
    def create_session_directory(self) -> Path:
        """Create unique session directory for file processing"""
        session_id = f"session_{int(time.time())}_{os.getpid()}"
        self.current_session_id = session_id
        
        session_dir = self.temp_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (session_dir / "input").mkdir(exist_ok=True)
        (session_dir / "output").mkdir(exist_ok=True)
        
        return session_dir
    
    def save_uploaded_file(self, file_data: bytes, filename: str) -> Path:
        """Save uploaded file to session directory"""
        if not self.current_session_id:
            self.create_session_directory()
        
        session_dir = self.temp_dir / self.current_session_id
        input_file_path = session_dir / "input" / filename
        
        with open(input_file_path, "wb") as f:
            f.write(file_data)
        
        logger.info(f"Saved uploaded file to: {input_file_path}")
        return input_file_path
    
    def process_pipeline(self, 
                        input_file_path: Path, 
                        progress_callback: Optional[ProgressCallback] = None) -> Tuple[bool, Path, Dict[str, Any]]:
        """
        Run complete 5-step pipeline with progress tracking
        
        Args:
            input_file_path: Path to input Excel file
            progress_callback: Callback for progress updates
            
        Returns:
            Tuple of (success, output_file_path, processing_stats)
        """
        start_time = time.time()
        session_dir = input_file_path.parent.parent
        output_dir = session_dir / "output"
        
        try:
            # Reset and initialize quality reporter
            reset_global_reporter()
            reporter = get_global_reporter()
            reporter.start_processing()
            
            # Initialize processing stats
            self.processing_stats = {
                "start_time": start_time,
                "input_file": str(input_file_path.name),
                "steps_completed": 0,
                "errors": []
            }
            
            # Step 1: Template Creation
            if progress_callback:
                progress_callback.start_step(1, "Create Template")
            
            step1_output = self._run_step1(input_file_path, output_dir)
            
            if progress_callback:
                progress_callback.complete_step(1, "Create Template")
            self.processing_stats["steps_completed"] = 1
            
            # Step 2: Data Extraction
            if progress_callback:
                progress_callback.start_step(2, "Extract Data")
            
            step2_output = self._run_step2(step1_output, input_file_path, output_dir)
            
            if progress_callback:
                progress_callback.complete_step(2, "Extract Data")
            self.processing_stats["steps_completed"] = 2
            
            # Step 3: Data Mapping
            if progress_callback:
                progress_callback.start_step(3, "Map Data")
            
            step3_output = self._run_step3(input_file_path, step2_output, output_dir)
            
            if progress_callback:
                progress_callback.complete_step(3, "Map Data")
            self.processing_stats["steps_completed"] = 3
            
            # Step 4: Data Fill
            if progress_callback:
                progress_callback.start_step(4, "Fill Data")
            
            step4_output = self._run_step4(step3_output, output_dir)
            
            if progress_callback:
                progress_callback.complete_step(4, "Fill Data")
            self.processing_stats["steps_completed"] = 4
            
            # Step 5: Filter & Deduplicate
            if progress_callback:
                progress_callback.start_step(5, "Filter & Deduplicate")
            
            final_output = self._run_step5(step4_output, output_dir)
            
            if progress_callback:
                progress_callback.complete_step(5, "Filter & Deduplicate")
            self.processing_stats["steps_completed"] = 5
            
            # Calculate final statistics
            end_time = time.time()
            reporter.end_processing()
            
            # Get quality summary
            quality_summary = reporter.get_user_summary()
            
            self.processing_stats.update({
                "end_time": end_time,
                "processing_time": end_time - start_time,
                "success": True,
                "final_output": str(final_output),
                "quality_score": quality_summary["quality_score"],
                "warnings_count": quality_summary["warnings_count"],
                "errors_count": quality_summary["errors_count"],
                "quality_summary": quality_summary
            })
            
            logger.info(f"Pipeline completed successfully: {final_output}")
            logger.info(f"Quality score: {quality_summary['quality_score']:.1f}/100")
            return True, final_output, self.processing_stats
            
        except Exception as e:
            error_msg = str(e)
            error_details = traceback.format_exc()
            
            logger.error(f"Pipeline failed: {error_msg}")
            logger.error(f"Error details: {error_details}")
            
            if progress_callback:
                current_step = self.processing_stats.get("steps_completed", 0) + 1
                progress_callback.error_step(current_step, error_msg)
            
            self.processing_stats.update({
                "end_time": time.time(),
                "processing_time": time.time() - start_time,
                "success": False,
                "error_message": error_msg,
                "error_details": error_details if STREAMLIT_CONFIG.get("show_error_details") else None
            })
            
            return False, None, self.processing_stats
    
    @with_retry(max_retries=2, backoff_factor=0.5, exceptions=(OSError, PermissionError))
    def _run_step1(self, input_file: Path, output_dir: Path) -> Path:
        """Run Step 1: Template Creation with retry logic"""
        with ResourceManager() as rm:
            try:
                creator = step1_template_creation.TemplateCreator()
                output_file = creator.create_template(str(input_file))
                
                # Move output to session output directory
                output_path = Path(output_file)
                session_output = output_dir / output_path.name
                
                # Add intermediate file to cleanup
                rm.add_temp_file(output_path)
                
                # Ensure target directory exists
                output_dir.mkdir(parents=True, exist_ok=True)
                
                # Use copy instead of move for safety
                shutil.copy2(output_path, session_output)
                
                logger.info(f"Step 1 completed successfully: {session_output}")
                return session_output
                
            except Exception as e:
                logger.error(f"Step 1 error: {str(e)}")
                raise TSConverterError(f"Template creation failed: {str(e)}")
    
    @with_retry(max_retries=2, backoff_factor=0.5, exceptions=(OSError, PermissionError))
    def _run_step2(self, step1_output: Path, source_file: Path, output_dir: Path) -> Path:
        """Run Step 2: Data Extraction with graceful fallbacks and retry logic"""
        with ResourceManager() as rm:
            try:
                extractor = step2_data_extraction.DataExtractor()
                
                # Use graceful fallback processing to handle missing headers and formula errors
                output_file = extractor.process_file_with_fallbacks(
                    str(step1_output), 
                    str(source_file),
                    allow_missing_headers=True
                )
                
                # Move output to session output directory
                output_path = Path(output_file)
                session_output = output_dir / output_path.name
                
                rm.add_temp_file(output_path)
                output_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(output_path, session_output)
                
                logger.info(f"Step 2 completed successfully (with graceful fallbacks): {session_output}")
                return session_output
                
            except Exception as e:
                logger.error(f"Step 2 error: {str(e)}")
                
                # Try fallback to regular processing if graceful processing fails
                try:
                    logger.info("Attempting fallback to regular processing...")
                    extractor = step2_data_extraction.DataExtractor()
                    output_file = extractor.process_file(str(step1_output), str(source_file))
                    
                    output_path = Path(output_file)
                    session_output = output_dir / output_path.name
                    
                    rm.add_temp_file(output_path)
                    shutil.copy2(output_path, session_output)
                    
                    logger.info(f"Step 2 completed with fallback processing: {session_output}")
                    return session_output
                    
                except Exception as fallback_error:
                    logger.error(f"Both graceful and fallback processing failed: {fallback_error}")
                    raise TSConverterError(f"Data extraction failed: {str(e)}")
                    
                raise TSConverterError(f"Data extraction failed: {str(e)}")
    
    @with_retry(max_retries=2, backoff_factor=0.5, exceptions=(OSError, PermissionError))
    def _run_step3(self, source_file: Path, step2_output: Path, output_dir: Path) -> Path:
        """Run Step 3: Data Mapping with retry logic"""
        with ResourceManager() as rm:
            try:
                mapper = step3_data_mapping.DataMapper()
                output_file = mapper.process_file(str(source_file), str(step2_output))
                
                output_path = Path(output_file)
                session_output = output_dir / output_path.name
                
                rm.add_temp_file(output_path)
                output_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(output_path, session_output)
                
                logger.info(f"Step 3 completed successfully: {session_output}")
                return session_output
                
            except Exception as e:
                logger.error(f"Step 3 error: {str(e)}")
                raise TSConverterError(f"Data mapping failed: {str(e)}")
    
    @with_retry(max_retries=2, backoff_factor=0.5, exceptions=(OSError, PermissionError))
    def _run_step4(self, step3_output: Path, output_dir: Path) -> Path:
        """Run Step 4: Data Fill with retry logic"""
        with ResourceManager() as rm:
            try:
                filler = step4_data_fill.DataFiller()
                output_file = filler.process_file(str(step3_output))
                
                output_path = Path(output_file)
                session_output = output_dir / output_path.name
                
                rm.add_temp_file(output_path)
                output_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(output_path, session_output)
                
                logger.info(f"Step 4 completed successfully: {session_output}")
                return session_output
                
            except Exception as e:
                logger.error(f"Step 4 error: {str(e)}")
                raise TSConverterError(f"Data fill failed: {str(e)}")
    
    @with_retry(max_retries=2, backoff_factor=0.5, exceptions=(OSError, PermissionError))
    def _run_step5(self, step4_output: Path, output_dir: Path) -> Path:
        """Run Step 5: Filter & Deduplicate with retry logic"""
        with ResourceManager() as rm:
            try:
                filter_dedup = step5_filter_deduplicate.DataFilter()
                output_file = filter_dedup.process_file(str(step4_output))
                
                output_path = Path(output_file)
                session_output = output_dir / output_path.name
                
                rm.add_temp_file(output_path)
                output_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(output_path, session_output)
                
                # Extract processing statistics
                self._extract_step5_stats(session_output)
                
                logger.info(f"Step 5 completed successfully: {session_output}")
                return session_output
                
            except Exception as e:
                logger.error(f"Step 5 error: {str(e)}")
                raise TSConverterError(f"Filter & deduplicate failed: {str(e)}")
    
    def _extract_step5_stats(self, output_file: Path):
        """Extract statistics from Step 5 output for display"""
        try:
            import openpyxl
            wb = openpyxl.load_workbook(output_file)
            ws = wb.active
            
            # Count final rows (excluding header)
            final_rows = ws.max_row - 3  # Subtract header rows
            
            # Update stats
            self.processing_stats.update({
                "final_rows": final_rows,
                # Add more statistics as needed
            })
            
            wb.close()
        except Exception as e:
            logger.warning(f"Could not extract statistics: {e}")
    
    def cleanup_session(self):
        """Clean up session directory and temporary files"""
        if self.current_session_id:
            session_dir = self.temp_dir / self.current_session_id
            try:
                if session_dir.exists():
                    shutil.rmtree(session_dir)
                    logger.info(f"Cleaned up session: {self.current_session_id}")
            except Exception as e:
                logger.error(f"Failed to cleanup session {self.current_session_id}: {e}")
            finally:
                self.current_session_id = None
    
    def validate_input_file(self, file_path: Path) -> Tuple[bool, str]:
        """
        Enhanced input file validation with security checks
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Use enhanced security validation
            FileValidator.validate_file_format(file_path)
            
            logger.info(f"File validation passed for: {file_path.name}")
            return True, "File validation successful"
            
        except TSConverterError as e:
            # Provide user-friendly error messages
            if "signature" in str(e).lower():
                return False, "Invalid file format. Please upload a valid Excel (.xlsx) file."
            elif "size" in str(e).lower():
                return False, f"File too large. Maximum size: {FileValidator.MAX_FILE_SIZE // (1024*1024)}MB"
            elif "malicious" in str(e).lower():
                return False, "File contains suspicious content and cannot be processed."
            elif "worksheets" in str(e).lower():
                return False, "File has too many worksheets or invalid structure."
            else:
                return False, f"File validation failed: {str(e)}"
                
        except Exception as e:
            logger.error(f"Unexpected validation error for {file_path}: {e}")
            return False, "File validation failed due to an unexpected error. Please try again."
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get current processing statistics"""
        return self.processing_stats.copy()