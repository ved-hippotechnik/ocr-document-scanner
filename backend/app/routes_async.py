"""
Async processing routes using Celery
"""

from flask import Blueprint, request, jsonify, current_app, g
import logging
from typing import Dict, Any
from .auth.jwt_utils import token_required, get_current_user
from .database import db, ScanHistory, BatchProcessingJob
from .resilience import structured_error
from .tasks import (
    process_document_async,
    batch_process_async,
    generate_analytics_async,
    process_with_mcp_thinking
)

logger = logging.getLogger(__name__)

# Create Blueprint
async_bp = Blueprint('async', __name__, url_prefix='/api/async')


def _check_celery_available():
    """Return structured 503 if no Celery workers are responding."""
    celery = getattr(current_app, 'celery', None)
    if celery is None:
        return structured_error('Task queue not configured', 'CELERY_UNAVAILABLE', 503, component='celery')
    try:
        inspect = celery.control.inspect(timeout=3)
        ping = inspect.ping()
        if not ping:
            return structured_error('No task workers available', 'NO_WORKERS', 503, component='celery')
    except Exception as e:
        logger.warning("Celery health check failed: %s", e)
        return structured_error('Task queue unreachable', 'CELERY_UNREACHABLE', 503, details=e, component='celery')
    return None


def _verify_task_ownership(task_id):
    """Verify the current user owns the task. Returns error response or None."""
    user = get_current_user()
    scan = ScanHistory.query.filter_by(task_id=task_id).first()
    job = BatchProcessingJob.query.filter_by(task_id=task_id).first()
    owner_id = None
    if scan:
        owner_id = scan.user_id
    elif job:
        owner_id = job.user_id
    if owner_id is not None and owner_id != user.id:
        logger.warning("User %s attempted to access task %s owned by %s", user.id, task_id, owner_id)
        return structured_error('Task not found', 'TASK_NOT_FOUND', 404)
    return None


@async_bp.route('/scan', methods=['POST'])
@token_required
def async_scan():
    """Submit document for async processing"""
    try:
        # Check Celery availability before accepting work
        celery_err = _check_celery_available()
        if celery_err:
            return celery_err

        data = request.get_json()

        if not data or 'image' not in data:
            return structured_error('No image data provided', 'IMAGE_REQUIRED', 400)

        user = get_current_user()

        # Create scan record
        scan = ScanHistory(
            user_id=user.id,
            filename=data.get('filename', 'async_upload'),
            status='queued',
            document_type=data.get('document_type')
        )
        db.session.add(scan)
        try:
            db.session.commit()
        except Exception as db_err:
            db.session.rollback()
            return structured_error('Failed to create scan record', 'DB_ERROR', 500, details=db_err)

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
            'message': 'Document submitted for processing',
            'request_id': getattr(g, 'request_id', None),
        }), 202

    except Exception as e:
        logger.error("Async scan error (request_id=%s): %s", getattr(g, 'request_id', 'unknown'), e)
        return structured_error('Async scan failed', 'ASYNC_SCAN_ERROR', 500, details=e)


@async_bp.route('/batch', methods=['POST'])
@token_required
def async_batch():
    """Submit batch of documents for async processing"""
    try:
        celery_err = _check_celery_available()
        if celery_err:
            return celery_err

        data = request.get_json()

        if not data or 'images' not in data or not isinstance(data['images'], list):
            return structured_error('No images array provided', 'IMAGES_REQUIRED', 400)

        if len(data['images']) > 100:
            return structured_error('Maximum 100 documents per batch', 'BATCH_TOO_LARGE', 400)

        user = get_current_user()

        # Create batch job
        job = BatchProcessingJob(
            user_id=user.id,
            total_documents=len(data['images']),
            status='queued'
        )
        db.session.add(job)
        try:
            db.session.commit()
        except Exception as db_err:
            db.session.rollback()
            return structured_error('Failed to create batch job', 'DB_ERROR', 500, details=db_err)

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
            'message': 'Batch submitted for processing',
            'request_id': getattr(g, 'request_id', None),
        }), 202

    except Exception as e:
        logger.error("Async batch error (request_id=%s): %s", getattr(g, 'request_id', 'unknown'), e)
        return structured_error('Async batch failed', 'ASYNC_BATCH_ERROR', 500, details=e)


@async_bp.route('/status/<task_id>', methods=['GET'])
@token_required
def get_task_status(task_id):
    """Get status of async task"""
    try:
        # Verify ownership
        ownership_err = _verify_task_ownership(task_id)
        if ownership_err:
            return ownership_err

        from celery.result import AsyncResult
        task = AsyncResult(task_id, app=current_app.celery)

        response = {
            'task_id': task_id,
            'state': task.state,
            'ready': task.ready(),
            'request_id': getattr(g, 'request_id', None),
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
        logger.error("Task status error (request_id=%s): %s", getattr(g, 'request_id', 'unknown'), e)
        return structured_error('Failed to get task status', 'TASK_STATUS_ERROR', 500, details=e)


@async_bp.route('/cancel/<task_id>', methods=['POST'])
@token_required
def cancel_task(task_id):
    """Cancel an async task"""
    try:
        # Verify ownership
        ownership_err = _verify_task_ownership(task_id)
        if ownership_err:
            return ownership_err

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
            'status': 'cancelled',
            'request_id': getattr(g, 'request_id', None),
        }), 200

    except Exception as e:
        logger.error("Task cancel error (request_id=%s): %s", getattr(g, 'request_id', 'unknown'), e)
        return structured_error('Failed to cancel task', 'TASK_CANCEL_ERROR', 500, details=e)


@async_bp.route('/analytics/generate', methods=['POST'])
@token_required
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
        logger.error("Analytics generation error (request_id=%s): %s", getattr(g, 'request_id', 'unknown'), e)
        return structured_error('Analytics generation failed', 'ANALYTICS_ERROR', 500, details=e)


@async_bp.route('/mcp/think', methods=['POST'])
@token_required
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
        logger.error("MCP thinking error (request_id=%s): %s", getattr(g, 'request_id', 'unknown'), e)
        return structured_error('MCP thinking failed', 'MCP_ERROR', 500, details=e)


@async_bp.route('/queue/stats', methods=['GET'])
@token_required
def get_queue_stats():
    """Get Celery queue statistics"""
    try:
        from celery import current_app as celery_app
        inspect = celery_app.control.inspect(timeout=5)

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
                except Exception:
                    queue_lengths[queue_name] = 0

        stats['queue_lengths'] = queue_lengths

        return jsonify({
            'success': True,
            'stats': stats,
            'request_id': getattr(g, 'request_id', None),
        }), 200

    except Exception as e:
        logger.error("Queue stats error (request_id=%s): %s", getattr(g, 'request_id', 'unknown'), e)
        return structured_error('Failed to get queue stats', 'QUEUE_STATS_ERROR', 500, details=e)