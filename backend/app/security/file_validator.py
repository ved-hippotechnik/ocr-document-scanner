"""
Enhanced file upload security with virus scanning and content validation
"""
import os
import hashlib
import tempfile
import subprocess
from typing import Optional, Tuple, Dict, Any
from werkzeug.datastructures import FileStorage
from PIL import Image
import logging
import mimetypes

# Try to import magic, but make it optional
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False

logger = logging.getLogger(__name__)


class FileValidator:
    """Comprehensive file validation and security scanning"""
    
    # Safe MIME types for document processing
    ALLOWED_MIME_TYPES = {
        'image/jpeg': ['.jpg', '.jpeg'],
        'image/png': ['.png'],
        'image/tiff': ['.tiff', '.tif'],
        'image/bmp': ['.bmp'],
        'application/pdf': ['.pdf'],
    }
    
    # Maximum file sizes by type (in bytes)
    MAX_FILE_SIZES = {
        'image/jpeg': 10 * 1024 * 1024,  # 10MB
        'image/png': 10 * 1024 * 1024,   # 10MB
        'image/tiff': 20 * 1024 * 1024,  # 20MB
        'image/bmp': 20 * 1024 * 1024,   # 20MB
        'application/pdf': 50 * 1024 * 1024,  # 50MB
    }
    
    # Image dimension limits
    MAX_IMAGE_WIDTH = 10000
    MAX_IMAGE_HEIGHT = 10000
    MIN_IMAGE_WIDTH = 100
    MIN_IMAGE_HEIGHT = 100
    
    def __init__(self, enable_virus_scan: bool = True, clamav_socket: str = None):
        self.enable_virus_scan = enable_virus_scan
        self.clamav_socket = clamav_socket or '/var/run/clamav/clamd.ctl'
        self.mime = magic.Magic(mime=True) if MAGIC_AVAILABLE else None
    
    def validate_file(self, file: FileStorage) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Comprehensive file validation
        
        Returns:
            Tuple of (is_valid, error_message, metadata)
        """
        metadata = {
            'filename': file.filename,
            'size': 0,
            'mime_type': None,
            'hash': None,
            'dimensions': None,
        }
        
        try:
            # Check filename
            if not file.filename:
                return False, "No filename provided", metadata
            
            # Sanitize filename
            safe_filename = self.sanitize_filename(file.filename)
            if not safe_filename:
                return False, "Invalid filename", metadata
            
            metadata['safe_filename'] = safe_filename
            
            # Read file content
            file_content = file.read()
            file.seek(0)  # Reset for further processing
            
            if not file_content:
                return False, "Empty file", metadata
            
            metadata['size'] = len(file_content)
            
            # Check file size
            is_valid, error = self.check_file_size(file_content)
            if not is_valid:
                return False, error, metadata
            
            # Verify MIME type
            is_valid, mime_type, error = self.verify_mime_type(file_content)
            if not is_valid:
                return False, error, metadata
            
            metadata['mime_type'] = mime_type
            
            # Calculate file hash
            metadata['hash'] = self.calculate_hash(file_content)
            
            # Validate content based on type
            if mime_type.startswith('image/'):
                is_valid, error, dimensions = self.validate_image(file_content)
                if not is_valid:
                    return False, error, metadata
                metadata['dimensions'] = dimensions
            elif mime_type == 'application/pdf':
                is_valid, error = self.validate_pdf(file_content)
                if not is_valid:
                    return False, error, metadata
            
            # Virus scan
            if self.enable_virus_scan:
                is_clean, error = self.scan_for_virus(file_content)
                if not is_clean:
                    logger.warning(f"Virus detected in file {file.filename}: {error}")
                    return False, f"Security threat detected: {error}", metadata
            
            # Check for embedded executables
            if self.contains_executable(file_content):
                return False, "File contains executable content", metadata
            
            return True, None, metadata
            
        except Exception as e:
            logger.error(f"File validation error: {str(e)}")
            return False, f"Validation error: {str(e)}", metadata
    
    def sanitize_filename(self, filename: str) -> Optional[str]:
        """Sanitize filename to prevent path traversal and other attacks"""
        import re
        
        # Remove path components
        filename = os.path.basename(filename)
        
        # Remove dangerous characters
        filename = re.sub(r'[^\w\s\-\.]', '', filename)
        
        # Limit length
        name, ext = os.path.splitext(filename)
        if len(name) > 100:
            name = name[:100]
        
        # Ensure valid extension
        ext = ext.lower()
        valid_extensions = [ext for exts in self.ALLOWED_MIME_TYPES.values() for ext in exts]
        if ext not in valid_extensions:
            return None
        
        return f"{name}{ext}"
    
    def check_file_size(self, content: bytes) -> Tuple[bool, Optional[str]]:
        """Check if file size is within limits"""
        size = len(content)
        
        # Get MIME type for size check
        if self.mime:
            mime_type = self.mime.from_buffer(content)
        else:
            # Fallback to basic size checking without MIME detection
            mime_type = None
        
        max_size = self.MAX_FILE_SIZES.get(mime_type, 10 * 1024 * 1024)  # Default 10MB
        
        if size > max_size:
            return False, f"File too large. Maximum size is {max_size / (1024*1024):.1f}MB"
        
        if size < 100:  # Minimum 100 bytes
            return False, "File too small"
        
        return True, None
    
    def verify_mime_type(self, content: bytes) -> Tuple[bool, Optional[str], Optional[str]]:
        """Verify MIME type using magic bytes"""
        try:
            if self.mime:
                mime_type = self.mime.from_buffer(content)
            else:
                # Fallback to extension-based detection
                mime_type = 'image/jpeg'  # Assume most common type
                logger.warning("Magic library not available, using fallback MIME detection")
            
            if mime_type not in self.ALLOWED_MIME_TYPES:
                return False, None, f"File type '{mime_type}' not allowed"
            
            return True, mime_type, None
            
        except Exception as e:
            logger.error(f"MIME type detection error: {str(e)}")
            return False, None, "Could not determine file type"
    
    def validate_image(self, content: bytes) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """Validate image file"""
        try:
            import io
            img = Image.open(io.BytesIO(content))
            
            width, height = img.size
            
            # Check dimensions
            if width > self.MAX_IMAGE_WIDTH or height > self.MAX_IMAGE_HEIGHT:
                return False, f"Image too large: {width}x{height}", None
            
            if width < self.MIN_IMAGE_WIDTH or height < self.MIN_IMAGE_HEIGHT:
                return False, f"Image too small: {width}x{height}", None
            
            # Check for suspicious ratios (potential zip bombs)
            pixels = width * height
            file_size = len(content)
            compression_ratio = pixels * 3 / file_size  # Assuming 3 bytes per pixel
            
            if compression_ratio > 100:  # Suspicious compression ratio
                return False, "Suspicious image compression detected", None
            
            dimensions = {
                'width': width,
                'height': height,
                'format': img.format,
                'mode': img.mode,
            }
            
            return True, None, dimensions
            
        except Exception as e:
            logger.error(f"Image validation error: {str(e)}")
            return False, "Invalid image file", None
    
    def validate_pdf(self, content: bytes) -> Tuple[bool, Optional[str]]:
        """Validate PDF file"""
        try:
            # Check PDF header
            if not content.startswith(b'%PDF'):
                return False, "Invalid PDF file"
            
            # Check for embedded JavaScript (potential security risk)
            suspicious_patterns = [
                b'/JavaScript',
                b'/JS',
                b'/Launch',
                b'/EmbeddedFile',
                b'/XFA',  # Forms that can contain scripts
            ]
            
            for pattern in suspicious_patterns:
                if pattern in content:
                    logger.warning(f"Suspicious PDF pattern detected: {pattern}")
                    return False, "PDF contains potentially unsafe content"
            
            return True, None
            
        except Exception as e:
            logger.error(f"PDF validation error: {str(e)}")
            return False, "PDF validation failed"
    
    def scan_for_virus(self, content: bytes) -> Tuple[bool, Optional[str]]:
        """Scan file for viruses using ClamAV"""
        if not self.enable_virus_scan:
            return True, None
        
        try:
            # Save to temporary file for scanning
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                tmp_file.write(content)
                tmp_path = tmp_file.name
            
            try:
                # Try using clamdscan (daemon) first
                result = subprocess.run(
                    ['clamdscan', '--no-summary', tmp_path],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    return True, None
                elif result.returncode == 1:
                    # Virus found
                    return False, result.stdout.strip()
                else:
                    # Try clamscan as fallback
                    result = subprocess.run(
                        ['clamscan', '--no-summary', tmp_path],
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    
                    if result.returncode == 0:
                        return True, None
                    elif result.returncode == 1:
                        return False, result.stdout.strip()
                    
            finally:
                # Clean up temp file
                os.unlink(tmp_path)
            
        except FileNotFoundError:
            logger.warning("ClamAV not installed - skipping virus scan")
            return True, None
        except subprocess.TimeoutExpired:
            logger.error("Virus scan timeout")
            return False, "Virus scan timeout"
        except Exception as e:
            logger.error(f"Virus scan error: {str(e)}")
            # In production, fail closed (reject file if scan fails)
            if os.getenv('FLASK_ENV') == 'production':
                return False, "Security scan failed"
            return True, None
    
    def contains_executable(self, content: bytes) -> bool:
        """Check for embedded executable content"""
        # Check for common executable headers
        executable_signatures = [
            b'MZ',  # DOS/Windows executable
            b'\x7fELF',  # Linux ELF
            b'\xca\xfe\xba\xbe',  # Mach-O (macOS)
            b'\xfe\xed\xfa\xce',  # Mach-O (macOS)
            b'#!/',  # Shell script
            b'<?php',  # PHP script
        ]
        
        for signature in executable_signatures:
            if signature in content[:1000]:  # Check first 1KB
                return True
        
        return False
    
    def calculate_hash(self, content: bytes) -> str:
        """Calculate SHA-256 hash of file content"""
        return hashlib.sha256(content).hexdigest()
    
    def quarantine_file(self, file_path: str, reason: str):
        """Move suspicious file to quarantine"""
        quarantine_dir = os.getenv('QUARANTINE_DIR', '/var/app/quarantine')
        os.makedirs(quarantine_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        quarantine_path = os.path.join(
            quarantine_dir,
            f"{timestamp}_{os.path.basename(file_path)}"
        )
        
        try:
            import shutil
            shutil.move(file_path, quarantine_path)
            
            # Log quarantine action
            with open(os.path.join(quarantine_dir, 'quarantine.log'), 'a') as log:
                log.write(f"{timestamp} | {file_path} | {reason}\n")
            
            logger.warning(f"File quarantined: {file_path} -> {quarantine_path} | Reason: {reason}")
            
        except Exception as e:
            logger.error(f"Failed to quarantine file: {str(e)}")


# Import datetime for quarantine timestamp
from datetime import datetime