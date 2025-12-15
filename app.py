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
from streamlit_pipeline import StreamlitTSSPipeline, ProgressCallback
from common.rate_limiter import check_request_allowed, RateLimitConfig, get_rate_limiter

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

def get_client_info():
    """Get client IP and session ID for rate limiting"""
    try:
        # Try to get real client IP from headers (for deployment behind proxy)
        client_ip = st.context.headers.get("x-forwarded-for", "")
        if not client_ip:
            client_ip = st.context.headers.get("x-real-ip", "127.0.0.1")
    except:
        # Fallback for local development
        client_ip = "127.0.0.1"
    
    # Use session ID from Streamlit
    session_id = st.session_state.get('session_id', f"session_{int(time.time())}")
    if 'session_id' not in st.session_state:
        st.session_state.session_id = session_id
    
    return client_ip, session_id

def check_rate_limits() -> bool:
    """Check rate limits and return True if request is allowed"""
    client_ip, session_id = get_client_info()
    
    allowed, reason = check_request_allowed(client_ip, session_id)
    
    if not allowed:
        st.error(f"🚫 {reason}")
        st.info("Please wait a few minutes before trying again.")
        
        # Show rate limiter stats for debugging (only in development)
        if STREAMLIT_CONFIG.get("show_error_details", False):
            limiter = get_rate_limiter()
            stats = limiter.get_stats()
            st.write("Debug - Rate Limiter Stats:", stats)
        
        return False
    
    return True

def initialize_session_state():
    """Initialize Streamlit session state variables"""
    if 'pipeline' not in st.session_state:
        st.session_state.pipeline = StreamlitTSSPipeline()
    
    if 'processing' not in st.session_state:
        st.session_state.processing = False
    
    if 'progress_data' not in st.session_state:
        st.session_state.progress_data = {
            "current_step": 0,
            "step_status": {f"step{i}": "pending" for i in range(1, 6)},
            "message": "Ready to process",
            "error": False
        }
    
    if 'processing_complete' not in st.session_state:
        st.session_state.processing_complete = False
    
    if 'output_file_path' not in st.session_state:
        st.session_state.output_file_path = None
    
    if 'processing_stats' not in st.session_state:
        st.session_state.processing_stats = {}

def process_file_sync(file_data: bytes, filename: str):
    """Process file synchronously to avoid session state issues"""
    try:
        # Initialize pipeline
        pipeline = StreamlitTSSPipeline()
        
        # Save uploaded file
        input_file_path = pipeline.save_uploaded_file(file_data, filename)
        
        # Validate file
        is_valid, error_message = pipeline.validate_input_file(input_file_path)
        if not is_valid:
            st.session_state.processing = False
            st.session_state.progress_data.update({
                "error": True,
                "message": f"File validation failed: {error_message}"
            })
            return
        
        # Create progress placeholder
        progress_placeholder = st.empty()
        
        def update_ui_progress(progress_data):
            """Update UI progress synchronously"""
            step = progress_data.get("current_step", 0)
            message = progress_data.get("message", "Processing...")
            
            # Update session state
            st.session_state.progress_data.update(progress_data)
            
            # Update UI
            with progress_placeholder.container():
                completed_steps = sum(1 for status in progress_data.get("step_status", {}).values() if status == "completed")
                progress_percentage = int((completed_steps / 5) * 100)
                st.progress(completed_steps / 5, text=f"📊 Progress: {progress_percentage}% ({completed_steps}/5 steps completed)")
            
        
        # Create progress callback
        progress_callback = ProgressCallback(update_ui_progress)
        
        # Run pipeline with progress updates
        with st.spinner("🔄 Processing file..."):
            success, output_file, stats = pipeline.process_pipeline(
                input_file_path, progress_callback
            )
        
        if success:
            # Copy file to a persistent location before cleanup
            import shutil
            persistent_output_dir = Path("temp/downloads")
            persistent_output_dir.mkdir(parents=True, exist_ok=True)
            
            persistent_file_path = persistent_output_dir / f"TSS_Converted_{int(time.time())}.xlsx"
            
            shutil.copy2(output_file, persistent_file_path)
            
            # Set session state after successful file copy
            st.session_state.processing_complete = True
            st.session_state.output_file_path = persistent_file_path
            st.session_state.processing_stats = stats
            st.session_state.progress_data.update({
                "message": "Processing completed successfully!",
                "error": False
            })
            
        else:
            st.session_state.progress_data.update({
                "error": True,
                "message": f"Processing failed: {stats.get('error_message', 'Unknown error')}"
            })
            st.session_state.processing_stats = stats
            
        # Cleanup session but keep output file
        pipeline.cleanup_session()
                
    except Exception as e:
        logger.error(f"Processing error: {e}")
        st.session_state.progress_data.update({
            "error": True,
            "message": f"Error during processing: {str(e)}"
        })
    finally:
        st.session_state.processing = False
        # Force UI refresh to show results (success or error)
        st.rerun()

def main():
    """Main application function"""
    # Initialize session state
    initialize_session_state()
    
    # Inject custom CSS
    inject_custom_css()
    
    # Render header
    render_app_header()
    
    # Main content area with responsive layout
    if not st.session_state.processing and not st.session_state.processing_complete:
        # Centered layout for upload only
        _, center_col, _ = st.columns([1, 2, 1])
        with center_col:
            st.markdown("### 📁 Upload File")
            
            file_data = render_file_upload_area()
            
            if file_data is not None:
                # Store uploaded file info in session state
                if 'uploaded_file_info' not in st.session_state:
                    st.session_state.uploaded_file_info = None
                
                st.session_state.uploaded_file_info = {
                    'data': file_data,
                    'name': f"uploaded_file_{int(time.time())}.xlsx"
                }
                
            if st.session_state.get('uploaded_file_info') and st.button("🚀 Start Conversion", type="primary"):
                # Check rate limits before processing
                if not check_rate_limits():
                    return  # Stop execution if rate limited
                
                file_info = st.session_state.uploaded_file_info
                file_data = file_info['data']
                filename = file_info['name']
                
                # Start processing
                st.session_state.processing = True
                st.session_state.processing_complete = False
                st.session_state.output_file_path = None
                st.session_state.processing_start_time = time.time()
                
                # Reset progress
                st.session_state.progress_data = {
                    "current_step": 0,
                    "step_status": {f"step{i}": "pending" for i in range(1, 6)},
                    "message": "Starting processing...",
                    "error": False
                }
                
                # Start synchronous processing
                process_file_sync(file_data, filename)
    
    else:
        # Full width for processing and results  
        # Simple status during processing
        if st.session_state.processing:
            with st.spinner("🔄 Processing... Please wait"):
                progress_data = st.session_state.progress_data
                if progress_data.get("error"):
                    render_error_message(
                        progress_data.get("message", "An error occurred"),
                        details=st.session_state.processing_stats.get("error_details")
                    )
        
        # Download section - centered
        if st.session_state.processing_complete and st.session_state.output_file_path:
            _, center_col, _ = st.columns([1, 2, 1])
            with center_col:
                st.markdown("## ⬇️ Download Results")
                render_download_section(
                    output_file_path=st.session_state.output_file_path,
                    processing_stats=st.session_state.processing_stats
                )
        
        # Reset/Clear section - centered
        if st.session_state.processing_complete or st.session_state.progress_data.get("error"):
            _, center_col, _ = st.columns([1, 2, 1])
            with center_col:
                col_reset, col_clear = st.columns(2, gap="small")
                
                with col_reset:
                    if st.button("🔄 Process New File", type="secondary"):
                        # Reset session state
                        st.session_state.processing = False
                        st.session_state.processing_complete = False
                        st.session_state.output_file_path = None
                        st.session_state.processing_stats = {}
                        st.session_state.progress_data = {
                            "current_step": 0,
                            "step_status": {f"step{i}": "pending" for i in range(1, 6)},
                            "message": "Ready to process",
                            "error": False
                        }
                        
                        # Cleanup previous session
                        if st.session_state.pipeline:
                            st.session_state.pipeline.cleanup_session()
                        
                        st.rerun()
                
                with col_clear:
                    clear_temp_files_button()

if __name__ == "__main__":
    # Set up proper error handling
    try:
        main()
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        logger.error(f"Application error: {e}", exc_info=True)
        
        # Show error details if in development
        if STREAMLIT_CONFIG.get("show_error_details", False):
            st.exception(e)