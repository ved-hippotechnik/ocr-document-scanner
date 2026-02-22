"""
Request signing and verification for enhanced security
"""
import hmac
import hashlib
import time
import base64
import json
from typing import Dict, Any, Optional, Tuple, List
from flask import request, current_app
import logging

logger = logging.getLogger(__name__)


class RequestSigner:
    """Handle request signing and verification"""
    
    def __init__(self, secret_key: str, algorithm: str = 'sha256'):
        self.secret_key = secret_key.encode() if isinstance(secret_key, str) else secret_key
        self.algorithm = algorithm
        self.hash_func = getattr(hashlib, algorithm)
    
    def sign_request(self, 
                    method: str,
                    path: str,
                    body: bytes = b'',
                    timestamp: Optional[int] = None,
                    nonce: Optional[str] = None) -> str:
        """
        Sign a request with HMAC
        
        Args:
            method: HTTP method (GET, POST, etc.)
            path: Request path
            body: Request body bytes
            timestamp: Unix timestamp (defaults to current time)
            nonce: Random nonce for replay protection
            
        Returns:
            Base64-encoded signature
        """
        if timestamp is None:
            timestamp = int(time.time())
        
        if nonce is None:
            nonce = base64.urlsafe_b64encode(hashlib.sha256(str(timestamp).encode()).digest())[:16].decode()
        
        # Create string to sign
        string_to_sign = self._create_string_to_sign(method, path, body, timestamp, nonce)
        
        # Generate HMAC signature
        signature = hmac.new(
            self.secret_key,
            string_to_sign.encode('utf-8'),
            self.hash_func
        ).digest()
        
        return base64.b64encode(signature).decode('utf-8')
    
    def verify_request(self,
                      method: str,
                      path: str,
                      body: bytes,
                      signature: str,
                      timestamp: int,
                      nonce: str,
                      max_age: int = 300) -> Tuple[bool, Optional[str]]:
        """
        Verify a signed request
        
        Args:
            method: HTTP method
            path: Request path
            body: Request body bytes
            signature: Base64-encoded signature
            timestamp: Request timestamp
            nonce: Request nonce
            max_age: Maximum age in seconds (default 5 minutes)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        current_time = int(time.time())
        
        # Check timestamp freshness
        if abs(current_time - timestamp) > max_age:
            return False, f"Request timestamp too old/new. Age: {abs(current_time - timestamp)}s"
        
        # Verify nonce format
        if not nonce or len(nonce) < 8:
            return False, "Invalid nonce format"
        
        try:
            # Recreate expected signature
            expected_signature = self.sign_request(method, path, body, timestamp, nonce)
            
            # Compare signatures using constant-time comparison
            if not hmac.compare_digest(signature, expected_signature):
                return False, "Signature verification failed"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Signature verification error: {e}")
            return False, f"Signature verification error: {str(e)}"
    
    def _create_string_to_sign(self, 
                              method: str,
                              path: str,
                              body: bytes,
                              timestamp: int,
                              nonce: str) -> str:
        """Create canonical string to sign"""
        # Create body hash
        body_hash = hashlib.sha256(body).hexdigest()
        
        # Create canonical string
        parts = [
            method.upper(),
            path,
            str(timestamp),
            nonce,
            body_hash
        ]
        
        return '\n'.join(parts)


class SecurityHardening:
    """Additional security hardening measures"""
    
    def __init__(self):
        self.rate_limits = {}
        self.blocked_ips = set()
        self.suspicious_patterns = [
            # Common injection patterns
            r'<script.*?>.*?</script>',
            r'javascript:',
            r'vbscript:',
            r'on\w+\s*=',
            r'eval\s*\(',
            r'exec\s*\(',
            r'system\s*\(',
            # SQL injection patterns
            r'union\s+select',
            r'or\s+1\s*=\s*1',
            r'drop\s+table',
            r'delete\s+from',
            # Command injection
            r'[;&|`$]',
            r'\.\./|\.\.\\'
        ]
    
    def validate_request_headers(self, headers: Dict[str, str]) -> Tuple[bool, Optional[str]]:
        """Validate request headers for security"""
        # Only require User-Agent for all requests
        if 'User-Agent' not in headers:
            return False, "Missing required header: User-Agent"
        
        # Validate Content-Type for POST requests only
        if request.method == 'POST':
            content_type = headers.get('Content-Type', '')
            if not content_type:
                return False, "Missing Content-Type header for POST request"
            
            allowed_types = [
                'application/json',
                'multipart/form-data',
                'application/x-www-form-urlencoded'
            ]
            if not any(ct in content_type for ct in allowed_types):
                return False, f"Invalid Content-Type: {content_type}"
        
        # Check for suspicious headers
        suspicious_headers = ['X-Forwarded-Host', 'X-Original-URL', 'X-Rewrite-URL']
        for header in suspicious_headers:
            if header in headers:
                logger.warning(f"Suspicious header detected: {header}")
        
        return True, None
    
    def check_ip_reputation(self, ip_address: str) -> Tuple[bool, Optional[str]]:
        """Check IP address reputation"""
        # Check if IP is blocked
        if ip_address in self.blocked_ips:
            return False, "IP address is blocked"
        
        # Check for private/localhost IPs in production
        if current_app.config.get('FLASK_ENV') == 'production':
            private_ranges = [
                '127.0.0.1',
                '10.',
                '172.16.',
                '192.168.'
            ]
            if any(ip_address.startswith(range_) for range_ in private_ranges):
                logger.warning(f"Private IP access in production: {ip_address}")
        
        return True, None
    
    def validate_request_size(self, content_length: int) -> Tuple[bool, Optional[str]]:
        """Validate request size limits"""
        max_size = current_app.config.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)  # 16MB default
        
        if content_length > max_size:
            return False, f"Request too large: {content_length} bytes (max: {max_size})"
        
        return True, None
    
    def scan_for_malicious_content(self, content: str) -> Tuple[bool, List[str]]:
        """Scan content for malicious patterns"""
        import re
        
        detected_patterns = []
        
        for pattern in self.suspicious_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                detected_patterns.append(pattern)
        
        is_safe = len(detected_patterns) == 0
        return is_safe, detected_patterns
    
    def apply_rate_limiting(self, 
                           identifier: str,
                           limit: int = 100,
                           window: int = 3600) -> Tuple[bool, Optional[str]]:
        """Apply rate limiting per identifier"""
        current_time = time.time()
        
        # Clean old entries
        self._cleanup_rate_limits(current_time - window)
        
        # Get current count for identifier
        if identifier not in self.rate_limits:
            self.rate_limits[identifier] = []
        
        # Count requests in current window
        request_times = self.rate_limits[identifier]
        recent_requests = [t for t in request_times if t > current_time - window]
        
        if len(recent_requests) >= limit:
            return False, f"Rate limit exceeded: {len(recent_requests)}/{limit} requests in {window}s"
        
        # Add current request
        recent_requests.append(current_time)
        self.rate_limits[identifier] = recent_requests
        
        return True, None
    
    def _cleanup_rate_limits(self, cutoff_time: float):
        """Clean up old rate limit entries"""
        for identifier in list(self.rate_limits.keys()):
            self.rate_limits[identifier] = [
                t for t in self.rate_limits[identifier] 
                if t > cutoff_time
            ]
            if not self.rate_limits[identifier]:
                del self.rate_limits[identifier]
    
    def validate_json_payload(self, payload: str) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """Validate and parse JSON payload safely"""
        try:
            # Check payload size
            if len(payload) > 1024 * 1024:  # 1MB limit for JSON
                return False, "JSON payload too large", None
            
            # Parse JSON with limits
            data = json.loads(payload)
            
            # Check nesting depth
            max_depth = 10
            if self._get_json_depth(data) > max_depth:
                return False, f"JSON nesting too deep (max: {max_depth})", None
            
            # Scan for malicious content in string values
            malicious_strings = []
            self._scan_json_values(data, malicious_strings, parent_key=None)
            
            if malicious_strings:
                return False, f"Malicious content detected: {malicious_strings[:3]}", None
            
            return True, None, data
            
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {str(e)}", None
        except Exception as e:
            return False, f"JSON validation error: {str(e)}", None
    
    def _get_json_depth(self, obj, depth=0):
        """Calculate JSON nesting depth"""
        if isinstance(obj, dict):
            return max([self._get_json_depth(v, depth + 1) for v in obj.values()], default=depth)
        elif isinstance(obj, list):
            return max([self._get_json_depth(item, depth + 1) for item in obj], default=depth)
        else:
            return depth
    
    def _scan_json_values(self, obj, malicious_strings, parent_key=None):
        """Recursively scan JSON values for malicious content"""
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(key, str):
                    is_safe, patterns = self.scan_for_malicious_content(key)
                    if not is_safe:
                        malicious_strings.extend(patterns)
                # Skip scanning image data and credential fields
                if key not in ['image', 'imageData', 'base64', 'file', 'data', 'password', 'secret', 'token', 'api_key']:
                    self._scan_json_values(value, malicious_strings, parent_key=key)
        elif isinstance(obj, list):
            for item in obj:
                self._scan_json_values(item, malicious_strings, parent_key=parent_key)
        elif isinstance(obj, str):
            # Skip base64 image data (starts with data:image or is very long)
            if obj.startswith('data:image') or (len(obj) > 1000 and parent_key in ['image', 'imageData', 'base64', 'file', 'data']):
                return
            is_safe, patterns = self.scan_for_malicious_content(obj)
            if not is_safe:
                malicious_strings.extend(patterns)


def create_request_signer() -> RequestSigner:
    """Create request signer with app secret"""
    secret_key = current_app.config.get('SECRET_KEY', 'dev-key')
    return RequestSigner(secret_key)


def verify_signed_request() -> Tuple[bool, Optional[str]]:
    """Verify current request signature"""
    try:
        # Get signature headers
        signature = request.headers.get('X-Signature')
        timestamp = request.headers.get('X-Timestamp')
        nonce = request.headers.get('X-Nonce')
        
        if not all([signature, timestamp, nonce]):
            return False, "Missing signature headers"
        
        # Parse timestamp
        try:
            timestamp = int(timestamp)
        except ValueError:
            return False, "Invalid timestamp format"
        
        # Get request data
        method = request.method
        path = request.path
        body = request.get_data()
        
        # Verify signature
        signer = create_request_signer()
        is_valid, error = signer.verify_request(method, path, body, signature, timestamp, nonce)
        
        return is_valid, error
        
    except Exception as e:
        logger.error(f"Request verification error: {e}")
        return False, f"Verification error: {str(e)}"


# Global security hardening instance
security_hardening = SecurityHardening()