"""
API routes for AI-powered document classification
"""

from flask import Blueprint, request, jsonify
from werkzeug.exceptions import BadRequest
import base64
import logging
from datetime import datetime

from .document_classifier import DocumentClassifier
from ..auth.jwt_utils import token_required
from ..cache import get_cache
from ..validation import validate_file_upload, validate_json_input

logger = logging.getLogger(__name__)

# Create blueprint
ai_bp = Blueprint('ai', __name__, url_prefix='/api/ai')

# Initialize document classifier
document_classifier = DocumentClassifier()

@ai_bp.route('/classify', methods=['POST'])
@token_required
def classify_document():
    """
    Classify document type from uploaded image
    
    Request formats:
    1. Multipart form data with 'image' file
    2. JSON with base64 encoded image
    """
    try:
        image_data = None
        
        # Handle multipart form data
        if 'image' in request.files:
            file = request.files['image']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            image_data = file.read()
            
        # Handle JSON with base64 image
        elif request.is_json:
            data = request.get_json()
            
            # Validate JSON input
            validation_result = validate_json_input(data)
            if not validation_result['valid']:
                return jsonify({'error': validation_result['message']}), 400
            
            if 'image' not in data:
                return jsonify({'error': 'Image data required'}), 400
            
            try:
                # Decode base64 image
                image_base64 = data['image']
                if ',' in image_base64:  # Remove data URL prefix if present
                    image_base64 = image_base64.split(',')[1]
                
                image_data = base64.b64decode(image_base64)
                
            except Exception as e:
                return jsonify({'error': f'Invalid base64 image data: {str(e)}'}), 400
        
        else:
            return jsonify({'error': 'No image data provided'}), 400
        
        # Validate file upload
        file_validation = validate_file_upload(image_data)
        if not file_validation['valid']:
            return jsonify({'error': file_validation['message']}), 400
        
        # Check cache first
        cache_key = f"classification:{hash(image_data)}"
        cached_result = get_cache().get(cache_key) if get_cache() else None
        
        if cached_result:
            logger.info("Returning cached classification result")
            return jsonify({
                'success': True,
                'cached': True,
                **cached_result
            })
        
        # Classify document
        classification_result = document_classifier.classify_document(image_data)
        
        # Cache result for 1 hour
        if get_cache():
            get_cache().set(cache_key, classification_result, ttl=3600)
        
        return jsonify({
            'success': True,
            'cached': False,
            **classification_result
        })
        
    except Exception as e:
        logger.error(f"Document classification failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_bp.route('/feedback', methods=['POST'])
@token_required
def submit_feedback():
    """
    Submit feedback for classification accuracy
    
    Expected JSON:
    {
        "image_hash": "string",
        "predicted_type": "string",
        "actual_type": "string",
        "confidence": "number"
    }
    """
    try:
        if not request.is_json:
            return jsonify({'error': 'JSON data required'}), 400
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['image_hash', 'predicted_type', 'actual_type']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Update classifier with feedback
        document_classifier.update_feedback(
            data['image_hash'],
            data['actual_type'],
            data['predicted_type']
        )
        
        return jsonify({
            'success': True,
            'message': 'Feedback submitted successfully'
        })
        
    except Exception as e:
        logger.error(f"Feedback submission failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_bp.route('/supported-types', methods=['GET'])
def get_supported_types():
    """Get list of supported document types"""
    try:
        supported_types = document_classifier.get_supported_document_types()
        
        return jsonify({
            'success': True,
            'document_types': supported_types,
            'total_types': len(supported_types)
        })
        
    except Exception as e:
        logger.error(f"Failed to get supported types: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_bp.route('/metrics', methods=['GET'])
@token_required
def get_classification_metrics():
    """Get classifier performance metrics"""
    try:
        metrics = document_classifier.get_performance_metrics()
        
        return jsonify({
            'success': True,
            'metrics': metrics
        })
        
    except Exception as e:
        logger.error(f"Failed to get classification metrics: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_bp.route('/train', methods=['POST'])
@token_required
def train_classifier():
    """
    Train the document classifier with new data
    
    Expected JSON:
    {
        "training_data": [
            {
                "image": "base64_string",
                "document_type": "string"
            }
        ]
    }
    """
    try:
        if not request.is_json:
            return jsonify({'error': 'JSON data required'}), 400
        
        data = request.get_json()
        
        if 'training_data' not in data:
            return jsonify({'error': 'Training data required'}), 400
        
        training_data = []
        
        for item in data['training_data']:
            if 'image' not in item or 'document_type' not in item:
                return jsonify({'error': 'Each training item must have image and document_type'}), 400
            
            try:
                # Decode base64 image
                image_base64 = item['image']
                if ',' in image_base64:
                    image_base64 = image_base64.split(',')[1]
                
                image_data = base64.b64decode(image_base64)
                training_data.append((image_data, item['document_type']))
                
            except Exception as e:
                return jsonify({'error': f'Invalid image data: {str(e)}'}), 400
        
        if len(training_data) < 10:
            return jsonify({'error': 'Minimum 10 training samples required'}), 400
        
        # Train the model
        training_result = document_classifier.train_model(training_data)
        
        return jsonify({
            'success': True,
            **training_result
        })
        
    except Exception as e:
        logger.error(f"Model training failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_bp.route('/batch-classify', methods=['POST'])
@token_required
def batch_classify():
    """
    Classify multiple documents at once
    
    Expected JSON:
    {
        "images": [
            {
                "id": "string",
                "image": "base64_string"
            }
        ]
    }
    """
    try:
        if not request.is_json:
            return jsonify({'error': 'JSON data required'}), 400
        
        data = request.get_json()
        
        if 'images' not in data:
            return jsonify({'error': 'Images array required'}), 400
        
        if len(data['images']) > 50:  # Limit batch size
            return jsonify({'error': 'Maximum 50 images per batch'}), 400
        
        results = []
        
        for item in data['images']:
            if 'id' not in item or 'image' not in item:
                results.append({
                    'id': item.get('id', 'unknown'),
                    'success': False,
                    'error': 'Missing id or image'
                })
                continue
            
            try:
                # Decode base64 image
                image_base64 = item['image']
                if ',' in image_base64:
                    image_base64 = image_base64.split(',')[1]
                
                image_data = base64.b64decode(image_base64)
                
                # Classify document
                classification_result = document_classifier.classify_document(image_data)
                
                results.append({
                    'id': item['id'],
                    'success': True,
                    **classification_result
                })
                
            except Exception as e:
                results.append({
                    'id': item['id'],
                    'success': False,
                    'error': str(e)
                })
        
        return jsonify({
            'success': True,
            'results': results,
            'total_processed': len(results)
        })
        
    except Exception as e:
        logger.error(f"Batch classification failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_bp.route('/confidence-threshold', methods=['POST'])
@token_required
def set_confidence_threshold():
    """
    Set confidence threshold for classification
    
    Expected JSON:
    {
        "threshold": 0.7
    }
    """
    try:
        if not request.is_json:
            return jsonify({'error': 'JSON data required'}), 400
        
        data = request.get_json()
        
        if 'threshold' not in data:
            return jsonify({'error': 'Threshold value required'}), 400
        
        threshold = data['threshold']
        
        if not isinstance(threshold, (int, float)) or threshold < 0 or threshold > 1:
            return jsonify({'error': 'Threshold must be between 0 and 1'}), 400
        
        document_classifier.confidence_threshold = threshold
        
        return jsonify({
            'success': True,
            'message': f'Confidence threshold set to {threshold}'
        })
        
    except Exception as e:
        logger.error(f"Failed to set confidence threshold: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_bp.route('/train/auto', methods=['POST'])
@token_required
def auto_train_classifier():
    """
    Automatically train the classifier from accumulated scan history data.
    """
    try:
        from .training_pipeline import TrainingDataGenerator

        generator = TrainingDataGenerator()
        stats = generator.get_training_stats()

        if stats['total_samples'] < 10:
            return jsonify({
                'success': False,
                'error': f"Not enough training data ({stats['total_samples']} samples). Need at least 10.",
                'training_stats': stats
            }), 400

        # Build training set with augmentation
        training_data = generator.build_training_set(augment=True)

        # Train the model
        result = document_classifier.train_model(training_data)

        return jsonify({
            'success': result.get('success', False),
            'training_stats': stats,
            **result
        })

    except Exception as e:
        logger.error(f"Auto-training failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_bp.route('/model/status', methods=['GET'])
def get_model_status():
    """Get current model status including training state and accuracy."""
    try:
        metrics = document_classifier.get_performance_metrics()

        return jsonify({
            'success': True,
            'is_fitted': document_classifier.is_fitted,
            'model_path': document_classifier.model_path,
            'confidence_threshold': document_classifier.confidence_threshold,
            'supported_types': len(document_classifier.document_types) - 1,
            'performance_metrics': metrics
        })

    except Exception as e:
        logger.error(f"Failed to get model status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_bp.route('/training-data/stats', methods=['GET'])
@token_required
def get_training_data_stats():
    """Get statistics about available training data."""
    try:
        from .training_pipeline import TrainingDataGenerator

        generator = TrainingDataGenerator()
        stats = generator.get_training_stats()

        return jsonify({
            'success': True,
            **stats
        })

    except Exception as e:
        logger.error(f"Failed to get training data stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai_bp.route('/health', methods=['GET'])
def health_check():
    """Health check for AI classification service"""
    try:
        # Check if classifier is loaded and trained
        classifier_ready = document_classifier.is_fitted
        
        metrics = document_classifier.get_performance_metrics()
        
        return jsonify({
            'success': True,
            'service': 'AI Document Classification',
            'status': 'healthy' if classifier_ready else 'degraded',
            'classifier_ready': classifier_ready,
            'supported_types': len(document_classifier.document_types) - 1,  # Exclude 'unknown'
            'performance_metrics': metrics
        })
        
    except Exception as e:
        logger.error(f"AI service health check failed: {e}")
        return jsonify({
            'success': False,
            'service': 'AI Document Classification',
            'status': 'unhealthy',
            'error': str(e)
        }), 500