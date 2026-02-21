"""
Structured logging with request ID tracking
"""
import json
import logging
import uuid
import time
from datetime import datetime
from typing import Dict, Any, Optional
from flask import request, g, current_app
import traceback


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging"""
    
    def __init__(self, include_request_info: bool = True):
        super().__init__()
        self.include_request_info = include_request_info
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON"""
        # Base log entry
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add request context if available and enabled
        if self.include_request_info and self._has_request_context():
            request_info = self._get_request_info()
            if request_info:
                log_entry['request'] = request_info
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields from record
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'lineno', 'funcName', 'created', 
                          'msecs', 'relativeCreated', 'thread', 'threadName', 
                          'processName', 'process', 'message', 'exc_info', 'exc_text',
                          'stack_info']:
                extra_fields[key] = value
        
        if extra_fields:
            log_entry['extra'] = extra_fields
        
        return json.dumps(log_entry, default=str, ensure_ascii=False)
    
    def _has_request_context(self) -> bool:
        """Check if we're in a request context"""
        try:
            return request is not None
        except RuntimeError:
            return False
    
    def _get_request_info(self) -> Optional[Dict[str, Any]]:
        """Extract request information for logging"""
        try:
            info = {
                'id': getattr(g, 'request_id', None),
                'method': request.method,
                'path': request.path,
                'remote_addr': getattr(g, 'client_ip', request.remote_addr),
                'user_agent': request.headers.get('User-Agent', 'unknown')[:200],  # Truncate long UAs
            }
            
            # Add user info if available
            if hasattr(g, 'current_user') and g.current_user:
                info['user_id'] = getattr(g.current_user, 'id', None)
                info['username'] = getattr(g.current_user, 'username', None)
            
            # Add timing info if available
            if hasattr(g, 'request_start_time'):
                info['duration_ms'] = round((time.time() - g.request_start_time) * 1000, 2)
            
            # Add response info if available
            if hasattr(g, 'response_status'):
                info['status_code'] = g.response_status
            
            return info
            
        except Exception:
            return None


class RequestIDMiddleware:
    """Middleware to add request IDs to all requests"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the middleware with Flask app"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
    
    def before_request(self):
        """Generate request ID and start timing"""
        # Generate unique request ID
        request_id = self._generate_request_id()
        g.request_id = request_id
        g.request_start_time = time.time()
        
        # Log request start
        current_app.logger.info(
            "Request started",
            extra={
                'event_type': 'request_start',
                'request_id': request_id,
                'method': request.method,
                'path': request.path,
                'content_length': request.content_length or 0
            }
        )
    
    def after_request(self, response):
        """Log request completion"""
        try:
            duration_ms = round((time.time() - g.request_start_time) * 1000, 2)
            g.response_status = response.status_code
            
            # Add request ID to response headers
            response.headers['X-Request-ID'] = g.request_id
            
            # Log request completion
            current_app.logger.info(
                "Request completed",
                extra={
                    'event_type': 'request_end',
                    'request_id': g.request_id,
                    'status_code': response.status_code,
                    'duration_ms': duration_ms,
                    'response_size': len(response.get_data()) if response.get_data() else 0
                }
            )
            
        except Exception as e:
            current_app.logger.error(f"Error in after_request logging: {e}")
        
        return response
    
    def _generate_request_id(self) -> str:
        """Generate a unique request ID"""
        return str(uuid.uuid4())


class CorrelationLogger:
    """Logger with correlation ID support for distributed tracing"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.name = name
    
    def _get_correlation_id(self) -> Optional[str]:
        """Get correlation ID from request context"""
        try:
            return getattr(g, 'correlation_id', getattr(g, 'request_id', None))
        except RuntimeError:
            return None
    
    def _log_with_correlation(self, level: int, message: str, **kwargs):
        """Log message with correlation ID"""
        extra = kwargs.pop('extra', {})
        
        # Add correlation ID
        correlation_id = self._get_correlation_id()
        if correlation_id:
            extra['correlation_id'] = correlation_id
        
        # Add any additional context
        extra.update(kwargs)
        
        self.logger.log(level, message, extra=extra)
    
    def debug(self, message: str, **kwargs):
        self._log_with_correlation(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        self._log_with_correlation(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self._log_with_correlation(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        self._log_with_correlation(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        self._log_with_correlation(logging.CRITICAL, message, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """Log exception with full traceback"""
        extra = kwargs.pop('extra', {})
        correlation_id = self._get_correlation_id()
        if correlation_id:
            extra['correlation_id'] = correlation_id
        extra.update(kwargs)
        
        self.logger.exception(message, extra=extra)


class PerformanceLogger:
    """Logger for performance metrics and timing"""
    
    def __init__(self, name: str = 'performance'):
        self.logger = CorrelationLogger(name)
    
    def log_operation_time(self, operation: str, duration_ms: float, **context):
        """Log operation timing"""
        self.logger.info(
            f"Operation completed: {operation}",
            extra={
                'event_type': 'performance',
                'operation': operation,
                'duration_ms': duration_ms,
                **context
            }
        )
    
    def log_database_query(self, query: str, duration_ms: float, rows_affected: int = None):
        """Log database query performance"""
        self.logger.info(
            "Database query executed",
            extra={
                'event_type': 'database_query',
                'query': query[:200],  # Truncate long queries
                'duration_ms': duration_ms,
                'rows_affected': rows_affected
            }
        )
    
    def log_external_api_call(self, 
                             service: str,
                             endpoint: str,
                             method: str,
                             duration_ms: float,
                             status_code: int,
                             response_size: int = None):
        """Log external API call performance"""
        self.logger.info(
            f"External API call: {service}",
            extra={
                'event_type': 'external_api',
                'service': service,
                'endpoint': endpoint,
                'method': method,
                'duration_ms': duration_ms,
                'status_code': status_code,
                'response_size': response_size
            }
        )


class SecurityLogger:
    """Logger for security events"""
    
    def __init__(self, name: str = 'security'):
        self.logger = CorrelationLogger(name)
    
    def log_authentication_attempt(self, username: str, success: bool, reason: str = None):
        """Log authentication attempt"""
        self.logger.info(
            f"Authentication {'successful' if success else 'failed'}: {username}",
            extra={
                'event_type': 'authentication',
                'username': username,
                'success': success,
                'reason': reason,
                'client_ip': getattr(g, 'client_ip', 'unknown')
            }
        )
    
    def log_authorization_failure(self, user_id: str, resource: str, action: str):
        """Log authorization failure"""
        self.logger.warning(
            f"Authorization denied: user {user_id} tried to {action} {resource}",
            extra={
                'event_type': 'authorization_denied',
                'user_id': user_id,
                'resource': resource,
                'action': action,
                'client_ip': getattr(g, 'client_ip', 'unknown')
            }
        )
    
    def log_suspicious_activity(self, activity_type: str, details: Dict[str, Any]):
        """Log suspicious activity"""
        self.logger.warning(
            f"Suspicious activity detected: {activity_type}",
            extra={
                'event_type': 'suspicious_activity',
                'activity_type': activity_type,
                'details': details,
                'client_ip': getattr(g, 'client_ip', 'unknown')
            }
        )
    
    def log_rate_limit_exceeded(self, identifier: str, limit: int, window: int):
        """Log rate limit violation"""
        self.logger.warning(
            f"Rate limit exceeded for {identifier}",
            extra={
                'event_type': 'rate_limit_exceeded',
                'identifier': identifier,
                'limit': limit,
                'window': window,
                'client_ip': getattr(g, 'client_ip', 'unknown')
            }
        )


def setup_structured_logging(app):
    """Setup structured logging for the Flask app"""
    # Configure root logger
    root_logger = logging.getLogger()
    
    # Remove default handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create structured formatter
    formatter = StructuredFormatter(include_request_info=True)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Create file handler if configured
    log_file = app.config.get('LOG_FILE')
    if log_file:
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Add console handler
    root_logger.addHandler(console_handler)
    
    # Set log level
    log_level = app.config.get('LOG_LEVEL', 'INFO')
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Setup request ID middleware
    request_id_middleware = RequestIDMiddleware()
    request_id_middleware.init_app(app)
    
    app.logger.info("Structured logging initialized")


def get_logger(name: str) -> CorrelationLogger:
    """Get a correlation-aware logger"""
    return CorrelationLogger(name)


def get_performance_logger() -> PerformanceLogger:
    """Get performance logger"""
    return PerformanceLogger()


def get_security_logger() -> SecurityLogger:
    """Get security logger"""
    return SecurityLogger()


# Performance monitoring decorator
def log_performance(operation_name: str = None):
    """Decorator to log function performance"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            operation = operation_name or f"{func.__module__}.{func.__name__}"
            
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                perf_logger = get_performance_logger()
                perf_logger.log_operation_time(operation, duration_ms)
                
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                logger = get_logger(func.__module__)
                logger.error(
                    f"Operation failed: {operation}",
                    extra={
                        'operation': operation,
                        'duration_ms': duration_ms,
                        'error': str(e)
                    }
                )
                raise
        
        return wrapper
    return decorator