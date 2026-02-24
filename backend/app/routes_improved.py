"""
Improved routes with proper error handling and validation
"""
from flask import Blueprint, request, jsonify, current_app, g
import io
import cv2
import numpy as np
from datetime import datetime
from PIL import Image
import pytesseract
from werkzeug.exceptions import BadRequest, RequestEntityTooLarge
import traceback
import time
from functools import wraps

from .processors.registry import processor_registry
from .rate_limiter import ratelimit_scan, ratelimit_medium, ratelimit_light
from .validators import DocumentScanSchema, FileUploadValidator, InputSanitizer
from .security.file_validator import FileValidator
from .database import db, ScanHistory
from marshmallow import ValidationError as MarshmallowValidationError

improved = Blueprint('improved', __name__)

# Initialize validators
scan_schema = DocumentScanSchema()
file_upload_validator = FileUploadValidator()
file_security_validator = FileValidator()

def measure_performance(f):
    """Decorator to measure endpoint performance"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        g.request_start_time = start_time
        
        try:
            result = f(*args, **kwargs)
            duration = (time.time() - start_time) * 1000  # Convert to ms
            
            # Log performance metrics
            if hasattr(current_app, 'performance_logger'):
                current_app.performance_logger.log_request_duration(
                    endpoint=request.endpoint,
                    method=request.method,
                    duration_ms=duration,
                    status_code=result[1] if isinstance(result, tuple) else 200
                )
            
            # Add performance header
            if isinstance(result, tuple):
                response, status_code = result
                if isinstance(response, dict):
                    response['_performance'] = {
                        'duration_ms': round(duration, 2),
                        'timestamp': datetime.utcnow().isoformat()
                    }
                return response, status_code
            
            return result
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            current_app.logger.error(f"Request failed after {duration}ms: {str(e)}")
            raise
    
    return decorated_function

def validate_request(f):
    """Decorator to validate incoming requests"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Validate content type for POST/PUT requests
        if request.method in ['POST', 'PUT']:
            content_type = request.content_type
            
            # Check for multipart/form-data (file uploads)
            if 'multipart/form-data' not in content_type and 'application/json' not in content_type:
                return jsonify({
                    'error': 'Invalid content type',
                    'message': f'Content-Type must be multipart/form-data or application/json, got {content_type}'
                }), 400
        
        return f(*args, **kwargs)
    
    return decorated_function

@improved.route('/api/v3/scan', methods=['POST'])
@ratelimit_scan()
@validate_request
@measure_performance
def scan_document_v3():
    """
    Scan a single document image (v3 — recommended).
    ---
    tags:
      - Scanning
    operationId: scanDocumentV3
    summary: Upload and OCR a document (recommended endpoint)
    description: >
      Upload a document image (JPEG, PNG, BMP, TIFF, or PDF) as
      multipart/form-data.  The engine will validate and sanitise the file,
      auto-classify the document type using the ML classifier, apply the
      matching specialist OCR processor, and return structured extracted fields
      together with the raw OCR text.

      Supported document types: Emirates ID, Aadhaar Card, Indian Driving
      License, Passport (various countries), US Driver's License.

      **Rate limit**: 10 requests / minute per IP.
    consumes:
      - multipart/form-data
    parameters:
      - in: formData
        name: image
        type: file
        required: true
        description: >
          Document image file.  Accepted: image/jpeg, image/png, image/bmp,
          image/tiff, application/pdf.  Maximum size: 16 MB.
          Minimum dimensions: 100x100 px.
      - in: formData
        name: language
        type: string
        required: false
        description: >
          ISO 639-3 language code for OCR hints (e.g. eng, ara, hin).
          If omitted the engine auto-detects the language.
        example: eng
      - in: formData
        name: document_type
        type: string
        required: false
        default: auto
        description: >
          Force a specific document processor instead of auto-detecting.
          Pass 'auto' (default) to let the classifier choose.
        enum:
          - auto
          - emirates_id
          - aadhaar_card
          - driving_license
          - passport
          - us_drivers_license
      - in: formData
        name: validate_with_vision
        type: boolean
        required: false
        default: false
        description: >
          When true, pass the image through Claude Vision for additional
          validation and confidence boost.  Requires ANTHROPIC_API_KEY.
      - in: formData
        name: quality_check
        type: boolean
        required: false
        default: true
        description: >
          Reject images with a quality score below 0.3.  Set to false to
          process low-quality images anyway.
      - in: formData
        name: enhance_image
        type: boolean
        required: false
        default: false
        description: Apply denoising and sharpening before OCR.
    responses:
      200:
        description: Document scanned and data extracted successfully.
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            document_type:
              type: string
              example: Emirates ID
            data:
              $ref: '#/definitions/ExtractedInfo'
            metadata:
              type: object
              properties:
                scan_id:
                  type: integer
                  example: 42
                quality_score:
                  type: number
                  example: 0.87
                processing_time:
                  type: number
                  description: Elapsed time in seconds.
                  example: 1.23
                timestamp:
                  type: string
                  format: date-time
      400:
        description: >
          Bad request — missing file, invalid format, empty file, poor image
          quality, or unsupported document type.
        schema:
          $ref: '#/definitions/ErrorResponse'
        examples:
          application/json:
            error: Missing required file
            code: FILE_REQUIRED
            message: No image file provided in request
      413:
        description: File exceeds the 16 MB upload limit.
        schema:
          $ref: '#/definitions/ErrorResponse'
      429:
        description: Rate limit exceeded.
        schema:
          $ref: '#/definitions/ErrorResponse'
      500:
        description: Internal OCR processing error.
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    try:
        # Step 1: Validate request has file
        if 'image' not in request.files:
            return jsonify({
                'error': 'Missing required file',
                'code': 'FILE_REQUIRED',
                'message': 'No image file provided in request'
            }), 400
        
        file = request.files['image']
        
        # Step 2: Validate filename
        if not file.filename:
            return jsonify({
                'error': 'Invalid file',
                'code': 'INVALID_FILENAME',
                'message': 'File has no filename'
            }), 400
        
        if not file_upload_validator.validate_filename(file.filename):
            return jsonify({
                'error': 'Invalid filename',
                'code': 'INVALID_FILENAME',
                'message': f'Filename contains invalid characters or extension: {file.filename}'
            }), 400
        
        # Step 3: Security validation (virus scan, content validation)
        is_valid, error_msg, file_metadata = file_security_validator.validate_file(file)
        if not is_valid:
            current_app.logger.warning(f"File validation failed: {error_msg}")
            
            # Log security event
            if hasattr(current_app, 'security_logger'):
                current_app.security_logger.log_file_upload(
                    user_id=g.get('user_id', 'anonymous'),
                    filename=file.filename,
                    file_size=file_metadata.get('size', 0),
                    validation_result=error_msg
                )
            
            return jsonify({
                'error': 'File validation failed',
                'code': 'FILE_VALIDATION_FAILED',
                'message': error_msg
            }), 400
        
        # Reset file pointer after validation
        file.seek(0)
        
        # Step 4: Validate request parameters
        try:
            params = scan_schema.load(request.form.to_dict())
        except MarshmallowValidationError as e:
            return jsonify({
                'error': 'Invalid parameters',
                'code': 'INVALID_PARAMETERS',
                'message': 'Request parameters validation failed',
                'details': e.messages
            }), 400
        
        # Step 5: Read and validate image data
        try:
            file_bytes = file.read()
            if not file_bytes:
                return jsonify({
                    'error': 'Empty file',
                    'code': 'EMPTY_FILE',
                    'message': 'Uploaded file is empty'
                }), 400
            
            # Decode image
            img_array = np.frombuffer(file_bytes, np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            
            if img is None:
                return jsonify({
                    'error': 'Invalid image data',
                    'code': 'INVALID_IMAGE',
                    'message': 'Unable to decode image data. File may be corrupted or not a valid image.'
                }), 400
            
            # Validate image dimensions
            height, width = img.shape[:2]
            if height < 100 or width < 100:
                return jsonify({
                    'error': 'Image too small',
                    'code': 'IMAGE_TOO_SMALL',
                    'message': f'Image dimensions {width}x{height} are too small. Minimum is 100x100.'
                }), 400
            
            if height > 10000 or width > 10000:
                return jsonify({
                    'error': 'Image too large',
                    'code': 'IMAGE_TOO_LARGE',
                    'message': f'Image dimensions {width}x{height} are too large. Maximum is 10000x10000.'
                }), 400
            
        except Exception as e:
            current_app.logger.error(f"Image processing error: {str(e)}")
            return jsonify({
                'error': 'Image processing failed',
                'code': 'IMAGE_PROCESSING_ERROR',
                'message': 'Failed to process image data',
                'details': str(e)
            }), 400
        
        # Step 6: Perform OCR processing
        try:
            # Convert to grayscale for OCR
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Quality check if requested
            quality_score = None
            if params.get('quality_check', True):
                quality_score = assess_image_quality(gray)
                if quality_score < 0.3:
                    return jsonify({
                        'error': 'Poor image quality',
                        'code': 'POOR_IMAGE_QUALITY',
                        'message': f'Image quality score {quality_score:.2f} is too low. Please provide a clearer image.',
                        'quality_score': quality_score
                    }), 400
            
            # Enhance image if requested
            if params.get('enhance_image', False):
                gray = enhance_image(gray)
            
            # Perform OCR
            initial_text = pytesseract.image_to_string(gray, lang=params.get('language', 'eng'), timeout=60)
            
            if not initial_text or len(initial_text.strip()) < 10:
                return jsonify({
                    'error': 'No text detected',
                    'code': 'NO_TEXT_DETECTED',
                    'message': 'Unable to extract text from image. Image may be blank or text is not readable.',
                    'quality_score': quality_score
                }), 400
            
            # Detect document type
            doc_type = params.get('document_type', 'auto')
            if doc_type == 'auto':
                doc_display_name, processor = processor_registry.detect_document_type(initial_text, img)
            else:
                processor = processor_registry.get_processor(doc_type)
                doc_display_name = doc_type
            
            if not processor:
                return jsonify({
                    'error': 'Document type not supported',
                    'code': 'UNSUPPORTED_DOCUMENT',
                    'message': f'Document type "{doc_type}" is not supported or could not be detected',
                    'available_types': processor_registry.get_available_processors()
                }), 400
            
            # Process with specific processor
            validate_vision = params.get('validate_with_vision', False)
            result = processor.process(img, validate_with_vision=validate_vision)
            
            # Validate extracted data
            if params.get('validate_document', True):
                validation_result = validate_extracted_data(result, doc_display_name)
                if not validation_result['is_valid']:
                    result['validation'] = validation_result
            
            # Store in database
            scan_record = ScanHistory(
                user_id=g.get('user_id'),
                session_id=params.get('session_id', 'unknown'),
                document_type=doc_display_name,
                confidence_score=result.get('confidence', 0),
                quality_score=quality_score,
                processing_time=(time.time() - g.request_start_time),
                file_size=len(file_bytes),
                file_format=file_metadata.get('mime_type', 'unknown'),
                filename=file_metadata.get('safe_filename'),
                extracted_data=str(result),
                ip_address=g.get('client_ip', request.remote_addr),
                user_agent=request.user_agent.string,
                status='completed'
            )
            db.session.add(scan_record)
            db.session.commit()
            
            # Prepare response
            response = {
                'success': True,
                'document_type': doc_display_name,
                'data': result,
                'metadata': {
                    'scan_id': scan_record.id,
                    'quality_score': quality_score,
                    'processing_time': round(time.time() - g.request_start_time, 3),
                    'file_hash': file_metadata.get('hash'),
                    'timestamp': datetime.utcnow().isoformat()
                }
            }
            
            return jsonify(response), 200
            
        except Exception as e:
            current_app.logger.error(f"OCR processing error: {str(e)}\n{traceback.format_exc()}")
            
            # Store failed attempt
            scan_record = ScanHistory(
                user_id=g.get('user_id'),
                session_id=params.get('session_id', 'unknown'),
                document_type='unknown',
                error_message=str(e),
                file_size=len(file_bytes),
                filename=file.filename,
                ip_address=g.get('client_ip', request.remote_addr),
                user_agent=request.user_agent.string,
                status='failed'
            )
            db.session.add(scan_record)
            db.session.commit()
            
            return jsonify({
                'error': 'Processing failed',
                'code': 'PROCESSING_ERROR',
                'message': 'Failed to process document',
                'details': str(e) if current_app.debug else 'Internal processing error'
            }), 500
            
    except RequestEntityTooLarge:
        return jsonify({
            'error': 'File too large',
            'code': 'FILE_TOO_LARGE',
            'message': f'File size exceeds maximum allowed size of {current_app.config.get("MAX_CONTENT_LENGTH", 16*1024*1024)} bytes'
        }), 413
        
    except Exception as e:
        current_app.logger.error(f"Unexpected error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR',
            'message': 'An unexpected error occurred',
            'details': str(e) if current_app.debug else None
        }), 500

def assess_image_quality(image):
    """Assess image quality for OCR readability"""
    try:
        # Calculate variance of Laplacian (blur detection)
        laplacian_var = cv2.Laplacian(image, cv2.CV_64F).var()
        
        # Calculate contrast
        min_val = np.min(image)
        max_val = np.max(image)
        contrast = (max_val - min_val) / 255.0
        
        # Calculate brightness
        brightness = np.mean(image) / 255.0
        
        # Combined quality score
        blur_score = min(laplacian_var / 1000, 1.0)  # Normalize
        
        # Weight the factors
        quality_score = (blur_score * 0.5 + contrast * 0.3 + brightness * 0.2)
        
        return min(max(quality_score, 0.0), 1.0)  # Clamp between 0 and 1
        
    except Exception as e:
        current_app.logger.error(f"Quality assessment error: {str(e)}")
        return 0.5  # Return neutral score on error

def enhance_image(image):
    """Enhance image for better OCR results"""
    try:
        # Denoise
        denoised = cv2.fastNlMeansDenoising(image, None, 10, 7, 21)
        
        # Adaptive thresholding
        enhanced = cv2.adaptiveThreshold(
            denoised, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        
        return enhanced
        
    except Exception as e:
        current_app.logger.error(f"Image enhancement error: {str(e)}")
        return image  # Return original on error

def validate_extracted_data(data, doc_type):
    """Validate extracted document data"""
    validation_result = {
        'is_valid': True,
        'errors': [],
        'warnings': []
    }
    
    # Basic validation rules
    if not data:
        validation_result['is_valid'] = False
        validation_result['errors'].append('No data extracted')
        return validation_result
    
    # Check for required fields based on document type
    required_fields = {
        'passport': ['passport_number', 'name', 'date_of_birth'],
        'emirates_id': ['id_number', 'name'],
        'aadhaar_card': ['aadhaar_number', 'name'],
        'driving_license': ['license_number', 'name']
    }
    
    if doc_type in required_fields:
        for field in required_fields[doc_type]:
            if field not in data or not data[field]:
                validation_result['errors'].append(f'Missing required field: {field}')
                validation_result['is_valid'] = False
    
    # Additional validation checks
    if 'expiry_date' in data:
        try:
            expiry = datetime.strptime(data['expiry_date'], '%d/%m/%Y')
            if expiry < datetime.now():
                validation_result['warnings'].append('Document appears to be expired')
        except:
            pass
    
    return validation_result

@improved.route('/api/v3/health', methods=['GET'])
@ratelimit_light()
def health_check_v3():
    """
    Comprehensive health check (v3).
    ---
    tags:
      - Health
    operationId: healthCheckV3
    summary: Detailed component health check
    description: >
      Probes each internal subsystem — database, OCR engine, cache, and rate
      limiter — and aggregates a single top-level status field.

      * **healthy** — all probed components are operational.
      * **degraded** — one or more components have issues.
      * **unhealthy** — critical failure; returns HTTP 503.

      **Rate limit**: 60 requests / minute per IP.
    responses:
      200:
        description: Health check completed (inspect `status` field for outcome).
        schema:
          $ref: '#/definitions/DetailedHealthResponse'
        examples:
          application/json:
            status: healthy
            version: "3.0"
            timestamp: "2026-02-22T10:00:00Z"
            services:
              database: healthy
              ocr_engine: healthy
              cache: healthy
              rate_limiter: healthy
      503:
        description: One or more critical components are unhealthy.
        schema:
          $ref: '#/definitions/DetailedHealthResponse'
    """
    try:
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '3.0',
            'services': {}
        }
        
        # Check database
        try:
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            health_status['services']['database'] = 'healthy'
        except Exception as e:
            current_app.logger.error(f"Database health check failed: {e}")
            health_status['services']['database'] = 'unhealthy'
            health_status['status'] = 'degraded'
        
        # Check OCR engine
        try:
            pytesseract.get_tesseract_version()
            health_status['services']['ocr_engine'] = 'healthy'
        except:
            health_status['services']['ocr_engine'] = 'unhealthy'
            health_status['status'] = 'degraded'
        
        # Check cache
        if hasattr(current_app, 'cache') and current_app.cache:
            try:
                # Test cache set and get operations
                test_key = 'health_check_test'
                test_value = 'ok'
                current_app.cache.set(test_key, test_value, timeout=1)
                retrieved_value = current_app.cache.get(test_key)
                if retrieved_value == test_value:
                    health_status['services']['cache'] = 'healthy'
                else:
                    health_status['services']['cache'] = 'unhealthy'
                # Clean up test key
                current_app.cache.delete(test_key)
            except Exception as e:
                current_app.logger.error(f"Cache health check failed: {e}")
                health_status['services']['cache'] = 'unavailable'
        else:
            health_status['services']['cache'] = 'not_configured'
        
        # Check rate limiter
        health_status['services']['rate_limiter'] = 'healthy' if current_app.config.get('RATE_LIMIT_ENABLED') else 'disabled'
        
        status_code = 200 if health_status['status'] == 'healthy' else 503
        return jsonify(health_status), status_code
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 503

@improved.route('/api/v3/processors', methods=['GET'])
@ratelimit_light()
def get_processors_v3():
    """Get available document processors with caching"""
    cache_key = 'processors_list_v3'
    
    # Try to get from cache
    if hasattr(current_app, 'cache'):
        cached = current_app.cache.get(cache_key)
        if cached:
            return jsonify(cached), 200
    
    processors = processor_registry.get_processor_info()
    
    response = {
        'processors': processors,
        'total': len(processors),
        'timestamp': datetime.utcnow().isoformat()
    }
    
    # Cache for 1 hour
    if hasattr(current_app, 'cache'):
        current_app.cache.set(cache_key, response, timeout=3600)
    
    return jsonify(response), 200