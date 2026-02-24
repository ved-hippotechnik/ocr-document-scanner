"""
Enhanced error handling and validation system
"""
import base64
import io
import logging
from PIL import Image
from typing import Dict, Any, Optional, List
from werkzeug.exceptions import BadRequest, RequestEntityTooLarge
from flask import jsonify, request
import traceback
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

_UTC_SUFFIX = '+00:00'


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace(_UTC_SUFFIX, 'Z')


class ValidationError(Exception):
    """Custom validation error"""
    def __init__(self, message: str, code: str = "VALIDATION_ERROR", details: str = None):
        self.message = message
        self.code = code
        self.details = details
        super().__init__(self.message)

class ProcessingError(Exception):
    """Custom processing error"""
    def __init__(self, message: str, code: str = "PROCESSING_ERROR", details: str = None):
        self.message = message
        self.code = code
        self.details = details
        super().__init__(self.message)

class DocumentValidator:
    """Validator for document processing requests"""
    
    MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
    SUPPORTED_FORMATS = {'JPEG', 'PNG', 'JPG', 'WEBP'}
    MIN_IMAGE_DIMENSION = 100
    MAX_IMAGE_DIMENSION = 8000
    
    @staticmethod
    def validate_request_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate incoming request data"""
        if not data:
            raise ValidationError("Request body is empty", "EMPTY_REQUEST")
        
        if 'image' not in data:
            raise ValidationError("Missing 'image' field in request", "MISSING_IMAGE")
        
        if not isinstance(data['image'], str):
            raise ValidationError("Image must be a base64 encoded string", "INVALID_IMAGE_FORMAT")
        
        if not data['image'].strip():
            raise ValidationError("Image data is empty", "EMPTY_IMAGE")
        
        # Validate image data
        image = DocumentValidator.validate_and_decode_image(data['image'])
        
        # Validate optional fields
        validated_data = {
            'image': image,
            'document_type': data.get('document_type'),
            'options': data.get('options', {})
        }
        
        # Validate options if provided
        if validated_data['options']:
            DocumentValidator.validate_options(validated_data['options'])
        
        return validated_data
    
    @staticmethod
    def validate_and_decode_image(image_data: str) -> Image.Image:
        """Validate and decode base64 image"""
        try:
            # Remove data URL prefix if present
            if ',' in image_data:
                image_data = image_data.split(',', 1)[1]
            
            # Decode base64
            image_bytes = base64.b64decode(image_data)
            
            # Check size
            if len(image_bytes) > DocumentValidator.MAX_IMAGE_SIZE:
                raise ValidationError(
                    f"Image size ({len(image_bytes)} bytes) exceeds maximum allowed size ({DocumentValidator.MAX_IMAGE_SIZE} bytes)",
                    "FILE_TOO_LARGE"
                )
            
            if len(image_bytes) < 1000:  # Very small file, likely invalid
                raise ValidationError("Image file is too small to be valid", "INVALID_IMAGE")
            
            # Try to open and validate image
            image = Image.open(io.BytesIO(image_bytes))
            
            # Check format
            if image.format not in DocumentValidator.SUPPORTED_FORMATS:
                raise ValidationError(
                    f"Unsupported image format: {image.format}. Supported formats: {', '.join(DocumentValidator.SUPPORTED_FORMATS)}",
                    "UNSUPPORTED_FORMAT"
                )
            
            # Check dimensions
            width, height = image.size
            if width < DocumentValidator.MIN_IMAGE_DIMENSION or height < DocumentValidator.MIN_IMAGE_DIMENSION:
                raise ValidationError(
                    f"Image dimensions ({width}x{height}) are too small. Minimum: {DocumentValidator.MIN_IMAGE_DIMENSION}x{DocumentValidator.MIN_IMAGE_DIMENSION}",
                    "IMAGE_TOO_SMALL"
                )
            
            if width > DocumentValidator.MAX_IMAGE_DIMENSION or height > DocumentValidator.MAX_IMAGE_DIMENSION:
                raise ValidationError(
                    f"Image dimensions ({width}x{height}) are too large. Maximum: {DocumentValidator.MAX_IMAGE_DIMENSION}x{DocumentValidator.MAX_IMAGE_DIMENSION}",
                    "IMAGE_TOO_LARGE"
                )
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            return image
            
        except base64.binascii.Error:
            raise ValidationError("Invalid base64 encoding", "INVALID_BASE64")
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise ValidationError(f"Failed to process image: {str(e)}", "INVALID_IMAGE")
    
    @staticmethod
    def validate_options(options: Dict[str, Any]) -> None:
        """Validate processing options"""
        valid_options = {
            'enable_quality_check': bool,
            'return_processed_images': bool,
            'ocr_language': str,
            'confidence_threshold': (int, float),
            'max_processing_time': (int, float)
        }
        
        for key, value in options.items():
            if key not in valid_options:
                raise ValidationError(f"Unknown option: {key}", "INVALID_OPTION")
            
            expected_type = valid_options[key]
            if not isinstance(value, expected_type):
                raise ValidationError(
                    f"Option '{key}' must be of type {expected_type.__name__ if hasattr(expected_type, '__name__') else expected_type}",
                    "INVALID_OPTION_TYPE"
                )
        
        # Validate specific option values
        if 'confidence_threshold' in options:
            threshold = options['confidence_threshold']
            if not 0 <= threshold <= 1:
                raise ValidationError("confidence_threshold must be between 0 and 1", "INVALID_THRESHOLD")
        
        if 'max_processing_time' in options:
            max_time = options['max_processing_time']
            if max_time <= 0 or max_time > 300:  # 5 minutes max
                raise ValidationError("max_processing_time must be between 0 and 300 seconds", "INVALID_TIMEOUT")

class ErrorHandler:
    """Enhanced error handling system"""
    
    @staticmethod
    def handle_error(error: Exception) -> tuple:
        """Handle and format errors for API responses"""
        from flask import g
        timestamp = _utc_timestamp()
        request_id = getattr(g, 'request_id', None)

        if isinstance(error, ValidationError):
            response = {
                'success': False,
                'error': {
                    'code': error.code,
                    'message': error.message,
                    'details': error.details
                },
                'timestamp': timestamp
            }
            status_code = 400

        elif isinstance(error, ProcessingError):
            response = {
                'success': False,
                'error': {
                    'code': error.code,
                    'message': error.message,
                    'details': error.details
                },
                'timestamp': timestamp
            }
            status_code = 422

        elif isinstance(error, RequestEntityTooLarge):
            response = {
                'success': False,
                'error': {
                    'code': 'FILE_TOO_LARGE',
                    'message': 'Request entity is too large',
                    'details': 'The uploaded file exceeds the maximum allowed size'
                },
                'timestamp': timestamp
            }
            status_code = 413

        elif isinstance(error, BadRequest):
            response = {
                'success': False,
                'error': {
                    'code': 'BAD_REQUEST',
                    'message': 'Invalid request format',
                    'details': str(error)
                },
                'timestamp': timestamp
            }
            status_code = 400

        else:
            logger.error(f"Unexpected error: {str(error)}", exc_info=True)
            response = {
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'An internal server error occurred',
                    'details': 'Please try again later or contact support if the problem persists'
                },
                'timestamp': timestamp
            }
            status_code = 500

        if request_id:
            response['request_id'] = request_id
        return jsonify(response), status_code
    
    @staticmethod
    def create_success_response(data: Dict[str, Any], status_code: int = 200) -> tuple:
        """Create a standardized success response"""
        response = {
            'success': True,
            'timestamp': _utc_timestamp(),
            **data
        }
        return jsonify(response), status_code

def validate_request_json():
    """Decorator to validate JSON request data"""
    def decorator(f):
        def wrapper(*args, **kwargs):
            try:
                if not request.is_json:
                    raise ValidationError("Content-Type must be application/json", "INVALID_CONTENT_TYPE")
                
                data = request.get_json()
                if data is None:
                    raise ValidationError("Invalid JSON in request body", "INVALID_JSON")
                
                # Validate the request data
                validated_data = DocumentValidator.validate_request_data(data)
                
                # Pass validated data to the route function
                return f(validated_data, *args, **kwargs)
                
            except Exception as e:
                return ErrorHandler.handle_error(e)
        
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator

def handle_processing_errors():
    """Decorator to handle processing errors"""
    def decorator(f):
        def wrapper(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception as e:
                return ErrorHandler.handle_error(e)
        
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator

def add_security_headers(response):
    """Add security headers to response"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response

class PerformanceMonitor:
    """Monitor API performance"""
    
    @staticmethod
    def log_performance(endpoint: str, processing_time: float, success: bool, document_type: str = None):
        """Log performance metrics"""
        logger.info(f"Performance: {endpoint} - {processing_time:.3f}s - {'SUCCESS' if success else 'FAILED'} - {document_type or 'N/A'}")
        
        # Here you could send metrics to external monitoring service
        # e.g., StatsD, Prometheus, etc.

def validate_email(email: str) -> bool:
    """Validate email format"""
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email) is not None

COMMON_PASSWORDS = frozenset([
    'password', 'password1', 'password123', '12345678', '123456789',
    '1234567890', 'qwerty123', 'abc12345', 'iloveyou', 'admin123',
    'welcome1', 'monkey123', 'master123', 'dragon123', 'login123',
    'princess1', 'football1', 'shadow123', 'sunshine1', 'trustno1',
    'letmein123', 'baseball1', 'michael1', 'charlie1', 'access14',
    'superman1', 'batman123', 'passw0rd', 'p@ssw0rd', 'p@ssword',
    'changeme1', 'welcome123', 'qwerty12', 'hello123', 'test1234',
    'password!', 'pass1234', 'admin1234', 'root1234', 'toor1234',
    'default1', 'guest1234', 'user1234', 'temp1234', 'secure123',
    'qwertyui', 'asdfghjk', 'zxcvbnm1', '1q2w3e4r', 'q1w2e3r4',
])

def validate_password(password: str, username: str = None) -> dict:
    """Validate password strength including common password check and username similarity."""
    if len(password) < 8:
        return {'valid': False, 'message': 'Password must be at least 8 characters long'}

    if len(password) > 128:
        return {'valid': False, 'message': 'Password must be less than 128 characters long'}

    if not any(c.isupper() for c in password):
        return {'valid': False, 'message': 'Password must contain at least one uppercase letter'}

    if not any(c.islower() for c in password):
        return {'valid': False, 'message': 'Password must contain at least one lowercase letter'}

    if not any(c.isdigit() for c in password):
        return {'valid': False, 'message': 'Password must contain at least one number'}

    if not any(c in '!@#$%^&*(),.?":{}|<>' for c in password):
        return {'valid': False, 'message': 'Password must contain at least one special character'}

    # Check against common passwords
    if password.lower() in COMMON_PASSWORDS:
        return {'valid': False, 'message': 'This password is too common. Please choose a more unique password'}

    # Check if password contains the username
    if username and len(username) >= 3 and username.lower() in password.lower():
        return {'valid': False, 'message': 'Password must not contain your username'}

    return {'valid': True, 'message': 'Password is valid'}

def sanitize_input(text: str) -> str:
    """Sanitize user input"""
    if not text:
        return ''
    
    # Remove potential script tags and other dangerous content
    import re
    text = re.sub(r'<[^>]*>', '', text)  # Remove HTML tags
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)  # Remove javascript:
    text = re.sub(r'vbscript:', '', text, flags=re.IGNORECASE)  # Remove vbscript:
    text = re.sub(r'onload=', '', text, flags=re.IGNORECASE)  # Remove onload
    text = re.sub(r'onerror=', '', text, flags=re.IGNORECASE)  # Remove onerror
    
    return text.strip()

def validate_json_input(data: dict) -> dict:
    """
    Validate JSON input data
    
    Args:
        data: JSON data to validate
        
    Returns:
        Dictionary with validation results
    """
    try:
        if not isinstance(data, dict):
            return {
                'valid': False,
                'error': 'Invalid data format. Expected JSON object.'
            }
        
        # Basic validation - can be extended based on specific requirements
        if not data:
            return {
                'valid': False,
                'error': 'Empty data provided'
            }
        
        # Check for required fields if any
        # Add specific validation logic here as needed
        
        return {
            'valid': True,
            'data': data
        }
    
    except Exception as e:
        return {
            'valid': False,
            'error': f'Validation error: {str(e)}'
        }

def validate_file_upload(file_content: bytes, allowed_extensions: List[str] = None) -> dict:
    """Validate uploaded file content"""
    if not file_content:
        return {'valid': False, 'message': 'File content is empty'}
    
    # Check file size
    if len(file_content) > 10 * 1024 * 1024:  # 10MB
        return {'valid': False, 'message': 'File size exceeds maximum allowed size (10MB)'}
    
    # Check for malicious content patterns
    malicious_patterns = [
        b'<?php',
        b'<script',
        b'javascript:',
        b'vbscript:',
        b'data:text/html',
        b'<iframe',
        b'<object',
        b'<embed'
    ]
    
    content_lower = file_content.lower()
    for pattern in malicious_patterns:
        if pattern in content_lower:
            return {'valid': False, 'message': 'File contains potentially malicious content'}
    
    # Validate file signature (magic bytes)
    magic_bytes = {
        'jpeg': [b'\xFF\xD8\xFF'],
        'png': [b'\x89PNG\r\n\x1a\n'],
        'gif': [b'GIF87a', b'GIF89a'],
        'webp': [b'RIFF', b'WEBP']
    }
    
    if allowed_extensions:
        valid_signature = False
        for ext in allowed_extensions:
            if ext.lower() in magic_bytes:
                for signature in magic_bytes[ext.lower()]:
                    if file_content.startswith(signature):
                        valid_signature = True
                        break
        
        if not valid_signature:
            return {'valid': False, 'message': 'File signature does not match allowed file types'}
    
    return {'valid': True, 'message': 'File is valid'}

class SecurityValidator:
    """Security validation utilities"""
    
    @staticmethod
    def validate_sql_injection(text: str) -> bool:
        """Check for potential SQL injection patterns"""
        if not text:
            return True
        
        sql_patterns = [
            r"(?i)(union|select|insert|delete|update|drop|create|alter|exec|execute)",
            r"(?i)(or|and)\s+\d+\s*=\s*\d+",
            r"(?i)(or|and)\s+\w+\s*=\s*\w+",
            r"(?i)(\-\-|\#|\/\*|\*\/)",
            r"(?i)(xp_|sp_|fn_)"
        ]
        
        import re
        for pattern in sql_patterns:
            if re.search(pattern, text):
                return False
        
        return True
    
    @staticmethod
    def validate_xss(text: str) -> bool:
        """Check for potential XSS patterns"""
        if not text:
            return True
        
        xss_patterns = [
            r"(?i)<script[^>]*>.*?</script>",
            r"(?i)javascript:",
            r"(?i)vbscript:",
            r"(?i)onload\s*=",
            r"(?i)onerror\s*=",
            r"(?i)onclick\s*=",
            r"(?i)onmouseover\s*=",
            r"(?i)<iframe[^>]*>",
            r"(?i)<object[^>]*>",
            r"(?i)<embed[^>]*>"
        ]
        
        import re
        for pattern in xss_patterns:
            if re.search(pattern, text):
                return False
        
        return True
    
    @staticmethod
    def validate_path_traversal(path: str) -> bool:
        """Check for path traversal patterns"""
        if not path:
            return True
        
        import os
        import urllib.parse
        
        # Decode URL-encoded characters multiple times to catch nested encoding
        decoded_path = path
        for _ in range(3):
            try:
                decoded_path = urllib.parse.unquote(decoded_path)
            except:
                pass
        
        # Normalize the path
        normalized = os.path.normpath(decoded_path)
        
        # Check for dangerous patterns in both original and decoded paths
        dangerous_patterns = [
            '../',
            '..\\',
            '..%2f',
            '..%5c', 
            '%2e%2e%2f',
            '%2e%2e%5c',
            '..%252f',
            '..%255c',
            '..%c0%af',
            '..%c1%9c'
        ]
        
        paths_to_check = [path.lower(), decoded_path.lower(), normalized.lower()]
        
        for check_path in paths_to_check:
            for pattern in dangerous_patterns:
                if pattern in check_path:
                    return False
            
            # Check for absolute paths
            if check_path.startswith('/') or check_path.startswith('\\'):
                return False
            
            # Check for drive letters (Windows)
            if len(check_path) > 1 and check_path[1] == ':':
                return False
        
        # Check if normalized path tries to go outside current directory
        if normalized.startswith('..') or normalized.startswith('/'):
            return False
        
        return True

class InputSanitizer:
    """Advanced input sanitization"""
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe storage"""
        if not filename:
            return 'unnamed_file'
        
        import re
        # Remove path separators and dangerous characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        filename = re.sub(r'\.+', '.', filename)  # Replace multiple dots with single dot
        filename = filename.strip('.')  # Remove leading/trailing dots
        
        # Limit length
        if len(filename) > 255:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            filename = name[:250] + ('.' + ext if ext else '')
        
        return filename or 'unnamed_file'
    
    @staticmethod
    def sanitize_json_data(data: dict) -> dict:
        """Recursively sanitize JSON data"""
        if isinstance(data, dict):
            return {key: InputSanitizer.sanitize_json_data(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [InputSanitizer.sanitize_json_data(item) for item in data]
        elif isinstance(data, str):
            return sanitize_input(data)
        else:
            return data


# ---------------------------------------------------------------------------
# Convenience response helpers
# ---------------------------------------------------------------------------

def api_response(data: Dict[str, Any], status: int = 200) -> tuple:
    """Return a standardised JSON success response."""
    from flask import g
    body = {
        'success': True,
        'timestamp': _utc_timestamp(),
        **data,
    }
    request_id = getattr(g, 'request_id', None)
    if request_id:
        body['request_id'] = request_id
    return jsonify(body), status


def api_error(message: str, status: int = 400, code: str = 'ERROR') -> tuple:
    """Return a standardised JSON error response."""
    from flask import g
    body = {
        'success': False,
        'error': {
            'code': code,
            'message': message,
        },
        'timestamp': _utc_timestamp(),
    }
    request_id = getattr(g, 'request_id', None)
    if request_id:
        body['request_id'] = request_id
    return jsonify(body), status
