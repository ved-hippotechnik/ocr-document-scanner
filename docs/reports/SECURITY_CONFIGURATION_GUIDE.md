# Security Configuration Guide for OCR Document Scanner API

## Immediate Security Fixes Required

### 1. Security Headers Implementation

Add the following security headers middleware to your Flask application:

```python
# Add to backend/app/__init__.py or create backend/app/security/headers.py

from flask import Flask

def configure_security_headers(app: Flask):
    """Configure comprehensive security headers"""
    
    @app.after_request
    def add_security_headers(response):
        # Prevent HTTPS downgrade attacks
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
        
        # Content Security Policy
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob:; "
            "font-src 'self'; "
            "connect-src 'self' ws: wss:; "
            "frame-ancestors 'none';"
        )
        
        # Referrer Policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Additional security headers (already present but ensure they're set)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Permissions Policy (formerly Feature Policy)
        response.headers['Permissions-Policy'] = (
            "camera=(), microphone=(), geolocation=(), "
            "payment=(), usb=(), magnetometer=(), gyroscope=()"
        )
        
        return response
```

### 2. Rate Limiting Configuration

Replace the current rate limiting with endpoint-specific limits:

```python
# backend/app/rate_limiter.py

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import redis

class SmartRateLimiter:
    def __init__(self, app=None):
        self.limiter = None
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        # Use Redis for production, memory for development
        storage_uri = app.config.get('RATE_LIMIT_STORAGE_URL', 'memory://')
        
        self.limiter = Limiter(
            app,
            key_func=get_remote_address,
            storage_uri=storage_uri,
            default_limits=["1000 per hour", "200 per minute"]
        )
        
        # Configure endpoint-specific limits
        self.configure_endpoint_limits()
    
    def configure_endpoint_limits(self):
        """Configure specific rate limits per endpoint type"""
        
        # File upload endpoints - more restrictive
        @self.limiter.limit("20 per minute")
        def limit_file_uploads():
            pass
        
        # Authentication endpoints - moderate limits
        @self.limiter.limit("50 per minute") 
        def limit_auth_endpoints():
            pass
        
        # Data endpoints - higher limits
        @self.limiter.limit("300 per minute")
        def limit_data_endpoints():
            pass

# Usage in routes
limiter = SmartRateLimiter()

# Apply to specific routes
@app.route('/api/scan', methods=['POST'])
@limiter.limit("20 per minute")
def scan_document():
    pass

@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("10 per minute")  # Stricter for auth
def login():
    pass
```

### 3. Input Validation Enhancement

```python
# backend/app/security/validators.py

import re
from flask import request, abort
from werkzeug.utils import secure_filename

class SecurityValidator:
    
    # File validation
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'tiff', 'bmp'}
    MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
    
    # Content validation
    MALICIOUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'eval\s*\(',
        r'exec\s*\(',
        r'\bDROP\s+TABLE\b',
        r'\bUNION\s+SELECT\b',
        r'\.\./',
        r'\.\.\\',
    ]
    
    @staticmethod
    def validate_file_upload(file):
        """Validate uploaded file security"""
        if not file or file.filename == '':
            return False, "No file provided"
        
        # Check filename
        filename = secure_filename(file.filename)
        if not filename:
            return False, "Invalid filename"
        
        # Check extension
        if '.' not in filename:
            return False, "File must have extension"
        
        ext = filename.rsplit('.', 1)[1].lower()
        if ext not in SecurityValidator.ALLOWED_EXTENSIONS:
            return False, f"File type {ext} not allowed"
        
        # Check file size
        file.seek(0, 2)  # Seek to end
        size = file.tell()
        file.seek(0)     # Reset position
        
        if size > SecurityValidator.MAX_FILE_SIZE:
            return False, "File too large"
        
        # Basic content validation
        content_sample = file.read(1024)  # Read first 1KB
        file.seek(0)  # Reset position
        
        if SecurityValidator.contains_malicious_content(content_sample.decode('utf-8', errors='ignore')):
            return False, "Malicious content detected"
        
        return True, "File valid"
    
    @staticmethod
    def validate_json_input(data):
        """Validate JSON input for malicious content"""
        if not data:
            return True, "No data"
        
        # Convert to string for pattern matching
        data_str = str(data)
        
        for pattern in SecurityValidator.MALICIOUS_PATTERNS:
            if re.search(pattern, data_str, re.IGNORECASE):
                return False, f"Malicious pattern detected: {pattern}"
        
        return True, "Input valid"
    
    @staticmethod
    def contains_malicious_content(content):
        """Check for malicious patterns in content"""
        for pattern in SecurityValidator.MALICIOUS_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        return False

# Decorator for route validation
def validate_request(validate_files=False, validate_json=False):
    def decorator(f):
        def wrapper(*args, **kwargs):
            if validate_files:
                for file_key in request.files:
                    file = request.files[file_key]
                    valid, message = SecurityValidator.validate_file_upload(file)
                    if not valid:
                        abort(400, description=message)
            
            if validate_json:
                valid, message = SecurityValidator.validate_json_input(request.json)
                if not valid:
                    abort(400, description=message)
            
            return f(*args, **kwargs)
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator
```

### 4. Authentication Security

```python
# backend/app/auth/secure_auth.py

import hashlib
import secrets
from datetime import datetime, timedelta
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

class SecureAuth:
    
    # Password requirements
    MIN_PASSWORD_LENGTH = 8
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGITS = True
    REQUIRE_SPECIAL = True
    
    @staticmethod
    def validate_password_strength(password):
        """Validate password meets security requirements"""
        if len(password) < SecureAuth.MIN_PASSWORD_LENGTH:
            return False, f"Password must be at least {SecureAuth.MIN_PASSWORD_LENGTH} characters"
        
        if SecureAuth.REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            return False, "Password must contain uppercase letter"
        
        if SecureAuth.REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            return False, "Password must contain lowercase letter"
        
        if SecureAuth.REQUIRE_DIGITS and not re.search(r'\d', password):
            return False, "Password must contain digit"
        
        if SecureAuth.REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain special character"
        
        # Check against common passwords
        if password.lower() in ['password', '123456', 'qwerty', 'admin', 'user']:
            return False, "Password is too common"
        
        return True, "Password valid"
    
    @staticmethod
    def hash_password(password, salt=None):
        """Securely hash password with salt"""
        if not salt:
            salt = secrets.token_hex(32)
        
        pwdhash = hashlib.pbkdf2_hmac('sha256', 
                                      password.encode('utf-8'),
                                      salt.encode('utf-8'), 
                                      100000)  # 100k iterations
        
        return f"{salt}${pwdhash.hex()}"
    
    @staticmethod
    def verify_password(password, hash_string):
        """Verify password against hash"""
        try:
            salt, stored_hash = hash_string.split('$')
            pwdhash = hashlib.pbkdf2_hmac('sha256',
                                          password.encode('utf-8'),
                                          salt.encode('utf-8'),
                                          100000)
            return pwdhash.hex() == stored_hash
        except:
            return False
```

### 5. Error Handling and Logging

```python
# backend/app/security/error_handler.py

import logging
from flask import request, jsonify
from datetime import datetime

# Configure security logging
security_logger = logging.getLogger('security')
security_handler = logging.FileHandler('logs/security.log')
security_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
))
security_logger.addHandler(security_handler)
security_logger.setLevel(logging.INFO)

def log_security_event(event_type, details, severity='INFO'):
    """Log security events"""
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'event_type': event_type,
        'ip_address': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', ''),
        'endpoint': request.endpoint,
        'method': request.method,
        'details': details,
        'severity': severity
    }
    
    if severity == 'CRITICAL':
        security_logger.critical(log_entry)
    elif severity == 'HIGH':
        security_logger.error(log_entry)
    elif severity == 'MEDIUM':
        security_logger.warning(log_entry)
    else:
        security_logger.info(log_entry)

@app.errorhandler(429)
def handle_rate_limit(e):
    """Handle rate limit exceeded"""
    log_security_event('RATE_LIMIT_EXCEEDED', 
                      {'limit': str(e.description)}, 
                      'MEDIUM')
    return jsonify({
        'error': 'Rate limit exceeded',
        'message': 'Please wait before making another request'
    }), 429

@app.errorhandler(400)
def handle_bad_request(e):
    """Handle bad requests"""
    log_security_event('BAD_REQUEST', 
                      {'error': str(e.description)}, 
                      'LOW')
    return jsonify({
        'error': 'Bad request',
        'message': 'Invalid request format'
    }), 400
```

## Implementation Priority

1. **Immediate (Today):**
   - Add security headers middleware
   - Fix rate limiting configuration
   - Implement basic input validation

2. **Within 24 hours:**
   - Strengthen authentication security
   - Add comprehensive error handling
   - Set up security logging

3. **Within 1 week:**
   - Implement advanced monitoring
   - Add intrusion detection
   - Conduct security audit

## Testing Security Configuration

```bash
# Test security headers
curl -I http://localhost:5001/health

# Test rate limiting
for i in {1..25}; do curl http://localhost:5001/api/stats; done

# Test file upload validation
curl -X POST -F "image=@malicious.php" http://localhost:5001/api/scan

# Test input validation
curl -X POST -H "Content-Type: application/json" \
     -d '{"test":"<script>alert(1)</script>"}' \
     http://localhost:5001/api/auth/login
```

This configuration will address all security vulnerabilities found in the assessment and establish a solid security foundation for production deployment.
