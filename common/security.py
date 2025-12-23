"""
Security utilities for TSS Converter
Provides file validation, sanitization, and security checks.
"""

import os
import mimetypes
import hashlib
import logging
from pathlib import Path
from typing import Tuple, Optional, List, Dict, Any
import re
import io

# Safe imports with fallback handling
try:
    import tempfile
    HAS_TEMPFILE = True
except ImportError:
    HAS_TEMPFILE = False
    tempfile = None
    logger.warning("tempfile module not available, using io.BytesIO fallback")

try:
    import zipfile
    HAS_ZIPFILE = True
except ImportError:
    HAS_ZIPFILE = False
    zipfile = None
    logger.warning("zipfile module not available, ZIP validation disabled")

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
    """Comprehensive file validation and security checks with graceful fallbacks"""
    
    def __init__(self, max_size: int = None, strict_mode: bool = True, enable_fallbacks: bool = True):
        self.max_size = max_size or MAX_FILE_SIZES['default']
        self.strict_mode = strict_mode
        self.enable_fallbacks = enable_fallbacks
        self.validation_warnings = []
    
    def validate_file(self, file_data: bytes, filename: str) -> Tuple[bool, Optional[str]]:
        """
        Comprehensive file validation with graceful fallbacks
        
        Returns:
            (is_valid, error_message)
        """
        self.validation_warnings = []
        validation_score = 0
        max_score = 6
        
        try:
            # 1. File size check (critical)
            if not self._check_file_size(file_data):
                if self.strict_mode:
                    return False, f"File size exceeds {self.max_size / (1024*1024):.1f}MB limit"
                else:
                    self.validation_warnings.append(f"Warning: Large file size {len(file_data) / (1024*1024):.1f}MB")
            else:
                validation_score += 1
            
            # 2. Filename security check (important)
            if not self._check_filename_security(filename):
                if self.strict_mode:
                    return False, "Filename contains potentially dangerous characters or patterns"
                else:
                    self.validation_warnings.append("Warning: Filename has security concerns")
            else:
                validation_score += 1
            
            # 3. File signature validation (important, with fallback)
            if not self._check_file_signature_with_fallback(file_data):
                if self.strict_mode:
                    return False, "File signature does not match Excel format"
                else:
                    self.validation_warnings.append("Warning: File signature validation failed")
            else:
                validation_score += 1
            
            # 4. MIME type validation (optional with fallback)
            if not self._check_mime_type_with_fallback(file_data, filename):
                if self.strict_mode:
                    return False, "File MIME type is not supported"
                else:
                    self.validation_warnings.append("Warning: MIME type validation failed")
            else:
                validation_score += 1
            
            # 5. Excel structure validation (important, with fallback)
            if not self._check_excel_structure_with_fallback(file_data):
                if self.strict_mode:
                    return False, "File does not contain valid Excel structure"
                else:
                    self.validation_warnings.append("Warning: Excel structure validation failed")
            else:
                validation_score += 1
            
            # 6. Malicious content scan (optional)
            if not self._scan_malicious_content_safe(file_data):
                if self.strict_mode:
                    return False, "File contains potentially malicious content"
                else:
                    self.validation_warnings.append("Warning: Malicious content scan detected issues")
            else:
                validation_score += 1
            
            # In lenient mode, require at least 50% validation success for basic files
            if not self.strict_mode and validation_score >= max_score // 2:
                if self.validation_warnings:
                    logger.warning(f"File validation passed with {len(self.validation_warnings)} warnings: {'; '.join(self.validation_warnings)}")
                return True, None
            elif not self.strict_mode:
                return False, f"Too many validation failures (score: {validation_score}/{max_score})"
            
            return True, None
            
        except Exception as e:
            logger.error(f"File validation error: {e}")
            if self.enable_fallbacks:
                return self._basic_file_validation(file_data, filename)
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
    
    def _check_file_signature_with_fallback(self, file_data: bytes) -> bool:
        """Check file magic bytes signature with fallback validation"""
        if len(file_data) < 4:
            logger.debug("File too small for signature check")
            return False
        
        try:
            # Primary check: Excel signatures
            file_header = file_data[:4]
            if any(file_header.startswith(sig) for sig in EXCEL_SIGNATURES):
                return True
            
            # Fallback check: Look for ZIP signature (XLSX is ZIP-based)
            zip_signatures = [
                b'\x50\x4B\x03\x04',  # Standard ZIP
                b'\x50\x4B\x05\x06',  # Empty ZIP
                b'\x50\x4B\x07\x08',  # Spanned ZIP
            ]
            
            if any(file_header.startswith(sig) for sig in zip_signatures):
                logger.debug("File has valid ZIP signature (XLSX is ZIP-based)")
                return True
                
            # Extended check: Look deeper into file for Office signatures
            if len(file_data) >= 512:
                extended_data = file_data[:512]
                # Check for Office Open XML signatures
                office_markers = [b'[Content_Types].xml', b'_rels/', b'xl/']
                if any(marker in extended_data for marker in office_markers):
                    logger.debug("Found Office Open XML markers in file")
                    return True
            
            logger.debug(f"File signature not recognized. Header: {file_header.hex()}")
            return False
            
        except Exception as e:
            logger.warning(f"File signature check error: {e}")
            return False
    
    def _check_file_signature(self, file_data: bytes) -> bool:
        """Legacy method - redirect to new method"""
        return self._check_file_signature_with_fallback(file_data)
    
    def _check_mime_type_with_fallback(self, file_data: bytes, filename: str) -> bool:
        """Check MIME type using multiple methods with fallbacks"""
        try:
            # Method 1: Use python-magic if available
            if HAS_MAGIC:
                try:
                    mime_type = magic.from_buffer(file_data, mime=True)
                    if mime_type in ALLOWED_MIME_TYPES:
                        return True
                except Exception as e:
                    logger.warning(f"python-magic error: {e}")
            
            # Method 2: Use mimetypes module
            try:
                mime_type, _ = mimetypes.guess_type(filename)
                if mime_type in ALLOWED_MIME_TYPES:
                    return True
            except Exception as e:
                logger.warning(f"mimetypes.guess_type error: {e}")
            
            # Method 3: Check ZIP structure (XLSX is ZIP-based) with safe fallback
            if HAS_ZIPFILE:
                try:
                    # Use BytesIO instead of tempfile for compatibility
                    file_buffer = io.BytesIO(file_data)
                    with zipfile.ZipFile(file_buffer) as zf:
                        # Check for Excel-specific files in the ZIP
                        excel_indicators = ['xl/workbook.xml', 'xl/styles.xml', '_rels/.rels']
                        return any(indicator in zf.namelist() for indicator in excel_indicators)
                except zipfile.BadZipFile:
                    logger.debug("File is not a valid ZIP file")
                except Exception as e:
                    logger.warning(f"ZIP structure check error: {e}")
            
            # Method 4: Basic filename check as last resort
            if filename.lower().endswith('.xlsx'):
                logger.debug("Fallback: File extension suggests Excel format")
                return True
                
        except Exception as e:
            logger.error(f"MIME type check failed: {e}")
            
        return False
        
    def _check_mime_type(self, file_data: bytes, filename: str) -> bool:
        """Legacy method - redirect to new method"""
        return self._check_mime_type_with_fallback(file_data, filename)
    
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
    
    def _check_excel_structure_with_fallback(self, file_data: bytes) -> bool:
        """Validate Excel file internal structure with fallbacks"""
        if not HAS_ZIPFILE:
            logger.warning("zipfile module not available, using basic structure check")
            return self._basic_excel_check(file_data)
            
        try:
            # Use BytesIO instead of tempfile for compatibility
            file_buffer = io.BytesIO(file_data)
            with zipfile.ZipFile(file_buffer) as zf:
                # Required Excel files (relaxed requirements for compatibility)
                critical_files = ['xl/workbook.xml']
                optional_files = ['_rels/.rels', '[Content_Types].xml', 'xl/styles.xml']
                
                file_list = zf.namelist()
                
                # Check for critical files
                critical_found = 0
                for critical_file in critical_files:
                    if critical_file in file_list:
                        critical_found += 1
                
                # Check for optional files
                optional_found = 0
                for optional_file in optional_files:
                    if optional_file in file_list:
                        optional_found += 1
                
                # Flexible validation: need at least one critical file
                if critical_found == 0 and self.strict_mode:
                    logger.warning(f"No critical Excel files found. Available: {file_list[:5]}...")
                    return False
                elif critical_found == 0:
                    self.validation_warnings.append("Warning: No critical Excel files found, but continuing")
                
                # Check for suspicious files
                suspicious_patterns = [
                    r'\.exe$', r'\.bat$', r'\.cmd$', r'\.scr$',
                    r'\.dll$', r'\.jar$', r'\.js$', r'\.vbs$'
                ]
                
                suspicious_found = []
                for file_path in file_list:
                    for pattern in suspicious_patterns:
                        if re.search(pattern, file_path, re.IGNORECASE):
                            suspicious_found.append(file_path)
                
                if suspicious_found:
                    if self.strict_mode:
                        logger.warning(f"Suspicious files found in Excel: {suspicious_found}")
                        return False
                    else:
                        self.validation_warnings.append(f"Warning: Suspicious files found: {suspicious_found}")
                
                # Success criteria: critical files found, no major issues
                return critical_found > 0 or optional_found >= 2
                
        except zipfile.BadZipFile:
            logger.debug("Not a valid ZIP file, trying fallback validation")
            if self.enable_fallbacks:
                return self._basic_excel_check(file_data)
            return False
        except Exception as e:
            logger.error(f"Excel structure validation failed: {e}")
            if self.enable_fallbacks:
                return self._basic_excel_check(file_data)
            return False
            
    def _basic_excel_check(self, file_data: bytes) -> bool:
        """Basic Excel format check when advanced validation fails"""
        try:
            # Check if file starts with ZIP signature (XLSX is ZIP-based)
            if len(file_data) < 4:
                return False
                
            zip_signatures = [b'\x50\x4B\x03\x04', b'\x50\x4B\x05\x06', b'\x50\x4B\x07\x08']
            has_zip_signature = any(file_data.startswith(sig) for sig in zip_signatures)
            
            # Look for Excel-specific content markers in raw data
            excel_markers = [
                b'xl/workbook.xml',
                b'xl/worksheets',
                b'xl/styles.xml',
                b'_rels',
                b'[Content_Types].xml'
            ]
            
            excel_markers_found = sum(1 for marker in excel_markers if marker in file_data)
            
            # Basic validation: ZIP signature + some Excel markers
            return has_zip_signature and excel_markers_found >= 2
            
        except Exception as e:
            logger.warning(f"Basic Excel check failed: {e}")
            return False
    
    def _scan_malicious_content_safe(self, file_data: bytes) -> bool:
        """Safe malicious content scanning with fallbacks"""
        try:
            # Check file size again (prevent zip bombs)
            if len(file_data) > self.max_size:
                return False
            
            # Check for zip bombs (high compression ratio) with safe handling
            if HAS_ZIPFILE:
                try:
                    file_buffer = io.BytesIO(file_data)
                    with zipfile.ZipFile(file_buffer) as zf:
                        total_compressed = sum(info.file_size for info in zf.infolist())
                        total_uncompressed = len(file_data)
                        
                        if total_uncompressed > 0:
                            compression_ratio = total_compressed / total_uncompressed
                            if compression_ratio > 100:  # Suspiciously high compression
                                logger.warning(f"Suspicious compression ratio: {compression_ratio}")
                                if self.strict_mode:
                                    return False
                                else:
                                    self.validation_warnings.append(f"High compression ratio: {compression_ratio}")
                        
                        # Check for too many files (zip bomb indicator)
                        if len(zf.infolist()) > 1000:
                            logger.warning(f"Too many files in archive: {len(zf.infolist())}")
                            if self.strict_mode:
                                return False
                            else:
                                self.validation_warnings.append(f"Many files in archive: {len(zf.infolist())}")
                                
                except zipfile.BadZipFile:
                    logger.debug("Cannot analyze ZIP structure for malicious content")
                except Exception as e:
                    logger.warning(f"ZIP analysis error: {e}")
            
            # Check for suspicious byte patterns (basic scan)
            try:
                suspicious_bytes = [
                    b'javascript:', b'vbscript:', b'data:text/html',
                    b'<script', b'</script>', b'eval(',
                    b'document.write', b'innerHTML'
                ]
                
                # Only scan first 1MB to avoid performance issues
                scan_data = file_data[:1024*1024].lower()
                suspicious_found = []
                
                for suspicious in suspicious_bytes:
                    if suspicious in scan_data:
                        suspicious_found.append(suspicious.decode('utf-8', errors='ignore'))
                
                if suspicious_found:
                    if self.strict_mode:
                        logger.warning(f"Suspicious content patterns found: {suspicious_found}")
                        return False
                    else:
                        self.validation_warnings.append(f"Suspicious patterns: {suspicious_found}")
            
            except Exception as e:
                logger.warning(f"Content pattern scan error: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Malicious content scan failed: {e}")
            # In lenient mode, continue even if scan fails
            return not self.strict_mode
    
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
    
    def _basic_file_validation(self, file_data: bytes, filename: str) -> Tuple[bool, Optional[str]]:
        """Basic file validation as ultimate fallback"""
        try:
            # Very basic checks when all else fails
            if len(file_data) == 0:
                return False, "Empty file"
                
            if len(file_data) > self.max_size * 2:  # Allow 2x size in emergency fallback
                return False, "File too large even for fallback validation"
                
            if not filename.lower().endswith('.xlsx'):
                return False, "File extension is not .xlsx"
                
            # Check if file starts with printable content or binary data
            sample = file_data[:100]
            if all(b < 32 or b > 126 for b in sample if b != 10 and b != 13):  # Mostly binary
                logger.info("File appears to be binary (good for Excel)")
                return True, "Basic validation passed (fallback mode)"
            
            return False, "File validation failed - all methods exhausted"
            
        except Exception as e:
            logger.error(f"Basic validation failed: {e}")
            return False, f"Basic validation error: {str(e)}"

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

# Security configuration with enhanced options
SECURITY_CONFIG = {
    'max_file_size_mb': 100,
    'allowed_extensions': ['.xlsx'],
    'enable_signature_validation': True,
    'enable_structure_validation': True,
    'enable_malicious_scan': True,
    'log_security_events': True,
    'strict_mode': False,  # Default to lenient for better compatibility
    'enable_fallbacks': True,
    'validation_timeout': 30,  # seconds
    'debug_validation': False
}

def get_security_config() -> Dict[str, Any]:
    """Get security configuration"""
    return SECURITY_CONFIG.copy()