"""
Custom exceptions for Excel Template Converter
Provides specific exception types for better error handling and debugging.
"""

from typing import Optional, Dict, Any, List


class TSConverterError(Exception):
    """Base exception for all TSS Converter errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, 
                 context: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.context = context or {}
        super().__init__(message)
    
    def __str__(self) -> str:
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class ValidationError(TSConverterError):
    """Raised when input validation fails."""
    pass


class FileFormatError(ValidationError):
    """Raised when file format is invalid or unsupported."""
    
    def __init__(self, file_path: str, expected_format: str, 
                 actual_format: Optional[str] = None):
        self.file_path = file_path
        self.expected_format = expected_format
        self.actual_format = actual_format
        
        message = f"Invalid file format for '{file_path}'. Expected: {expected_format}"
        if actual_format:
            message += f", got: {actual_format}"
            
        super().__init__(
            message=message,
            error_code="FILE_FORMAT_ERROR",
            context={
                "file_path": file_path,
                "expected_format": expected_format,
                "actual_format": actual_format
            }
        )


class WorksheetNotFoundError(ValidationError):
    """Raised when required worksheet is not found."""
    
    def __init__(self, worksheet_name: str, available_sheets: List[str]):
        self.worksheet_name = worksheet_name
        self.available_sheets = available_sheets
        
        message = f"Worksheet '{worksheet_name}' not found. Available sheets: {', '.join(available_sheets)}"
        super().__init__(
            message=message,
            error_code="WORKSHEET_NOT_FOUND",
            context={
                "worksheet_name": worksheet_name,
                "available_sheets": available_sheets
            }
        )


class DataIntegrityError(TSConverterError):
    """Raised when data integrity checks fail."""
    pass


class InsufficientDataError(DataIntegrityError):
    """Raised when there's not enough data to process."""
    
    def __init__(self, data_type: str, required_count: int, actual_count: int):
        self.data_type = data_type
        self.required_count = required_count
        self.actual_count = actual_count
        
        message = f"Insufficient {data_type}. Required: {required_count}, found: {actual_count}"
        super().__init__(
            message=message,
            error_code="INSUFFICIENT_DATA",
            context={
                "data_type": data_type,
                "required_count": required_count,
                "actual_count": actual_count
            }
        )


class ColumnMissingError(DataIntegrityError):
    """Raised when required columns are missing."""
    
    def __init__(self, missing_columns: List[str], worksheet_name: Optional[str] = None):
        self.missing_columns = missing_columns
        self.worksheet_name = worksheet_name
        
        message = f"Missing required columns: {', '.join(missing_columns)}"
        if worksheet_name:
            message += f" in worksheet '{worksheet_name}'"
            
        super().__init__(
            message=message,
            error_code="COLUMN_MISSING",
            context={
                "missing_columns": missing_columns,
                "worksheet_name": worksheet_name
            }
        )


class HeaderNotFoundError(DataIntegrityError):
    """Raised when expected headers are not found."""
    
    def __init__(self, header_name: str, search_area: Optional[str] = None):
        self.header_name = header_name
        self.search_area = search_area
        
        message = f"Header '{header_name}' not found"
        if search_area:
            message += f" in {search_area}"
            
        super().__init__(
            message=message,
            error_code="HEADER_NOT_FOUND",
            context={
                "header_name": header_name,
                "search_area": search_area
            }
        )


class ProcessingError(TSConverterError):
    """Raised during data processing operations."""
    pass


class FileAccessError(ProcessingError):
    """Raised when file access fails."""
    
    def __init__(self, file_path: str, operation: str, reason: Optional[str] = None):
        self.file_path = file_path
        self.operation = operation
        self.reason = reason
        
        message = f"Cannot {operation} file '{file_path}'"
        if reason:
            message += f": {reason}"
            
        super().__init__(
            message=message,
            error_code="FILE_ACCESS_ERROR",
            context={
                "file_path": file_path,
                "operation": operation,
                "reason": reason
            }
        )


class ConfigurationError(TSConverterError):
    """Raised when configuration is invalid."""
    
    def __init__(self, config_key: str, issue: str):
        self.config_key = config_key
        self.issue = issue
        
        message = f"Configuration error for '{config_key}': {issue}"
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            context={
                "config_key": config_key,
                "issue": issue
            }
        )


class DependencyMissingError(TSConverterError):
    """Raised when required dependencies are missing."""
    
    def __init__(self, step_name: str, dependency: str):
        self.step_name = step_name
        self.dependency = dependency
        
        message = f"Step '{step_name}' requires '{dependency}' which is missing or incomplete"
        super().__init__(
            message=message,
            error_code="DEPENDENCY_MISSING",
            context={
                "step_name": step_name,
                "dependency": dependency
            }
        )