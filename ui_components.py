"""
Reusable UI components for TSS Converter Streamlit Web App
Provides consistent styling and functionality across the application.
"""

import streamlit as st
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import time

from config_streamlit import get_custom_css, get_step_config, STREAMLIT_CONFIG

def inject_custom_css():
    """Inject custom CSS styling into Streamlit app"""
    st.markdown(get_custom_css(), unsafe_allow_html=True)
    
    # Additional JavaScript to hide Streamlit Cloud elements
    hide_streamlit_js = """
    <script>
    function hideStreamlitCloudElements() {
        // More specific selectors for Streamlit Cloud
        const elementsToHide = [
            // Toolbar area
            '[data-testid="stToolbar"]',
            '[data-testid="stHeader"]', 
            '[data-testid="stDecoration"]',
            'header[data-testid="stHeader"]',
            
            // Buttons in toolbar
            'button[title="View app source on GitHub"]',
            'button[aria-label="Share"]',
            'button[aria-label="Star"]', 
            'button[aria-label="Edit"]',
            'button[title="Share"]',
            'button[title="Star"]',
            'button[title="Edit"]',
            
            // Manage app
            '[data-testid="manage-app-button"]',
            'button:has-text("Manage app")',
            
            // GitHub links
            'a[href*="github.com"]',
            
            // Generic CSS classes
            '.stToolbar',
            '.css-1rs6os', 
            '.css-18e3th9',
            '.css-1d391kg',
            '.css-1kyxreq',
            '.css-k1vhr4'
        ];
        
        elementsToHide.forEach(selector => {
            const elements = document.querySelectorAll(selector);
            elements.forEach(el => {
                if (el) {
                    el.style.display = 'none !important';
                    el.style.visibility = 'hidden !important';
                    el.style.opacity = '0 !important';
                    el.style.height = '0 !important';
                    el.style.width = '0 !important';
                    el.style.overflow = 'hidden !important';
                    el.remove(); // Remove from DOM completely
                }
            });
        });
        
        // Hide parent containers that might contain these elements
        const parentContainers = document.querySelectorAll('header, [role="banner"]');
        parentContainers.forEach(container => {
            const hasUnwantedContent = container.textContent.includes('Share') || 
                                     container.textContent.includes('Star') ||
                                     container.textContent.includes('Edit') ||
                                     container.textContent.includes('Manage app') ||
                                     container.querySelector('a[href*="github"]');
            if (hasUnwantedContent) {
                container.style.display = 'none !important';
                container.remove();
            }
        });
    }
    
    // Run multiple times to ensure elements are hidden
    hideStreamlitCloudElements();
    setTimeout(hideStreamlitCloudElements, 100);
    setTimeout(hideStreamlitCloudElements, 500);
    setTimeout(hideStreamlitCloudElements, 1000);
    setTimeout(hideStreamlitCloudElements, 2000);
    
    // Create observer for dynamic content
    const observer = new MutationObserver(hideStreamlitCloudElements);
    observer.observe(document.body, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ['class', 'id']
    });
    
    // Run on various events
    window.addEventListener('load', hideStreamlitCloudElements);
    document.addEventListener('DOMContentLoaded', hideStreamlitCloudElements);
    
    // Aggressive periodic cleanup
    setInterval(hideStreamlitCloudElements, 500);
    </script>
    """
    
    st.markdown(hide_streamlit_js, unsafe_allow_html=True)

def render_app_header():
    """Render main application header"""
    # Use Streamlit native components for proper centering
    st.markdown("<div style='text-align: center; margin: 0 auto; max-width: 80%;'>", unsafe_allow_html=True)
    st.title("📊 Ngoc Son Internal TSS converter")
    st.caption("Convert Ngoc Son Internal TSS to Standard Internal TSS")
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Add shorter separator line that matches content width
    st.markdown("""
        <div style='text-align: center; margin: 1.5rem auto;'>
            <hr style='width: 60%; max-width: 600px; margin: 0 auto; border: none; border-top: 1px solid #e5e7eb;'>
        </div>
    """, unsafe_allow_html=True)

def render_file_upload_area() -> Optional[bytes]:
    """
    Render file upload area with validation
    Returns uploaded file bytes if valid
    """
    st.markdown("""
        <div class="upload-area">
            <h3>📁 Upload Excel File</h3>
            <p>Select Excel file (.xlsx) to convert</p>
        </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        label="Select Excel file",
        type=["xlsx"],
        help=f"Maximum file size: {STREAMLIT_CONFIG['max_file_size_mb']}MB",
        label_visibility="collapsed"
    )
    
    if uploaded_file is not None:
        # Validate file size
        file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
        if file_size_mb > STREAMLIT_CONFIG['max_file_size_mb']:
            render_error_message(
                f"File too large! Maximum size: {STREAMLIT_CONFIG['max_file_size_mb']}MB"
            )
            return None
        
        # Display file info
        render_info_message(
            f"✅ File uploaded: {uploaded_file.name} ({file_size_mb:.1f}MB)"
        )
        return uploaded_file.getvalue()
    
    return None

def render_progress_section(current_step: int = 0, step_status: Dict[str, str] = None):
    """
    Render progress section with step indicators
    
    Args:
        current_step: Current step number (0-5)
        step_status: Dict with step status ('pending', 'running', 'completed', 'error')
    """
    if step_status is None:
        step_status = {f"step{i}": "pending" for i in range(1, 6)}
    
    st.markdown("""
        <div class="progress-container">
            <h3>🔄 Tiến trình xử lý</h3>
        </div>
    """, unsafe_allow_html=True)
    
    step_config = get_step_config()
    
    # Calculate progress percentage
    completed_steps = sum(1 for status in step_status.values() if status == "completed")
    running_steps = sum(1 for status in step_status.values() if status == "running")
    
    # Include partial progress for running step
    progress_value = (completed_steps + (0.5 if running_steps > 0 else 0)) / 5
    progress_percentage = int(progress_value * 100)
    
    # Progress bar with percentage
    st.progress(progress_value, text=f"📊 Tiến độ: {progress_percentage}% ({completed_steps}/5 steps hoàn thành)")
    
    # Show current status
    if running_steps > 0:
        st.info(f"⏳ Đang xử lý step {current_step}... Vui lòng đợi.")
    elif completed_steps == 5:
        st.success("✅ Tất cả steps đã hoàn thành!")
    elif completed_steps > 0:
        st.info(f"🔄 Đã hoàn thành {completed_steps}/5 steps")
    
    # Step indicators
    for i in range(1, 6):
        step_key = f"step{i}"
        step_info = step_config[step_key]
        status = step_status.get(step_key, "pending")
        
        # Status icon and color
        if status == "completed":
            icon = "✅"
            css_class = "step-completed"
        elif status == "running":
            icon = "⏳"
            css_class = "step-running"
        elif status == "error":
            icon = "❌"
            css_class = "step-error"
        else:
            icon = "⏸️"
            css_class = "step-pending"
        
        # Show estimated time for running step
        time_info = ""
        if status == "running":
            time_info = f"<br><small>⏱️ Ước tính: {step_info.get('estimated_time', '?')} </small>"
        
        st.markdown(f"""
            <div class="step-indicator {css_class}">
                <strong>{icon} Step {i}: {step_info['name']}</strong><br>
                <small>{step_info['description']}</small>
                {time_info}
            </div>
        """, unsafe_allow_html=True)

def render_download_section(output_file_path: Optional[Path] = None, 
                          processing_stats: Optional[Dict[str, Any]] = None):
    """
    Render download section for final output
    
    Args:
        output_file_path: Path to final output file
        processing_stats: Statistics from processing pipeline
    """
    if output_file_path and output_file_path.exists():
        st.markdown("""
            <div class="download-section">
                <h3>🎉 Processing Complete!</h3>
                <p>File has been converted successfully. Click to download.</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Read file for download
        try:
            with open(output_file_path, "rb") as file:
                file_data = file.read()
            
            download_filename = f"TSS_Converted_{int(time.time())}.xlsx"
            
            st.download_button(
                label="📥 Download Converted File",
                data=file_data,
                file_name=download_filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help="Click to download the converted Excel file"
            )
            
            # Show processing statistics if available
            if processing_stats:
                render_processing_stats(processing_stats)
                
        except Exception as e:
            render_error_message(f"Error preparing download file: {str(e)}")
    else:
        render_warning_message("Output file is not ready for download yet.")

def render_processing_stats(stats: Dict[str, Any]):
    """Render processing statistics in expandable section"""
    with st.expander("📊 Processing Result Details"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Initial rows", 
                stats.get("initial_rows", 0)
            )
        
        with col2:
            st.metric(
                "Rows removed", 
                stats.get("removed_rows", 0),
                delta=f"-{stats.get('removal_percentage', 0):.1f}%"
            )
        
        with col3:
            st.metric(
                "Final rows", 
                stats.get("final_rows", 0)
            )
        
        # Additional details
        if stats.get("na_removed"):
            st.write(f"🗑️ NA rows removed: {stats['na_removed']}")
        if stats.get("duplicates_removed"):
            st.write(f"🔄 Duplicate rows removed: {stats['duplicates_removed']}")
        if stats.get("processing_time"):
            st.write(f"⏱️ Processing time: {stats['processing_time']:.1f} seconds")

def render_info_message(message: str):
    """Render info message box"""
    st.markdown(f"""
        <div class="info-box">
            ℹ️ {message}
        </div>
    """, unsafe_allow_html=True)

def render_success_message(message: str):
    """Render success message box"""
    st.markdown(f"""
        <div class="info-box success-box">
            ✅ {message}
        </div>
    """, unsafe_allow_html=True)

def render_warning_message(message: str):
    """Render warning message box"""
    st.markdown(f"""
        <div class="info-box warning-box">
            ⚠️ {message}
        </div>
    """, unsafe_allow_html=True)

def render_error_message(message: str, details: Optional[str] = None):
    """Render error message box with optional details"""
    st.markdown(f"""
        <div class="info-box error-box">
            ❌ {message}
        </div>
    """, unsafe_allow_html=True)
    
    if details and STREAMLIT_CONFIG.get("show_error_details", True):
        with st.expander("Chi tiết lỗi"):
            st.code(details)

def render_help_section():
    """Render help section in sidebar"""
    with st.sidebar:
        st.markdown("## 📖 Hướng dẫn sử dụng")
        
        st.markdown("""
        ### 📋 Yêu cầu file input:
        - Format: Excel (.xlsx)
        - Size: Tối đa 50MB
        - Headers: Product name + Article number
        
        ### 🔄 Quy trình xử lý:
        1. **Template**: Tạo template chuẩn 17 cột
        2. **Extract**: Trích xuất article data
        3. **Mapping**: Ánh xạ dữ liệu
        4. **Fill**: Điền dữ liệu vertical
        5. **Filter**: Lọc và deduplicate
        
        ### ⬇️ Output:
        - File Excel đã chuyển đổi
        - Format chuẩn TSS
        - Đã lọc và deduplicate
        """)
        
        st.markdown("### 🚨 Lưu ý:")
        st.warning("""
        - File sẽ bị xóa sau 30 phút
        - Chỉ xử lý 1 file tại 1 thời điểm
        - Kiểm tra format trước khi upload
        """)

def render_footer():
    """Render application footer"""
    st.markdown("""
        <div class="footer">
            <p>
                🛠️ TSS Converter v1.0 | 
                Powered by Streamlit | 
                Built with ❤️ for data processing
            </p>
        </div>
    """, unsafe_allow_html=True)

def create_two_column_layout() -> Tuple[Any, Any]:
    """Create two-column layout for main content"""
    return st.columns([2, 1])

def display_loading_spinner(message: str = "Đang xử lý..."):
    """Display loading spinner with message"""
    return st.spinner(message)

def clear_temp_files_button():
    """Render button to clear temporary files"""
    if st.button("🗑️ Clear Temp Files", help="Delete all temporary files"):
        try:
            temp_dir = Path("temp")
            if temp_dir.exists():
                import shutil
                shutil.rmtree(temp_dir)
                render_success_message("Temporary files have been cleared")
                st.rerun()
        except Exception as e:
            render_error_message(f"Unable to clear temp files: {str(e)}")