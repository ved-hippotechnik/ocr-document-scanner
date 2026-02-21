"""
Comprehensive input validation for OCR Document Scanner
"""
from marshmallow import Schema, fields, validate, ValidationError, pre_load, post_load
from typing import Any, Dict, List, Optional
import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class BaseValidator(Schema):
    """Base validator with common methods"""
    
    @pre_load
    def sanitize_strings(self, data, **kwargs):
        """Sanitize all string inputs"""
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str):
                    # Remove null bytes
                    value = value.replace('\x00', '')
                    # Strip whitespace
                    value = value.strip()
                    # Limit length
                    if len(value) > 10000:
                        value = value[:10000]
                    data[key] = value
        return data
    
    @post_load
    def log_validation(self, data, **kwargs):
        """Log successful validation"""
        logger.debug(f"Validation successful for {self.__class__.__name__}")
        return data


class UserRegistrationSchema(BaseValidator):
    """Validate user registration data"""
    username = fields.Str(
        required=True,
        validate=[
            validate.Length(min=3, max=30),
            validate.Regexp(
                r'^[a-zA-Z0-9_-]+$',
                error='Username must contain only letters, numbers, hyphens, and underscores'
            )
        ]
    )
    email = fields.Email(required=True, validate=validate.Length(max=120))
    password = fields.Str(
        required=True,
        validate=[
            validate.Length(min=8, max=128),
            validate.Regexp(
                r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]',
                error='Password must contain uppercase, lowercase, digit, and special character'
            )
        ]
    )


class UserLoginSchema(BaseValidator):
    """Validate user login data"""
    username = fields.Str(required=True, validate=validate.Length(max=30))
    password = fields.Str(required=True, validate=validate.Length(max=128))
    remember_me = fields.Bool(load_default=False)


class DocumentScanSchema(BaseValidator):
    """Validate document scan request"""
    document_type = fields.Str(
        validate=validate.OneOf([
            'emirates_id', 'aadhaar_card', 'driving_license',
            'passport', 'us_drivers_license', 'auto'
        ])
    )
    quality_check = fields.Bool(load_default=True)
    enhance_image = fields.Bool(load_default=False)
    extract_face = fields.Bool(load_default=False)
    validate_document = fields.Bool(load_default=True)
    output_format = fields.Str(
        load_default='json',
        validate=validate.OneOf(['json', 'xml', 'csv'])
    )
    language = fields.Str(
        load_default='eng',
        validate=validate.Regexp(r'^[a-z]{3}$')
    )
    session_id = fields.Str(
        validate=[
            validate.Length(max=255),
            validate.Regexp(r'^[a-zA-Z0-9_-]+$')
        ]
    )


class BatchProcessingSchema(BaseValidator):
    """Validate batch processing request"""
    job_name = fields.Str(
        required=True,
        validate=[
            validate.Length(min=1, max=100),
            validate.Regexp(r'^[a-zA-Z0-9\s_-]+$')
        ]
    )
    priority = fields.Int(
        load_default=5,
        validate=validate.Range(min=1, max=10)
    )
    max_workers = fields.Int(
        load_default=4,
        validate=validate.Range(min=1, max=10)
    )
    timeout = fields.Int(
        load_default=300,
        validate=validate.Range(min=60, max=3600)
    )
    notification_email = fields.Email(required=False)
    tags = fields.List(
        fields.Str(validate=validate.Length(max=50)),
        validate=validate.Length(max=10)
    )


class SearchQuerySchema(BaseValidator):
    """Validate search query parameters"""
    query = fields.Str(
        required=True,
        validate=[
            validate.Length(min=1, max=200),
            validate.Regexp(
                r'^[a-zA-Z0-9\s\-_.@]+$',
                error='Search query contains invalid characters'
            )
        ]
    )
    page = fields.Int(load_default=1, validate=validate.Range(min=1))
    per_page = fields.Int(
        load_default=20,
        validate=validate.Range(min=1, max=100)
    )
    sort_by = fields.Str(
        load_default='created_at',
        validate=validate.OneOf([
            'created_at', 'updated_at', 'document_type',
            'confidence_score', 'processing_time'
        ])
    )
    sort_order = fields.Str(
        load_default='desc',
        validate=validate.OneOf(['asc', 'desc'])
    )
    date_from = fields.DateTime(format='%Y-%m-%d')
    date_to = fields.DateTime(format='%Y-%m-%d')
    document_types = fields.List(
        fields.Str(),
        validate=validate.Length(max=10)
    )


class AnalyticsQuerySchema(BaseValidator):
    """Validate analytics query parameters"""
    metric = fields.Str(
        required=True,
        validate=validate.OneOf([
            'scans_count', 'success_rate', 'avg_processing_time',
            'document_types', 'quality_scores', 'error_rate'
        ])
    )
    granularity = fields.Str(
        load_default='day',
        validate=validate.OneOf(['hour', 'day', 'week', 'month'])
    )
    start_date = fields.DateTime(required=True, format='%Y-%m-%d')
    end_date = fields.DateTime(required=True, format='%Y-%m-%d')
    group_by = fields.List(
        fields.Str(validate=validate.OneOf([
            'document_type', 'user_id', 'status', 'hour', 'day'
        ])),
        validate=validate.Length(max=3)
    )
    filters = fields.Dict(load_default={})
    
    @post_load
    def validate_date_range(self, data, **kwargs):
        """Validate date range"""
        if data['end_date'] < data['start_date']:
            raise ValidationError('End date must be after start date')
        
        # Limit date range to 90 days
        delta = data['end_date'] - data['start_date']
        if delta.days > 90:
            raise ValidationError('Date range cannot exceed 90 days')
        
        return data


class FileUploadValidator:
    """Validate file uploads"""
    
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'pdf', 'tiff', 'tif', 'bmp'}
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    
    @classmethod
    def validate_filename(cls, filename: str) -> bool:
        """Validate filename"""
        if not filename:
            return False
        
        # Check for path traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            return False
        
        # Check extension
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        if ext not in cls.ALLOWED_EXTENSIONS:
            return False
        
        # Check for double extensions
        if filename.count('.') > 1:
            parts = filename.split('.')
            for part in parts[:-1]:
                if part.lower() in cls.ALLOWED_EXTENSIONS:
                    return False  # Potential bypass attempt
        
        return True
    
    @classmethod
    def validate_file_size(cls, file_size: int) -> bool:
        """Validate file size"""
        return 0 < file_size <= cls.MAX_FILE_SIZE


class InputSanitizer:
    """Sanitize user inputs"""
    
    @staticmethod
    def sanitize_html(text: str) -> str:
        """Remove HTML tags and scripts"""
        import html
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Escape HTML entities
        text = html.escape(text)
        return text
    
    @staticmethod
    def sanitize_sql(text: str) -> str:
        """Sanitize potential SQL injection attempts"""
        # Remove SQL keywords and special characters
        dangerous_patterns = [
            r';\s*DROP',
            r';\s*DELETE',
            r';\s*UPDATE',
            r';\s*INSERT',
            r'UNION\s+SELECT',
            r'OR\s+1\s*=\s*1',
            r'--',
            r'/\*.*\*/',
        ]
        
        for pattern in dangerous_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        return text
    
    @staticmethod
    def sanitize_path(path: str) -> str:
        """Sanitize file paths"""
        # Remove path traversal attempts
        path = path.replace('..', '')
        path = path.replace('//', '/')
        path = path.replace('\\', '/')
        
        # Remove null bytes
        path = path.replace('\x00', '')
        
        return path
    
    @staticmethod
    def sanitize_json(data: Any) -> Any:
        """Sanitize JSON data recursively"""
        if isinstance(data, str):
            return InputSanitizer.sanitize_html(data)
        elif isinstance(data, dict):
            return {k: InputSanitizer.sanitize_json(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [InputSanitizer.sanitize_json(item) for item in data]
        else:
            return data


class RequestValidator:
    """Validate HTTP requests"""
    
    @staticmethod
    def validate_content_type(content_type: str, allowed: List[str]) -> bool:
        """Validate Content-Type header"""
        if not content_type:
            return False
        
        # Extract main content type
        main_type = content_type.split(';')[0].strip().lower()
        
        return main_type in allowed
    
    @staticmethod
    def validate_api_key(api_key: str) -> bool:
        """Validate API key format"""
        if not api_key:
            return False
        
        # Check format (alphanumeric with hyphens)
        if not re.match(r'^[a-zA-Z0-9-]{32,64}$', api_key):
            return False
        
        return True
    
    @staticmethod
    def validate_jwt_token(token: str) -> bool:
        """Validate JWT token format"""
        if not token:
            return False
        
        # Check JWT structure (header.payload.signature)
        parts = token.split('.')
        if len(parts) != 3:
            return False
        
        # Check each part is base64url encoded
        for part in parts:
            if not re.match(r'^[a-zA-Z0-9_-]+$', part):
                return False
        
        return True
    
    @staticmethod
    def validate_ip_address(ip: str) -> bool:
        """Validate IP address"""
        import ipaddress
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False


class ParameterValidator:
    """Validate query parameters"""
    
    @staticmethod
    def validate_pagination(page: Any, per_page: Any) -> tuple:
        """Validate and sanitize pagination parameters"""
        try:
            page = int(page) if page else 1
            per_page = int(per_page) if per_page else 20
        except (ValueError, TypeError):
            raise ValidationError("Invalid pagination parameters")
        
        # Enforce limits
        page = max(1, min(page, 10000))
        per_page = max(1, min(per_page, 100))
        
        return page, per_page
    
    @staticmethod
    def validate_date_range(start: str, end: str) -> tuple:
        """Validate date range parameters"""
        try:
            start_date = datetime.fromisoformat(start) if start else None
            end_date = datetime.fromisoformat(end) if end else None
        except ValueError:
            raise ValidationError("Invalid date format")
        
        if start_date and end_date:
            if end_date < start_date:
                raise ValidationError("End date must be after start date")
            
            # Limit range
            delta = end_date - start_date
            if delta.days > 365:
                raise ValidationError("Date range cannot exceed 365 days")
        
        return start_date, end_date
    
    @staticmethod
    def validate_sort_params(sort_by: str, sort_order: str, allowed_fields: List[str]) -> tuple:
        """Validate sorting parameters"""
        if sort_by and sort_by not in allowed_fields:
            raise ValidationError(f"Invalid sort field: {sort_by}")
        
        if sort_order and sort_order.upper() not in ['ASC', 'DESC']:
            raise ValidationError(f"Invalid sort order: {sort_order}")
        
        return sort_by or 'id', sort_order.upper() if sort_order else 'DESC'


# Export schemas for easy access
schemas = {
    'user_registration': UserRegistrationSchema(),
    'user_login': UserLoginSchema(),
    'document_scan': DocumentScanSchema(),
    'batch_processing': BatchProcessingSchema(),
    'search_query': SearchQuerySchema(),
    'analytics_query': AnalyticsQuerySchema(),
}