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
        timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        
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
            return jsonify(response), 400
        
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
            return jsonify(response), 422
        
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
            return jsonify(response), 413
        
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
            return jsonify(response), 400
        
        else:
            # Log unexpected errors
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
            return jsonify(response), 500
    
    @staticmethod
    def create_success_response(data: Dict[str, Any], status_code: int = 200) -> tuple:
        """Create a standardized success response"""
        response = {
            'success': True,
            'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            **data
        }
        return jsonify(response), status_code

class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self, max_requests: int = 100, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = {}  # IP -> list of timestamps
    
    def is_allowed(self, client_ip: str) -> tuple:
        """Check if request is allowed and return (allowed, remaining, reset_time)"""
        current_time = datetime.now(timezone.utc).timestamp()
        
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        
        # Clean old requests
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if current_time - req_time < self.time_window
        ]
        
        # Check limit
        if len(self.requests[client_ip]) >= self.max_requests:
            oldest_request = min(self.requests[client_ip])
            reset_time = oldest_request + self.time_window
            return False, 0, reset_time
        
        # Add current request
        self.requests[client_ip].append(current_time)
        remaining = self.max_requests - len(self.requests[client_ip])
        reset_time = current_time + self.time_window
        
        return True, remaining, reset_time

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

# Global rate limiter instance
rate_limiter = RateLimiter()

def check_rate_limit():
    """Check rate limit for current request"""
    client_ip = request.remote_addr or 'unknown'
    allowed, remaining, reset_time = rate_limiter.is_allowed(client_ip)
    
    if not allowed:
        raise ValidationError(
            "Rate limit exceeded. Please try again later.",
            "RATE_LIMIT_EXCEEDED",
            f"Reset time: {datetime.fromtimestamp(reset_time).isoformat()}"
        )
    
    # Add rate limit headers to response (will be added by Flask after)
    return {
        'X-RateLimit-Limit': str(rate_limiter.max_requests),
        'X-RateLimit-Remaining': str(remaining),
        'X-RateLimit-Reset': str(int(reset_time))
    }

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
