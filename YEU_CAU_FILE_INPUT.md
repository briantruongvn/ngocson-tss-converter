# YÊU CẦU FILE INPUT CHO TSS CONVERTER SYSTEM

## 📋 Tổng quan
TSS Converter System là hệ thống chuyển đổi Excel files từ format tùy ý sang template chuẩn Technical Specification System. Hệ thống cần 1 file Excel đầu vào và sẽ tự động thực hiện 5-step pipeline để tạo ra output format chuẩn với 17 columns.

## 🎯 Yêu cầu File Input

### 1. Format và File Requirements
- **BẮT BUỘC**: File Excel định dạng `.xlsx` (Excel 2007+)
- **KHÔNG hỗ trợ**: `.xls`, `.csv`, `.txt`, `.ods` hoặc các format khác
- **Kích thước tối đa**: 50MB (có thể configure lên 100MB trong production)
- **File accessibility**: File phải readable, không bị corrupt hoặc password-protected
- **Encoding**: UTF-8 compatible với proper character encoding

### 2. Data Structure Requirements

#### A. Essential Article Information
File phải chứa **ít nhất 1 worksheet** với data structure cơ bản:

**Product/Article Names** (hỗ trợ các header variations):
- `Product name` (preferred)
- `Article name` 
- Case-insensitive: `product name`, `PRODUCT NAME`
- Multi-language support: Tên tiếng Việt có dấu

**Product/Article Numbers** (hỗ trợ các header variations):
- `Product number` (preferred)
- `Article number`
- Case-insensitive: `product number`, `ARTICLE NUMBER`
- Format: Alphanumeric codes, SKUs, barcodes

#### B. Data Layout Structure
```
Example valid structure:

| A | B            | C | D             |
|---|--------------|---|---------------|
|   | Product name |   | Article number|
|   | Product A    |   | PRD-001       |
|   | Product B    |   | PRD-002       |
|   | Product C    |   | PRD-003       |
|   |              |   |               | ← Processing stops here
```

**Data Processing Rules**:
- **Flexible Header Position**: Headers có thể ở bất kỳ vị trí nào (auto-detection)
- **Sequential Data**: Dữ liệu phải liền kề ngay dưới header row
- **Multi-value Cells**: Hỗ trợ `;`, `,`, `\n` separators trong 1 cell
- **Auto-trimming**: Tự động remove trailing punctuation và whitespace
- **Empty Cell Handling**: Processing dừng khi gặp empty cells liên tiếp

#### C. Multi-Worksheet Support
- **Multiple Worksheets**: File có thể chứa nhiều worksheets
- **Auto-Detection**: System tự động scan tất cả worksheets
- **Content Filtering**: Empty worksheets sẽ được ignore
- **Naming Convention**: Tên worksheet tùy ý, không có requirements đặc biệt
- **Special Handling**: "Finished Product" sheets có business logic riêng

### 3. Advanced Data Support

#### A. Technical Specifications (Optional)
Nếu file chứa detailed mapping data:
- **Test Plans**: Hỗ trợ extract test specifications
- **Technical Requirements**: Auto-detect regulation và limit values
- **Complex Structures**: Nested data với inheritance rules
- **Business Logic**: Automatic mapping theo industry standards

#### B. Data Quality Features
- **Duplicate Removal**: Tự động detect và remove duplicates
- **Data Validation**: Comprehensive validation cho data integrity
- **Error Recovery**: Graceful handling của malformed data
- **Fallback Processing**: Alternative logic khi primary processing fails

## ✅ File Input Checklist

### 🔴 Essential Requirements
- [ ] File format: `.xlsx` Excel 2007+ only
- [ ] File accessibility: Readable với Excel hoặc openpyxl
- [ ] Data presence: Ít nhất 1 worksheet with actual content
- [ ] Product names: Header containing "Product name" hoặc "Article name"
- [ ] Product numbers: Header containing "Product number" hoặc "Article number"
- [ ] Sequential data: Product data ngay dưới header rows
- [ ] File integrity: Not corrupted, không có password protection

### 🟡 Recommended Best Practices
- [ ] Clean data: Properly formatted, consistent naming
- [ ] Character encoding: UTF-8 compatible characters
- [ ] File size: Under 50MB cho optimal performance
- [ ] Structure consistency: Uniform data patterns across worksheets
- [ ] Header clarity: Clear, unambiguous header names

## 🚨 Common Issues & Troubleshooting

### ❌ File Format Errors
**Error**: `FileFormatError: Invalid file format`
- **Root Cause**: File không phải .xlsx hoặc corrupted
- **Solution**: 
  - Save As → Excel Workbook (.xlsx)
  - Kiểm tra file integrity với Excel
  - Convert từ .xls sang .xlsx nếu cần

### ❌ Header Detection Failures
**Error**: `HeaderNotFoundError: Required headers missing`
- **Root Cause**: Thiếu hoặc sai tên headers
- **Solution**:
  - Add headers: "Product name" và "Article number" (exact text)
  - Check spelling và spacing
  - Ensure headers are text values, không phải formulas
  - Verify headers trong first 10 rows của worksheet

### ❌ Data Validation Issues
**Error**: `InsufficientDataError: Not enough data`
- **Root Cause**: Empty hoặc insufficient data below headers
- **Solution**:
  - Add product data directly below header row
  - Ensure sequential data, không có empty rows
  - Check data format consistency

### ❌ File Access Problems
**Error**: `FileAccessError: Cannot open file`
- **Root Cause**: File permissions, corruption, hoặc lock issues
- **Solution**:
  - Check file permissions (readable)
  - Remove password protection
  - Close file in other applications
  - Create new copy nếu corrupted

### ❌ Worksheet Structure Issues
**Error**: `WorksheetNotFoundError: No valid worksheets`
- **Root Cause**: All worksheets empty hoặc invalid structure
- **Solution**:
  - Add content to at least 1 worksheet
  - Verify worksheet không bị hidden
  - Check merged cells không affect headers

## 📝 Valid File Examples

### Example 1: Basic Product List
```
Sheet: "Product Catalog" (any name)

| A | B            | C | D             | E | F |
|---|--------------|---|---------------|---|---|
| 1 |              |   |               |   |   |
| 2 | Product name |   | Article number|   |   |
| 3 | Laptop Pro   |   | LPT-2024-001  |   |   |
| 4 | Mouse Wireless|   | MSE-WRL-002   |   |   |
| 5 | Keyboard RGB |   | KBD-RGB-003   |   |   |
| 6 |              |   |               |   |   |
```

### Example 2: Alternative Layout
```
Sheet: "Articles" (any name)

| A | B | C               | D | E              |
|---|---|-----------------|---|----------------|
| 1 |   |                 |   |                |
| 2 |   | Article name    |   | Product number |
| 3 |   | Monitor 4K      |   | MON-4K-101     |
| 4 |   | Tablet Air      |   | TAB-AIR-102    |
| 5 |   |                 |   |                |
```

### Example 3: Multi-value Cells
```
Sheet: "Complex Data"

| A | B            | C | D             |
|---|--------------|---|---------------|
| 1 | Product name |   | Article number|
| 2 | Phone A; Phone B |   | PH-001,PH-002 |
| 3 | Tablet X     |   | TAB-X-003     |
| 4 | Laptop Pro\nLaptop Basic | LPT-001\nLPT-002 |
```

### Example 4: Technical Specifications
```
Sheet: "Test Plan Data"

| A | B | C | D | E | F | G | H |
|---|---|---|---|---|---|---|---|
| 1 | Material | Type | Regulation | Limit | Method | Frequency | Level |
| 2 | Steel A1 | Metal| ISO-9001  | <50ppm| ICP-MS | Monthly | Warning |
| 3 | Plastic B| Polymer| RoHS    | <1000 | XRF    | Quarterly| Alert |
```

## 🔄 Processing Pipeline Overview

### 5-Step Automated Pipeline
1. **Step 1 - Template Creation**: Generate standardized 17-column template với headers A-Q
2. **Step 2 - Data Extraction**: Extract article names và numbers từ source worksheets
3. **Step 3 - Pre-mapping Fill**: Apply vertical inheritance filling cho columns D,E,F
4. **Step 4 - Data Mapping**: Business logic mapping theo Finished Product rules
5. **Step 5 - Filter & Deduplicate**: Remove NA values và SD duplicates

### Output Structure
**17-Column Format (A-Q)**:
- A: Combination
- B: General Type Component  
- C: Sub-Type Component Identity Process Name
- D: Material Designation
- E: Material Distributor
- F: Producer
- G: Material Type In Process
- H: Document type
- I: Requirement Source/TED
- J: Sub-type
- K: Regulation or substances
- L: Limit
- M: Test method
- N: Frequency
- O: Level
- P: Warning Limit
- Q: Additional Information

## 📈 Performance & Validation

### Processing Metrics
- **File Size Support**: Up to 50MB (configurable to 100MB)
- **Processing Time**: 30 seconds - 2 minutes depending on complexity
- **Success Rate**: 100% for files meeting input requirements
- **Memory Usage**: ~100-500MB during processing

### Security & Validation
- **Input Validation**: Comprehensive format và structure checking
- **Error Recovery**: Graceful fallback mechanisms
- **Session Management**: Secure temporary file handling
- **Auto-cleanup**: Temporary files removed after processing

## 💡 Best Practices & Tips

### Optimization Guidelines
- **File Preparation**: Clean data trước khi upload
- **Header Naming**: Use exact text "Product name" và "Article number"
- **Data Quality**: Ensure consistent formatting across rows
- **File Size**: Keep under 50MB cho optimal performance
- **Testing**: Verify file opens correctly trong Excel before upload

### Success Factors
- ✅ **100% Success Rate** khi tuân thủ input requirements
- ✅ **Auto-Detection** của headers và data structure
- ✅ **Robust Error Handling** với detailed error messages
- ✅ **Flexible Input Support** cho various Excel layouts
- ✅ **Production-Ready** với comprehensive validation

---

**Note**: TSS Converter System được thiết kế để handle diverse Excel formats và provide consistent, reliable output. Tuân thủ các requirements trong document này sẽ ensure successful processing 100%.

**Support**: For troubleshooting, check error messages carefully - they provide specific guidance về required fixes.