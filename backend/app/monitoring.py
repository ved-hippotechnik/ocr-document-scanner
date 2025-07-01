"""
Monitoring and metrics for OCR Document Scanner
"""
import time
import functools
from flask import request, g
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import logging

# Prometheus metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration', ['method', 'endpoint'])
DOCUMENT_PROCESSING_COUNT = Counter('document_processing_total', 'Total documents processed', ['document_type', 'status'])
DOCUMENT_PROCESSING_DURATION = Histogram('document_processing_duration_seconds', 'Document processing duration', ['document_type'])
OCR_CONFIDENCE_GAUGE = Gauge('ocr_confidence_score', 'OCR confidence score', ['document_type'])
ACTIVE_PROCESSING = Gauge('active_document_processing', 'Currently processing documents')

logger = logging.getLogger(__name__)


def setup_metrics(app):
    """Setup metrics collection for Flask app"""
    
    @app.before_request
    def before_request():
        g.start_time = time.time()
    
    @app.after_request
    def after_request(response):
        # Record request metrics
        duration = time.time() - g.start_time
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.endpoint or 'unknown',
            status=response.status_code
        ).inc()
        
        REQUEST_DURATION.labels(
            method=request.method,
            endpoint=request.endpoint or 'unknown'
        ).observe(duration)
        
        return response
    
    @app.route('/metrics')
    def metrics():
        """Prometheus metrics endpoint"""
        return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}


def track_document_processing(document_type):
    """Decorator to track document processing metrics"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            ACTIVE_PROCESSING.inc()
            
            try:
                result = func(*args, **kwargs)
                
                # Record success metrics
                DOCUMENT_PROCESSING_COUNT.labels(
                    document_type=document_type,
                    status='success'
                ).inc()
                
                # Record confidence if available
                if isinstance(result, dict) and 'confidence' in result:
                    confidence_map = {'high': 0.9, 'medium': 0.7, 'low': 0.5}
                    confidence_score = confidence_map.get(result['confidence'], 0.5)
                    OCR_CONFIDENCE_GAUGE.labels(document_type=document_type).set(confidence_score)
                
                return result
                
            except Exception as e:
                DOCUMENT_PROCESSING_COUNT.labels(
                    document_type=document_type,
                    status='error'
                ).inc()
                logger.error(f"Document processing error for {document_type}: {e}")
                raise
                
            finally:
                duration = time.time() - start_time
                DOCUMENT_PROCESSING_DURATION.labels(document_type=document_type).observe(duration)
                ACTIVE_PROCESSING.dec()
        
        return wrapper
    return decorator


class PerformanceMonitor:
    """Monitor system performance and OCR accuracy"""
    
    def __init__(self):
        self.processing_times = {}
        self.accuracy_scores = {}
        self.error_counts = {}
    
    def record_processing_time(self, document_type: str, duration: float):
        """Record processing time for document type"""
        if document_type not in self.processing_times:
            self.processing_times[document_type] = []
        self.processing_times[document_type].append(duration)
        
        # Keep only last 100 measurements
        if len(self.processing_times[document_type]) > 100:
            self.processing_times[document_type] = self.processing_times[document_type][-100:]
    
    def record_accuracy(self, document_type: str, confidence: str):
        """Record accuracy score for document type"""
        if document_type not in self.accuracy_scores:
            self.accuracy_scores[document_type] = []
        
        score_map = {'high': 1.0, 'medium': 0.7, 'low': 0.3}
        score = score_map.get(confidence, 0.0)
        self.accuracy_scores[document_type].append(score)
        
        # Keep only last 100 measurements
        if len(self.accuracy_scores[document_type]) > 100:
            self.accuracy_scores[document_type] = self.accuracy_scores[document_type][-100:]
    
    def get_stats(self):
        """Get performance statistics"""
        stats = {
            'processing_times': {},
            'accuracy_scores': {},
            'total_documents': sum(len(times) for times in self.processing_times.values())
        }
        
        for doc_type, times in self.processing_times.items():
            if times:
                stats['processing_times'][doc_type] = {
                    'avg': sum(times) / len(times),
                    'min': min(times),
                    'max': max(times),
                    'count': len(times)
                }
        
        for doc_type, scores in self.accuracy_scores.items():
            if scores:
                stats['accuracy_scores'][doc_type] = {
                    'avg': sum(scores) / len(scores),
                    'count': len(scores)
                }
        
        return stats


# Global performance monitor instance
performance_monitor = PerformanceMonitor()
