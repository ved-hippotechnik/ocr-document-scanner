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
from datetime import datetime, timezone

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

# Batch processing metrics (Q7)
batch_jobs_active = Gauge(
    'batch_jobs_active',
    'Number of currently active batch jobs',
)

batch_jobs_total = Counter(
    'batch_jobs_total',
    'Total batch jobs submitted',
    ['status'],
)

batch_documents_processed = Counter(
    'batch_documents_processed_total',
    'Total documents processed in batches',
    ['status'],
)

batch_job_duration = Histogram(
    'batch_job_duration_seconds',
    'Duration of batch processing jobs',
    buckets=[1, 5, 10, 30, 60, 120, 300, 600],
)

# Vision API metrics (Q7)
vision_api_duration = Histogram(
    'vision_api_duration_seconds',
    'Claude Vision API call duration',
    ['operation'],
    buckets=[0.5, 1, 2, 5, 10, 30],
)

vision_api_errors = Counter(
    'vision_api_errors_total',
    'Claude Vision API error count',
    ['operation', 'error_type'],
)

# Redis reconnection metrics (Q7)
redis_reconnection_attempts = Counter(
    'redis_reconnection_attempts_total',
    'Number of Redis reconnection attempts',
    ['result'],
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
            'timestamp': datetime.now(timezone.utc).isoformat(),
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
    except Exception:
        return 0


def get_error_rate():
    """
    Calculate error rate by iterating over all collected label values.

    Previous implementation hardcoded endpoint names — this version
    dynamically discovers all recorded label combinations.
    """
    try:
        total_requests = 0
        error_requests = 0

        # Iterate over all samples in the request_count metric family
        for metric_family in request_count.collect():
            for sample in metric_family.samples:
                if sample.name.endswith('_total') or sample.name == metric_family.name:
                    count = sample.value
                    total_requests += count
                    status = sample.labels.get('status', '200')
                    if status.startswith('4') or status.startswith('5'):
                        error_requests += count

        if total_requests == 0:
            return 0

        return round(error_requests / total_requests * 100, 2)
    except Exception as e:
        logger.error("Failed to compute error rate: %s", e)
        return 0


def get_avg_response_time():
    """Calculate average response time in milliseconds."""
    try:
        total_sum = 0
        total_count = 0
        for metric_family in request_duration.collect():
            for sample in metric_family.samples:
                if sample.name.endswith('_sum'):
                    total_sum += sample.value
                elif sample.name.endswith('_count'):
                    total_count += sample.value

        if total_count == 0:
            return 0
        return round(total_sum / total_count * 1000, 2)
    except Exception as e:
        logger.error("Failed to compute avg response time: %s", e)
        return 0


def get_percentile_response_time(percentile):
    """
    Estimate percentile response time from Histogram buckets.

    Uses linear interpolation across histogram bucket boundaries —
    the same algorithm Prometheus uses for histogram_quantile().
    """
    try:
        buckets, total_count = _collect_histogram_buckets()
        if total_count == 0 or not buckets:
            return 0
        return round(_interpolate_quantile(buckets, total_count, percentile) * 1000, 2)
    except Exception as e:
        logger.error("Failed to compute p%d response time: %s", int(percentile * 100), e)
        return 0


def _collect_histogram_buckets():
    """Collect cumulative bucket counts from the request_duration histogram."""
    buckets = {}
    total_count = 0
    for metric_family in request_duration.collect():
        for sample in metric_family.samples:
            if sample.name.endswith('_bucket'):
                le = sample.labels.get('le', '+Inf')
                le_float = float('inf') if le == '+Inf' else float(le)
                buckets[le_float] = buckets.get(le_float, 0) + sample.value
            elif sample.name.endswith('_count'):
                total_count += sample.value
    return buckets, total_count


def _interpolate_quantile(buckets, total_count, percentile):
    """Linear interpolation within histogram buckets to estimate a quantile."""
    target = percentile * total_count
    prev_boundary = 0
    prev_count = 0
    for boundary in sorted(buckets.keys()):
        current_count = buckets[boundary]
        if current_count >= target:
            if current_count == prev_count:
                return boundary
            fraction = (target - prev_count) / (current_count - prev_count)
            return prev_boundary + fraction * (boundary - prev_boundary)
        prev_boundary = boundary
        prev_count = current_count
    return get_avg_response_time() / 1000  # fallback in seconds


def get_cache_hit_rate():
    """Calculate cache hit rate"""
    try:
        hits = get_metric_value(cache_hits)
        misses = get_metric_value(cache_misses)
        total = hits + misses

        if total == 0:
            return 0

        return round(hits / total * 100, 2)
    except Exception as e:
        logger.error("Failed to compute cache hit rate: %s", e)
        return 0


_ALERT_LOG_FMT = "ALERT: %s"


def _emit_alert(alerts, msg):
    """Log a critical alert and append it to the alerts list."""
    logger.critical(_ALERT_LOG_FMT, msg)
    alerts.append(msg)


def check_alerting_rules():
    """
    Check system metrics and return alerts for critical conditions.

    Thresholds:
    - CPU > 90%
    - Memory > 90%
    - Error rate > 5%
    - Average response time > 10s
    - Active requests > 100
    """
    alerts = []

    try:
        cpu = psutil.cpu_percent(interval=0.5)
        if cpu > 90:
            _emit_alert(alerts, f"CPU usage critically high: {cpu}%")
    except Exception as e:
        logger.error("Failed to check CPU usage: %s", e)

    try:
        mem = psutil.virtual_memory().percent
        if mem > 90:
            _emit_alert(alerts, f"Memory usage critically high: {mem}%")
    except Exception as e:
        logger.error("Failed to check memory usage: %s", e)

    try:
        error_rate = get_error_rate()
        if error_rate > 5:
            _emit_alert(alerts, f"Error rate critically high: {error_rate}%")
    except Exception as e:
        logger.error("Failed to check error rate: %s", e)

    try:
        avg_response = get_avg_response_time()
        if avg_response > 10000:  # 10 seconds in ms
            _emit_alert(alerts, f"Average response time critically high: {avg_response}ms")
    except Exception as e:
        logger.error("Failed to check response time: %s", e)

    try:
        active = get_metric_value(active_requests)
        if active > 100:
            _emit_alert(alerts, f"Active requests critically high: {active}")
    except Exception as e:
        logger.error("Failed to check active requests: %s", e)

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