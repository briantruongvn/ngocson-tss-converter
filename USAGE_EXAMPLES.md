# TSS Converter - Usage Examples & Implementation Guide

## 📚 Tổng quan

Document này cung cấp comprehensive usage examples cho TSS Converter System, bao gồm command line usage, Streamlit web interface, programmatic integration, và advanced configuration scenarios.

## 🖥️ Command Line Usage

### Basic Single-Step Processing

#### Step 1: Template Creation
```bash
# Basic template creation
python step1_template_creation.py input.xlsx

# With verbose logging
python step1_template_creation.py input.xlsx -v

# Custom output directory
python step1_template_creation.py input.xlsx -o custom_output/

# Multiple files
python step1_template_creation.py input1.xlsx input2.xlsx input3.xlsx
```

#### Step 2: Data Extraction
```bash
# Extract article data from source
python step2_data_extraction.py output/input-Step1.xlsx -s source_data.xlsx

# Custom source file
python step2_data_extraction.py template.xlsx -s product_catalog.xlsx

# Verbose extraction with debugging
python step2_data_extraction.py template.xlsx -s data.xlsx -v
```

#### Step 3: Pre-mapping Fill
```bash
# Apply vertical inheritance filling
python step3_pre_mapping_fill.py output/input-Step2.xlsx

# With detailed logging
python step3_pre_mapping_fill.py extracted_data.xlsx -v
```

#### Step 4: Data Mapping
```bash
# Business logic mapping
python step4_data_mapping.py source.xlsx filled_data.xlsx

# Force specific mapping rules
python step4_data_mapping.py source.xlsx data.xlsx --force-mapping
```

#### Step 5: Filter & Deduplicate
```bash
# Final filtering and deduplication
python step5_filter_deduplicate.py output/input-Step4.xlsx

# Custom NA values
python step5_filter_deduplicate.py final_data.xlsx --na-values "NA,N/A,-,TBD"
```

### Complete Pipeline Examples

#### Sequential Processing
```bash
#!/bin/bash
# Complete 5-step pipeline script

# Input file
INPUT="product_data.xlsx"
BASE_NAME=$(basename "$INPUT" .xlsx)

echo "🚀 Starting TSS Converter Pipeline for $INPUT"

# Step 1: Create Template
echo "📋 Step 1: Creating Template..."
python step1_template_creation.py "$INPUT" -v
STEP1_OUTPUT="output/${BASE_NAME}-Step1.xlsx"

# Step 2: Extract Data
echo "🔍 Step 2: Extracting Data..."
python step2_data_extraction.py "$STEP1_OUTPUT" -s "$INPUT" -v
STEP2_OUTPUT="output/${BASE_NAME}-Step2.xlsx"

# Step 3: Pre-mapping Fill
echo "📝 Step 3: Pre-mapping Fill..."
python step3_pre_mapping_fill.py "$STEP2_OUTPUT" -v
STEP3_OUTPUT="output/${BASE_NAME}-Step3.xlsx"

# Step 4: Data Mapping
echo "🗂️ Step 4: Data Mapping..."
python step4_data_mapping.py "$INPUT" "$STEP3_OUTPUT" -v
STEP4_OUTPUT="output/${BASE_NAME}-Step4.xlsx"

# Step 5: Filter & Deduplicate
echo "🎯 Step 5: Filter & Deduplicate..."
python step5_filter_deduplicate.py "$STEP4_OUTPUT" -v
FINAL_OUTPUT="output/${BASE_NAME}-Step5.xlsx"

echo "✅ Pipeline completed! Final output: $FINAL_OUTPUT"
```

#### Batch Processing Script
```bash
#!/bin/bash
# Batch process multiple files

for file in input/*.xlsx; do
    echo "Processing: $file"
    
    # Run complete pipeline
    python step1_template_creation.py "$file" -v
    
    base_name=$(basename "$file" .xlsx)
    step1_out="output/${base_name}-Step1.xlsx"
    
    if [ -f "$step1_out" ]; then
        python step2_data_extraction.py "$step1_out" -s "$file" -v
        step2_out="output/${base_name}-Step2.xlsx"
        
        python step3_pre_mapping_fill.py "$step2_out" -v
        step3_out="output/${base_name}-Step3.xlsx"
        
        python step4_data_mapping.py "$file" "$step3_out" -v
        step4_out="output/${base_name}-Step4.xlsx"
        
        python step5_filter_deduplicate.py "$step4_out" -v
        
        echo "✅ Completed: $file"
    else
        echo "❌ Failed: $file"
    fi
done
```

### Advanced Command Line Options

#### Configuration Examples
```bash
# Set environment variables
export TSCONVERTER_LOG_LEVEL="DEBUG"
export TSCONVERTER_OUTPUT_DIR="/custom/output/path"
export TSCONVERTER_TEMP_DIR="/tmp/tss_converter"

# Run with custom config
python step1_template_creation.py input.xlsx --config custom_config.json

# Override specific settings
python step2_data_extraction.py template.xlsx -s data.xlsx \
  --name-headers "Product Name,Item Name" \
  --number-headers "SKU,Barcode"

# Performance tuning
python step4_data_mapping.py source.xlsx data.xlsx \
  --max-workers 8 \
  --chunk-size 1000 \
  --memory-limit 2GB
```

#### Debugging and Troubleshooting
```bash
# Maximum verbosity with debug info
python step1_template_creation.py problem_file.xlsx -vvv

# Validation-only mode
python -c "
from common.validation import validate_step1_input
try:
    validate_step1_input('input.xlsx')
    print('✅ File validation passed')
except Exception as e:
    print(f'❌ Validation failed: {e}')
"

# Check pipeline health
python -c "
from step1_template_creation import TemplateCreator
from common.config import init_config

config = init_config()
creator = TemplateCreator(config)
print('Pipeline initialized successfully')
"
```

## 🌐 Streamlit Web Interface

### Basic Web Usage

#### Starting the Application
```bash
# Start Streamlit app
streamlit run app.py

# Custom port and configuration
streamlit run app.py --server.port 8502 --server.headless true

# Development mode with debug
STREAMLIT_ENV=development streamlit run app.py --logger.level debug

# Production deployment
STREAMLIT_ENV=production streamlit run app.py \
  --server.port 8501 \
  --server.headless true \
  --server.maxUploadSize 100
```

#### Web Interface Workflow
```
1. 📤 Upload File
   ↓
   [Drag & drop .xlsx file or click browse]
   ↓
   [File validation: format, size, structure]
   
2. ✅ Validation Success
   ↓
   [Display file info: name, size, worksheets]
   ↓
   [Show "Start Conversion" button]
   
3. 🚀 Processing
   ↓
   [Real-time progress tracking]
   ↓
   [Step-by-step indicators with estimated times]
   
4. 📥 Download
   ↓
   [Custom filename: {original}_Converted_YYYYMMDD.xlsx]
   ↓
   [Automatic session cleanup]
```

### Advanced Web Configuration

#### Custom Configuration File
```python
# config_streamlit.py modifications
STREAMLIT_CONFIG.update({
    "max_file_size_mb": 100,  # Increase limit
    "processing_timeout_minutes": 15,  # Longer timeout
    "security_mode": "strict",  # Enhanced security
    "enable_enhanced_logging": True,  # Detailed logs
    "auto_cleanup_temp_files": True,  # Auto cleanup
})

# Custom step configuration
STEP_CONFIG["step4"]["estimated_time"] = "30-60 seconds"  # Update estimates
```

#### Environment-Specific Setup
```bash
# Development environment
export STREAMLIT_ENV=development
export STREAMLIT_DEBUG_MODE=true
export STREAMLIT_SHOW_ERROR_DETAILS=true

# Production environment  
export STREAMLIT_ENV=production
export STREAMLIT_SECURITY_MODE=strict
export STREAMLIT_SESSION_TIMEOUT=43200  # 12 hours
export STREAMLIT_MAX_FILE_SIZE=104857600  # 100MB
```

## 🔧 Programmatic Integration

### Python API Usage

#### Basic Integration
```python
from step1_template_creation import TemplateCreator
from step2_data_extraction import DataExtractor
from step3_pre_mapping_fill import PreMappingFiller
from step4_data_mapping import DataMapper
from step5_filter_deduplicate import FilterDeduplicator
from common.config import init_config
from common.exceptions import TSConverterError

# Initialize configuration
config = init_config("tsconverter.json")

def process_file(input_file: str) -> str:
    """Complete TSS conversion pipeline"""
    try:
        # Step 1: Create Template
        template_creator = TemplateCreator(config)
        step1_output = template_creator.create_template(input_file)
        print(f"Step 1 completed: {step1_output}")
        
        # Step 2: Extract Data
        data_extractor = DataExtractor(config)
        step2_output = data_extractor.extract_data(step1_output, input_file)
        print(f"Step 2 completed: {step2_output}")
        
        # Step 3: Pre-mapping Fill
        pre_mapper = PreMappingFiller(config)
        step3_output = pre_mapper.fill_data(step2_output)
        print(f"Step 3 completed: {step3_output}")
        
        # Step 4: Data Mapping
        data_mapper = DataMapper(config)
        step4_output = data_mapper.map_data(input_file, step3_output)
        print(f"Step 4 completed: {step4_output}")
        
        # Step 5: Filter & Deduplicate
        filter_dedup = FilterDeduplicator(config)
        final_output = filter_dedup.process(step4_output)
        print(f"Final output: {final_output}")
        
        return final_output
        
    except TSConverterError as e:
        print(f"TSS Converter Error: {e}")
        print(f"Error Context: {e.context}")
        raise
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise

# Usage
if __name__ == "__main__":
    result = process_file("input/product_data.xlsx")
    print(f"Processing completed: {result}")
```

#### Advanced Integration with Error Handling
```python
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from streamlit_pipeline import StreamlitTSSPipeline
from common.exceptions import (
    FileFormatError, ValidationError, ProcessingError,
    TSConverterError
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TSSConverterService:
    """High-level service for TSS conversion with robust error handling"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.pipeline = StreamlitTSSPipeline(config_file)
        self.session_id = None
        
    def process_file(self, file_path: str, 
                    progress_callback: Optional[callable] = None) -> Dict[str, Any]:
        """
        Process file with comprehensive error handling and progress tracking
        
        Args:
            file_path: Path to input file
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary with processing results
        """
        start_time = datetime.now()
        result = {
            "success": False,
            "output_file": None,
            "processing_time": None,
            "error": None,
            "steps_completed": 0,
            "session_id": None
        }
        
        try:
            # Initialize session
            self.session_id = self.pipeline.initialize_session()
            result["session_id"] = self.session_id
            
            logger.info(f"Starting processing for {file_path}")
            
            # Process with progress tracking
            def internal_callback(step: int, total: int, message: str):
                result["steps_completed"] = step
                logger.info(f"Step {step}/{total}: {message}")
                if progress_callback:
                    progress_callback(step, total, message)
            
            output_file = self.pipeline.process_file(
                file_path, 
                progress_callback=internal_callback
            )
            
            # Success
            result.update({
                "success": True,
                "output_file": output_file,
                "processing_time": (datetime.now() - start_time).total_seconds(),
                "steps_completed": 5
            })
            
            logger.info(f"Processing completed successfully: {output_file}")
            
        except FileFormatError as e:
            result["error"] = {
                "type": "FILE_FORMAT_ERROR",
                "message": "Invalid file format",
                "details": str(e),
                "suggestion": "Please save file as Excel Workbook (.xlsx)"
            }
            logger.error(f"File format error: {e}")
            
        except ValidationError as e:
            result["error"] = {
                "type": "VALIDATION_ERROR", 
                "message": "File validation failed",
                "details": str(e),
                "suggestion": "Check file structure and required headers"
            }
            logger.error(f"Validation error: {e}")
            
        except ProcessingError as e:
            result["error"] = {
                "type": "PROCESSING_ERROR",
                "message": "Processing failed",
                "details": str(e),
                "suggestion": "Check file content and try again"
            }
            logger.error(f"Processing error: {e}")
            
        except TSConverterError as e:
            result["error"] = {
                "type": "CONVERTER_ERROR",
                "message": "TSS Converter specific error",
                "details": str(e),
                "context": getattr(e, 'context', None)
            }
            logger.error(f"TSS Converter error: {e}")
            
        except Exception as e:
            result["error"] = {
                "type": "UNEXPECTED_ERROR",
                "message": "Unexpected system error",
                "details": str(e),
                "suggestion": "Contact system administrator"
            }
            logger.exception(f"Unexpected error: {e}")
            
        finally:
            # Cleanup
            if self.session_id:
                try:
                    self.pipeline.cleanup_session(self.session_id)
                except Exception as e:
                    logger.warning(f"Cleanup error: {e}")
            
            result["processing_time"] = (datetime.now() - start_time).total_seconds()
            
        return result

# Usage example
def main():
    """Example usage of TSSConverterService"""
    
    service = TSSConverterService("config.json")
    
    def progress_handler(step: int, total: int, message: str):
        print(f"Progress: {step}/{total} - {message}")
    
    # Process file
    result = service.process_file(
        "input/test_data.xlsx",
        progress_callback=progress_handler
    )
    
    # Handle results
    if result["success"]:
        print(f"✅ Success! Output: {result['output_file']}")
        print(f"⏱️ Processing time: {result['processing_time']:.2f} seconds")
    else:
        error = result["error"]
        print(f"❌ Error: {error['message']}")
        print(f"Details: {error['details']}")
        if "suggestion" in error:
            print(f"Suggestion: {error['suggestion']}")

if __name__ == "__main__":
    main()
```

### Async Integration Example
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any

class AsyncTSSConverter:
    """Async wrapper for TSS Converter for handling multiple files"""
    
    def __init__(self, max_workers: int = 4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.service = TSSConverterService()
    
    async def process_file_async(self, file_path: str) -> Dict[str, Any]:
        """Process single file asynchronously"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            self.service.process_file, 
            file_path
        )
    
    async def process_multiple_files(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """Process multiple files concurrently"""
        tasks = [
            self.process_file_async(file_path) 
            for file_path in file_paths
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)

# Usage
async def batch_process_example():
    converter = AsyncTSSConverter(max_workers=4)
    
    files = [
        "input/file1.xlsx",
        "input/file2.xlsx", 
        "input/file3.xlsx",
        "input/file4.xlsx"
    ]
    
    print("Starting batch processing...")
    results = await converter.process_multiple_files(files)
    
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"File {files[i]} failed: {result}")
        elif result["success"]:
            print(f"File {files[i]} completed: {result['output_file']}")
        else:
            print(f"File {files[i]} failed: {result['error']['message']}")

# Run async example
# asyncio.run(batch_process_example())
```

## 🏗️ Integration Scenarios

### Docker Integration

#### Dockerfile
```dockerfile
FROM python:3.8-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p temp/uploads temp/outputs

# Expose Streamlit port
EXPOSE 8501

# Run Streamlit app
CMD ["streamlit", "run", "app.py", "--server.port", "8501", "--server.headless", "true"]
```

#### Docker Compose
```yaml
version: '3.8'

services:
  tss-converter:
    build: .
    ports:
      - "8501:8501"
    volumes:
      - ./data:/app/data
      - ./output:/app/output
      - ./temp:/app/temp
    environment:
      - STREAMLIT_ENV=production
      - STREAMLIT_SECURITY_MODE=strict
      - STREAMLIT_MAX_FILE_SIZE=104857600
    restart: unless-stopped
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - tss-converter
    restart: unless-stopped
```

#### Usage
```bash
# Build and run
docker-compose up --build -d

# Check logs
docker-compose logs -f tss-converter

# Scale for load balancing
docker-compose up --scale tss-converter=3

# Stop services
docker-compose down
```

### API Integration

#### Flask API Wrapper
```python
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
import uuid
from pathlib import Path

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB limit

converter_service = TSSConverterService()

@app.route('/api/convert', methods=['POST'])
def convert_file():
    """API endpoint for file conversion"""
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.lower().endswith('.xlsx'):
        return jsonify({'error': 'Only .xlsx files supported'}), 400
    
    try:
        # Save uploaded file
        session_id = str(uuid.uuid4())
        upload_dir = Path(f"temp/{session_id}")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        filename = secure_filename(file.filename)
        filepath = upload_dir / filename
        file.save(str(filepath))
        
        # Process file
        result = converter_service.process_file(str(filepath))
        
        if result['success']:
            return jsonify({
                'status': 'success',
                'session_id': session_id,
                'output_file': result['output_file'],
                'processing_time': result['processing_time']
            })
        else:
            return jsonify({
                'status': 'error',
                'error': result['error']
            }), 400
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': {'message': str(e), 'type': 'SYSTEM_ERROR'}
        }), 500

@app.route('/api/download/<session_id>/<filename>')
def download_file(session_id, filename):
    """Download converted file"""
    try:
        filepath = Path(f"temp/{session_id}") / filename
        if filepath.exists():
            return send_file(str(filepath), as_attachment=True)
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'TSS Converter API'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
```

#### API Usage Examples
```bash
# Upload and convert file
curl -X POST -F "file=@product_data.xlsx" \
  http://localhost:5000/api/convert

# Download result
curl -O http://localhost:5000/api/download/session123/output.xlsx

# Health check
curl http://localhost:5000/api/health
```

## 📊 Performance Optimization

### Batch Processing Optimization
```python
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor
import time

def process_file_optimized(file_info):
    """Optimized file processing for batch operations"""
    file_path, session_id = file_info
    
    # Initialize service in worker process
    service = TSSConverterService()
    
    start_time = time.time()
    result = service.process_file(file_path)
    processing_time = time.time() - start_time
    
    return {
        'file_path': file_path,
        'session_id': session_id,
        'result': result,
        'processing_time': processing_time
    }

def batch_process_optimized(file_paths, max_workers=None):
    """Optimized batch processing with multiprocessing"""
    
    if max_workers is None:
        max_workers = min(mp.cpu_count(), len(file_paths))
    
    # Prepare file info
    file_infos = [
        (file_path, f"batch_{i}") 
        for i, file_path in enumerate(file_paths)
    ]
    
    print(f"Processing {len(file_paths)} files with {max_workers} workers")
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(process_file_optimized, file_infos))
    
    # Summarize results
    successful = [r for r in results if r['result']['success']]
    failed = [r for r in results if not r['result']['success']]
    
    print(f"✅ Successful: {len(successful)}")
    print(f"❌ Failed: {len(failed)}")
    
    total_time = sum(r['processing_time'] for r in results)
    avg_time = total_time / len(results)
    
    print(f"⏱️ Total processing time: {total_time:.2f}s")
    print(f"⏱️ Average time per file: {avg_time:.2f}s")
    
    return results

# Usage
if __name__ == "__main__":
    files = [f"input/batch_file_{i}.xlsx" for i in range(1, 11)]
    results = batch_process_optimized(files, max_workers=4)
```

### Memory Management
```python
import gc
import psutil
import os

class MemoryOptimizedConverter:
    """TSS Converter with memory optimization"""
    
    def __init__(self, memory_limit_gb=2):
        self.memory_limit = memory_limit_gb * 1024 * 1024 * 1024  # Convert to bytes
        self.service = TSSConverterService()
    
    def check_memory_usage(self):
        """Check current memory usage"""
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        return memory_info.rss  # Resident Set Size
    
    def process_with_memory_management(self, file_path: str):
        """Process file with memory monitoring"""
        
        # Check memory before processing
        initial_memory = self.check_memory_usage()
        print(f"Initial memory: {initial_memory / 1024 / 1024:.2f} MB")
        
        if initial_memory > self.memory_limit:
            print("Memory limit exceeded before processing")
            gc.collect()  # Force garbage collection
            
            # Check again after cleanup
            after_gc_memory = self.check_memory_usage()
            if after_gc_memory > self.memory_limit:
                raise MemoryError("Insufficient memory to process file")
        
        try:
            # Process file
            result = self.service.process_file(file_path)
            
            # Check memory after processing
            final_memory = self.check_memory_usage()
            memory_increase = final_memory - initial_memory
            
            print(f"Final memory: {final_memory / 1024 / 1024:.2f} MB")
            print(f"Memory increase: {memory_increase / 1024 / 1024:.2f} MB")
            
            return result
            
        finally:
            # Cleanup
            gc.collect()

# Usage example
converter = MemoryOptimizedConverter(memory_limit_gb=1)
result = converter.process_with_memory_management("large_file.xlsx")
```

## 🔧 Troubleshooting Guide

### Common Error Scenarios & Solutions

#### Error Diagnosis Script
```python
#!/usr/bin/env python3
"""
TSS Converter Diagnostic Tool
Comprehensive system check and troubleshooting
"""

import sys
import os
from pathlib import Path
import importlib
import traceback

def check_python_version():
    """Check Python version compatibility"""
    print("🐍 Checking Python version...")
    version = sys.version_info
    
    if version >= (3, 8):
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Requires 3.8+")
        return False

def check_dependencies():
    """Check required dependencies"""
    print("\n📦 Checking dependencies...")
    
    required_packages = [
        'openpyxl',
        'streamlit',
        'pathlib',
        'typing',
        'logging'
    ]
    
    missing = []
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - Missing")
            missing.append(package)
    
    return len(missing) == 0

def check_file_structure():
    """Check project file structure"""
    print("\n📁 Checking file structure...")
    
    required_files = [
        'step1_template_creation.py',
        'step2_data_extraction.py', 
        'step3_pre_mapping_fill.py',
        'step4_data_mapping.py',
        'step5_filter_deduplicate.py',
        'app.py',
        'streamlit_pipeline.py',
        'common/config.py',
        'common/validation.py',
        'common/exceptions.py'
    ]
    
    missing = []
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - Missing")
            missing.append(file_path)
    
    return len(missing) == 0

def check_permissions():
    """Check file permissions"""
    print("\n🔐 Checking permissions...")
    
    directories = ['temp', 'output', 'input']
    
    all_good = True
    for dir_path in directories:
        path = Path(dir_path)
        
        # Create if doesn't exist
        if not path.exists():
            try:
                path.mkdir(parents=True, exist_ok=True)
                print(f"✅ Created directory: {dir_path}")
            except Exception as e:
                print(f"❌ Cannot create {dir_path}: {e}")
                all_good = False
                continue
        
        # Check read/write permissions
        if os.access(path, os.R_OK | os.W_OK):
            print(f"✅ {dir_path} - Read/Write OK")
        else:
            print(f"❌ {dir_path} - Permission denied")
            all_good = False
    
    return all_good

def test_basic_functionality():
    """Test basic TSS Converter functionality"""
    print("\n🧪 Testing basic functionality...")
    
    try:
        # Import core modules
        from common.config import init_config
        from common.validation import FileValidator
        
        print("✅ Core modules import successfully")
        
        # Test config initialization
        config = init_config()
        print("✅ Configuration initialization successful")
        
        # Test file validator
        validator = FileValidator()
        print("✅ File validator initialization successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        traceback.print_exc()
        return False

def test_file_validation():
    """Test file validation with sample file"""
    print("\n📄 Testing file validation...")
    
    # Create test file if it doesn't exist
    test_file = Path("test_sample.xlsx")
    
    if not test_file.exists():
        try:
            import openpyxl
            wb = openpyxl.Workbook()
            ws = wb.active
            ws['A1'] = 'Product name'
            ws['B1'] = 'Article number'
            ws['A2'] = 'Test Product'
            ws['B2'] = 'TEST-001'
            wb.save(str(test_file))
            print("✅ Created test file")
        except Exception as e:
            print(f"❌ Cannot create test file: {e}")
            return False
    
    try:
        from common.validation import validate_step1_input
        validate_step1_input(str(test_file))
        print("✅ File validation test passed")
        
        # Cleanup
        test_file.unlink()
        print("✅ Test file cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ File validation test failed: {e}")
        return False

def main():
    """Run complete diagnostic"""
    print("🔧 TSS Converter System Diagnostic")
    print("=" * 50)
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("File Structure", check_file_structure),
        ("Permissions", check_permissions),
        ("Basic Functionality", test_basic_functionality),
        ("File Validation", test_file_validation)
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} check failed with exception: {e}")
            results.append((name, False))
    
    # Summary
    print("\n📊 Diagnostic Summary")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name}: {status}")
    
    print(f"\nOverall: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 All systems operational!")
        return 0
    else:
        print("⚠️  Some issues detected. Please review failed checks.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
```

#### Quick Fix Scripts
```bash
#!/bin/bash
# Quick fix script for common issues

echo "🛠️  TSS Converter Quick Fix"

# Fix permissions
echo "Fixing permissions..."
mkdir -p temp output input
chmod 755 temp output input

# Install missing dependencies
echo "Installing dependencies..."
pip install -r requirements.txt --upgrade

# Clean temporary files
echo "Cleaning temporary files..."
find temp -type f -name "*.xlsx" -mtime +1 -delete
find output -type f -name "*-Step*.xlsx" -mtime +7 -delete

# Test basic functionality
echo "Testing basic functionality..."
python3 -c "
try:
    from common.config import init_config
    config = init_config()
    print('✅ Configuration OK')
except Exception as e:
    print(f'❌ Configuration failed: {e}')
"

echo "Quick fix completed!"
```

---

**🎯 Summary**

This comprehensive usage guide covers all aspects of TSS Converter implementation:

- **Command Line**: Complete pipeline examples, batch processing, debugging
- **Web Interface**: Streamlit configuration, deployment, advanced features  
- **Programmatic**: Python API integration, async processing, error handling
- **Integration**: Docker, API wrappers, performance optimization
- **Troubleshooting**: Diagnostic tools, quick fixes, error resolution

The TSS Converter System is designed to be flexible, robust, và production-ready with comprehensive documentation và examples cho all use cases.