"""
Enhanced routes with integrated monitoring, classification, and quality assessment
"""
from flask import Blueprint, request, jsonify, current_app
import io
import cv2
import numpy as np
from datetime import datetime, timezone
from PIL import Image
import time
import logging
import re
import uuid

from .monitoring import setup_metrics, track_document_processing, performance_monitor
from .classification import document_classifier
from .quality import quality_analyzer
from .processors import processor_registry
from .validation import (
    validate_request_json, 
    handle_processing_errors, 
    ErrorHandler, 
    ProcessingError,
    check_rate_limit,
    add_security_headers
)
from .database import log_scan_result, get_analytics_data, ScanHistory, DocumentTypeStats, db
from .tasks import process_document_async, process_batch_documents

enhanced = Blueprint('enhanced', __name__)
logger = logging.getLogger(__name__)


@enhanced.after_request
def after_request(response):
    """Add security headers and rate limit headers to all responses"""
    response = add_security_headers(response)
    return response


@enhanced.route('/api/v2/scan', methods=['POST'])
@validate_request_json()
@handle_processing_errors()
@track_document_processing('enhanced_scan')
def enhanced_scan(validated_data):
    """
    Enhanced document scanning with quality assessment and classification
    """
    start_time = time.time()
    
    # Check rate limit
    rate_limit_headers = check_rate_limit()
    
    try:
        # Extract validated data
        image = validated_data['image']
        document_type = validated_data.get('document_type')
        options = validated_data.get('options', {})
        
        # Convert PIL image to OpenCV format
        image_array = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Get processing options
        enable_quality_check = options.get('enable_quality_check', True)
        return_processed_images = options.get('return_processed_images', False)
        confidence_threshold = options.get('confidence_threshold', 0.6)
        
        result = {
            'document_type': None,
            'confidence': 0.0,
            'extracted_info': {},
            'processor_used': None
        }
        
        # Quality assessment (if enabled)
        if enable_quality_check:
            quality_result = quality_analyzer.analyze_quality(image_array)
            result['quality_score'] = quality_result['quality_score']
            result['quality_issues'] = quality_result['issues']
            
            # Check if quality is too low
            if quality_result['quality_score'] < 0.3:
                logger.warning(f"Very low quality image detected: {quality_result['quality_score']}")
        
        # Document classification and processing
        classification_result = document_classifier.classify_document(image_array)
        
        if classification_result['document_type'] == 'unknown':
            # Try with provided document type if available
            if document_type:
                processor = processor_registry.get_processor(document_type)
                if processor:
                    try:
                        processing_result = processor.process_document(image_array)
                        if processing_result['confidence'] >= confidence_threshold:
                            result.update(processing_result)
                            result['processor_used'] = processor.__class__.__name__
                        else:
                            raise ProcessingError(
                                f"Low confidence result: {processing_result['confidence']:.2f}",
                                "LOW_CONFIDENCE"
                            )
                    except Exception as e:
                        logger.error(f"Error processing with {processor.__class__.__name__}: {str(e)}")
                        raise ProcessingError(
                            f"Failed to process document with {document_type} processor",
                            "PROCESSING_FAILED",
                            str(e)
                        )
                else:
                    raise ProcessingError(
                        f"No processor available for document type: {document_type}",
                        "UNSUPPORTED_DOCUMENT_TYPE"
                    )
            else:
                raise ProcessingError(
                    "Could not identify document type. Please specify document_type or improve image quality.",
                    "DOCUMENT_NOT_DETECTED"
                )
        else:
            # Use classified document type
            result['document_type'] = classification_result['document_type']
            result['confidence'] = classification_result['confidence']
            result['processor_used'] = classification_result.get('processor_used', 'Unknown')
            
            # Get the processor and extract detailed information
            processor = processor_registry.get_processor_by_country_and_type(
                classification_result.get('country', 'Unknown'),
                classification_result['document_type']
            )
            
            if processor:
                try:
                    processing_result = processor.process_document(image_array)
                    result['extracted_info'] = processing_result['extracted_info']
                    result['confidence'] = max(result['confidence'], processing_result['confidence'])
                    result['processor_used'] = processor.__class__.__name__
                except Exception as e:
                    logger.error(f"Error extracting info with {processor.__class__.__name__}: {str(e)}")
                    # Continue with classification result even if extraction fails
        
        # Add processing metadata
        processing_time = time.time() - start_time
        result['processing_time'] = round(processing_time, 3)
        
        # Check final confidence
        if result['confidence'] < confidence_threshold:
            logger.warning(f"Final confidence {result['confidence']:.2f} below threshold {confidence_threshold}")
        
        # Log performance
        performance_monitor.log_processing_time('enhanced_scan', processing_time)
        
        # Log scan result to database
        try:
            session_id = request.headers.get('X-Session-ID', str(uuid.uuid4()))
            
            # Get file info from validated data
            image_data = validated_data.get('image_data', '')
            file_format = validated_data.get('file_format', 'unknown')
            
            file_info = {
                'size': len(image_data) if image_data else 0,
                'format': file_format
            }
            
            request_info = {
                'ip': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', 'Unknown')
            }
            
            log_scan_result(
                session_id=session_id,
                document_type=result.get('document_type', 'unknown'),
                result_data=result,
                processing_time=processing_time,
                file_info=file_info,
                request_info=request_info
            )
        except Exception as e:
            logger.error(f"Failed to log scan result to database: {str(e)}")
        
        # Return success response with rate limit headers
        response_data = ErrorHandler.create_success_response(result)
        response = response_data[0]
        
        # Add rate limit headers
        for header, value in rate_limit_headers.items():
            response.headers[header] = value
            
        return response
        
    except Exception as e:
        # Log error for monitoring
        performance_monitor.log_error('enhanced_scan', str(e))
        raise  # Re-raise to be handled by error handler decorator


@enhanced.route('/api/v2/classify', methods=['POST'])
@validate_request_json()
@handle_processing_errors()
@track_document_processing('classify')
def classify_document_endpoint(validated_data):
    """
    Classify document type without full information extraction
    """
    start_time = time.time()
    
    # Check rate limit
    rate_limit_headers = check_rate_limit()
    
    try:
        # Extract validated data
        image = validated_data['image']
        
        # Convert PIL image to OpenCV format
        image_array = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Classify document
        classification_result = document_classifier.classify_document(image_array)
        
        if classification_result['document_type'] == 'unknown':
            raise ProcessingError(
                "Could not identify document type. Please check image quality and try again.",
                "DOCUMENT_NOT_DETECTED"
            )
        
        # Add processing time
        processing_time = time.time() - start_time
        classification_result['processing_time'] = round(processing_time, 3)
        
        # Log performance
        performance_monitor.log_processing_time('classify', processing_time)
        
        # Return success response with rate limit headers
        response_data = ErrorHandler.create_success_response(classification_result)
        response = response_data[0]
        
        # Add rate limit headers
        for header, value in rate_limit_headers.items():
            response.headers[header] = value
            
        return response
        
    except Exception as e:
        # Log error for monitoring
        performance_monitor.log_error('classify', str(e))
        raise  # Re-raise to be handled by error handler decorator


@enhanced.route('/api/v2/quality', methods=['POST'])
@validate_request_json()
@handle_processing_errors()
@track_document_processing('quality_check')
def quality_check_endpoint(validated_data):
    """
    Assess document image quality
    """
    start_time = time.time()
    
    # Check rate limit
    rate_limit_headers = check_rate_limit()
    
    try:
        # Extract validated data
        image = validated_data['image']
        
        # Convert PIL image to OpenCV format
        image_array = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Analyze quality
        quality_result = quality_analyzer.analyze_quality(image_array)
        
        # Add processing time
        processing_time = time.time() - start_time
        quality_result['processing_time'] = round(processing_time, 3)
        
        # Log performance
        performance_monitor.log_processing_time('quality_check', processing_time)
        
        # Return success response with rate limit headers
        response_data = ErrorHandler.create_success_response(quality_result)
        response = response_data[0]
        
        # Add rate limit headers
        for header, value in rate_limit_headers.items():
            response.headers[header] = value
            
        return response
        
    except Exception as e:
        # Log error for monitoring
        performance_monitor.log_error('quality_check', str(e))
        raise  # Re-raise to be handled by error handler decorator


@enhanced.route('/api/v2/stats', methods=['GET'])
@handle_processing_errors()
def enhanced_stats():
    """Enhanced statistics with performance metrics"""
    try:
        # Get basic stats from performance monitor
        performance_stats = performance_monitor.get_stats()
        
        # Get system health metrics
        system_stats = {
            'uptime': time.time(),  # Simplified uptime
            'total_processors': len(processor_registry.processors),
            'supported_documents': len(processor_registry.list_supported_documents())
        }
        
        return ErrorHandler.create_success_response({
            'stats': {
                'performance': performance_stats,
                'system': system_stats,
                'processors': processor_registry.list_supported_documents()
            }
        })
    
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise


@enhanced.route('/api/v2/health', methods=['GET'])
def health_check():
    """Comprehensive health check"""
    try:
        # Check system components
        health_status = {
            'status': 'healthy',
            'version': '2.0.0',
            'components': {
                'ocr_engine': check_ocr_engine(),
                'processors': len(processor_registry.processors) > 0,
                'classification': True,  # Classification system is always available
                'quality_assessment': True  # Quality assessment is always available
            }
        }
        
        # Overall health
        all_healthy = all(health_status['components'].values())
        if not all_healthy:
            health_status['status'] = 'degraded'
        
        status_code = 200 if all_healthy else 503
        return jsonify(health_status), status_code
    
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        }), 503


@enhanced.route('/analytics', methods=['GET'])
def get_analytics():
    """Get analytics data for the dashboard"""
    try:
        days = request.args.get('days', 30, type=int)
        if days < 1 or days > 365:
            return jsonify({'error': 'Days must be between 1 and 365'}), 400
        
        analytics_data = get_analytics_data(days)
        return jsonify(analytics_data)
        
    except Exception as e:
        logger.error(f"Error getting analytics: {str(e)}")
        return jsonify({'error': 'Failed to get analytics data'}), 500


@enhanced.route('/analytics/scan-history', methods=['GET'])
def get_scan_history():
    """Get scan history with pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        document_type = request.args.get('document_type')
        
        query = ScanHistory.query
        
        if document_type:
            query = query.filter_by(document_type=document_type)
        
        query = query.order_by(ScanHistory.created_at.desc())
        
        paginated = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'scans': [scan.to_dict() for scan in paginated.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': paginated.total,
                'pages': paginated.pages,
                'has_next': paginated.has_next,
                'has_prev': paginated.has_prev
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting scan history: {str(e)}")
        return jsonify({'error': 'Failed to get scan history'}), 500


@enhanced.route('/analytics/document-stats', methods=['GET'])
def get_document_stats():
    """Get document type statistics"""
    try:
        stats = DocumentTypeStats.query.all()
        return jsonify({
            'document_types': [stat.to_dict() for stat in stats]
        })
        
    except Exception as e:
        logger.error(f"Error getting document stats: {str(e)}")
        return jsonify({'error': 'Failed to get document statistics'}), 500


def check_ocr_engine() -> bool:
    """Check if OCR engine is working"""
    try:
        import pytesseract
        # Create a simple test image
        test_image = np.ones((100, 200), dtype=np.uint8) * 255
        cv2.putText(test_image, 'TEST', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, 0, 2)
        
        # Try OCR
        result = pytesseract.image_to_string(test_image)
        return 'TEST' in result.upper()
    except Exception:
        return False


@enhanced.route('/async/scan', methods=['POST'])
@validate_request_json()
@handle_processing_errors()
def async_scan(validated_data):
    """
    Start asynchronous document processing
    """
    try:
        # Extract image data and options
        image_data = validated_data.get('image_data')
        document_type = validated_data.get('document_type')
        options = validated_data.get('options', {})
        
        # Add session ID to options
        options['session_id'] = request.headers.get('X-Session-ID', str(uuid.uuid4()))
        
        # Start async task
        task = process_document_async.delay(image_data, document_type, options)
        
        return jsonify({
            'task_id': task.id,
            'status': 'accepted',
            'message': 'Document processing started',
            'check_url': f'/api/v2/async/status/{task.id}'
        }), 202
        
    except Exception as e:
        logger.error(f"Failed to start async processing: {str(e)}")
        return jsonify({'error': 'Failed to start processing'}), 500


@enhanced.route('/async/batch', methods=['POST'])
@validate_request_json()
@handle_processing_errors() 
def async_batch_scan(validated_data):
    """
    Start asynchronous batch document processing
    """
    try:
        batch_data = validated_data.get('documents', [])
        
        if not batch_data or len(batch_data) == 0:
            return jsonify({'error': 'No documents provided'}), 400
        
        if len(batch_data) > 50:  # Limit batch size
            return jsonify({'error': 'Batch size cannot exceed 50 documents'}), 400
        
        # Start batch processing task
        task = process_batch_documents.delay(batch_data)
        
        return jsonify({
            'batch_id': task.id,
            'status': 'accepted',
            'total_documents': len(batch_data),
            'message': 'Batch processing started',
            'check_url': f'/api/v2/async/status/{task.id}'
        }), 202
        
    except Exception as e:
        logger.error(f"Failed to start batch processing: {str(e)}")
        return jsonify({'error': 'Failed to start batch processing'}), 500


@enhanced.route('/async/status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """
    Get the status of an async task
    """
    try:
        from .tasks import celery
        
        task = celery.AsyncResult(task_id)
        
        if task.state == 'PENDING':
            response = {
                'task_id': task_id,
                'state': task.state,
                'status': 'Task is waiting to be processed',
                'progress': 0
            }
        elif task.state == 'PROCESSING':
            response = {
                'task_id': task_id,
                'state': task.state,
                'status': task.info.get('status', 'Processing'),
                'progress': task.info.get('progress', 0),
                'completed': task.info.get('completed', 0),
                'total': task.info.get('total', 1)
            }
        elif task.state == 'SUCCESS':
            response = {
                'task_id': task_id,
                'state': task.state,
                'status': 'Task completed successfully',
                'progress': 100,
                'result': task.result
            }
        elif task.state == 'FAILURE':
            response = {
                'task_id': task_id,
                'state': task.state,
                'status': 'Task failed',
                'error': str(task.info),
                'progress': 0
            }
        else:
            response = {
                'task_id': task_id,
                'state': task.state,
                'status': 'Unknown task state',
                'progress': 0
            }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Failed to get task status: {str(e)}")
        return jsonify({
            'task_id': task_id,
            'state': 'ERROR',
            'error': 'Failed to retrieve task status'
        }), 500


@enhanced.route('/async/cancel/<task_id>', methods=['POST'])
def cancel_task(task_id):
    """
    Cancel a running async task
    """
    try:
        from .tasks import celery
        
        celery.control.revoke(task_id, terminate=True)
        
        return jsonify({
            'task_id': task_id,
            'status': 'cancelled',
            'message': 'Task cancellation requested'
        })
        
    except Exception as e:
        logger.error(f"Failed to cancel task: {str(e)}")
        return jsonify({'error': 'Failed to cancel task'}), 500
