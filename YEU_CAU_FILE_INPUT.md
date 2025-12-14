# YÊU CẦU FILE INPUT CHO EXCEL TEMPLATE CONVERTER

## 📋 TỔNG QUAN
Hệ thống Excel Template Converter cần 1 file Excel đầu vào để bắt đầu quá trình chuyển đổi. Tất cả các bước tiếp theo sẽ được xử lý tự động.

## 🎯 YÊU CẦU FILE ĐẦU VÀO

### 1. Định dạng file
- **BẮT BUỘC**: File Excel định dạng `.xlsx` (Excel 2007+)
- **KHÔNG hỗ trợ**: `.xls`, `.csv`, `.txt`, hoặc các định dạng khác
- **Kích thước tối đa**: 100MB
- **File phải mở được**: Không bị lỗi, không bị khóa (protected)

### 2. Cấu trúc dữ liệu BẮT BUỘC

#### A. Article Information (Thông tin sản phẩm)
File phải chứa **ít nhất 1 worksheet** có các header sau:

**Tên sản phẩm** (1 trong các header sau):
- `Product name`
- `Article name`
- `product name`
- `article name`

**Mã sản phẩm** (1 trong các header sau):
- `Product number`
- `Article number`
- `product number`
- `article number`

#### B. Cấu trúc dữ liệu
```
Ví dụ cấu trúc đúng:

| A | B | C | D |
|---|---|---|---|
|   |Product name|   |Article number|
|   |Product A   |   |PRD-001       |
|   |Product B   |   |PRD-002       |
|   |Product C   |   |PRD-003       |
|   |            |   |              | ← Dừng ở đây
```

**Quy tắc**:
- Header có thể ở bất kỳ vị trí nào trong worksheet
- Dữ liệu phải nằm **ngay dưới** header (dòng tiếp theo)
- Dữ liệu đọc từ trên xuống dưới cho đến khi gặp ô trống
- Mỗi ô có thể chứa nhiều giá trị phân tách bằng `;` hoặc xuống dòng

#### C. Worksheet Requirements
- File có thể chứa nhiều worksheet
- Hệ thống sẽ tự động tìm và xử lý tất cả worksheet có nội dung
- Worksheet trống sẽ bị bỏ qua
- **Tên worksheet tùy ý** - không có yêu cầu đặc biệt

### 3. Dữ liệu mapping (nếu có)
Nếu file chứa dữ liệu mapping chi tiết:
- Worksheet có thể chứa dữ liệu test plan, technical specifications
- Hệ thống sẽ tự động detect và ánh xạ theo cấu trúc chuẩn
- Không cần chuẩn bị đặc biệt - hệ thống xử lý tự động

## ✅ CHECKLIST FILE INPUT

### Bắt buộc
- [ ] File định dạng `.xlsx`
- [ ] Mở được bằng Excel
- [ ] Có ít nhất 1 worksheet chứa data
- [ ] Có header `Product name` hoặc `Article name`
- [ ] Có header `Product number` hoặc `Article number`
- [ ] Có dữ liệu sản phẩm dưới header

### Khuyến nghị
- [ ] Dữ liệu được clean, không có ký tự lạ
- [ ] Encoding UTF-8 hoặc tương thích
- [ ] Kích thước file hợp lý (< 50MB)

## 🚨 CÁC LỖI THƯỜNG GẶP

### ❌ File không đúng định dạng
- **Lỗi**: "File format not supported"
- **Nguyên nhân**: File không phải .xlsx
- **Khắc phục**: Save As → Excel Workbook (*.xlsx)

### ❌ Không tìm thấy header
- **Lỗi**: "Header not found"  
- **Nguyên nhân**: Thiếu header "Product name" hoặc "Article name"
- **Khắc phục**: 
  - Thêm header chính xác
  - Kiểm tra chính tả và khoảng trắng
  - Đảm bảo header ở dạng text, không phải formula

### ❌ Không có dữ liệu
- **Lỗi**: "No data found"
- **Nguyên nhân**: Không có dữ liệu dưới header
- **Khắc phục**: Thêm dữ liệu sản phẩm ngay dưới dòng header

### ❌ File bị lỗi
- **Lỗi**: "Cannot open file"
- **Nguyên nhân**: File bị corrupt hoặc protected
- **Khắc phục**: 
  - Kiểm tra file mở được bằng Excel
  - Remove password protection nếu có
  - Tạo file mới và copy dữ liệu

## 📝 VÍ DỤ FILE CHUẨN

```
Sheet: "Product List" (tên tùy ý)

| A | B            | C | D           | E | F |
|---|--------------|---|-------------|---|---|
| 1 |              |   |             |   |   |
| 2 | Product name |   |Article number|  |   |
| 3 | Product A    |   | PRD-001     |   |   |
| 4 | Product B    |   | PRD-002     |   |   |
| 5 | Product C    |   | PRD-003     |   |   |
| 6 |              |   |             |   |   |
```

**hoặc**

```
Sheet: "Data" (tên tùy ý)

| A | B | C               | D | E              |
|---|---|-----------------|---|----------------|
| 1 |   |                 |   |                |
| 2 |   | Article name    |   | Product number |
| 3 |   | Product X       |   | PRD-101        |
| 4 |   | Product Y       |   | PRD-102        |
| 5 |   |                 |   |                |
```

## 🔄 QUÁ TRÌNH XỬ LÝ

1. **Input**: File Excel (.xlsx) với article data
2. **Tự động**: Hệ thống tạo template và extract dữ liệu  
3. **Tự động**: Mapping và transform theo business rules
4. **Tự động**: Fill và deduplicate data
5. **Output**: File Excel đã được convert theo format chuẩn

## 📞 LƯU Ý

- **Chỉ cần chuẩn bị 1 file input** theo yêu cầu trên
- **Tất cả logic conversion** được xử lý tự động
- **Không cần hiểu** các bước mapping phức tạp
- **File output** sẽ có format chuẩn với 17 columns (A-Q)

Nếu file input đáp ứng checklist trên, hệ thống sẽ xử lý thành công 100%.