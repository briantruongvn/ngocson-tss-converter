# TSS Converter Streamlit Web App

## 📊 Tổng quan
Web application Streamlit cho TSS Converter - chuyển đổi Excel files từ format tùy ý sang template chuẩn TSS (Technical Specification System) với giao diện web user-friendly, real-time progress tracking và comprehensive security features.

## 🌟 Tính năng chính
- **📤 File Upload**: Drag & drop interface với validation (max 50MB)
- **📈 Progress Tracking**: Real-time progress với estimated time cho từng step
- **🔒 Security**: File validation, session management và secure processing
- **📥 Smart Download**: Custom filename format với original name preservation
- **🎯 Error Handling**: Comprehensive error handling với user-friendly messages
- **📱 Responsive UI**: Modern design optimized cho desktop và mobile
- **🧹 Session Management**: Auto-cleanup temporary files và session isolation

## 🏗️ Architecture & Components

### Core Application Files
```
Web Interface/
├── app.py                    # 🚀 Main Streamlit application
│   ├── File upload handling
│   ├── Session state management
│   ├── Progress tracking coordination
│   └── Download file generation
│
├── ui_components.py          # 🎨 Reusable UI components
│   ├── File upload area với validation
│   ├── Progress indicators với estimated time
│   ├── Download section với custom naming
│   ├── Error/success message system
│   └── Help và footer sections
│
├── config_streamlit.py       # ⚙️ Configuration management
│   ├── App settings và limits
│   ├── Step configurations
│   ├── CSS styling definitions
│   └── Security parameters
│
└── streamlit_pipeline.py     # 🔧 Pipeline integration
    ├── Streamlit wrapper cho existing pipeline
    ├── Session-based file management
    ├── Progress callback system
    └── Error handling và validation
```

### Backend Integration
```
Backend Pipeline/
├── step1_template_creation.py    # Template generation
├── step2_data_extraction.py      # Article data extraction
├── step3_pre_mapping_fill.py     # Pre-mapping data fill
├── step4_data_mapping.py         # Data mapping logic
├── step5_filter_deduplicate.py   # Filter và deduplicate
└── common/                       # Shared utilities
    ├── config.py                 # Configuration utilities
    ├── exceptions.py             # Custom exceptions
    ├── validation.py             # File validation
    ├── security.py               # Security utilities
    └── session_manager.py        # Session management
```

## 🚀 Quick Start

### Prerequisites
- **Python 3.8+** (specified in runtime.txt)
- **Dependencies**: Install từ requirements.txt

### Installation & Setup
```bash
# 1. Clone repository
git clone <repository-url>
cd ngocson-tss-converter

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run Streamlit app
streamlit run app.py

# 4. Access application
# Browser sẽ tự động mở http://localhost:8501
```

### Basic Usage
1. **📤 Upload File**: Drag & drop .xlsx file vào upload area
2. **✅ Validation**: System sẽ validate file format và size
3. **🚀 Process**: Click "Start Conversion" để bắt đầu processing
4. **📊 Monitor**: Watch real-time progress với estimated time
5. **📥 Download**: Download converted file với custom filename

## 🔧 Configuration

### Streamlit Configuration (`config_streamlit.py`)
```python
STREAMLIT_CONFIG = {
    # App Settings
    "app_title": "TSS Converter - Excel Template Converter",
    "page_title": "TSS Converter",
    "layout": "wide",
    
    # File Upload Settings
    "max_file_size_mb": 50,
    "allowed_file_types": [".xlsx"],
    
    # Security Settings
    "security_mode": "lenient",  # "strict" or "lenient"
    "enable_fallback_validation": True,
    "session_timeout_hours": 24,
    
    # UI Settings
    "show_error_details": True,
    "enable_progress_animation": True,
    "compact_progress_mode": True
}
```

### Step Configuration
```python
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
        "name": "Pre-mapping Fill",
        "description": "Fill data using vertical inheritance",
        "icon": "📝", 
        "estimated_time": "5-15 seconds"
    },
    "step4": {
        "name": "Data Mapping",
        "description": "Map data according to business logic",
        "icon": "🗂️",
        "estimated_time": "15-45 seconds"
    },
    "step5": {
        "name": "Filter & Deduplicate",
        "description": "Filter NA values and remove duplicates", 
        "icon": "🎯",
        "estimated_time": "10-20 seconds"
    }
}
```

## 🔒 Security Features

### File Upload Security
- **Format Validation**: Strict .xlsx only với MIME type checking
- **Size Limits**: 50MB maximum với configurable limits
- **Content Scanning**: Basic malware signature detection
- **Path Sanitization**: Secure file path handling
- **Session Isolation**: Files isolated per session

### Session Management
```python
# Session Security Features
- Cryptographically secure session IDs
- Temporary file isolation (temp/session_<id>/)
- Auto-cleanup after 24 hours
- Secure file permissions (0o600)
- Session state protection
```

### Error Handling
- **Graceful Degradation**: Fallback validation khi strict mode fails
- **User-Friendly Messages**: Clear error descriptions without technical details
- **Debug Information**: Detailed logging for troubleshooting
- **Security Logging**: Track suspicious activities

## 🎨 UI/UX Features

### Modern Design
- **Clean Interface**: Minimalist design với focus on functionality
- **Responsive Layout**: Works on desktop, tablet và mobile
- **Progress Visualization**: Visual indicators với estimated completion time
- **Custom Styling**: Consistent font và color scheme

### User Experience
```python
# UX Enhancements
✅ Drag & drop file upload
✅ Real-time progress tracking
✅ Estimated time display
✅ Step-by-step indicators
✅ Success/error notifications
✅ Download with custom filenames
✅ Help section với instructions
✅ Automatic session cleanup
```

## 📁 File Management

### Upload Process
1. **File Selection**: Drag & drop hoặc click to browse
2. **Validation**: Format, size và content validation
3. **Session Creation**: Generate unique session ID
4. **Secure Storage**: Store in session-specific directory
5. **Processing Ready**: File ready cho pipeline processing

### Processing Workflow
```
Upload → Validate → Session → Process → Download → Cleanup
   ↓        ↓         ↓        ↓        ↓        ↓
 temp/   security   unique   5-step   custom   auto-
 file    checks     session  pipeline filename delete
```

### Download Features
- **Custom Naming**: `{original_name}_Converted_YYYYMMDD.xlsx`
- **Secure Access**: Session-based download links
- **Auto-Cleanup**: Files deleted after session timeout
- **Error Recovery**: Graceful handling của download failures

## 📊 Performance & Monitoring

### Performance Metrics
- **Upload Speed**: Dependent on file size và network
- **Processing Time**: 30 seconds - 2 minutes (based on file complexity)
- **Memory Usage**: ~100-500MB during processing
- **Session Overhead**: ~10-50MB per active session

### Monitoring Features
```python
# Built-in Monitoring
📈 Processing time tracking
📊 File size và row count metrics  
🔍 Error categorization và reporting
📝 Session activity logging
🧹 Cleanup operation tracking
```

## 🛠️ Development Guide

### Local Development Setup
```bash
# Development environment setup
pip install -r requirements.txt

# Run với hot reload
streamlit run app.py --logger.level debug

# Run với custom port
streamlit run app.py --server.port 8502

# Run với specific config
STREAMLIT_CONFIG_FILE=config.toml streamlit run app.py
```

### Custom Configuration
```python
# Environment Variables
STREAMLIT_MAX_FILE_SIZE=52428800    # 50MB in bytes
STREAMLIT_SESSION_TIMEOUT=86400     # 24 hours in seconds
STREAMLIT_SECURITY_MODE=strict      # strict or lenient
STREAMLIT_DEBUG_MODE=false          # Enable debug features
```

### Testing Interface
```bash
# Test upload functionality
python -c "
from streamlit_pipeline import StreamlitTSSPipeline
pipeline = StreamlitTSSPipeline()
print('Pipeline initialized successfully')
"

# Test file validation
python -c "
from common.validation import validate_step1_input
validate_step1_input('input/test-1.xlsx')
print('Validation passed')
"
```

## 🔍 Troubleshooting

### Common Issues

#### Upload Problems
```
❌ File too large (>50MB)
→ Solution: Reduce file size hoặc increase limit trong config

❌ Invalid file format
→ Solution: Save file as Excel Workbook (.xlsx)

❌ Upload stuck/timeout
→ Solution: Check network connection, refresh page
```

#### Processing Errors
```
❌ Processing failed at step X
→ Solution: Check file content, ensure required headers exist

❌ Session expired
→ Solution: Refresh page và re-upload file

❌ Download not working
→ Solution: Check browser settings, disable popup blockers
```

### Debug Mode
```python
# Enable debug logging trong config_streamlit.py
STREAMLIT_CONFIG = {
    "debug_mode": True,
    "show_error_details": True,
    "enable_enhanced_logging": True
}
```

### Performance Optimization
- **Large Files**: Consider splitting files > 30MB
- **Slow Processing**: Check available memory và CPU
- **Session Issues**: Clear browser cache và cookies
- **Network Problems**: Use wired connection for large uploads

## 🎯 Production Deployment

### Environment Setup
```bash
# Production configuration
export STREAMLIT_SECURITY_MODE=strict
export STREAMLIT_SESSION_TIMEOUT=43200  # 12 hours
export STREAMLIT_MAX_FILE_SIZE=52428800  # 50MB
export STREAMLIT_DEBUG_MODE=false

# Run với production settings
streamlit run app.py --server.port 8501 --server.headless true
```

### Docker Deployment (Optional)
```dockerfile
FROM python:3.8-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port", "8501", "--server.headless", "true"]
```

### Nginx Configuration (Optional)
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 📈 Monitoring & Analytics

### Built-in Metrics
- **Session Count**: Active và total sessions
- **Processing Time**: Average time per step
- **Error Rates**: Success/failure ratios
- **File Statistics**: Size distribution, format compliance

### Log Analysis
```bash
# Check processing logs
tail -f app.log | grep "PROCESSING"

# Monitor session activity
tail -f app.log | grep "SESSION"

# Track errors
tail -f app.log | grep "ERROR"
```

## 📚 Additional Resources

### Documentation Links
- **Main Documentation**: [CLAUDE.md](CLAUDE.md)
- **Input Requirements**: [YEU_CAU_FILE_INPUT.md](YEU_CAU_FILE_INPUT.md) 
- **Security Details**: [SECURITY_FIXES_SUMMARY.md](SECURITY_FIXES_SUMMARY.md)
- **Quick Start**: [START_WEBAPP.md](START_WEBAPP.md)

### Support & Maintenance
- **Issue Tracking**: Check logs trong temp/ directory
- **Performance Monitoring**: Monitor memory và disk usage
- **Session Cleanup**: Automatic cleanup runs every hour
- **Security Updates**: Regular review của validation rules

---

**Version**: 2.0  
**Last Updated**: January 2026  
**Streamlit Version**: 1.28.0+  
**Python Support**: 3.8+  
**License**: Internal Use - Ngoc Son Company