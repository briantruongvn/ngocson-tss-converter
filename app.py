"""
TSS Converter Streamlit Web Application
Main application file for the Excel Template Converter web interface.
"""

import streamlit as st
import time
import threading
from typing import Dict, Any
from pathlib import Path
import logging

# Import custom modules
from config_streamlit import STREAMLIT_CONFIG
from ui_components import (
    inject_custom_css, render_app_header, render_file_upload_area,
    render_progress_section, render_download_section, render_help_section,
    render_footer, render_error_message, render_success_message,
    render_info_message, clear_temp_files_button
)
from streamlit_pipeline import StreamlitTSSPipeline, ProgressCallback, ResourceManager
from common.security import SecurityError, validate_path_security, generate_secure_filename
from common.session_manager import session_manager, ProcessingState, safe_update_session_state, safe_get_session_value

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title=STREAMLIT_CONFIG["page_title"],
    page_icon=STREAMLIT_CONFIG["app_icon"],
    layout=STREAMLIT_CONFIG["layout"],
    initial_sidebar_state=STREAMLIT_CONFIG["initial_sidebar_state"]
)

def initialize_session_state():
    """Initialize Streamlit session state variables with security"""
    try:
        # Initialize secure session manager
        session_manager.initialize_session_state()
        
        # Initialize pipeline if not exists
        if 'pipeline' not in st.session_state:
            st.session_state.pipeline = StreamlitTSSPipeline()
        
        # Use secure session management for other state variables
        if not safe_get_session_value('app_initialized', False):
            safe_update_session_state({
                'processing': False,
                'progress_data': {
                    "current_step": 0,
                    "step_status": {f"step{i}": "pending" for i in range(1, 7)},
                    "message": "Sẵn sàng xử lý",
                    "error": False
                },
                'processing_complete': False,
                'output_file_path': None,
                'processing_stats': {},
                'app_initialized': True
            })
            
    except Exception as e:
        logger.error(f"Session initialization error: {e}")
        # Fallback to basic initialization
        if 'pipeline' not in st.session_state:
            st.session_state.pipeline = StreamlitTSSPipeline()

def process_file_sync(file_data: bytes, filename: str):
    """Process file synchronously with enhanced security and resource management"""
    temp_files = []
    
    try:
        # Update processing state securely
        session_manager.update_processing_state(ProcessingState.UPLOADING)
        
        # Initialize pipeline
        pipeline = StreamlitTSSPipeline()
        
        # Security: validate file before processing
        if len(file_data) == 0:
            raise SecurityError("Empty file uploaded")
            
        # Use secure filename generation
        secure_filename = generate_secure_filename("upload")
        logger.info(f"Processing file with secure name: {secure_filename}")
        
        # Save uploaded file securely
        session_manager.update_processing_state(ProcessingState.VALIDATING)
        input_file_path = pipeline.save_uploaded_file(file_data, secure_filename)
        temp_files.append(input_file_path)
        
        # Validate file
        is_valid, error_message = pipeline.validate_input_file(input_file_path)
        if not is_valid:
            safe_update_session_state({
                'processing': False,
                'progress_data': {
                    "error": True,
                    "message": f"File validation failed: {error_message}"
                }
            })
            session_manager.update_processing_state(ProcessingState.ERROR)
            return
        
        # Create progress placeholder
        progress_placeholder = st.empty()
        
        def update_ui_progress(progress_data):
            """Update UI progress synchronously with secure session management"""
            try:
                step = progress_data.get("current_step", 0)
                message = progress_data.get("message", "Processing...")
                
                # Update session state securely
                current_progress = safe_get_session_value('progress_data', {})
                current_progress.update(progress_data)
                
                safe_update_session_state({
                    'progress_data': current_progress
                })
                
                # Update UI
                with progress_placeholder.container():
                    completed_steps = sum(1 for status in progress_data.get("step_status", {}).values() if status == "completed")
                    progress_percentage = int((completed_steps / 6) * 100)
                    st.progress(completed_steps / 6, text=f"📊 Progress: {progress_percentage}% ({completed_steps}/6 steps completed)")
                    
            except Exception as e:
                logger.warning(f"Progress update error: {e}")
            
        
        # Create progress callback
        progress_callback = ProgressCallback(update_ui_progress)
        
        # Run pipeline with progress updates using resource manager
        session_manager.update_processing_state(ProcessingState.PROCESSING)
        
        with ResourceManager(pipeline.temp_dir) as rm:
            with st.spinner("🔄 Processing file..."):
                success, output_file, stats = pipeline.process_pipeline(
                    input_file_path, progress_callback
                )
            
            if output_file:
                # DO NOT add output_file to ResourceManager cleanup - we need to keep it!
                # rm.add_temp_file(output_file)  # ← REMOVED: This was deleting our output file!
                temp_files.append(output_file)
        
        if success:
            # Copy file to a persistent location before cleanup with security validation
            import shutil
            persistent_output_dir = Path("temp/downloads")
            
            # Security: validate output directory
            if not validate_path_security(persistent_output_dir, Path.cwd()):
                raise SecurityError("Output directory path validation failed")
                
            persistent_output_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
            
            # Generate secure output filename with date format
            from datetime import datetime
            current_date = datetime.now().strftime("%Y%m%d")
            secure_output_name = f"TSS_Converted_{current_date}.xlsx"
            persistent_file_path = persistent_output_dir / secure_output_name
            
            # Security: validate final output path
            if not validate_path_security(persistent_file_path, Path.cwd()):
                raise SecurityError("Output file path validation failed")
            
            shutil.copy2(output_file, persistent_file_path)
            persistent_file_path.chmod(0o600)  # Secure file permissions
            
            # Set session state after successful file copy
            safe_update_session_state({
                'processing_complete': True,
                'output_file_path': str(persistent_file_path),
                'processing_stats': stats,
                'progress_data': {
                    "message": "Processing completed successfully!",
                    "error": False
                }
            })
            
            session_manager.update_processing_state(ProcessingState.COMPLETED)
            logger.info(f"File processed successfully: {persistent_file_path}")
            
        else:
            safe_update_session_state({
                'progress_data': {
                    "error": True,
                    "message": f"Processing failed: {stats.get('error_message', 'Unknown error')}"
                },
                'processing_stats': stats
            })
            session_manager.update_processing_state(ProcessingState.ERROR)
            
        # Cleanup session but keep output file
        try:
            pipeline.cleanup_session()
        except Exception as cleanup_error:
            logger.warning(f"Session cleanup error: {cleanup_error}")
                
    except SecurityError as se:
        logger.error(f"Security error during processing: {se}")
        safe_update_session_state({
            'progress_data': {
                "error": True,
                "message": f"Security error: {str(se)}"
            }
        })
        session_manager.update_processing_state(ProcessingState.ERROR)
        
    except Exception as e:
        logger.error(f"Processing error: {e}")
        safe_update_session_state({
            'progress_data': {
                "error": True,
                "message": f"Error during processing: {str(e)}"
            }
        })
        session_manager.update_processing_state(ProcessingState.ERROR)
        
    finally:
        # Secure cleanup of temporary files
        for temp_file in temp_files:
            try:
                temp_path = Path(temp_file)
                if temp_path.exists() and validate_path_security(temp_path, Path.cwd()):
                    temp_path.unlink(missing_ok=True)
            except Exception as cleanup_error:
                logger.warning(f"Temp file cleanup error for {temp_file}: {cleanup_error}")
        
        safe_update_session_state({'processing': False})
        # Force UI refresh to show results (success or error)
        st.rerun()

def main():
    """Main application function"""
    # Initialize session state
    initialize_session_state()
    
    # Inject custom CSS
    inject_custom_css()
    
    # Determine layout state for optimal space usage
    is_compact_mode = st.session_state.processing or st.session_state.processing_complete
    
    # Render header with appropriate compactness
    render_app_header(compact=is_compact_mode)
    
    # Main content area with optimized layout - use secure session state
    processing = safe_get_session_value('processing', False)
    processing_complete = safe_get_session_value('processing_complete', False)
    
    if not processing and not processing_complete:
        # Responsive layout for upload
        col1, col2, col3 = st.columns([0.5, 2, 0.5])
        with col2:
            file_upload_result = render_file_upload_area()
            
            if file_upload_result is not None:
                file_data, original_filename = file_upload_result
                # Store uploaded file info in session state with original filename
                if 'uploaded_file_info' not in st.session_state:
                    st.session_state.uploaded_file_info = None
                
                st.session_state.uploaded_file_info = {
                    'data': file_data,
                    'name': f"uploaded_file_{int(time.time())}.xlsx",  # Internal name
                    'original_filename': original_filename  # Preserve original filename
                }
                
            if st.session_state.get('uploaded_file_info') and st.button("🚀 Start Conversion", type="primary"):
                try:
                    file_info = st.session_state.uploaded_file_info
                    file_data = file_info['data']
                    filename = file_info['name']
                    
                    # Start processing with secure session state
                    safe_update_session_state({
                        'processing': True,
                        'processing_complete': False,
                        'output_file_path': None,
                        'processing_start_time': time.time(),
                        'progress_data': {
                            "current_step": 0,
                            "step_status": {f"step{i}": "pending" for i in range(1, 7)},
                            "message": "Starting processing...",
                            "error": False
                        }
                    })
                    
                    # Start synchronous processing
                    logger.info(f"Starting file processing: {filename}")
                    process_file_sync(file_data, filename)
                    
                except SecurityError as se:
                    logger.error(f"Security error starting conversion: {se}")
                    st.error(f"Security error: {str(se)}")
                    safe_update_session_state({'processing': False})
                    session_manager.update_processing_state(ProcessingState.ERROR)
                    
                except Exception as e:
                    logger.error(f"Error starting conversion: {e}")
                    st.error(f"Error starting conversion: {str(e)}")
                    safe_update_session_state({'processing': False})
                    session_manager.update_processing_state(ProcessingState.ERROR)
    
    else:
        # Processing and results with minimal spacing - use secure session state
        processing = safe_get_session_value('processing', False)
        if processing:
            # Compact progress display - prioritize visibility
            progress_data = safe_get_session_value('progress_data', {})
            if progress_data.get("error"):
                processing_stats = safe_get_session_value('processing_stats', {})
                render_error_message(
                    progress_data.get("message", "An error occurred"),
                    details=processing_stats.get("error_details")
                )
            else:
                # Show compact progress in main area for visibility
                render_progress_section(
                    current_step=progress_data.get("current_step", 0),
                    step_status=progress_data.get("step_status", {}),
                    compact=True
                )
        
        # Download section - optimized spacing with secure session state
        processing_complete = safe_get_session_value('processing_complete', False)
        output_file_path_str = safe_get_session_value('output_file_path')
        
        # Convert string to Path object for proper .exists() method support
        output_file_path = None
        if output_file_path_str:
            try:
                output_file_path = Path(output_file_path_str)
            except (TypeError, ValueError) as e:
                logger.warning(f"Failed to convert output_file_path to Path: {e}")
                output_file_path = None
        
        if processing_complete and output_file_path:
            col1, col2, col3 = st.columns([0.5, 2, 0.5])
            with col2:
                st.markdown("### ⬇️ Download Results")
                processing_stats = safe_get_session_value('processing_stats', {})
                render_download_section(
                    output_file_path=output_file_path,
                    processing_stats=processing_stats
                )
        
        # Reset/Clear section - compact with secure session state
        progress_data = safe_get_session_value('progress_data', {})
        if processing_complete or progress_data.get("error"):
            col1, col2, col3 = st.columns([0.5, 2, 0.5])
            with col2:
                col_reset, col_clear = st.columns(2, gap="small")
                
                with col_reset:
                    if st.button("🔄 Process New File", type="secondary"):
                        # Reset session state securely
                        safe_update_session_state({
                            'processing': False,
                            'processing_complete': False,
                            'output_file_path': None,
                            'processing_stats': {},
                            'progress_data': {
                                "current_step": 0,
                                "step_status": {f"step{i}": "pending" for i in range(1, 7)},
                                "message": "Ready to process",
                                "error": False
                            }
                        })
                        
                        # Cleanup previous session
                        if st.session_state.pipeline:
                            try:
                                st.session_state.pipeline.cleanup_session()
                            except Exception as cleanup_error:
                                logger.warning(f"Pipeline cleanup error: {cleanup_error}")
                        
                        # Reset processing state
                        session_manager.update_processing_state(ProcessingState.IDLE)
                        session_manager.cleanup_session_state()
                        
                        st.rerun()
                
                with col_clear:
                    clear_temp_files_button()

if __name__ == "__main__":
    # Set up proper error handling with security considerations
    try:
        # Ensure session cleanup on app restart
        try:
            session_manager.cleanup_old_sessions(max_age_hours=1.0)
        except Exception as cleanup_error:
            logger.warning(f"Old session cleanup error: {cleanup_error}")
            
        main()
        
    except SecurityError as se:
        st.error(f"Security error: {str(se)}")
        logger.error(f"Security error: {se}", exc_info=True)
        
        # Reset to safe state
        session_manager.update_processing_state(ProcessingState.ERROR)
        
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        logger.error(f"Application error: {e}", exc_info=True)
        
        # Show error details if in development
        if STREAMLIT_CONFIG.get("show_error_details", False):
            st.exception(e)
            
        # Reset to safe state
        try:
            session_manager.update_processing_state(ProcessingState.ERROR)
        except Exception:
            pass