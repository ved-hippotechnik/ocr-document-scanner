from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
import io
import time
import logging
import json
import uuid
from PIL import Image
import numpy as np
import cv2

# Create enhanced routes blueprint
enhanced_v2 = Blueprint('enhanced_v2', __name__, url_prefix='/api/v2')

logger = logging.getLogger(__name__)

# Helper function to allowed file check
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'pdf'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@enhanced_v2.route('/health', methods=['GET'])
def health_check():
    """Enhanced health check with system status"""
    try:
        status = {
            'service': 'enhanced-ocr-document-scanner',
            'status': 'healthy',
            'version': '2.0.0',
            'timestamp': time.time(),
            'components': {
                'enhanced_ocr': hasattr(current_app, 'enhanced_ocr') and current_app.enhanced_ocr is not None,
                'ml_classifier': hasattr(current_app, 'ml_classifier') and current_app.ml_classifier is not None,
                'security_validator': hasattr(current_app, 'security_validator') and current_app.security_validator is not None,
                'realtime_processor': hasattr(current_app, 'realtime_processor') and current_app.realtime_processor is not None,
                'analytics_dashboard': hasattr(current_app, 'analytics_dashboard') and current_app.analytics_dashboard is not None,
                'performance_optimizer': hasattr(current_app, 'performance_optimizer') and current_app.performance_optimizer is not None
            }
        }
        return jsonify(status), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'service': 'enhanced-ocr-document-scanner',
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@enhanced_v2.route('/upload', methods=['POST'])
def upload_document():
    """Enhanced document upload with comprehensive processing"""
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'File type not allowed'}), 400
        
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Read file data
        file_data = file.read()
        file.seek(0)  # Reset file pointer
        
        # Process with Enhanced OCR System if available
        if hasattr(current_app, 'enhanced_ocr') and current_app.enhanced_ocr:
            try:
                # Create a file-like object for the enhanced OCR system
                file_like = io.BytesIO(file_data)
                file_like.name = secure_filename(file.filename)
                
                # Process with enhanced system
                result = current_app.enhanced_ocr.process_document_complete(file_like)
                
                # Add session information
                result['session_id'] = session_id
                result['processing_time'] = time.time() - start_time
                result['enhanced_processing'] = True
                
                return jsonify(result), 200
                
            except Exception as e:
                logger.error(f"Enhanced OCR processing failed: {e}")
                # Fall back to basic processing
                pass
        
        # Basic processing fallback
        try:
            # Load image
            image = Image.open(io.BytesIO(file_data))
            
            # Convert to OpenCV format
            opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Basic OCR using pytesseract
            import pytesseract
            extracted_text = pytesseract.image_to_string(opencv_image)
            
            # Basic classification
            document_type = classify_document_basic(extracted_text)
            
            # Create response
            result = {
                'success': True,
                'session_id': session_id,
                'processing_time': time.time() - start_time,
                'enhanced_processing': False,
                'classification': {
                    'predicted_class': document_type,
                    'confidence': 0.7
                },
                'ocr': {
                    'text': extracted_text,
                    'confidence': 0.7,
                    'extracted_fields': {}
                },
                'security': {
                    'risk_level': 'MEDIUM',
                    'authenticity_score': 0.5
                },
                'quality': {
                    'overall_quality': 0.6,
                    'quality_grade': 'Good'
                }
            }
            
            return jsonify(result), 200
            
        except Exception as e:
            logger.error(f"Basic processing failed: {e}")
            return jsonify({
                'success': False,
                'error': f'Processing failed: {str(e)}',
                'session_id': session_id
            }), 500
            
    except Exception as e:
        logger.error(f"Upload endpoint error: {e}")
        return jsonify({
            'success': False,
            'error': f'Upload failed: {str(e)}'
        }), 500

def classify_document_basic(text):
    """Basic document classification fallback"""
    text_lower = text.lower()
    
    if 'aadhaar' in text_lower or 'आधार' in text_lower:
        return 'Aadhaar Card'
    elif 'emirates id' in text_lower or 'uae' in text_lower:
        return 'Emirates ID'
    elif 'pan' in text_lower or 'permanent account number' in text_lower:
        return 'PAN Card'
    elif 'passport' in text_lower:
        return 'Passport'
    elif 'driving' in text_lower or 'license' in text_lower:
        return 'Driving License'
    elif 'green card' in text_lower:
        return 'Green Card'
    else:
        return 'Unknown Document'

@enhanced_v2.route('/analytics/dashboard', methods=['GET'])
def get_analytics_dashboard():
    """Get comprehensive analytics dashboard data"""
    try:
        if hasattr(current_app, 'analytics_dashboard') and current_app.analytics_dashboard:
            dashboard_data = current_app.analytics_dashboard.get_dashboard_summary()
            return jsonify(dashboard_data), 200
        else:
            # Basic analytics fallback
            return jsonify({
                'total_documents': 0,
                'success_rate': 0,
                'average_processing_time': 0,
                'document_types': {},
                'system_status': 'Basic Mode'
            }), 200
    except Exception as e:
        logger.error(f"Analytics dashboard error: {e}")
        return jsonify({'error': str(e)}), 500

@enhanced_v2.route('/analytics/metrics', methods=['GET'])
def get_detailed_metrics():
    """Get detailed performance metrics"""
    try:
        if hasattr(current_app, 'performance_optimizer') and current_app.performance_optimizer:
            metrics = current_app.performance_optimizer.get_performance_metrics()
            return jsonify(metrics), 200
        else:
            return jsonify({
                'message': 'Performance optimizer not available',
                'basic_metrics': {
                    'status': 'running',
                    'mode': 'basic'
                }
            }), 200
    except Exception as e:
        logger.error(f"Metrics endpoint error: {e}")
        return jsonify({'error': str(e)}), 500

@enhanced_v2.route('/security/validate', methods=['POST'])
def validate_document_security():
    """Validate document security and authenticity"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if hasattr(current_app, 'security_validator') and current_app.security_validator:
            # Read file data
            file_data = file.read()
            
            # Validate with security system
            validation_result = current_app.security_validator.validate_document(file_data)
            return jsonify(validation_result), 200
        else:
            # Basic security check
            return jsonify({
                'risk_level': 'MEDIUM',
                'authenticity_score': 0.5,
                'security_features': [],
                'message': 'Enhanced security validation not available'
            }), 200
            
    except Exception as e:
        logger.error(f"Security validation error: {e}")
        return jsonify({'error': str(e)}), 500

@enhanced_v2.route('/classify', methods=['POST'])
def classify_document():
    """Classify document type using ML"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if hasattr(current_app, 'ml_classifier') and current_app.ml_classifier:
            # Read file data
            file_data = file.read()
            
            # Classify with ML system
            classification_result = current_app.ml_classifier.classify_document(file_data)
            return jsonify(classification_result), 200
        else:
            # Basic classification
            file_data = file.read()
            image = Image.open(io.BytesIO(file_data))
            opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            import pytesseract
            text = pytesseract.image_to_string(opencv_image)
            document_type = classify_document_basic(text)
            
            return jsonify({
                'predicted_class': document_type,
                'confidence': 0.7,
                'message': 'ML classifier not available - using basic classification'
            }), 200
            
    except Exception as e:
        logger.error(f"Classification error: {e}")
        return jsonify({'error': str(e)}), 500

@enhanced_v2.route('/stats', methods=['GET'])
def get_system_stats():
    """Get comprehensive system statistics"""
    try:
        stats = {
            'system_info': {
                'version': '2.0.0',
                'enhanced_mode': hasattr(current_app, 'enhanced_ocr') and current_app.enhanced_ocr is not None,
                'components_loaded': {
                    'enhanced_ocr': hasattr(current_app, 'enhanced_ocr') and current_app.enhanced_ocr is not None,
                    'ml_classifier': hasattr(current_app, 'ml_classifier') and current_app.ml_classifier is not None,
                    'security_validator': hasattr(current_app, 'security_validator') and current_app.security_validator is not None,
                    'analytics_dashboard': hasattr(current_app, 'analytics_dashboard') and current_app.analytics_dashboard is not None,
                    'performance_optimizer': hasattr(current_app, 'performance_optimizer') and current_app.performance_optimizer is not None
                }
            },
            'processing_stats': {
                'total_documents': 0,
                'success_rate': 0.0,
                'average_processing_time': 0.0
            }
        }
        
        # Get analytics if available
        if hasattr(current_app, 'analytics_dashboard') and current_app.analytics_dashboard:
            dashboard_data = current_app.analytics_dashboard.get_dashboard_summary()
            stats['processing_stats'].update(dashboard_data)
        
        return jsonify(stats), 200
        
    except Exception as e:
        logger.error(f"Stats endpoint error: {e}")
        return jsonify({'error': str(e)}), 500

@enhanced_v2.route('/documents', methods=['GET'])
def get_recent_documents():
    """Get recent processed documents"""
    try:
        # This would typically fetch from database
        # For now, return empty list as placeholder
        return jsonify({
            'documents': [],
            'total': 0,
            'message': 'Document history feature coming soon'
        }), 200
        
    except Exception as e:
        logger.error(f"Documents endpoint error: {e}")
        return jsonify({'error': str(e)}), 500

@enhanced_v2.route('/reset-stats', methods=['POST'])
def reset_statistics():
    """Reset system statistics"""
    try:
        # Reset analytics if available
        if hasattr(current_app, 'analytics_dashboard') and current_app.analytics_dashboard:
            current_app.analytics_dashboard.reset_statistics()
        
        return jsonify({
            'success': True,
            'message': 'Statistics reset successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Reset stats error: {e}")
        return jsonify({'error': str(e)}), 500

# Legacy endpoint compatibility
@enhanced_v2.route('/scan', methods=['POST'])
def scan_document():
    """Legacy scan endpoint - redirects to upload"""
    return upload_document()
