"""
Async processing routes using Celery
"""

from flask import Blueprint, request, jsonify, current_app
import logging
from typing import Dict, Any
from .auth.jwt_utils import jwt_required, get_current_user
from .database import db, ScanHistory, BatchProcessingJob
from .tasks import (
    process_document_async,
    batch_process_async,
    generate_analytics_async,
    process_with_mcp_thinking
)

logger = logging.getLogger(__name__)

# Create Blueprint
async_bp = Blueprint('async', __name__, url_prefix='/api/async')


@async_bp.route('/scan', methods=['POST'])
@jwt_required
def async_scan():
    """Submit document for async processing"""
    try:
        data = request.get_json()
        
        if not data or 'image' not in data:
            return jsonify({'error': 'No image data provided'}), 400
        
        user = get_current_user()
        
        # Create scan record
        scan = ScanHistory(
            user_id=user.id,
            filename=data.get('filename', 'async_upload'),
            status='queued',
            document_type=data.get('document_type')
        )
        db.session.add(scan)
        db.session.commit()
        
        # Submit async task
        task = process_document_async.delay(
            scan.id,
            data['image'],
            data.get('document_type')
        )
        
        # Update scan with task ID
        scan.task_id = task.id
        db.session.commit()
        
        return jsonify({
            'success': True,
            'scan_id': scan.id,
            'task_id': task.id,
            'status': 'queued',
            'message': 'Document submitted for processing'
        }), 202
        
    except Exception as e:
        logger.error(f"Async scan error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@async_bp.route('/batch', methods=['POST'])
@jwt_required
def async_batch():
    """Submit batch of documents for async processing"""
    try:
        data = request.get_json()
        
        if not data or 'images' not in data or not isinstance(data['images'], list):
            return jsonify({'error': 'No images array provided'}), 400
        
        if len(data['images']) > 100:
            return jsonify({'error': 'Maximum 100 documents per batch'}), 400
        
        user = get_current_user()
        
        # Create batch job
        job = BatchProcessingJob(
            user_id=user.id,
            total_documents=len(data['images']),
            status='queued'
        )
        db.session.add(job)
        db.session.commit()
        
        # Submit async task
        task = batch_process_async.delay(job.id, data['images'])
        
        # Update job with task ID
        job.task_id = task.id
        db.session.commit()
        
        return jsonify({
            'success': True,
            'job_id': job.id,
            'task_id': task.id,
            'status': 'queued',
            'total_documents': len(data['images']),
            'message': 'Batch submitted for processing'
        }), 202
        
    except Exception as e:
        logger.error(f"Async batch error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@async_bp.route('/status/<task_id>', methods=['GET'])
@jwt_required
def get_task_status(task_id):
    """Get status of async task"""
    try:
        from celery.result import AsyncResult
        task = AsyncResult(task_id, app=current_app.celery)
        
        response = {
            'task_id': task_id,
            'state': task.state,
            'ready': task.ready()
        }
        
        if task.state == 'PENDING':
            response['status'] = 'Task not found or pending'
        elif task.state == 'PROCESSING':
            response['current'] = task.info
        elif task.state == 'SUCCESS':
            response['result'] = task.result
        elif task.state == 'FAILURE':
            response['error'] = str(task.info)
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Task status error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@async_bp.route('/cancel/<task_id>', methods=['POST'])
@jwt_required
def cancel_task(task_id):
    """Cancel an async task"""
    try:
        from celery.result import AsyncResult
        task = AsyncResult(task_id, app=current_app.celery)
        
        # Revoke the task
        task.revoke(terminate=True)
        
        # Update database record if applicable
        scan = ScanHistory.query.filter_by(task_id=task_id).first()
        if scan:
            scan.status = 'cancelled'
            db.session.commit()
        
        job = BatchProcessingJob.query.filter_by(task_id=task_id).first()
        if job:
            job.status = 'cancelled'
            db.session.commit()
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'status': 'cancelled'
        }), 200
        
    except Exception as e:
        logger.error(f"Task cancel error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@async_bp.route('/analytics/generate', methods=['POST'])
@jwt_required
def async_generate_analytics():
    """Generate analytics report asynchronously"""
    try:
        data = request.get_json() or {}
        user = get_current_user()
        
        # Submit analytics generation task
        task = generate_analytics_async.delay(
            user_id=user.id if not data.get('global', False) else None,
            days=data.get('days', 30)
        )
        
        return jsonify({
            'success': True,
            'task_id': task.id,
            'status': 'generating',
            'message': 'Analytics report generation started'
        }), 202
        
    except Exception as e:
        logger.error(f"Analytics generation error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@async_bp.route('/mcp/think', methods=['POST'])
@jwt_required
def async_mcp_thinking():
    """Process document with MCP sequential thinking"""
    try:
        data = request.get_json()
        
        if not data or 'document_id' not in data:
            return jsonify({'error': 'No document_id provided'}), 400
        
        # Submit thinking task
        task = process_with_mcp_thinking.delay(
            document_id=data['document_id'],
            requirements=data.get('requirements', {})
        )
        
        return jsonify({
            'success': True,
            'task_id': task.id,
            'status': 'thinking',
            'message': 'MCP thinking process started'
        }), 202
        
    except Exception as e:
        logger.error(f"MCP thinking error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@async_bp.route('/queue/stats', methods=['GET'])
@jwt_required
def get_queue_stats():
    """Get Celery queue statistics"""
    try:
        from celery import current_app as celery_app
        inspect = celery_app.control.inspect()
        
        stats = {
            'active': inspect.active(),
            'scheduled': inspect.scheduled(),
            'reserved': inspect.reserved(),
            'registered': inspect.registered(),
            'stats': inspect.stats()
        }
        
        # Get queue lengths
        from kombu import Connection
        with Connection(current_app.config.get('CELERY_BROKER_URL')) as conn:
            queues = ['default', 'ocr_processing', 'batch_processing', 'analytics', 'maintenance']
            queue_lengths = {}
            
            for queue_name in queues:
                try:
                    queue = conn.SimpleQueue(queue_name)
                    queue_lengths[queue_name] = queue.qsize()
                    queue.close()
                except:
                    queue_lengths[queue_name] = 0
        
        stats['queue_lengths'] = queue_lengths
        
        return jsonify({
            'success': True,
            'stats': stats
        }), 200
        
    except Exception as e:
        logger.error(f"Queue stats error: {str(e)}")
        return jsonify({'error': str(e)}), 500