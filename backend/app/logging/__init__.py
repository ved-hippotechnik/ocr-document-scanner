"""
Structured logging module for OCR Document Scanner

Provides structured JSON logging with request ID tracking,
correlation logging, performance metrics, and security event logging.
"""

from .structured_logger import (
    StructuredFormatter,
    RequestIDMiddleware,
    CorrelationLogger,
    PerformanceLogger,
    SecurityLogger,
    setup_structured_logging,
    get_logger,
    get_performance_logger,
    get_security_logger,
    log_performance
)

__all__ = [
    'StructuredFormatter',
    'RequestIDMiddleware', 
    'CorrelationLogger',
    'PerformanceLogger',
    'SecurityLogger',
    'setup_structured_logging',
    'get_logger',
    'get_performance_logger',
    'get_security_logger',
    'log_performance'
]