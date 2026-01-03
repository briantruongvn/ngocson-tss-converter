# Excel Template Converter - TSS Converter System

## 🎯 Tổng quan
Hệ thống Python chuyên nghiệp để chuyển đổi Excel files từ format tùy ý sang template chuẩn TSS (Technical Specification System). Bao gồm 5 steps tự động với validation toàn diện, error handling robust và configuration management.

## ⚡ Chức năng chính
- **5-step automated pipeline**: Template → Extract → Map → Fill → Filter
- **Robust validation framework** với custom exceptions
- **Configuration management** với JSON config và environment variables
- **Comprehensive error handling** và detailed logging
- **File format validation** strict (.xlsx only)
- **Batch processing** support
- **Professional output** với 17-column standardized format

## 🏗️ Kiến trúc hệ thống

### Core Components
```
TSS Converter/
├── step1_template_creation.py    # Template generation với formatting
├── step2_data_extraction.py      # Article data extraction từ source
├── step3_pre_mapping_fill.py     # Pre-mapping data fill và business logic  
├── step4_data_fill.py            # Vertical inheritance filling
├── step5_filter_deduplicate.py   # NA filtering và SD deduplication
├── common/
│   ├── exceptions.py             # Custom exception framework
│   ├── validation.py             # File & structure validation
│   └── config.py                 # Configuration management
├── tsconverter.example.json      # Sample configuration
└── YEU_CAU_FILE_INPUT.md        # Input requirements documentation
```

### Processing Pipeline
```mermaid
graph LR
    A[Input Excel File] --> B[Step 1: Create Template]
    B --> C[Step 2: Extract Data]
    C --> D[Step 3: Map Data]
    D --> E[Step 4: Fill Data]
    E --> F[Step 5: Filter & Deduplicate]
    F --> G[Final Output]
```

## 🔧 Yêu cầu kỹ thuật

### Dependencies
```python
openpyxl>=3.0.0        # Excel file processing
pathlib                # File path handling (built-in)
logging                # Logging system (built-in)
json                   # Configuration files (built-in)
argparse               # Command line interface (built-in)
typing                 # Type hints (built-in)
re                     # Regular expressions (built-in)
os                     # Operating system interface (built-in)
mimetypes              # File type detection (built-in)
collections            # Data structures (built-in)
```

### System Requirements
- **Python**: 3.7+
- **File Format**: Excel .xlsx files only (strict validation)
- **Memory**: Minimum 1GB RAM for large datasets
- **Storage**: 200MB+ free space for intermediate files
- **Encoding**: UTF-8 compatible

### Platform Support
- ✅ Windows 10/11
- ✅ macOS 10.14+
- ✅ Linux (Ubuntu 18.04+, CentOS 7+)
- ✅ Docker containers

## 📊 Template Structure & Business Logic

### Step 1: Template Creation
**Input**: Any .xlsx file
**Output**: Standardized 17-column template

**Template Headers (A-Q)**:
1. **Combination** (Yellow background)
2. **General Type Component(Type)** (Red background, white text)
3. **Sub-Type Component Identity Process Name** (Red background)
4. **Material Designation** (Red background)
5. **Material Distributor** (Red background)
6. **Producer** (Red background)
7. **Material Type In Process** (Red background)
8. **Document type** (Blue background, white text)
9. **Requirement Source/TED** (Blue background)
10. **Sub-type** (Blue background)
11. **Regulation or substances** (Blue background)
12. **Limit** (Light green background)
13. **Test method** (Light green background)
14. **Frequency** (Light green background)
15. **Level** (Blue background, white text)
16. **Warning Limit** (Light green background)
17. **Additional Information** (Light green background)

### Step 2: Data Extraction
**Logic**: Extract article names và numbers từ source files
**Search Headers**:
- Names: `Product name`, `Article name` (case-insensitive)
- Numbers: `Product number`, `Article number` (case-insensitive)
**Features**:
- Multi-value cell parsing (`;`, `,`, `\n` delimiters)
- Automatic duplicate removal
- Trailing punctuation cleanup

### Step 3: Data Mapping
**Business Rules**:
- **Finished Product sheets**: Special column mapping (C→D, H→F, K+L→I, etc.)
- **Other sheets**: General mapping (I→D, J→F, N+O→I, etc.)
- **Sheet Detection**: Keyword-based (`finished product`) + content-based (>10 rows)
- **Column Combination**: Multiple columns joined with `-` delimiter

### Step 4: Data Fill
**Algorithm**: Vertical inheritance filling
- **Target Columns**: D, E, F
- **Start Row**: 4 (after headers)
- **Logic**: Empty cells inherit value từ cell phía trên

### Step 5: Filter & Deduplicate
**Two-stage Process**:
1. **NA Filtering**: Remove rows với Column H = `""`, `"NA"`, `"-"`
2. **SD Deduplication**: Group SD rows by columns B,C,D,E,F,I,J similarity
   - Keep first occurrence
   - Clear columns K,L,M in kept row  
   - Set column N to common value or "Yearly"

## 🛡️ Validation & Error Handling

### File Validation
```python
# Format validation
- Extension: .xlsx only
- MIME type verification
- File accessibility check
- Structure integrity validation

# Content validation  
- Required headers presence
- Data sufficiency checks
- Column availability verification
- Worksheet structure validation
```

### Custom Exception Framework
```python
TSConverterError                 # Base exception
├── ValidationError              # Input validation failures
│   ├── FileFormatError         # Invalid file format
│   ├── WorksheetNotFoundError  # Missing worksheets  
│   └── ColumnMissingError      # Missing required columns
├── DataIntegrityError          # Data quality issues
│   ├── InsufficientDataError   # Not enough data
│   └── HeaderNotFoundError     # Missing headers
├── ProcessingError             # Runtime processing errors
│   └── FileAccessError         # File I/O problems
└── ConfigurationError          # Configuration issues
```

### Error Context & Debugging
- **Error codes**: Specific identifiers for each error type
- **Context information**: File paths, row/column positions, expected vs actual values
- **Detailed logging**: DEBUG, INFO, WARNING, ERROR levels
- **User-friendly messages**: Clear error descriptions với suggested fixes

## ⚙️ Configuration Management

### Configuration Sources (Priority Order)
1. **Environment Variables**: `TSCONVERTER_*`
2. **JSON Config Files**: `tsconverter.json`, `config.json`
3. **Default Configuration**: Built-in fallbacks

### Sample Configuration
```json
{
  "general": {
    "base_dir": ".",
    "output_dir": "output",
    "log_level": "INFO",
    "max_workers": 4
  },
  "validation": {
    "strict_mode": true,
    "skip_format_validation": false
  },
  "step2": {
    "name_headers": ["Product name", "Article name"],
    "number_headers": ["Product number", "Article number"]
  },
  "step3": {
    "column_delimiter": "-",
    "finished_product_keyword": "finished product"
  },
  "step5": {
    "na_values": ["", "NA", "-"],
    "default_frequency": "Yearly"
  }
}
```

### Environment Variables
```bash
export TSCONVERTER_BASE_DIR="/path/to/project"
export TSCONVERTER_LOG_LEVEL="DEBUG"
export TSCONVERTER_STRICT_MODE="true"
export TSCONVERTER_MAX_WORKERS="8"
```

## 🚀 Usage Examples

### Command Line Interface
```bash
# Step 1: Create template
python step1_template_creation.py input.xlsx

# Step 2: Extract data
python step2_data_extraction.py output/input-Step1.xlsx -s source_data.xlsx

# Step 3: Map data  
python step3_pre_mapping_fill.py source_data.xlsx output/input-Step2.xlsx

# Step 4: Fill data
python step4_data_fill.py output/input-Step3.xlsx

# Step 5: Filter and deduplicate
python step5_filter_deduplicate.py output/input-Step4.xlsx

# Verbose logging
python step1_template_creation.py input.xlsx -v

# Custom output path
python step1_template_creation.py input.xlsx -o /path/to/output.xlsx

# Batch processing
python step1_template_creation.py *.xlsx --batch
```

### Programmatic Usage
```python
from step1_template_creation import TemplateCreator
from common.config import init_config
from common.exceptions import TSConverterError

# Initialize configuration
config = init_config("tsconverter.json")

# Create template
try:
    creator = TemplateCreator()
    output = creator.create_template("input.xlsx")
    print(f"Template created: {output}")
except TSConverterError as e:
    print(f"Error: {e}")
    print(f"Context: {e.context}")
```

## 📝 Input File Requirements

### Essential Requirements
- **File Format**: `.xlsx` only (Excel 2007+)
- **File Size**: Maximum 100MB
- **Required Headers**: `Product name` + `Article number` (hoặc variations)
- **Data Structure**: Headers với data ngay phía dưới
- **Encoding**: UTF-8 compatible

### Data Structure Example
```
| A | B            | C | D             |
|---|--------------|---|---------------|
|   | Product name |   | Article number|
|   | Product A    |   | PRD-001       |
|   | Product B    |   | PRD-002       |
|   | Product C    |   | PRD-003       |
```

### Supported Features
- Multiple worksheets (auto-detection)
- Flexible header positions
- Multi-value cells (`Product A; Product B`)
- Various naming conventions
- Mixed data types

## 🔍 Troubleshooting

### Common Issues
```
❌ FileFormatError: Invalid file format
→ Solution: Save file as Excel Workbook (.xlsx)

❌ HeaderNotFoundError: Required headers missing  
→ Solution: Add "Product name" and "Article number" headers

❌ InsufficientDataError: Not enough data
→ Solution: Add product data below headers

❌ ValidationError: File validation failed
→ Solution: Check file accessibility and format
```

### Debug Mode
```bash
# Enable detailed logging
export TSCONVERTER_LOG_LEVEL="DEBUG"
python step1_template_creation.py input.xlsx -v

# Check validation details
python -c "
from common.validation import validate_step1_template
validate_step1_template('input.xlsx')
"
```

### Performance Optimization
- **Large files**: Increase memory allocation
- **Batch processing**: Use parallel workers
- **Network storage**: Copy files locally first
- **Multiple formats**: Convert to .xlsx before processing

## 🎯 Success Metrics
- **Validation Coverage**: 100% input validation với detailed errors
- **Error Handling**: Comprehensive exception framework
- **Configuration**: Flexible config management
- **Documentation**: Complete usage guidelines
- **Robustness**: Handle edge cases và malformed inputs
- **User Experience**: Clear error messages và examples

## 📞 Support Information
- **Documentation**: `YEU_CAU_FILE_INPUT.md` for detailed input requirements
- **Configuration**: `tsconverter.example.json` for setup examples
- **Validation**: Built-in validation với detailed error reporting
- **Logging**: Comprehensive logging for debugging

**Note**: Hệ thống được thiết kế để robust và user-friendly. Tuân thủ input requirements trong `YEU_CAU_FILE_INPUT.md` sẽ đảm bảo processing thành công 100%.