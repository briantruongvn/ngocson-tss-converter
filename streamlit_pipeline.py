"""
Streamlit Pipeline Integration for TSS Converter
Wraps the existing 5-step pipeline with progress tracking and error handling.
"""

import os
import sys
import tempfile
import shutil
import time
from pathlib import Path
from typing import Dict, Any, Optional, Callable, Tuple
import logging
import traceback

# Import existing pipeline modules (they use function-based approach)
import step1_template_creation
import step2_data_extraction
import step3_data_mapping
import step4_data_fill
import step5_filter_deduplicate
from common.exceptions import TSConverterError
from common.validation import FileValidator
from config_streamlit import get_temp_directory, STREAMLIT_CONFIG

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
            self.processing_stats.update({
                "end_time": end_time,
                "processing_time": end_time - start_time,
                "success": True,
                "final_output": str(final_output)
            })
            
            logger.info(f"Pipeline completed successfully: {final_output}")
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
    
    def _run_step1(self, input_file: Path, output_dir: Path) -> Path:
        """Run Step 1: Template Creation"""
        try:
            creator = step1_template_creation.TemplateCreator()
            output_file = creator.create_template(str(input_file))
            
            # Move output to session output directory
            output_path = Path(output_file)
            session_output = output_dir / output_path.name
            shutil.move(output_path, session_output)
            
            return session_output
        except Exception as e:
            raise TSConverterError(f"Step 1 failed: {str(e)}")
    
    def _run_step2(self, step1_output: Path, source_file: Path, output_dir: Path) -> Path:
        """Run Step 2: Data Extraction"""
        try:
            extractor = step2_data_extraction.DataExtractor()
            output_file = extractor.process_file(str(step1_output), str(source_file))
            
            # Move output to session output directory
            output_path = Path(output_file)
            session_output = output_dir / output_path.name
            shutil.move(output_path, session_output)
            
            return session_output
        except Exception as e:
            raise TSConverterError(f"Step 2 failed: {str(e)}")
    
    def _run_step3(self, source_file: Path, step2_output: Path, output_dir: Path) -> Path:
        """Run Step 3: Data Mapping"""
        try:
            mapper = step3_data_mapping.DataMapper()
            output_file = mapper.process_file(str(source_file), str(step2_output))
            
            # Move output to session output directory
            output_path = Path(output_file)
            session_output = output_dir / output_path.name
            shutil.move(output_path, session_output)
            
            return session_output
        except Exception as e:
            raise TSConverterError(f"Step 3 failed: {str(e)}")
    
    def _run_step4(self, step3_output: Path, output_dir: Path) -> Path:
        """Run Step 4: Data Fill"""
        try:
            filler = step4_data_fill.DataFiller()
            output_file = filler.process_file(str(step3_output))
            
            # Move output to session output directory
            output_path = Path(output_file)
            session_output = output_dir / output_path.name
            shutil.move(output_path, session_output)
            
            return session_output
        except Exception as e:
            raise TSConverterError(f"Step 4 failed: {str(e)}")
    
    def _run_step5(self, step4_output: Path, output_dir: Path) -> Path:
        """Run Step 5: Filter & Deduplicate"""
        try:
            filter_dedup = step5_filter_deduplicate.DataFilter()
            output_file = filter_dedup.process_file(str(step4_output))
            
            # Move output to session output directory and extract statistics
            output_path = Path(output_file)
            session_output = output_dir / output_path.name
            shutil.move(output_path, session_output)
            
            # Extract processing statistics from logs or output
            self._extract_step5_stats(session_output)
            
            return session_output
        except Exception as e:
            raise TSConverterError(f"Step 5 failed: {str(e)}")
    
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
        Validate input file format and structure
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            validator = FileValidator()
            
            # Basic file validation
            if not file_path.exists():
                return False, "File không tồn tại"
            
            if not file_path.suffix.lower() == '.xlsx':
                return False, "File phải có định dạng .xlsx"
            
            # File size validation
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            max_size = STREAMLIT_CONFIG.get("max_file_size_mb", 50)
            if file_size_mb > max_size:
                return False, f"File quá lớn. Kích thước tối đa: {max_size}MB"
            
            # Basic structure validation
            import openpyxl
            wb = openpyxl.load_workbook(file_path, read_only=True)
            if not wb.worksheets:
                return False, "File Excel không có worksheet nào"
            wb.close()
            
            return True, "File hợp lệ"
            
        except Exception as e:
            return False, f"Lỗi validate file: {str(e)}"
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get current processing statistics"""
        return self.processing_stats.copy()