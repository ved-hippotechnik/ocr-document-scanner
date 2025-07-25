"""
Documented API routes using Flask-RESTX
"""

from flask import request, current_app
from flask_restx import Resource, marshal_with
import logging
from typing import Dict, Any

from .api_docs import (
    scan_ns, async_ns, batch_ns, auth_ns, analytics_ns, mcp_ns,
    scan_request, scan_response, async_scan_request, async_scan_response,
    task_status_response, batch_request, batch_response,
    login_request, login_response, analytics_request, analytics_response,
    mcp_thinking_request, mcp_thinking_response, mcp_context_request,
    mcp_memory_request, success_response, error_model
)
from .auth.jwt_utils import jwt_required, get_current_user
from .database import db, ScanHistory, BatchProcessingJob
from .tasks import (
    process_document_async,
    batch_process_async,
    generate_analytics_async
)

logger = logging.getLogger(__name__)


# Scan endpoints
@scan_ns.route('')
class ScanResource(Resource):
    @scan_ns.expect(scan_request)
    @scan_ns.marshal_with(scan_response)
    @scan_ns.response(400, 'Bad Request', error_model)
    @scan_ns.response(401, 'Unauthorized', error_model)
    @scan_ns.response(500, 'Internal Server Error', error_model)
    @jwt_required
    def post(self):
        """Process a document synchronously"""
        try:
            data = request.get_json()
            user = get_current_user()
            
            # Process document using enhanced OCR
            from .routes_enhanced import process_document_enhanced
            result = process_document_enhanced(
                data['image'],
                data.get('document_type'),
                user.id
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Scan error: {str(e)}")
            scan_ns.abort(500, str(e))


@scan_ns.route('/processors')
class ProcessorsResource(Resource):
    @scan_ns.response(200, 'Success')
    def get(self):
        """Get list of available document processors"""
        from .processors import processor_registry
        return {
            'supported_documents': processor_registry.list_supported_documents(),
            'total_processors': len(processor_registry.processors)
        }


# Async endpoints
@async_ns.route('/scan')
class AsyncScanResource(Resource):
    @async_ns.expect(async_scan_request)
    @async_ns.marshal_with(async_scan_response)
    @async_ns.response(202, 'Accepted', async_scan_response)
    @async_ns.response(400, 'Bad Request', error_model)
    @async_ns.response(401, 'Unauthorized', error_model)
    @jwt_required
    def post(self):
        """Submit document for asynchronous processing"""
        try:
            data = request.get_json()
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
            task = process_document_async.apply_async(
                args=[scan.id, data['image'], data.get('document_type')],
                priority=data.get('priority', 0)
            )
            
            # Update scan with task ID
            scan.task_id = task.id
            db.session.commit()
            
            return {
                'success': True,
                'scan_id': scan.id,
                'task_id': task.id,
                'status': 'queued',
                'message': 'Document submitted for processing'
            }, 202
            
        except Exception as e:
            logger.error(f"Async scan error: {str(e)}")
            async_ns.abort(500, str(e))


@async_ns.route('/status/<string:task_id>')
class TaskStatusResource(Resource):
    @async_ns.marshal_with(task_status_response)
    @async_ns.response(200, 'Success', task_status_response)
    @async_ns.response(404, 'Task not found', error_model)
    @jwt_required
    def get(self, task_id):
        """Get status of an asynchronous task"""
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
            
            return response
            
        except Exception as e:
            logger.error(f"Task status error: {str(e)}")
            async_ns.abort(500, str(e))


@async_ns.route('/cancel/<string:task_id>')
class TaskCancelResource(Resource):
    @async_ns.response(200, 'Success', success_response)
    @async_ns.response(404, 'Task not found', error_model)
    @jwt_required
    def post(self, task_id):
        """Cancel an asynchronous task"""
        try:
            from celery.result import AsyncResult
            task = AsyncResult(task_id, app=current_app.celery)
            
            # Revoke the task
            task.revoke(terminate=True)
            
            # Update database records
            scan = ScanHistory.query.filter_by(task_id=task_id).first()
            if scan:
                scan.status = 'cancelled'
                db.session.commit()
            
            job = BatchProcessingJob.query.filter_by(task_id=task_id).first()
            if job:
                job.status = 'cancelled'
                db.session.commit()
            
            return {
                'success': True,
                'message': f'Task {task_id} has been cancelled'
            }
            
        except Exception as e:
            logger.error(f"Task cancel error: {str(e)}")
            async_ns.abort(500, str(e))


# Batch endpoints
@batch_ns.route('')
class BatchResource(Resource):
    @batch_ns.expect(batch_request)
    @batch_ns.marshal_with(batch_response)
    @batch_ns.response(202, 'Accepted', batch_response)
    @batch_ns.response(400, 'Bad Request', error_model)
    @batch_ns.response(401, 'Unauthorized', error_model)
    @jwt_required
    def post(self):
        """Submit batch of documents for processing"""
        try:
            data = request.get_json()
            user = get_current_user()
            
            if len(data['images']) > 100:
                batch_ns.abort(400, 'Maximum 100 documents per batch')
            
            # Create batch job
            job = BatchProcessingJob(
                user_id=user.id,
                job_name=data.get('job_name', 'Batch Processing'),
                total_documents=len(data['images']),
                status='queued'
            )
            db.session.add(job)
            db.session.commit()
            
            # Submit async task
            task = batch_process_async.apply_async(
                args=[job.id, data['images']],
                priority=data.get('priority', 0)
            )
            
            # Update job with task ID
            job.task_id = task.id
            db.session.commit()
            
            return {
                'success': True,
                'job_id': job.id,
                'task_id': task.id,
                'total_documents': len(data['images']),
                'status': 'queued',
                'message': 'Batch submitted for processing'
            }, 202
            
        except Exception as e:
            logger.error(f"Batch processing error: {str(e)}")
            batch_ns.abort(500, str(e))


@batch_ns.route('/<int:job_id>')
class BatchJobResource(Resource):
    @batch_ns.response(200, 'Success')
    @batch_ns.response(404, 'Job not found', error_model)
    @jwt_required
    def get(self, job_id):
        """Get batch job status"""
        try:
            job = BatchProcessingJob.query.get_or_404(job_id)
            
            # Check user access
            user = get_current_user()
            if job.user_id != user.id and not user.is_admin:
                batch_ns.abort(403, 'Access denied')
            
            return job.to_dict()
            
        except Exception as e:
            logger.error(f"Batch job status error: {str(e)}")
            batch_ns.abort(500, str(e))


# Analytics endpoints
@analytics_ns.route('/generate')
class AnalyticsGenerateResource(Resource):
    @analytics_ns.expect(analytics_request)
    @analytics_ns.response(202, 'Accepted')
    @analytics_ns.response(401, 'Unauthorized', error_model)
    @jwt_required
    def post(self):
        """Generate analytics report asynchronously"""
        try:
            data = request.get_json() or {}
            user = get_current_user()
            
            # Submit analytics generation task
            task = generate_analytics_async.delay(
                user_id=user.id if not data.get('global', False) else None,
                days=data.get('days', 30)
            )
            
            return {
                'success': True,
                'task_id': task.id,
                'status': 'generating',
                'message': 'Analytics report generation started'
            }, 202
            
        except Exception as e:
            logger.error(f"Analytics generation error: {str(e)}")
            analytics_ns.abort(500, str(e))


@analytics_ns.route('/dashboard')
class AnalyticsDashboardResource(Resource):
    @analytics_ns.response(200, 'Success', analytics_response)
    @analytics_ns.response(401, 'Unauthorized', error_model)
    @jwt_required
    def get(self):
        """Get analytics dashboard data"""
        try:
            from .analytics.dashboard import get_dashboard_data
            user = get_current_user()
            
            # Get date range from query params
            from datetime import datetime, timedelta
            days = int(request.args.get('days', 30))
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            data = get_dashboard_data(
                start_date=start_date,
                end_date=end_date,
                user_id=user.id if not request.args.get('global') else None
            )
            
            return {
                'success': True,
                'data': data,
                'summary': {
                    'total_scans': data.get('total_scans', 0),
                    'success_rate': data.get('success_rate', 0),
                    'avg_processing_time': data.get('avg_processing_time', 0)
                }
            }
            
        except Exception as e:
            logger.error(f"Analytics dashboard error: {str(e)}")
            analytics_ns.abort(500, str(e))


# MCP endpoints
@mcp_ns.route('/thinking/create')
class MCPThinkingResource(Resource):
    @mcp_ns.expect(mcp_thinking_request)
    @mcp_ns.marshal_with(mcp_thinking_response)
    @mcp_ns.response(201, 'Created', mcp_thinking_response)
    @mcp_ns.response(401, 'Unauthorized', error_model)
    @jwt_required
    def post(self):
        """Create a new sequential thinking context"""
        try:
            from .mcp.routes import sequential_thinking_mcp
            data = request.get_json()
            
            session_id = sequential_thinking_mcp.create_context(
                goal=data['goal'],
                metadata=data.get('metadata', {})
            )
            
            return {
                'success': True,
                'session_id': session_id,
                'goal': data['goal']
            }, 201
            
        except Exception as e:
            logger.error(f"MCP thinking error: {str(e)}")
            mcp_ns.abort(500, str(e))


@mcp_ns.route('/context/<string:context_id>/set')
class MCPContextSetResource(Resource):
    @mcp_ns.expect(mcp_context_request)
    @mcp_ns.response(200, 'Success', success_response)
    @mcp_ns.response(404, 'Context not found', error_model)
    @jwt_required
    def post(self, context_id):
        """Set a value in context7"""
        try:
            from .mcp.routes import context7_mcp
            from .mcp.context7 import ContextLayer
            
            data = request.get_json()
            layer = ContextLayer(data['layer'])
            
            success = context7_mcp.set_context(
                context_id=context_id,
                layer=layer,
                key=data['key'],
                value=data['value'],
                confidence=data.get('confidence', 1.0),
                source='api',
                metadata=data.get('metadata', {})
            )
            
            if success:
                return {'success': True, 'message': 'Context updated successfully'}
            else:
                mcp_ns.abort(404, 'Context not found')
                
        except Exception as e:
            logger.error(f"MCP context error: {str(e)}")
            mcp_ns.abort(500, str(e))


@mcp_ns.route('/memory/store')
class MCPMemoryStoreResource(Resource):
    @mcp_ns.expect(mcp_memory_request)
    @mcp_ns.response(201, 'Created')
    @mcp_ns.response(401, 'Unauthorized', error_model)
    @jwt_required
    def post(self):
        """Store a new memory"""
        try:
            from .mcp.routes import memory_mcp
            data = request.get_json()
            
            memory_id = memory_mcp.store_memory(
                content=data['content'],
                context=data.get('context', {}),
                tags=data.get('tags', []),
                importance=data.get('importance', 1.0)
            )
            
            return {
                'success': True,
                'memory_id': memory_id
            }, 201
            
        except Exception as e:
            logger.error(f"MCP memory error: {str(e)}")
            mcp_ns.abort(500, str(e))