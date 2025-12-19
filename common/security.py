"""
Security utilities for TSS Converter
Provides file validation, sanitization, and security checks.
"""

import os
import mimetypes
import hashlib
import tempfile
import zipfile
import logging
from pathlib import Path
from typing import Tuple, Optional, List, Dict, Any
import re
try:
    import magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False

logger = logging.getLogger(__name__)

# Excel file signatures (magic bytes)
EXCEL_SIGNATURES = [
    b'\x50\x4B\x03\x04',  # XLSX (ZIP-based)
    b'\x50\x4B\x05\x06',  # XLSX (ZIP-based, empty file)
    b'\x50\x4B\x07\x08',  # XLSX (ZIP-based, spanned)
]

# Maximum file sizes (in bytes)
MAX_FILE_SIZES = {
    'xlsx': 100 * 1024 * 1024,  # 100MB for Excel files
    'default': 50 * 1024 * 1024   # 50MB for other files
}

# Allowed MIME types
ALLOWED_MIME_TYPES = [
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-excel',
    'application/zip'  # XLSX files are ZIP-based
]

# Dangerous file patterns to reject
DANGEROUS_PATTERNS = [
    r'\.exe$', r'\.bat$', r'\.cmd$', r'\.scr$', r'\.pif$',
    r'\.com$', r'\.dll$', r'\.jar$', r'\.js$', r'\.vbs$',
    r'\.ps1$', r'\.sh$', r'\.php$', r'\.asp$', r'\.jsp$'
]

class SecurityError(Exception):
    """Raised when security validation fails"""
    pass

class FileValidator:
    """Comprehensive file validation and security checks"""
    
    def __init__(self, max_size: int = None):
        self.max_size = max_size or MAX_FILE_SIZES['default']
    
    def validate_file(self, file_data: bytes, filename: str) -> Tuple[bool, Optional[str]]:
        """
        Comprehensive file validation
        
        Returns:
            (is_valid, error_message)
        """
        try:
            # 1. File size check
            if not self._check_file_size(file_data):
                return False, f"File size exceeds {self.max_size / (1024*1024):.1f}MB limit"
            
            # 2. Filename security check
            if not self._check_filename_security(filename):
                return False, "Filename contains potentially dangerous characters or patterns"
            
            # 3. File signature validation
            if not self._check_file_signature(file_data):
                return False, "File signature does not match Excel format"
            
            # 4. MIME type validation
            if not self._check_mime_type(file_data, filename):
                return False, "File MIME type is not supported"
            
            # 5. Excel structure validation
            if not self._check_excel_structure(file_data):
                return False, "File does not contain valid Excel structure"
            
            # 6. Malicious content scan
            if not self._scan_malicious_content(file_data):
                return False, "File contains potentially malicious content"
            
            return True, None
            
        except Exception as e:
            logger.error(f"File validation error: {e}")
            return False, f"Validation error: {str(e)}"
    
    def _check_file_size(self, file_data: bytes) -> bool:
        """Check if file size is within allowed limits"""
        return len(file_data) <= self.max_size
    
    def _check_filename_security(self, filename: str) -> bool:
        """Check filename for security issues"""
        # Sanitize filename
        filename = os.path.basename(filename)  # Remove path components
        
        # Check for dangerous patterns
        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, filename, re.IGNORECASE):
                return False
        
        # Check for path traversal attempts
        dangerous_chars = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in dangerous_chars:
            if char in filename:
                return False
        
        # Must have .xlsx extension
        if not filename.lower().endswith('.xlsx'):
            return False
        
        return True
    
    def _check_file_signature(self, file_data: bytes) -> bool:
        """Check file magic bytes signature"""
        if len(file_data) < 4:
            return False
        
        # Check for Excel signatures
        file_header = file_data[:4]
        return any(file_header.startswith(sig) for sig in EXCEL_SIGNATURES)
    
    def _check_mime_type(self, file_data: bytes, filename: str) -> bool:
        """Check MIME type using multiple methods"""
        try:
            # Method 1: Use python-magic if available
            if HAS_MAGIC:
                try:
                    mime_type = magic.from_buffer(file_data, mime=True)
                    if mime_type in ALLOWED_MIME_TYPES:
                        return True
                except Exception as e:
                    logger.warning(f"python-magic error: {e}")
            else:
                logger.debug("python-magic not available, using alternative MIME detection")
            
            # Method 2: Use mimetypes module
            mime_type, _ = mimetypes.guess_type(filename)
            if mime_type in ALLOWED_MIME_TYPES:
                return True
            
            # Method 3: Check ZIP structure (XLSX is ZIP-based)
            try:
                with zipfile.ZipFile(tempfile.BytesIO(file_data)) as zf:
                    # Check for Excel-specific files in the ZIP
                    excel_indicators = ['xl/workbook.xml', 'xl/styles.xml', '_rels/.rels']
                    return any(indicator in zf.namelist() for indicator in excel_indicators)
            except zipfile.BadZipFile:
                return False
                
        except Exception as e:
            logger.error(f"MIME type check failed: {e}")
            return False
        
        return False
    
    def _check_excel_structure(self, file_data: bytes) -> bool:
        """Validate Excel file internal structure"""
        try:
            with zipfile.ZipFile(tempfile.BytesIO(file_data)) as zf:
                # Required Excel files
                required_files = [
                    'xl/workbook.xml',
                    '_rels/.rels',
                    '[Content_Types].xml'
                ]
                
                file_list = zf.namelist()
                
                # Check for required files
                for required_file in required_files:
                    if required_file not in file_list:
                        logger.warning(f"Missing required Excel file: {required_file}")
                        return False
                
                # Check for suspicious files
                suspicious_patterns = [
                    r'\.exe$', r'\.bat$', r'\.cmd$', r'\.scr$',
                    r'\.dll$', r'\.jar$', r'\.js$', r'\.vbs$'
                ]
                
                for file_path in file_list:
                    for pattern in suspicious_patterns:
                        if re.search(pattern, file_path, re.IGNORECASE):
                            logger.warning(f"Suspicious file found in Excel: {file_path}")
                            return False
                
                return True
                
        except zipfile.BadZipFile:
            logger.error("Invalid ZIP structure in Excel file")
            return False
        except Exception as e:
            logger.error(f"Excel structure validation failed: {e}")
            return False
    
    def _scan_malicious_content(self, file_data: bytes) -> bool:
        """Basic malicious content scanning"""
        try:
            # Check file size again (prevent zip bombs)
            if len(file_data) > self.max_size:
                return False
            
            # Check for zip bombs (high compression ratio)
            try:
                with zipfile.ZipFile(tempfile.BytesIO(file_data)) as zf:
                    total_compressed = sum(info.file_size for info in zf.infolist())
                    total_uncompressed = len(file_data)
                    
                    if total_uncompressed > 0:
                        compression_ratio = total_compressed / total_uncompressed
                        if compression_ratio > 100:  # Suspiciously high compression
                            logger.warning(f"Suspicious compression ratio: {compression_ratio}")
                            return False
                    
                    # Check for too many files (zip bomb indicator)
                    if len(zf.infolist()) > 1000:
                        logger.warning(f"Too many files in archive: {len(zf.infolist())}")
                        return False
                        
            except zipfile.BadZipFile:
                return False
            
            # Check for suspicious byte patterns
            suspicious_bytes = [
                b'javascript:', b'vbscript:', b'data:text/html',
                b'<script', b'</script>', b'eval(',
                b'document.write', b'innerHTML'
            ]
            
            file_lower = file_data.lower()
            for suspicious in suspicious_bytes:
                if suspicious in file_lower:
                    logger.warning(f"Suspicious content pattern found")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Malicious content scan failed: {e}")
            return False

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent security issues
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove path components
    filename = os.path.basename(filename)
    
    # Remove dangerous characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove control characters
    filename = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', filename)
    
    # Limit length
    name, ext = os.path.splitext(filename)
    if len(name) > 100:
        name = name[:100]
    filename = name + ext
    
    # Ensure .xlsx extension
    if not filename.lower().endswith('.xlsx'):
        filename += '.xlsx'
    
    return filename

def generate_secure_filename(prefix: str = "upload") -> str:
    """
    Generate a secure filename with timestamp and random component
    
    Args:
        prefix: Prefix for the filename
        
    Returns:
        Secure filename
    """
    import time
    import random
    import string
    
    timestamp = int(time.time())
    random_part = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}_{timestamp}_{random_part}.xlsx"

def validate_path_security(file_path: Path, allowed_base: Path) -> bool:
    """
    Validate that a file path is secure and within allowed directory
    
    Args:
        file_path: Path to validate
        allowed_base: Base directory that should contain the file
        
    Returns:
        True if path is secure
    """
    try:
        # Resolve all symlinks and relative components
        resolved_path = file_path.resolve()
        resolved_base = allowed_base.resolve()
        
        # Check if path is within allowed base
        try:
            resolved_path.relative_to(resolved_base)
            return True
        except ValueError:
            # Path is outside allowed base
            return False
            
    except (OSError, ValueError) as e:
        logger.error(f"Path validation error: {e}")
        return False

def calculate_file_hash(file_data: bytes, algorithm: str = 'sha256') -> str:
    """
    Calculate hash of file data for integrity verification
    
    Args:
        file_data: File content as bytes
        algorithm: Hash algorithm to use
        
    Returns:
        Hex digest of file hash
    """
    hash_obj = hashlib.new(algorithm)
    hash_obj.update(file_data)
    return hash_obj.hexdigest()

# Security configuration
SECURITY_CONFIG = {
    'max_file_size_mb': 100,
    'allowed_extensions': ['.xlsx'],
    'enable_signature_validation': True,
    'enable_structure_validation': True,
    'enable_malicious_scan': True,
    'log_security_events': True
}

def get_security_config() -> Dict[str, Any]:
    """Get security configuration"""
    return SECURITY_CONFIG.copy()