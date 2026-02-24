"""
API routes for batch processing system
"""

from flask import Blueprint, request, jsonify
from werkzeug.exceptions import BadRequest
import logging
from datetime import datetime
from typing import List, Dict

from .processor import batch_manager, BatchStatus
from ..auth.jwt_utils import token_required, get_current_user
from ..validation import validate_json_input
from ..database import db
from ..database import BatchProcessingJob
from ..rate_limiter import ratelimit_batch, ratelimit_light, ratelimit_medium

logger = logging.getLogger(__name__)

# Create blueprint
batch_bp = Blueprint('batch', __name__, url_prefix='/api/batch')

@batch_bp.route('/submit', methods=['POST'])
@token_required
@ratelimit_batch()
def submit_batch():
    """
    Submit a batch document processing job.
    ---
    tags:
      - Batch
    operationId: submitBatch
    summary: Queue multiple documents for asynchronous OCR
    description: >
      Submit up to 100 documents encoded as base64 strings for background
      processing.  The endpoint returns a `job_id` immediately; poll
      `GET /api/batch/status/{job_id}` for completion.  Retrieve results
      with `GET /api/batch/results/{job_id}`.

      **Authentication**: JWT Bearer token required.

      **Rate limit**: 5 requests / minute per authenticated user.
    security:
      - BearerAuth: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          $ref: '#/definitions/BatchSubmitRequest'
    responses:
      200:
        description: Batch job queued — job_id returned.
        schema:
          $ref: '#/definitions/BatchSubmitResponse'
        examples:
          application/json:
            success: true
            job_id: job_2026022210300001
            message: Batch job submitted successfully with 5 documents
      400:
        description: >
          Validation error — missing documents array, empty array, more than
          100 documents, or individual document missing id/image fields.
        schema:
          $ref: '#/definitions/ErrorResponse'
        examples:
          application/json:
            error: Maximum 100 documents per batch
      401:
        description: Missing or invalid JWT Bearer token.
        schema:
          $ref: '#/definitions/ErrorResponse'
      429:
        description: Rate limit exceeded.
        schema:
          $ref: '#/definitions/ErrorResponse'
      500:
        description: Internal server error or job queue failure.
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    try:
        if not request.is_json:
            return jsonify({'error': 'JSON data required'}), 400
        
        data = request.get_json()
        
        # Validate JSON input
        validation_result = validate_json_input(data)
        if not validation_result['valid']:
            return jsonify({'error': validation_result['message']}), 400
        
        # Validate required fields
        if 'documents' not in data:
            return jsonify({'error': 'Documents array required'}), 400
        
        documents = data['documents']
        
        if not isinstance(documents, list) or len(documents) == 0:
            return jsonify({'error': 'Documents array must contain at least one document'}), 400
        
        if len(documents) > 100:  # Limit batch size
            return jsonify({'error': 'Maximum 100 documents per batch'}), 400
        
        # Validate each document
        for i, doc in enumerate(documents):
            if not isinstance(doc, dict):
                return jsonify({'error': f'Document {i} must be an object'}), 400
            
            if 'id' not in doc or 'image' not in doc:
                return jsonify({'error': f'Document {i} must have id and image fields'}), 400
            
            if not isinstance(doc['id'], str) or not doc['id'].strip():
                return jsonify({'error': f'Document {i} id must be a non-empty string'}), 400
            
            if not isinstance(doc['image'], str) or not doc['image'].strip():
                return jsonify({'error': f'Document {i} image must be a non-empty string'}), 400
        
        # Get current user
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'User not found'}), 401
        
        # Get job configuration
        config = data.get('config', {})
        
        # Create batch job
        job_id = batch_manager.create_job(
            user_id=current_user.id,
            documents=documents,
            job_config=config
        )
        
        # Submit job for processing
        success = batch_manager.submit_job(job_id)
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Failed to submit job for processing'
            }), 500
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': f'Batch job submitted successfully with {len(documents)} documents'
        })
        
    except Exception as e:
        logger.error(f"Error submitting batch job: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@batch_bp.route('/status/<job_id>', methods=['GET'])
@token_required
def get_job_status(job_id: str):
    """
    Get status of a batch processing job
    
    Args:
        job_id: ID of the batch job
    """
    try:
        # Validate job_id
        if not job_id or not job_id.strip():
            return jsonify({'error': 'Job ID required'}), 400
        
        # Get current user
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'User not found'}), 401
        
        # Get job status
        status = batch_manager.get_job_status(job_id)
        
        if not status:
            return jsonify({'error': 'Job not found'}), 404
        
        # Check if user owns this job (for security)
        if hasattr(status, 'user_id') and status.user_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        return jsonify({
            'success': True,
            'job_status': status
        })
        
    except Exception as e:
        logger.error(f"Error getting job status for {job_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@batch_bp.route('/results/<job_id>', methods=['GET'])
@token_required
def get_job_results(job_id: str):
    """
    Get results of a completed batch processing job
    
    Args:
        job_id: ID of the batch job
    """
    try:
        # Validate job_id
        if not job_id or not job_id.strip():
            return jsonify({'error': 'Job ID required'}), 400
        
        # Get current user
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'User not found'}), 401
        
        # Get job results
        results = batch_manager.get_job_results(job_id)
        
        if not results:
            return jsonify({'error': 'Job not found or not completed'}), 404
        
        return jsonify({
            'success': True,
            'job_results': results
        })
        
    except Exception as e:
        logger.error(f"Error getting job results for {job_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@batch_bp.route('/cancel/<job_id>', methods=['POST'])
@token_required
def cancel_job(job_id: str):
    """
    Cancel a batch processing job
    
    Args:
        job_id: ID of the batch job to cancel
    """
    try:
        # Validate job_id
        if not job_id or not job_id.strip():
            return jsonify({'error': 'Job ID required'}), 400
        
        # Get current user
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'User not found'}), 401
        
        # Check if user owns this job
        job_record = BatchProcessingJob.query.filter_by(job_id=job_id).first()
        if not job_record:
            return jsonify({'error': 'Job not found'}), 404
        
        if job_record.user_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Cancel job
        success = batch_manager.cancel_job(job_id)
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Failed to cancel job - may already be completed'
            }), 400
        
        return jsonify({
            'success': True,
            'message': 'Job cancelled successfully'
        })
        
    except Exception as e:
        logger.error(f"Error cancelling job {job_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@batch_bp.route('/jobs', methods=['GET'])
@token_required
def list_user_jobs():
    """
    List all batch jobs for the current user
    """
    try:
        # Get current user
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'User not found'}), 401
        
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 100)
        status_filter = request.args.get('status')
        
        # Query jobs
        query = BatchProcessingJob.query.filter_by(user_id=current_user.id)
        
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        # Order by creation date (newest first)
        query = query.order_by(BatchProcessingJob.created_at.desc())
        
        # Paginate
        jobs = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'success': True,
            'jobs': [job.to_dict() for job in jobs.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': jobs.total,
                'pages': jobs.pages,
                'has_next': jobs.has_next,
                'has_prev': jobs.has_prev
            }
        })
        
    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@batch_bp.route('/stats', methods=['GET'])
@token_required
def get_batch_stats():
    """
    Get batch processing statistics
    """
    try:
        # Get current user
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'User not found'}), 401
        
        # Get user-specific stats
        user_stats = db.session.query(
            db.func.count(BatchProcessingJob.id).label('total_jobs'),
            db.func.count(db.case([(BatchProcessingJob.status == 'completed', 1)])).label('completed_jobs'),
            db.func.count(db.case([(BatchProcessingJob.status == 'failed', 1)])).label('failed_jobs'),
            db.func.count(db.case([(BatchProcessingJob.status == 'processing', 1)])).label('processing_jobs'),
            db.func.sum(BatchProcessingJob.total_documents).label('total_documents'),
            db.func.sum(BatchProcessingJob.successful_extractions).label('successful_extractions')
        ).filter_by(user_id=current_user.id).first()
        
        # Get manager stats
        manager_stats = batch_manager.get_manager_stats()
        
        return jsonify({
            'success': True,
            'user_stats': {
                'total_jobs': user_stats.total_jobs or 0,
                'completed_jobs': user_stats.completed_jobs or 0,
                'failed_jobs': user_stats.failed_jobs or 0,
                'processing_jobs': user_stats.processing_jobs or 0,
                'total_documents': user_stats.total_documents or 0,
                'successful_extractions': user_stats.successful_extractions or 0,
                'success_rate': (user_stats.successful_extractions / user_stats.total_documents 
                               if user_stats.total_documents else 0)
            },
            'system_stats': manager_stats
        })
        
    except Exception as e:
        logger.error(f"Error getting batch stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@batch_bp.route('/cleanup', methods=['POST'])
@token_required
def cleanup_jobs():
    """
    Clean up old completed jobs
    Admin endpoint for maintenance
    """
    try:
        # Get current user
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'User not found'}), 401
        
        # Check if user is admin
        if not current_user.is_admin():
            return jsonify({'error': 'Admin access required'}), 403
        
        # Get parameters
        max_age_hours = request.json.get('max_age_hours', 24) if request.is_json else 24
        
        # Perform cleanup
        batch_manager.cleanup_completed_jobs(max_age_hours)
        
        return jsonify({
            'success': True,
            'message': f'Cleaned up jobs older than {max_age_hours} hours'
        })
        
    except Exception as e:
        logger.error(f"Error cleaning up jobs: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@batch_bp.route('/health', methods=['GET'])
def health_check():
    """Health check for batch processing service"""
    try:
        # Get manager stats
        stats = batch_manager.get_manager_stats()
        
        # Check if service is healthy
        is_healthy = (
            stats['active_jobs'] < stats['max_workers'] * 2 and  # Not overloaded
            stats['success_rate'] > 0.8  # Good success rate
        )
        
        return jsonify({
            'success': True,
            'service': 'Batch Processing',
            'status': 'healthy' if is_healthy else 'degraded',
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Batch service health check failed: {e}")
        return jsonify({
            'success': False,
            'service': 'Batch Processing',
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@batch_bp.route('/export/<job_id>', methods=['GET'])
@token_required
def export_job_results(job_id: str):
    """
    Export batch job results in various formats
    
    Args:
        job_id: ID of the batch job
    """
    try:
        # Validate job_id
        if not job_id or not job_id.strip():
            return jsonify({'error': 'Job ID required'}), 400
        
        # Get current user
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'User not found'}), 401
        
        # Get export format
        export_format = request.args.get('format', 'json').lower()
        
        if export_format not in ['json', 'csv', 'excel']:
            return jsonify({'error': 'Unsupported format. Use json, csv, or excel'}), 400
        
        # Get job results
        results = batch_manager.get_job_results(job_id)
        
        if not results:
            return jsonify({'error': 'Job not found or not completed'}), 404
        
        # Export based on format
        if export_format == 'json':
            from flask import Response
            import json
            
            response = Response(
                json.dumps(results, indent=2),
                mimetype='application/json',
                headers={'Content-Disposition': f'attachment; filename=batch_results_{job_id}.json'}
            )
            return response
        
        elif export_format == 'csv':
            import csv
            from io import StringIO
            from flask import Response
            
            output = StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(['Document ID', 'Success', 'Document Type', 'Confidence', 'Quality Score', 'Error'])
            
            # Write data
            for result in results['results']:
                writer.writerow([
                    result.get('document_id', ''),
                    result.get('success', False),
                    result.get('classification', {}).get('document_type', ''),
                    result.get('classification', {}).get('confidence', 0),
                    result.get('quality_score', 0),
                    result.get('error', '')
                ])
            
            response = Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={'Content-Disposition': f'attachment; filename=batch_results_{job_id}.csv'}
            )
            return response
        
        elif export_format == 'excel':
            import pandas as pd
            from io import BytesIO
            from flask import Response
            
            # Prepare data for DataFrame
            data = []
            for result in results['results']:
                data.append({
                    'Document ID': result.get('document_id', ''),
                    'Success': result.get('success', False),
                    'Document Type': result.get('classification', {}).get('document_type', ''),
                    'Confidence': result.get('classification', {}).get('confidence', 0),
                    'Quality Score': result.get('quality_score', 0),
                    'Error': result.get('error', '')
                })
            
            df = pd.DataFrame(data)
            
            # Create Excel file
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Batch Results')
            
            output.seek(0)
            
            response = Response(
                output.read(),
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                headers={'Content-Disposition': f'attachment; filename=batch_results_{job_id}.xlsx'}
            )
            return response
        
    except Exception as e:
        logger.error(f"Error exporting job results for {job_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500