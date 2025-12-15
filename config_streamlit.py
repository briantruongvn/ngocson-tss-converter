"""
Streamlit-specific configuration for TSS Converter Web App
Provides UI settings, file handling limits, and app configuration.
"""

import os
from pathlib import Path
from typing import Dict, Any

# Streamlit App Configuration
STREAMLIT_CONFIG = {
    # App metadata
    "app_title": "TSS Converter - Excel Template Converter",
    "app_icon": "📊",
    "page_title": "TSS Converter",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
    
    # File upload settings
    "max_file_size_mb": 50,
    "allowed_file_types": [".xlsx"],
    "upload_directory": "temp/uploads",
    "output_directory": "temp/outputs",
    
    # UI settings
    "show_progress_bar": True,
    "show_step_details": False,  # Hide intermediate steps from user
    "auto_cleanup_temp_files": True,
    "session_timeout_minutes": 30,
    
    # Processing settings
    "enable_async_processing": True,
    "max_concurrent_uploads": 3,
    "processing_timeout_minutes": 10,
    
    # Display settings
    "theme": {
        "primary_color": "#FF6B6B",
        "background_color": "#FFFFFF",
        "secondary_background_color": "#F0F2F6",
        "text_color": "#262730",
        "font": "sans serif"
    },
    
    # Error handling
    "show_error_details": True,
    "log_user_actions": True,
    "enable_error_reporting": True
}

# CSS Styling for Streamlit
CUSTOM_CSS = """
<style>
    /* Global font unification */
    *, *::before, *::after,
    html, body, 
    [class*="css"], 
    .stApp,
    .stMarkdown,
    .stText,
    .stCaption,
    .stButton,
    .stSelectbox,
    .stFileUploader,
    .stExpander,
    .stMetric,
    .stProgress,
    div, span, p, h1, h2, h3, h4, h5, h6,
    button, input, textarea, select {
        font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif !important;
        -webkit-font-smoothing: antialiased !important;
        -moz-osx-font-smoothing: grayscale !important;
        font-feature-settings: normal !important;
        font-display: swap !important;
        text-rendering: optimizeLegibility !important;
    }
    
    /* Force consistent font rendering */
    .stApp * {
        font-family: inherit !important;
        text-shadow: none !important;
    }
    
    /* Hide any stray text or duplicate content */
    .stApp *::before,
    .stApp *::after {
        font-family: inherit !important;
    }
    
    /* Force clean text rendering for expanders */
    .stExpander, .stExpander * {
        text-shadow: none !important;
        -webkit-transform: translateZ(0) !important;
        transform: translateZ(0) !important;
        backface-visibility: hidden !important;
    }
    
    /* Fix text overlapping issues */
    .stButton > button {
        z-index: 1;
        position: relative;
    }
    
    .stExpander {
        z-index: 1;
        position: relative;
    }
    
    /* Ensure proper stacking context */
    .main .block-container {
        z-index: 1;
    }
    
    /* Main app styling */
    .main-header {
        text-align: center !important;
        color: #111827;
        margin-bottom: 0.75rem;
        padding: 0.75rem;
        background: transparent;
        width: 100% !important;
        display: block !important;
    }
    
    .main-header h1 {
        color: #111827;
        font-weight: 600;
        font-size: 1.875rem;
        margin-bottom: 0.125rem;
        letter-spacing: -0.025em;
        margin-top: 0;
        text-align: center !important;
        width: 100% !important;
    }
    
    .main-header p {
        color: #6b7280;
        font-weight: 400;
        font-size: 1rem;
        margin-top: 0;
        margin-bottom: 0;
        text-align: center !important;
        width: 100% !important;
    }
    
    /* Upload area styling - compact version */
    .upload-area-compact {
        border: 1px dashed #d1d5db;
        border-radius: 6px;
        padding: 0.75rem;
        text-align: center;
        margin: 0.5rem 0;
        background-color: #f9fafb;
        transition: all 0.15s ease;
    }
    
    /* Compact spacing for file uploader */
    .stFileUploader {
        margin-top: 0.5rem !important;
        margin-bottom: 0.5rem !important;
    }
    
    .upload-area-compact:hover {
        border-color: #9ca3af;
        background-color: #f3f4f6;
    }
    
    .upload-title {
        color: #374151 !important;
        font-weight: 600 !important;
        margin: 0 0 0.25rem 0 !important;
        font-size: 1.1rem !important;
    }
    
    .upload-subtitle {
        color: #6b7280 !important;
        font-weight: 400 !important;
        font-size: 0.9rem !important;
        margin: 0 !important;
    }
    
    /* Legacy upload area - keep for compatibility */
    .upload-area {
        border: 1px dashed #d1d5db;
        border-radius: 8px;
        padding: 0.1875rem;
        text-align: center;
        margin: 0.125rem 0 0.375rem 0;
        background-color: #f9fafb;
        transition: all 0.15s ease;
    }
    
    .upload-area:hover {
        border-color: #9ca3af;
        background-color: #f3f4f6;
    }
    
    .upload-area h3 {
        color: #374151;
        font-weight: 500;
        margin-bottom: 0.125rem;
        font-size: 1rem;
        margin-top: 0;
    }
    
    .upload-area p {
        color: #6b7280;
        font-weight: 400;
        font-size: 0.875rem;
        margin-top: 0;
        margin-bottom: 0;
    }
    
    /* Progress bar container - compact version */
    .progress-container-compact {
        margin: 0.5rem 0;
        padding: 0.75rem;
        background-color: #ffffff;
        border-radius: 4px;
        border: 1px solid #e5e7eb;
    }
    
    .progress-title {
        color: #111827 !important;
        font-weight: 600 !important;
        margin: 0 0 0.5rem 0 !important;
        font-size: 1.1rem !important;
    }
    
    /* Legacy progress container */
    .progress-container {
        margin: 1rem 0;
        padding: 1rem;
        background-color: #ffffff;
        border-radius: 6px;
        border: 1px solid #e5e7eb;
    }
    
    .progress-container h3 {
        color: #111827;
        font-weight: 500;
        margin-bottom: 0.5rem;
        font-size: 1rem;
    }
    
    /* Step indicators */
    .step-indicator {
        display: block;
        margin: 0.75rem 0;
        padding: 1rem;
        border-radius: 8px;
        transition: all 0.2s ease-in-out;
        font-weight: 500;
    }
    
    .step-completed {
        background-color: #f0f9f4;
        border: 1px solid #d1fae5;
        color: #065f46;
    }
    
    .step-running {
        background-color: #fffbeb;
        border: 1px solid #fed7aa;
        color: #92400e;
    }
    
    .step-pending {
        background-color: #f9fafb;
        border: 1px solid #e5e7eb;
        color: #6b7280;
    }
    
    .step-error {
        background-color: #fef2f2;
        border: 1px solid #fecaca;
        color: #991b1b;
    }
    
    /* Download section */
    .download-section {
        background-color: #f0f9f4;
        padding: 1.25rem;
        border-radius: 6px;
        margin-top: 1rem;
        text-align: center;
        border: 1px solid #d1fae5;
    }
    
    .download-section h3 {
        color: #065f46;
        font-weight: 500;
        font-size: 1rem;
        margin-bottom: 0.25rem;
    }
    
    .download-section p {
        color: #047857;
        font-weight: 400;
        font-size: 0.875rem;
        margin-top: 0;
    }
    
    /* Info boxes */
    .info-box {
        padding: 0.75rem 1rem;
        margin: 0.75rem 0;
        border-radius: 6px;
        border: 1px solid #e5e7eb;
        background-color: #f8fafc;
        color: #374151;
        font-weight: 400;
        font-size: 0.875rem;
    }
    
    .success-box {
        border-color: #d1fae5;
        background-color: #f0f9f4;
        color: #065f46;
    }
    
    .warning-box {
        border-color: #fed7aa;
        background-color: #fffbeb;
        color: #92400e;
    }
    
    .error-box {
        border-color: #fecaca;
        background-color: #fef2f2;
        color: #991b1b;
    }
    
    /* Hide Streamlit elements */
    .css-1dp5vir {
        background-color: transparent;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 1rem;
        color: #9ca3af;
        font-size: 0.75rem;
        font-weight: 400;
        margin-top: 1.5rem;
        border-top: 1px solid #e5e7eb;
    }
    
    /* Typography improvements */
    h1, h2, h3, h4, h5, h6 {
        color: #111827;
        font-weight: 600;
        line-height: 1.25;
    }
    
    p {
        color: #4b5563;
        line-height: 1.6;
    }
    
    /* Button styling */
    .stButton > button {
        font-weight: 500;
        border-radius: 6px;
        transition: all 0.15s ease;
        z-index: 10;
        position: relative;
        white-space: nowrap;
        overflow: visible;
        font-size: 0.875rem;
        padding: 0.5rem 1rem;
    }
    
    /* Primary button blue styling */
    .stButton > button[kind="primary"] {
        background-color: #2563eb !important;
        border-color: #2563eb !important;
        color: #ffffff !important;
    }
    
    .stButton > button[kind="primary"]:hover {
        background-color: #1d4ed8 !important;
        border-color: #1d4ed8 !important;
        color: #ffffff !important;
    }
    
    .stButton > button[kind="primary"]:focus {
        background-color: #2563eb !important;
        border-color: #2563eb !important;
        color: #ffffff !important;
        box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.2) !important;
    }
    
    /* Force white text for primary buttons */
    .stButton > button[kind="primary"] * {
        color: #ffffff !important;
    }
    
    .stButton > button[kind="primary"]:hover * {
        color: #ffffff !important;
    }
    
    /* Compact layout adjustments for better space utilization */
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 0.5rem !important;
        max-width: 100% !important;
    }
    
    /* Reduce default Streamlit spacing */
    .stMarkdown {
        margin-bottom: 0.5rem !important;
    }
    
    /* Standardize body text sizes */
    .stMarkdown p, .element-container p {
        font-size: 0.9rem !important;
        line-height: 1.5 !important;
    }
    
    /* File uploader text standardization */
    .stFileUploader label, .stFileUploader div {
        font-size: 0.9rem !important;
    }
    
    /* Button text standardization */
    .stButton button {
        font-size: 1rem !important;
        font-weight: 600 !important;
    }
    
    /* Progress text standardization */
    .stProgress div {
        font-size: 0.9rem !important;
    }
    
    /* Responsive optimizations */
    @media (max-width: 768px) {
        .app-header-container {
            max-width: 95% !important;
        }
        
        .compact-title {
            font-size: 2.1rem !important;
        }
        
        .compact-subtitle {
            font-size: 0.9rem !important;
        }
        
        .upload-title {
            font-size: 1rem !important;
        }
        
        .upload-subtitle {
            font-size: 0.85rem !important;
        }
        
        .progress-title {
            font-size: 1rem !important;
        }
        
        .upload-area-compact {
            padding: 0.5rem !important;
            margin: 0.25rem 0 !important;
        }
        
        .progress-container-compact {
            padding: 0.5rem !important;
            margin: 0.25rem 0 !important;
        }
    }
    
    /* Viewport height optimization */
    .main .block-container {
        min-height: auto !important;
    }
    
    .stMarkdown h2 {
        margin-top: 1rem;
        margin-bottom: 0.5rem;
        font-size: 1.25rem;
        font-weight: 600;
    }
    
    .stMarkdown h3 {
        margin-top: 2.25rem;
        margin-bottom: 0.5rem;
        font-size: 1.125rem;
        font-weight: 500;
    }
    
    /* Fix overlapping text in expanders */
    .streamlit-expanderHeader {
        z-index: 10 !important;
        position: relative !important;
        background: white !important;
        line-height: 1.5 !important;
        padding: 0.75rem 1rem !important;
        margin: 0 !important;
        display: block !important;
        width: 100% !important;
        overflow: hidden !important;
        transform: translateZ(0) !important;
        isolation: isolate !important;
    }
    
    /* Hide any pseudo-elements that might cause duplicate text */
    .streamlit-expanderHeader::before,
    .streamlit-expanderHeader::after {
        display: none !important;
        content: none !important;
    }
    
    /* Fix expander content spacing */
    .streamlit-expanderContent {
        background: white !important;
        padding: 0.5rem 1rem !important;
        z-index: 5 !important;
        margin-top: 0.25rem !important;
        clear: both !important;
    }
    
    /* Fix expander arrow and text */
    .streamlit-expanderHeader > div {
        display: flex !important;
        align-items: center !important;
        gap: 0.5rem !important;
    }
    
    /* Ensure expander text doesn't overlap */
    .stExpander > div > div > div {
        overflow: visible !important;
        white-space: normal !important;
        line-height: 1.5 !important;
    }
    
    /* Prevent font inheritance conflicts */
    .stMarkdown, .stText, .stCaption, .stButton, .stFileUploader, .stExpander {
        font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif !important;
        line-height: 1.6;
    }
    
    /* Override Streamlit default fonts */
    .stSelectbox > div > div, 
    .stFileUploader > div,
    .stButton > button,
    .stDownloadButton > button,
    .stExpander > div {
        font-family: inherit !important;
    }
    
    /* Fix general text overlapping */
    .stExpander label {
        display: block !important;
        line-height: 1.5 !important;
        padding: 0.5rem 0 !important;
        white-space: normal !important;
        font-size: 0.875rem !important;
        clear: both !important;
        overflow: visible !important;
    }
    
    .stExpander summary {
        line-height: 1.5 !important;
        white-space: normal !important;
        overflow: visible !important;
        clear: both !important;
    }
    
    /* Additional fix for specific expander classes */
    .stExpander [data-testid="stExpander"] {
        overflow: hidden !important;
        clear: both !important;
        background: white !important;
        isolation: isolate !important;
    }
    
    .stExpander [data-testid="stExpanderDetails"] {
        clear: both !important;
        margin-top: 0.5rem !important;
        overflow: hidden !important;
        background: white !important;
        isolation: isolate !important;
    }
    
    /* Nuclear option - hide any unwanted text nodes */
    .stExpander > div:not([data-testid]) {
        visibility: hidden !important;
        height: 0 !important;
        overflow: hidden !important;
    }
    
    /* Ensure only the correct expander content shows */
    .stExpander summary,
    .stExpander [data-testid="stExpanderDetails"] {
        visibility: visible !important;
        height: auto !important;
        overflow: visible !important;
    }
    
    /* Clean up any floating text */
    .stExpander::before,
    .stExpander::after,
    .stExpander *::before,
    .stExpander *::after {
        content: none !important;
        display: none !important;
    }
    
    /* Ultimate fix - target duplicate text specifically */
    .stExpander {
        contain: layout style paint !important;
    }
    
    /* Hide any text nodes that are not in proper containers */
    .stExpander > text,
    .stExpander > span:not([class]),
    .stExpander > div:empty {
        display: none !important;
        visibility: hidden !important;
    }
    
    /* Force correct stacking for expanders */
    .stExpander {
        transform: translateZ(0) !important;
        isolation: isolate !important;
        position: relative !important;
    }
    
    /* Override any Streamlit layout that might affect header */
    .stApp .main-header,
    .stApp .main-header h1,
    .stApp .main-header p {
        text-align: center !important;
        margin-left: auto !important;
        margin-right: auto !important;
        width: 100% !important;
    }
    
    /* Ensure header is not affected by column layouts */
    .main .block-container > div:first-child .main-header {
        text-align: center !important;
        width: 100% !important;
    }
    
    /* Nuclear option - target all possible Streamlit containers */
    div[data-testid="stMarkdownContainer"] .main-header,
    div[data-testid="stMarkdownContainer"] .main-header h1,
    div[data-testid="stMarkdownContainer"] .main-header p,
    .element-container .main-header,
    .element-container .main-header h1,
    .element-container .main-header p,
    .stMarkdown .main-header,
    .stMarkdown .main-header h1,
    .stMarkdown .main-header p {
        text-align: center !important;
        margin-left: auto !important;
        margin-right: auto !important;
        width: 100% !important;
        display: block !important;
    }
    
    /* Force center alignment on any div containing main-header */
    div:has(.main-header) {
        text-align: center !important;
        width: 100% !important;
    }
    
    /* Backup approach - center the parent container */
    .main-header {
        margin: 0 auto !important;
        max-width: 100% !important;
        position: relative !important;
        left: 50% !important;
        transform: translateX(-50%) !important;
    }
    
    /* Force center native Streamlit title and caption components */
    .stTitle,
    .stCaption,
    h1[data-testid="stHeader"],
    [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] .stCaption,
    div[data-testid="element-container"] h1,
    div[data-testid="element-container"] .stCaption,
    div[data-testid="stMarkdownContainer"] p,
    p[data-testid="stCaption"] {
        text-align: center !important;
        width: 100% !important;
        margin-left: auto !important;
        margin-right: auto !important;
    }
    
    /* Additional targeting for caption text */
    .stApp [data-testid="element-container"] p,
    .stApp div p:has-text("Convert Ngoc Son Internal TSS"),
    .stApp p:contains("Convert") {
        text-align: center !important;
        width: 100% !important;
        margin: 0 auto !important;
    }
    
    /* Enhanced centering for subtitle and caption */
    .stApp p[data-testid="stText"],
    .stApp div[data-testid="stMarkdownContainer"] p,
    .stApp .element-container p {
        text-align: center !important;
        margin: 0.5rem auto !important;
        display: block !important;
        width: 100% !important;
    }
    
    /* Make sure title and subtitle container is properly centered */
    .stApp .element-container:has(h1),
    .stApp .block-container > div:first-child {
        text-align: center !important;
        margin: 0 auto !important;
    }
    
    /* Compact header styling */
    .app-header-container {
        margin: 0.5rem auto !important;
        text-align: center !important;
    }
    
    .compact-title {
        font-size: 2.4rem !important;
        font-weight: 700 !important;
        color: #111827 !important;
        margin: 0.5rem 0 0.25rem 0 !important;
        text-align: center !important;
        line-height: 1.2 !important;
    }
    
    .compact-subtitle {
        font-size: 1rem !important;
        color: #6b7280 !important;
        margin: 0 0 0.5rem 0 !important;
        text-align: center !important;
        line-height: 1.4 !important;
    }
    
    /* Fix sidebar text overlap */
    .css-1d391kg {
        z-index: 1;
    }
    
    /* Hide GitHub icon and related elements */
    [data-testid="stToolbar"] {
        display: none !important;
        visibility: hidden !important;
    }
    
    /* Hide GitHub button specifically */
    button[title="View app source on GitHub"] {
        display: none !important;
        visibility: hidden !important;
    }
    
    /* Hide the entire toolbar area */
    .stToolbar {
        display: none !important;
    }
    
    /* Hide Share, Star, Edit buttons */
    [aria-label="Share"],
    [aria-label="Star"],
    [aria-label="Edit"],
    [title="Star"],
    [title="Share"],
    [title="Edit"] {
        display: none !important;
        visibility: hidden !important;
    }
    
    /* Hide Manage app section */
    [data-testid="manage-app-button"],
    .css-1kyxreq,
    .css-k1vhr4 {
        display: none !important;
        visibility: hidden !important;
    }
    
    /* Hide top toolbar completely */
    .css-1rs6os.edgvbvh3,
    .css-18e3th9,
    .css-1d391kg.e1fqkh3o3 {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        overflow: hidden !important;
    }
    
    /* Hide any GitHub related elements */
    [href*="github.com"],
    a[href*="github"] {
        display: none !important;
        visibility: hidden !important;
    }
    
    /* Generic toolbar hiding */
    header[data-testid="stToolbar"],
    .stToolbar,
    .toolbar {
        display: none !important;
        visibility: hidden !important;
    }
</style>

<script>
    // Function to hide elements dynamically
    function hideStreamlitElements() {
        // Hide toolbar elements
        const toolbarSelectors = [
            '[data-testid="stToolbar"]',
            'header[data-testid="stHeader"]',
            '.stToolbar',
            '[data-testid="stDecoration"]',
            '.css-1rs6os',
            '.css-18e3th9',
            '.css-1d391kg'
        ];
        
        toolbarSelectors.forEach(selector => {
            const elements = document.querySelectorAll(selector);
            elements.forEach(element => {
                element.style.display = 'none';
                element.style.visibility = 'hidden';
                element.style.height = '0';
                element.style.overflow = 'hidden';
            });
        });
        
        // Hide specific buttons by text content
        const buttons = document.querySelectorAll('button');
        buttons.forEach(button => {
            const buttonText = button.textContent.toLowerCase();
            if (buttonText.includes('share') || 
                buttonText.includes('star') || 
                buttonText.includes('edit') ||
                buttonText.includes('manage app') ||
                button.getAttribute('title')?.includes('GitHub')) {
                button.style.display = 'none';
                button.style.visibility = 'hidden';
            }
        });
        
        // Hide GitHub links
        const links = document.querySelectorAll('a[href*="github"]');
        links.forEach(link => {
            link.style.display = 'none';
            link.style.visibility = 'hidden';
        });
        
        // Hide manage app section
        const manageButtons = document.querySelectorAll('[data-testid="manage-app-button"], .css-1kyxreq, .css-k1vhr4');
        manageButtons.forEach(button => {
            button.style.display = 'none';
            button.style.visibility = 'hidden';
        });
        
        // Hide entire header if it contains unwanted elements
        const headers = document.querySelectorAll('header');
        headers.forEach(header => {
            if (header.querySelector('[title*="GitHub"]') || 
                header.textContent.includes('Share') ||
                header.textContent.includes('Star')) {
                header.style.display = 'none';
                header.style.visibility = 'hidden';
            }
        });
    }
    
    // Run immediately and on DOM changes
    hideStreamlitElements();
    
    // Use MutationObserver to hide elements as they're added
    const observer = new MutationObserver(function(mutations) {
        hideStreamlitElements();
    });
    
    // Start observing
    observer.observe(document.body, {
        childList: true,
        subtree: true,
        attributes: true
    });
    
    // Also run on page load and window events
    document.addEventListener('DOMContentLoaded', hideStreamlitElements);
    window.addEventListener('load', hideStreamlitElements);
    
    // Run periodically as backup
    setInterval(hideStreamlitElements, 1000);
    
    // Function to force center the header
    function centerHeader() {
        const headers = document.querySelectorAll('.main-header, .main-header h1, .main-header p');
        headers.forEach(header => {
            header.style.textAlign = 'center';
            header.style.marginLeft = 'auto';
            header.style.marginRight = 'auto';
            header.style.width = '100%';
            header.style.display = 'block';
        });
        
        // Center Streamlit title and caption
        const streamlitHeaders = document.querySelectorAll('h1, .stCaption, [data-testid="stMarkdownContainer"] p, p, .element-container p');
        streamlitHeaders.forEach(header => {
            if (header.textContent.includes('Ngoc Son') || header.textContent.includes('Convert Ngoc Son') || header.textContent.includes('Convert')) {
                header.style.textAlign = 'center';
                header.style.marginLeft = 'auto';
                header.style.marginRight = 'auto';
                header.style.width = '100%';
                header.style.display = 'block';
            }
        });
        
        // Force center all paragraph elements in header section
        const allParagraphs = document.querySelectorAll('p');
        allParagraphs.forEach(p => {
            if (p.textContent.includes('Convert') && p.textContent.includes('TSS')) {
                p.style.textAlign = 'center';
                p.style.margin = '0 auto';
                p.style.width = '100%';
                p.style.display = 'block';
            }
        });
        
        // Also center parent containers
        const headerContainers = document.querySelectorAll('div:has(.main-header)');
        headerContainers.forEach(container => {
            container.style.textAlign = 'center';
            container.style.width = '100%';
        });
    }
    
    // Run header centering function
    centerHeader();
    setTimeout(centerHeader, 100);
    setTimeout(centerHeader, 500);
    setTimeout(centerHeader, 1000);
    
    // Add to the existing observer
    const headerObserver = new MutationObserver(function(mutations) {
        centerHeader();
    });
    
    headerObserver.observe(document.body, {
        childList: true,
        subtree: true,
        attributes: true
    });
    
    // Run on load events
    document.addEventListener('DOMContentLoaded', centerHeader);
    window.addEventListener('load', centerHeader);
    
    // Run periodically
    setInterval(centerHeader, 500);
</script>
"""

# Step configuration for UI display
STEP_CONFIG = {
    "step1": {
        "name": "Create Template",
        "description": "Create standard template with 17 column headers",
        "icon": "📋",
        "estimated_time": "2-5 seconds"
    },
    "step2": {
        "name": "Extract Data", 
        "description": "Extract article names and numbers",
        "icon": "🔍",
        "estimated_time": "10-30 seconds"
    },
    "step3": {
        "name": "Map Data",
        "description": "Map data according to business logic",
        "icon": "🗂️",
        "estimated_time": "15-45 seconds"
    },
    "step4": {
        "name": "Fill Data",
        "description": "Fill data using vertical inheritance",
        "icon": "📝",
        "estimated_time": "5-15 seconds"
    },
    "step5": {
        "name": "Filter & Deduplicate",
        "description": "Filter NA values and remove duplicates",
        "icon": "🎯",
        "estimated_time": "10-20 seconds"
    }
}

def get_temp_directory(subdir: str = "") -> Path:
    """Get temporary directory path for file operations"""
    base_temp = Path("temp")
    if subdir:
        temp_dir = base_temp / subdir
    else:
        temp_dir = base_temp
    
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir

def get_streamlit_config() -> Dict[str, Any]:
    """Get complete Streamlit configuration"""
    return STREAMLIT_CONFIG

def get_custom_css() -> str:
    """Get custom CSS for Streamlit app styling"""
    return CUSTOM_CSS

def get_step_config() -> Dict[str, Dict[str, str]]:
    """Get step configuration for UI display"""
    return STEP_CONFIG

# Environment-specific overrides
if os.getenv("STREAMLIT_ENV") == "production":
    STREAMLIT_CONFIG.update({
        "show_error_details": False,
        "log_user_actions": True,
        "max_file_size_mb": 100,
        "processing_timeout_minutes": 15
    })
elif os.getenv("STREAMLIT_ENV") == "development":
    STREAMLIT_CONFIG.update({
        "show_error_details": True,
        "log_user_actions": True,
        "auto_cleanup_temp_files": False  # Keep files for debugging
    })