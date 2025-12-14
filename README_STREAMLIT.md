# TSS Converter Streamlit Web App

## 📊 Tổng quan
Web application Streamlit cho TSS Converter - chuyển đổi Excel files từ format tùy ý sang template chuẩn TSS (Technical Specification System) với giao diện web user-friendly.

## 🌟 Tính năng chính
- **Upload file Excel**: Giao diện kéo thả đơn giản
- **Progress tracking**: Theo dõi tiến trình 5 bước real-time
- **Download kết quả**: Chỉ hiển thị file Step 5 cuối cùng
- **Error handling**: Xử lý lỗi và validation toàn diện
- **Responsive UI**: Giao diện thân thiện, hiện đại
- **Session management**: Quản lý files tạm thời tự động

## 🏗️ Cấu trúc Files

### Core Files
```
├── app.py                     # Main Streamlit application
├── streamlit_pipeline.py      # Pipeline integration wrapper  
├── ui_components.py          # Reusable UI components
├── config_streamlit.py       # Streamlit configuration
├── requirements.txt          # Dependencies
└── temp/                     # Temporary file storage
    ├── uploads/
    └── outputs/
```

### Existing Files (Unchanged)
```
├── step1_template_creation.py
├── step2_data_extraction.py
├── step3_data_mapping.py
├── step4_data_fill.py
├── step5_filter_deduplicate.py
└── common/
    ├── config.py
    ├── exceptions.py
    └── validation.py
```

## 🚀 Hướng dẫn chạy

### 1. Cài đặt Dependencies
```bash
pip install -r requirements.txt
```

### 2. Chạy Web App
```bash
streamlit run app.py
```

### 3. Truy cập Web App
- Local: http://localhost:8501
- Network: http://[YOUR_IP]:8501

## 📋 Hướng dẫn sử dụng

### Upload File
1. Click vào upload area
2. Chọn file Excel (.xlsx) 
3. File tối đa 50MB
4. Yêu cầu có headers: Product name + Article number

### Xử lý Pipeline
1. Click "🚀 Bắt đầu chuyển đổi"
2. Theo dõi progress bar 5 steps:
   - Step 1: Tạo Template (17 cột chuẩn)
   - Step 2: Trích xuất dữ liệu
   - Step 3: Mapping dữ liệu  
   - Step 4: Fill dữ liệu vertical
   - Step 5: Lọc & deduplicate

### Download Kết quả
1. Sau khi hoàn thành, click "📥 Download File Đã Chuyển Đổi"
2. File Excel format TSS chuẩn sẽ được download

### Reset & Làm mới
- "🔄 Xử lý file mới": Reset session, xử lý file khác
- "🗑️ Xóa files tạm": Clean up temporary files

## ⚙️ Configuration

### File Limits
- Max file size: 50MB (configurable)
- Supported formats: .xlsx only
- Session timeout: 30 minutes

### UI Customization
Edit `config_streamlit.py`:
```python
STREAMLIT_CONFIG = {
    "max_file_size_mb": 50,
    "theme": {
        "primary_color": "#FF6B6B",
        # ... other theme settings
    }
}
```

### Error Handling
- Development mode: Show detailed errors
- Production mode: User-friendly messages only

## 🚨 Troubleshooting

### Common Issues

1. **Import Errors**
```bash
ModuleNotFoundError: No module named 'streamlit'
```
**Solution**: `pip install streamlit`

2. **File Upload Fails**
- Check file format (.xlsx only)
- Check file size (< 50MB)
- Ensure file has required headers

3. **Processing Timeout**
- Large files may take longer
- Check file structure (avoid 16k+ columns)
- Monitor temp directory space

4. **Permission Errors**
```bash
PermissionError: [Errno 13] Permission denied
```
**Solution**: Check write permissions for `temp/` directory

### Debug Mode
```bash
STREAMLIT_ENV=development streamlit run app.py
```

## 🌐 Deployment

### Local Development
```bash
streamlit run app.py --server.port 8501
```

### Production Deployment

#### Option 1: Streamlit Cloud
1. Push code to GitHub
2. Connect to Streamlit Cloud
3. Deploy from repository

#### Option 2: Docker
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

#### Option 3: Self-hosted Server
```bash
# Install dependencies
pip install -r requirements.txt

# Run with custom config
streamlit run app.py \\
  --server.port 8501 \\
  --server.address 0.0.0.0 \\
  --server.headless true
```

### Environment Variables
```bash
export STREAMLIT_ENV=production
export TSCONVERTER_LOG_LEVEL=INFO
export TSCONVERTER_MAX_FILE_SIZE=100
```

## 📊 Performance

### Optimization Tips
1. **File Processing**: Large files processed in background threads
2. **Memory Management**: Automatic cleanup of temp files
3. **Session State**: Efficient state management
4. **Error Recovery**: Robust error handling and recovery

### Monitoring
- Check `temp/` directory size regularly
- Monitor processing times for large files
- Watch memory usage during concurrent uploads

## 🔒 Security

### File Validation
- Strict file format checking (.xlsx only)
- File size limits
- Content structure validation
- No executable file uploads

### Data Protection
- Temporary files auto-deleted
- No persistent storage of user data
- Session-based file isolation

## 📞 Support

### Development
- Check logs in terminal running Streamlit
- Use debug mode for detailed error info
- Monitor `temp/` directory

### Production Issues
1. Check server logs
2. Verify file permissions
3. Monitor resource usage
4. Review error reporting

---

**Note**: Web app giữ nguyên 100% functionality của CLI version, chỉ thêm giao diện web user-friendly và file management tự động.