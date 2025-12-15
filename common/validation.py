"""
File validation utilities for Excel Template Converter
Provides robust validation for file formats, structure, and data integrity.
"""

import os
import hashlib
import re
from pathlib import Path
from typing import Union, List, Optional, Dict, Any
import logging

try:
    import openpyxl
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False
    openpyxl = None

from .exceptions import (
    FileFormatError, FileAccessError, WorksheetNotFoundError, 
    ColumnMissingError, HeaderNotFoundError, InsufficientDataError,
    ValidationError
)

logger = logging.getLogger(__name__)


class FileValidator:
    """
    Enhanced file validation utilities for Excel files
    Validates format, accessibility, content security, and basic structure
    """
    
    SUPPORTED_EXTENSIONS = ['.xlsx']
    
    # Excel file signatures (magic bytes)
    EXCEL_SIGNATURES = [
        b'PK\x03\x04',  # ZIP-based format (xlsx)
        b'\xD0\xCF\x11\xE0',  # OLE2 format (older Excel)
    ]
    
    # Maximum file size (50MB)
    MAX_FILE_SIZE = 50 * 1024 * 1024
    
    # Maximum number of worksheets
    MAX_WORKSHEETS = 100
    
    # Suspicious patterns to detect malicious content
    SUSPICIOUS_PATTERNS = [
        rb'<script.*?>',
        rb'javascript:',
        rb'vbscript:',
        rb'data:text/html',
        rb'ActiveXObject',
        rb'Shell\.Application',
        rb'WScript\.Shell',
        rb'eval\(',
        rb'document\.write',
    ]
    
    @classmethod
    def validate_file_exists(cls, file_path: Union[str, Path]) -> Path:
        """
        Validate that file exists and is accessible
        
        Args:
            file_path: Path to file
            
        Returns:
            Path object if valid
            
        Raises:
            FileAccessError: If file doesn't exist or isn't accessible
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileAccessError(
                file_path=str(path),
                operation="read",
                reason="File does not exist"
            )
        
        if not path.is_file():
            raise FileAccessError(
                file_path=str(path),
                operation="read", 
                reason="Path is not a file"
            )
        
        if not os.access(path, os.R_OK):
            raise FileAccessError(
                file_path=str(path),
                operation="read",
                reason="File is not readable"
            )
        
        return path
    
    @classmethod
    def validate_file_security(cls, file_path: Union[str, Path]) -> Path:
        """
        Enhanced security validation for uploaded files
        
        Args:
            file_path: Path to file
            
        Returns:
            Path object if secure
            
        Raises:
            FileFormatError: If file is potentially malicious
        """
        path = cls.validate_file_exists(file_path)
        
        # Check file size
        file_size = path.stat().st_size
        if file_size > cls.MAX_FILE_SIZE:
            raise FileFormatError(
                file_path=str(path),
                expected_format=f"File size <= {cls.MAX_FILE_SIZE // (1024*1024)}MB",
                actual_format=f"File size: {file_size // (1024*1024)}MB"
            )
        
        # Check if file is empty
        if file_size == 0:
            raise FileFormatError(
                file_path=str(path),
                expected_format="Non-empty file",
                actual_format="Empty file"
            )
        
        # Validate file signature
        cls._validate_file_signature(path)
        
        # Scan for malicious content
        cls._scan_malicious_content(path)
        
        # Validate filename
        cls._validate_filename(path.name)
        
        return path
    
    @classmethod
    def _validate_file_signature(cls, file_path: Path) -> None:
        """Validate file magic bytes"""
        try:
            with open(file_path, 'rb') as f:
                header = f.read(8)
                
            if not header:
                raise FileFormatError(
                    file_path=str(file_path),
                    expected_format="Valid file header",
                    actual_format="Empty file"
                )
            
            # Check if header matches Excel signatures
            valid_signature = any(header.startswith(sig) for sig in cls.EXCEL_SIGNATURES)
            if not valid_signature:
                raise FileFormatError(
                    file_path=str(file_path),
                    expected_format="Valid Excel file signature",
                    actual_format=f"Invalid signature: {header[:4].hex()}"
                )
                
        except IOError as e:
            raise FileFormatError(
                file_path=str(file_path),
                expected_format="Readable file",
                actual_format=f"IO Error: {str(e)}"
            )
    
    @classmethod
    def _scan_malicious_content(cls, file_path: Path) -> None:
        """Scan file content for suspicious patterns"""
        try:
            # Read file in chunks to handle large files
            chunk_size = 8192
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                        
                    # Check for suspicious patterns
                    for pattern in cls.SUSPICIOUS_PATTERNS:
                        if re.search(pattern, chunk, re.IGNORECASE):
                            logger.warning(f"Suspicious pattern detected in {file_path}: {pattern}")
                            raise FileFormatError(
                                file_path=str(file_path),
                                expected_format="Clean file content",
                                actual_format="Potentially malicious content detected"
                            )
                            
        except IOError as e:
            logger.error(f"Error scanning file {file_path}: {e}")
            raise FileFormatError(
                file_path=str(file_path),
                expected_format="Scannable file",
                actual_format=f"Scan error: {str(e)}"
            )
    
    @classmethod
    def _validate_filename(cls, filename: str) -> None:
        """Validate filename for security"""
        # Check for path traversal attempts
        if '..' in filename or '/' in filename or '\\' in filename:
            raise FileFormatError(
                file_path=filename,
                expected_format="Safe filename",
                actual_format="Path traversal attempt"
            )
        
        # Check for suspicious characters
        suspicious_chars = ['<', '>', ':', '"', '|', '?', '*', '\0']
        if any(char in filename for char in suspicious_chars):
            raise FileFormatError(
                file_path=filename,
                expected_format="Clean filename",
                actual_format="Suspicious characters in filename"
            )
        
        # Check filename length
        if len(filename) > 255:
            raise FileFormatError(
                file_path=filename,
                expected_format="Filename <= 255 chars",
                actual_format=f"Filename: {len(filename)} chars"
            )
    
    @classmethod
    def validate_file_format(cls, file_path: Union[str, Path]) -> Path:
        """
        Comprehensive file validation including security checks
        
        Args:
            file_path: Path to file
            
        Returns:
            Path object if valid
            
        Raises:
            FileFormatError: If format is not supported or file is insecure
        """
        # First run security validation (includes file existence check)
        path = cls.validate_file_security(file_path)
        
        # Check file extension
        if path.suffix.lower() not in cls.SUPPORTED_EXTENSIONS:
            raise FileFormatError(
                file_path=str(path),
                expected_format=".xlsx",
                actual_format=path.suffix
            )
        
        # Validate Excel structure integrity
        cls._validate_excel_integrity(path)
        
        return path
    
    @classmethod
    def _validate_excel_integrity(cls, file_path: Path) -> None:
        """Validate Excel file structure and integrity"""
        if not OPENPYXL_AVAILABLE:
            logger.warning("openpyxl not available, skipping Excel structure validation")
            return
            
        try:
            # Attempt to open and validate Excel structure
            wb = openpyxl.load_workbook(str(file_path), read_only=True)
            
            # Check number of worksheets
            if len(wb.worksheets) > cls.MAX_WORKSHEETS:
                wb.close()
                raise FileFormatError(
                    file_path=str(file_path),
                    expected_format=f"<= {cls.MAX_WORKSHEETS} worksheets",
                    actual_format=f"{len(wb.worksheets)} worksheets"
                )
            
            # Check if file has at least one worksheet
            if not wb.worksheets:
                wb.close()
                raise FileFormatError(
                    file_path=str(file_path),
                    expected_format="At least 1 worksheet",
                    actual_format="No worksheets found"
                )
            
            # Basic structure validation for each worksheet
            for ws in wb.worksheets:
                # Check worksheet size limits
                if ws.max_row > 100000:  # Reasonable limit
                    wb.close()
                    raise FileFormatError(
                        file_path=str(file_path),
                        expected_format="<= 100,000 rows per worksheet",
                        actual_format=f"Worksheet '{ws.title}' has {ws.max_row} rows"
                    )
                
                if ws.max_column > 100:  # Reasonable limit
                    wb.close()
                    raise FileFormatError(
                        file_path=str(file_path),
                        expected_format="<= 100 columns per worksheet",
                        actual_format=f"Worksheet '{ws.title}' has {ws.max_column} columns"
                    )
            
            wb.close()
            logger.debug(f"Excel integrity validation passed for {file_path}")
            
        except openpyxl.utils.exceptions.InvalidFileException as e:
            raise FileFormatError(
                file_path=str(file_path),
                expected_format="Valid Excel file structure",
                actual_format=f"Corrupted Excel file: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Error validating Excel integrity for {file_path}: {e}")
            raise FileFormatError(
                file_path=str(file_path),
                expected_format="Valid Excel file",
                actual_format=f"Validation error: {str(e)}"
            )
    
    @classmethod
    def validate_output_writable(cls, file_path: Union[str, Path]) -> Path:
        """
        Validate output file path is writable
        
        Args:
            file_path: Path to output file
            
        Returns:
            Path object if valid
            
        Raises:
            FileAccessError: If path is not writable
        """
        path = Path(file_path)
        
        # Check if parent directory exists and is writable
        parent = path.parent
        if not parent.exists():
            try:
                parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                raise FileAccessError(
                    file_path=str(path),
                    operation="write",
                    reason=f"Cannot create parent directory: {str(e)}"
                )
        
        if not os.access(parent, os.W_OK):
            raise FileAccessError(
                file_path=str(path),
                operation="write",
                reason="Parent directory is not writable"
            )
        
        # If file exists, check if it's writable
        if path.exists():
            if not os.access(path, os.W_OK):
                raise FileAccessError(
                    file_path=str(path),
                    operation="write",
                    reason="File exists but is not writable"
                )
        
        return path


class ExcelStructureValidator:
    """
    Validates Excel file structure and content
    """
    
    @classmethod
    def validate_worksheets_exist(cls, file_path: Union[str, Path], 
                                 required_sheets: Optional[List[str]] = None) -> List[str]:
        """
        Validate that required worksheets exist
        
        Args:
            file_path: Path to Excel file
            required_sheets: List of required sheet names (optional)
            
        Returns:
            List of available sheet names
            
        Raises:
            WorksheetNotFoundError: If required sheets are missing
        """
        path = FileValidator.validate_file_format(file_path)
        
        if not OPENPYXL_AVAILABLE:
            logger.warning("openpyxl not available, skipping worksheet validation")
            return []
        
        try:
            wb = openpyxl.load_workbook(str(path), read_only=True)
            available_sheets = wb.sheetnames
            wb.close()
        except Exception as e:
            raise FileAccessError(
                file_path=str(path),
                operation="read",
                reason=f"Failed to read worksheets: {str(e)}"
            )
        
        if required_sheets:
            missing_sheets = [sheet for sheet in required_sheets if sheet not in available_sheets]
            if missing_sheets:
                raise WorksheetNotFoundError(
                    worksheet_name=", ".join(missing_sheets),
                    available_sheets=available_sheets
                )
        
        return available_sheets
    
    @classmethod
    def validate_columns_exist(cls, file_path: Union[str, Path], 
                             required_columns: List[str],
                             worksheet_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate that required columns exist in worksheet
        
        Args:
            file_path: Path to Excel file
            required_columns: List of required column letters (e.g., ['A', 'B', 'C'])
            worksheet_name: Name of worksheet to check (if None, use active sheet)
            
        Returns:
            Dictionary with validation results
            
        Raises:
            ColumnMissingError: If required columns are missing
        """
        path = FileValidator.validate_file_format(file_path)
        
        if not OPENPYXL_AVAILABLE:
            logger.warning("openpyxl not available, skipping column validation")
            return {"worksheet_name": worksheet_name or "unknown", "available_columns": [], "max_column": 0, "required_columns": required_columns}
        
        try:
            wb = openpyxl.load_workbook(str(path), read_only=True)
            
            if worksheet_name:
                if worksheet_name not in wb.sheetnames:
                    raise WorksheetNotFoundError(worksheet_name, wb.sheetnames)
                ws = wb[worksheet_name]
            else:
                ws = wb.active
                worksheet_name = ws.title
            
            # Check if columns have data or headers
            max_col = ws.max_column
            available_columns = [openpyxl.utils.get_column_letter(i) for i in range(1, max_col + 1)]
            
            missing_columns = [col for col in required_columns if col not in available_columns]
            
            wb.close()
            
            if missing_columns:
                raise ColumnMissingError(
                    missing_columns=missing_columns,
                    worksheet_name=worksheet_name
                )
            
            return {
                "worksheet_name": worksheet_name,
                "available_columns": available_columns,
                "max_column": max_col,
                "required_columns": required_columns
            }
            
        except (ColumnMissingError, WorksheetNotFoundError):
            raise
        except Exception as e:
            raise FileAccessError(
                file_path=str(path),
                operation="read",
                reason=f"Failed to validate columns: {str(e)}"
            )
    
    @classmethod
    def validate_headers_exist(cls, file_path: Union[str, Path],
                              required_headers: List[str],
                              search_rows: int = 10,
                              worksheet_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate that required headers exist in worksheet
        
        Args:
            file_path: Path to Excel file
            required_headers: List of required header texts
            search_rows: Number of rows to search for headers
            worksheet_name: Name of worksheet to check
            
        Returns:
            Dictionary with found headers and their positions
            
        Raises:
            HeaderNotFoundError: If required headers are missing
        """
        path = FileValidator.validate_file_format(file_path)
        
        if not OPENPYXL_AVAILABLE:
            logger.warning("openpyxl not available, skipping header validation")
            return {"worksheet_name": worksheet_name or "unknown", "found_headers": {}, "search_rows": search_rows}
        
        try:
            wb = openpyxl.load_workbook(str(path), read_only=True)
            
            if worksheet_name:
                if worksheet_name not in wb.sheetnames:
                    raise WorksheetNotFoundError(worksheet_name, wb.sheetnames)
                ws = wb[worksheet_name]
            else:
                ws = wb.active
                worksheet_name = ws.title
            
            found_headers = {}
            missing_headers = []
            
            # Search for headers in first N rows
            for header in required_headers:
                found = False
                for row in range(1, min(search_rows + 1, ws.max_row + 1)):
                    for col in range(1, ws.max_column + 1):
                        cell_value = ws.cell(row, col).value
                        if cell_value and isinstance(cell_value, str):
                            if header.lower() in cell_value.lower():
                                found_headers[header] = {"row": row, "column": col, "value": cell_value}
                                found = True
                                break
                    if found:
                        break
                
                if not found:
                    missing_headers.append(header)
            
            wb.close()
            
            if missing_headers:
                search_area = f"first {search_rows} rows of '{worksheet_name}'"
                raise HeaderNotFoundError(
                    header_name=", ".join(missing_headers),
                    search_area=search_area
                )
            
            return {
                "worksheet_name": worksheet_name,
                "found_headers": found_headers,
                "search_rows": search_rows
            }
            
        except (HeaderNotFoundError, WorksheetNotFoundError):
            raise
        except Exception as e:
            raise FileAccessError(
                file_path=str(path),
                operation="read",
                reason=f"Failed to validate headers: {str(e)}"
            )
    
    @classmethod 
    def validate_data_sufficient(cls, file_path: Union[str, Path],
                                min_rows: int = 1,
                                worksheet_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate that worksheet has sufficient data
        
        Args:
            file_path: Path to Excel file
            min_rows: Minimum number of data rows required
            worksheet_name: Name of worksheet to check
            
        Returns:
            Dictionary with data statistics
            
        Raises:
            InsufficientDataError: If not enough data
        """
        path = FileValidator.validate_file_format(file_path)
        
        if not OPENPYXL_AVAILABLE:
            logger.warning("openpyxl not available, skipping data validation")
            return {"worksheet_name": worksheet_name or "unknown", "total_rows": 0, "total_columns": 0, "data_rows": 0, "min_required": min_rows}
        
        try:
            wb = openpyxl.load_workbook(str(path), read_only=True)
            
            if worksheet_name:
                if worksheet_name not in wb.sheetnames:
                    raise WorksheetNotFoundError(worksheet_name, wb.sheetnames)
                ws = wb[worksheet_name]
            else:
                ws = wb.active
                worksheet_name = ws.title
            
            max_row = ws.max_row
            max_col = ws.max_column
            
            # Count non-empty data rows (skip first few rows that might be headers)
            data_rows = 0
            for row in range(4, max_row + 1):  # Start from row 4 (common header location)
                has_data = False
                for col in range(1, max_col + 1):
                    cell_value = ws.cell(row, col).value
                    if cell_value is not None and str(cell_value).strip():
                        has_data = True
                        break
                if has_data:
                    data_rows += 1
            
            wb.close()
            
            if data_rows < min_rows:
                raise InsufficientDataError(
                    data_type="data rows",
                    required_count=min_rows,
                    actual_count=data_rows
                )
            
            return {
                "worksheet_name": worksheet_name,
                "total_rows": max_row,
                "total_columns": max_col,
                "data_rows": data_rows,
                "min_required": min_rows
            }
            
        except (InsufficientDataError, WorksheetNotFoundError):
            raise
        except Exception as e:
            raise FileAccessError(
                file_path=str(path),
                operation="read",
                reason=f"Failed to validate data: {str(e)}"
            )


def validate_step1_template(file_path: Union[str, Path]) -> bool:
    """
    Validate Step1 template structure
    
    Args:
        file_path: Path to Step1 template file
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If validation fails
    """
    try:
        # Basic file validation
        FileValidator.validate_file_format(file_path)
        
        # Check for required template structure
        expected_headers = ["Combination", "General Type Component", "Sub-Type Component"]
        
        ExcelStructureValidator.validate_headers_exist(
            file_path, 
            expected_headers, 
            search_rows=5
        )
        
        # Check minimum column count (17 columns A-Q)
        if OPENPYXL_AVAILABLE:
            ExcelStructureValidator.validate_columns_exist(
                file_path,
                [openpyxl.utils.get_column_letter(i) for i in range(1, 18)]  # A-Q
            )
        
        logger.info(f"Step1 template validation passed: {file_path}")
        return True
        
    except Exception as e:
        logger.error(f"Step1 template validation failed: {e}")
        raise ValidationError(f"Step1 template validation failed: {str(e)}")


def validate_step2_input(step1_file: Union[str, Path], source_file: Union[str, Path]) -> bool:
    """
    Validate Step2 inputs (Step1 template + source data file)
    
    Args:
        step1_file: Path to Step1 template
        source_file: Path to source data file
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If validation fails
    """
    try:
        # Validate Step1 template
        validate_step1_template(step1_file)
        
        # Validate source file
        FileValidator.validate_file_format(source_file)
        
        # Check source has data
        ExcelStructureValidator.validate_data_sufficient(source_file, min_rows=1)
        
        logger.info(f"Step2 input validation passed: {step1_file}, {source_file}")
        return True
        
    except Exception as e:
        logger.error(f"Step2 input validation failed: {e}")
        raise ValidationError(f"Step2 input validation failed: {str(e)}")


def validate_step3_input(step2_file: Union[str, Path]) -> bool:
    """
    Validate Step3 input (Step2 output file)
    
    Args:
        step2_file: Path to Step2 output file
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If validation fails
    """
    try:
        # Basic file validation
        FileValidator.validate_file_format(step2_file)
        
        # Check has article data in rows 1-2
        ExcelStructureValidator.validate_data_sufficient(step2_file, min_rows=1)
        
        logger.info(f"Step3 input validation passed: {step2_file}")
        return True
        
    except Exception as e:
        logger.error(f"Step3 input validation failed: {e}")
        raise ValidationError(f"Step3 input validation failed: {str(e)}")


def validate_step4_input(step3_file: Union[str, Path]) -> bool:
    """
    Validate Step4 input (Step3 output file)
    
    Args:
        step3_file: Path to Step3 output file
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If validation fails
    """
    try:
        # Basic file validation
        FileValidator.validate_file_format(step3_file)
        
        # Check required columns D, E, F exist
        ExcelStructureValidator.validate_columns_exist(step3_file, ['D', 'E', 'F'])
        
        # Check has sufficient data
        ExcelStructureValidator.validate_data_sufficient(step3_file, min_rows=3)
        
        logger.info(f"Step4 input validation passed: {step3_file}")
        return True
        
    except Exception as e:
        logger.error(f"Step4 input validation failed: {e}")
        raise ValidationError(f"Step4 input validation failed: {str(e)}")


def validate_step5_input(step4_file: Union[str, Path]) -> bool:
    """
    Validate Step5 input (Step4 output file)
    
    Args:
        step4_file: Path to Step4 output file
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If validation fails
    """
    try:
        # Basic file validation
        FileValidator.validate_file_format(step4_file)
        
        # Check required columns for filtering (H for NA, B,C,D,E,F,I,J for SD comparison)
        required_cols = ['B', 'C', 'D', 'E', 'F', 'H', 'I', 'J']
        ExcelStructureValidator.validate_columns_exist(step4_file, required_cols)
        
        # Check has sufficient data
        ExcelStructureValidator.validate_data_sufficient(step4_file, min_rows=3)
        
        logger.info(f"Step5 input validation passed: {step4_file}")
        return True
        
    except Exception as e:
        logger.error(f"Step5 input validation failed: {e}")
        raise ValidationError(f"Step5 input validation failed: {str(e)}")