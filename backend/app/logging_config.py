"""
Production-ready logging configuration for OCR Document Scanner
"""
import os
import sys
import logging
import logging.handlers
from pathlib import Path
from pythonjsonlogger import jsonlogger
import traceback
from datetime import datetime

def setup_logging(app):
    """Configure comprehensive logging for production"""
    
    # Get configuration from environment
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    log_file = os.getenv('LOG_FILE', 'logs/app.log')
    log_format = os.getenv('LOG_FORMAT', 'json')  # 'json' or 'text'
    flask_env = os.getenv('FLASK_ENV', 'development')
    
    # Create logs directory if it doesn't exist
    if log_file:
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    
    # Remove default handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create formatters
    if log_format == 'json':
        # JSON formatter for structured logging
        json_formatter = jsonlogger.JsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s',
            rename_fields={
                'timestamp': '@timestamp',
                'level': 'log.level',
                'name': 'log.logger'
            }
        )
        formatter = json_formatter
    else:
        # Text formatter for human-readable logs
        text_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        formatter = text_formatter
    
    # Console handler (always enabled)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO if flask_env == 'production' else logging.DEBUG)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=int(os.getenv('LOG_MAX_BYTES', 10485760)),  # 10MB default
            backupCount=int(os.getenv('LOG_BACKUP_COUNT', 5))
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(getattr(logging, log_level))
        root_logger.addHandler(file_handler)
    
    # Sentry integration for error tracking (production only)
    if flask_env == 'production':
        sentry_dsn = os.getenv('SENTRY_DSN')
        if sentry_dsn:
            try:
                import sentry_sdk
                from sentry_sdk.integrations.flask import FlaskIntegration
                from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
                from sentry_sdk.integrations.celery import CeleryIntegration
                
                sentry_sdk.init(
                    dsn=sentry_dsn,
                    integrations=[
                        FlaskIntegration(transaction_style='endpoint'),
                        SqlalchemyIntegration(),
                        CeleryIntegration(),
                    ],
                    traces_sample_rate=float(os.getenv('SENTRY_TRACES_SAMPLE_RATE', 0.1)),
                    environment=flask_env,
                    attach_stacktrace=True,
                    send_default_pii=False,  # Don't send PII
                )
                app.logger.info("Sentry error tracking initialized")
            except ImportError:
                app.logger.warning("Sentry SDK not installed, error tracking disabled")
            except Exception as e:
                app.logger.error(f"Failed to initialize Sentry: {e}")
    
    # Configure specific loggers
    configure_module_loggers(formatter, log_level)
    
    # Add context filter for additional fields
    for handler in root_logger.handlers:
        handler.addFilter(ContextFilter())
    
    # Log uncaught exceptions
    sys.excepthook = log_uncaught_exception
    
    app.logger.info(f"Logging configured - Level: {log_level}, Format: {log_format}, Environment: {flask_env}")
    
    return root_logger


def configure_module_loggers(formatter, log_level):
    """Configure logging for specific modules"""
    
    # Reduce verbosity of certain modules
    noisy_loggers = [
        'werkzeug',
        'urllib3',
        'requests',
        'PIL',
        'matplotlib',
        'tensorflow',
    ]
    
    for logger_name in noisy_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.WARNING)
    
    # Configure SQLAlchemy logging
    if os.getenv('LOG_SQL_QUERIES', 'false').lower() == 'true':
        logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
        logging.getLogger('sqlalchemy.pool').setLevel(logging.DEBUG)
    else:
        logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
    
    # Configure app-specific loggers with appropriate levels
    app_loggers = {
        'app.auth': logging.INFO,
        'app.ocr': logging.INFO,
        'app.security': logging.INFO,
        'app.database': logging.WARNING,
        'app.cache': logging.WARNING,
        'app.celery': logging.INFO,
    }
    
    for logger_name, level in app_loggers.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)


class ContextFilter(logging.Filter):
    """Add context information to log records"""
    
    def filter(self, record):
        """Add additional context to log records"""
        from flask import g, request, has_request_context
        
        # Add timestamp
        record.timestamp = datetime.utcnow().isoformat()
        
        # Add request context if available
        if has_request_context():
            record.request_id = getattr(g, 'request_id', 'no-request-id')
            record.user_id = getattr(g, 'user_id', 'anonymous')
            record.ip_address = getattr(g, 'client_ip', request.remote_addr)
            record.method = request.method
            record.path = request.path
            record.user_agent = request.user_agent.string
        else:
            record.request_id = 'no-request-context'
            record.user_id = 'system'
            record.ip_address = 'localhost'
            record.method = 'SYSTEM'
            record.path = 'internal'
            record.user_agent = 'internal'
        
        # Add hostname
        import socket
        record.hostname = socket.gethostname()
        
        # Add process info
        record.process_id = os.getpid()
        
        return True


def log_uncaught_exception(exc_type, exc_value, exc_traceback):
    """Log uncaught exceptions"""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    logger = logging.getLogger('app.uncaught')
    logger.critical(
        "Uncaught exception",
        exc_info=(exc_type, exc_value, exc_traceback),
        extra={
            'exception_type': exc_type.__name__,
            'exception_value': str(exc_value),
            'traceback': ''.join(traceback.format_tb(exc_traceback))
        }
    )


class SecurityLogger:
    """Specialized logger for security events"""
    
    def __init__(self):
        self.logger = logging.getLogger('app.security.audit')
        
        # Create separate handler for security logs
        security_log_file = os.getenv('SECURITY_LOG_FILE', 'logs/security.log')
        if security_log_file:
            handler = logging.handlers.RotatingFileHandler(
                security_log_file,
                maxBytes=10485760,  # 10MB
                backupCount=10
            )
            
            # Use JSON format for security logs
            formatter = jsonlogger.JsonFormatter(
                '%(timestamp)s %(level)s %(event_type)s %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def log_auth_attempt(self, username, success, ip_address, reason=None):
        """Log authentication attempts"""
        self.logger.info(
            "Authentication attempt",
            extra={
                'event_type': 'auth_attempt',
                'username': username,
                'success': success,
                'ip_address': ip_address,
                'reason': reason,
                'timestamp': datetime.utcnow().isoformat()
            }
        )
    
    def log_access_denied(self, user_id, resource, reason):
        """Log access denied events"""
        self.logger.warning(
            "Access denied",
            extra={
                'event_type': 'access_denied',
                'user_id': user_id,
                'resource': resource,
                'reason': reason,
                'timestamp': datetime.utcnow().isoformat()
            }
        )
    
    def log_suspicious_activity(self, ip_address, activity_type, details):
        """Log suspicious activities"""
        self.logger.warning(
            "Suspicious activity detected",
            extra={
                'event_type': 'suspicious_activity',
                'ip_address': ip_address,
                'activity_type': activity_type,
                'details': details,
                'timestamp': datetime.utcnow().isoformat()
            }
        )
    
    def log_file_upload(self, user_id, filename, file_size, validation_result):
        """Log file upload events"""
        self.logger.info(
            "File upload",
            extra={
                'event_type': 'file_upload',
                'user_id': user_id,
                'filename': filename,
                'file_size': file_size,
                'validation_result': validation_result,
                'timestamp': datetime.utcnow().isoformat()
            }
        )


class PerformanceLogger:
    """Logger for performance metrics"""
    
    def __init__(self):
        self.logger = logging.getLogger('app.performance')
    
    def log_request_duration(self, endpoint, method, duration_ms, status_code):
        """Log request duration"""
        self.logger.info(
            "Request completed",
            extra={
                'endpoint': endpoint,
                'method': method,
                'duration_ms': duration_ms,
                'status_code': status_code,
                'timestamp': datetime.utcnow().isoformat()
            }
        )
    
    def log_db_query(self, query, duration_ms):
        """Log database query performance"""
        self.logger.debug(
            "Database query executed",
            extra={
                'query': query[:200],  # Truncate long queries
                'duration_ms': duration_ms,
                'timestamp': datetime.utcnow().isoformat()
            }
        )
    
    def log_ocr_processing(self, document_type, processing_time, success):
        """Log OCR processing metrics"""
        self.logger.info(
            "OCR processing completed",
            extra={
                'document_type': document_type,
                'processing_time': processing_time,
                'success': success,
                'timestamp': datetime.utcnow().isoformat()
            }
        )


# Initialize specialized loggers
security_logger = SecurityLogger()
performance_logger = PerformanceLogger()