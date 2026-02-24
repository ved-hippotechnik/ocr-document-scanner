"""
Application monitoring and metrics collection
"""
import time
import os
import psutil
import logging
from flask import request, g
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from functools import wraps
from datetime import datetime

logger = logging.getLogger(__name__)

# Prometheus metrics
request_count = Counter(
    'app_requests_total',
    'Total request count',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'app_request_duration_seconds',
    'Request latency in seconds',
    ['method', 'endpoint']
)

active_requests = Gauge(
    'app_active_requests',
    'Number of active requests'
)

ocr_processing_time = Histogram(
    'ocr_processing_duration_seconds',
    'OCR processing time in seconds',
    ['document_type', 'status']
)

ocr_error_count = Counter(
    'ocr_errors_total',
    'Total OCR processing errors',
    ['document_type', 'error_type']
)

database_query_duration = Histogram(
    'database_query_duration_seconds',
    'Database query duration',
    ['operation']
)

cache_hits = Counter(
    'cache_hits_total',
    'Cache hit count',
    ['cache_type']
)

cache_misses = Counter(
    'cache_misses_total',
    'Cache miss count',
    ['cache_type']
)

ocr_timeout_count = Counter(
    'ocr_timeouts_total',
    'Total OCR timeout events',
    ['document_type']
)

circuit_breaker_state = Gauge(
    'circuit_breaker_state',
    'Circuit breaker state (0=closed, 1=half_open, 2=open)',
    ['service']
)

celery_queue_depth = Gauge(
    'celery_queue_depth',
    'Number of tasks in Celery queue',
    ['queue_name']
)

rate_limit_exceeded = Counter(
    'rate_limit_exceeded_total',
    'Rate limit exceeded count',
    ['endpoint']
)

# System metrics
cpu_usage = Gauge('system_cpu_usage_percent', 'CPU usage percentage')
memory_usage = Gauge('system_memory_usage_percent', 'Memory usage percentage')
disk_usage = Gauge('system_disk_usage_percent', 'Disk usage percentage')
open_file_descriptors = Gauge('system_open_fds', 'Open file descriptors')

def setup_metrics(app):
    """Setup monitoring and metrics collection"""
    
    @app.before_request
    def before_request():
        """Track request start time and active requests"""
        g.start_time = time.time()
        active_requests.inc()
    
    @app.after_request
    def after_request(response):
        """Record request metrics"""
        if hasattr(g, 'start_time'):
            # Calculate request duration
            duration = time.time() - g.start_time
            
            # Get endpoint information
            endpoint = request.endpoint or 'unknown'
            method = request.method
            status = str(response.status_code)
            
            # Record metrics
            request_count.labels(method=method, endpoint=endpoint, status=status).inc()
            request_duration.labels(method=method, endpoint=endpoint).observe(duration)
            
            # Add timing header
            response.headers['X-Request-Duration'] = str(round(duration * 1000, 2)) + 'ms'
        
        # Decrement active requests
        active_requests.dec()
        
        return response
    
    @app.errorhandler(429)
    def handle_rate_limit(e):
        """Track rate limit violations"""
        endpoint = request.endpoint or 'unknown'
        rate_limit_exceeded.labels(endpoint=endpoint).inc()
        return {'error': 'Rate limit exceeded', 'message': str(e.description)}, 429
    
    @app.route('/metrics')
    def metrics():
        """Prometheus metrics endpoint"""
        # Update system metrics
        update_system_metrics()
        
        # Generate Prometheus format metrics
        return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}
    
    @app.route('/api/metrics/summary')
    def metrics_summary():
        """JSON format metrics summary"""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'requests': {
                'total': get_metric_value(request_count),
                'active': get_metric_value(active_requests),
                'errors': get_error_rate()
            },
            'performance': {
                'avg_response_time': get_avg_response_time(),
                'p95_response_time': get_percentile_response_time(0.95),
                'p99_response_time': get_percentile_response_time(0.99)
            },
            'system': {
                'cpu_usage': psutil.cpu_percent(),
                'memory_usage': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('/').percent
            },
            'cache': {
                'hit_rate': get_cache_hit_rate()
            }
        }
    
    logger.info("Monitoring and metrics initialized")

def update_system_metrics():
    """Update system resource metrics"""
    try:
        # CPU usage
        cpu_usage.set(psutil.cpu_percent(interval=0.1))
        
        # Memory usage
        memory_usage.set(psutil.virtual_memory().percent)
        
        # Disk usage
        disk_usage.set(psutil.disk_usage('/').percent)
        
        # Open file descriptors
        process = psutil.Process()
        open_file_descriptors.set(len(process.open_files()))
        
    except Exception as e:
        logger.error(f"Failed to update system metrics: {e}")

def track_ocr_processing(document_type: str):
    """Decorator to track OCR processing metrics"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            status = 'success'
            
            try:
                result = f(*args, **kwargs)
                return result
            except Exception as e:
                status = 'error'
                error_type = type(e).__name__
                ocr_error_count.labels(document_type=document_type, error_type=error_type).inc()
                raise
            finally:
                duration = time.time() - start_time
                ocr_processing_time.labels(document_type=document_type, status=status).observe(duration)
        
        return wrapper
    return decorator

def track_database_operation(operation: str):
    """Decorator to track database operation metrics"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = f(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                database_query_duration.labels(operation=operation).observe(duration)
        
        return wrapper
    return decorator

def track_cache_access(cache_type: str = 'default'):
    """Track cache hits and misses"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            result = f(*args, **kwargs)
            
            # Determine if it's a hit or miss based on result
            if result is not None:
                cache_hits.labels(cache_type=cache_type).inc()
            else:
                cache_misses.labels(cache_type=cache_type).inc()
            
            return result
        
        return wrapper
    return decorator

# Helper functions for metrics calculation
def get_metric_value(metric):
    """Get current value of a metric"""
    try:
        return metric._value.get()
    except:
        return 0

def get_error_rate():
    """Calculate error rate"""
    try:
        total = get_metric_value(request_count)
        if total == 0:
            return 0
        
        # Count 4xx and 5xx responses
        errors = sum([
            request_count.labels(method=m, endpoint=e, status=s)._value.get()
            for m in ['GET', 'POST', 'PUT', 'DELETE']
            for e in ['main.scan_document', 'improved.scan_document_v3']
            for s in ['400', '401', '403', '404', '500', '502', '503']
        ])
        
        return round(errors / total * 100, 2)
    except:
        return 0

def get_avg_response_time():
    """Calculate average response time"""
    try:
        # This is a simplification - in production, use Prometheus query
        return round(request_duration._sum.get() / request_duration._count.get() * 1000, 2)
    except:
        return 0

def get_percentile_response_time(percentile):
    """Calculate percentile response time"""
    try:
        # This would require proper histogram calculation
        # For now, return a placeholder
        avg = get_avg_response_time()
        if percentile == 0.95:
            return avg * 1.5
        elif percentile == 0.99:
            return avg * 2
        return avg
    except:
        return 0

def get_cache_hit_rate():
    """Calculate cache hit rate"""
    try:
        hits = get_metric_value(cache_hits)
        misses = get_metric_value(cache_misses)
        total = hits + misses
        
        if total == 0:
            return 0
        
        return round(hits / total * 100, 2)
    except:
        return 0

def check_alerting_rules():
    """Check system metrics and return alerts for critical conditions."""
    alerts = []

    try:
        cpu = psutil.cpu_percent(interval=0.5)
        if cpu > 90:
            alert_msg = f"CPU usage critically high: {cpu}%"
            logger.critical("ALERT: %s", alert_msg)
            alerts.append(alert_msg)
    except Exception as e:
        logger.error(f"Failed to check CPU usage: {e}")

    try:
        mem = psutil.virtual_memory().percent
        if mem > 90:
            alert_msg = f"Memory usage critically high: {mem}%"
            logger.critical("ALERT: %s", alert_msg)
            alerts.append(alert_msg)
    except Exception as e:
        logger.error(f"Failed to check memory usage: {e}")

    return alerts


class PerformanceMonitor:
    """Context manager for performance monitoring"""
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        if exc_type is None:
            logger.info(f"{self.operation_name} completed in {duration:.3f}s")
        else:
            logger.error(f"{self.operation_name} failed after {duration:.3f}s: {exc_val}")
        
        return False