"""
Celery tasks for async processing
"""

import os
import json
import base64
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from celery import current_task, group, chain
from celery.exceptions import SoftTimeLimitExceeded
from sqlalchemy import and_

from .celery_app import celery_app
from .database import db, ScanHistory, BatchProcessingJob
from .processors import processor_registry
from .classification import DocumentClassifier
from .quality import QualityAnalyzer
from .validation import EnhancedValidator
from .cache import get_cache_manager
from .mcp.sequential_thinking import SequentialThinkingMCP, ThinkingStage, ThoughtStep
from .mcp.memory import MemoryMCP
from .mcp.filesystem import FilesystemMCP

logger = logging.getLogger(__name__)

# Initialize services (will be properly initialized with app context)
classifier = None
quality_analyzer = None
validator = None
cache_manager = None
sequential_thinking_mcp = None
memory_mcp = None
filesystem_mcp = None


def init_task_services(app):
    """Initialize services for tasks"""
    global classifier, quality_analyzer, validator, cache_manager
    global sequential_thinking_mcp, memory_mcp, filesystem_mcp
    
    classifier = DocumentClassifier()
    quality_analyzer = QualityAnalyzer()
    validator = EnhancedValidator()
    cache_manager = get_cache_manager()
    
    # Initialize MCP services
    sequential_thinking_mcp = SequentialThinkingMCP()
    memory_mcp = MemoryMCP(
        max_memory_size=app.config.get('MCP_MAX_MEMORY_SIZE', 10000),
        persistence_path=app.config.get('MCP_MEMORY_PERSISTENCE_PATH')
    )
    filesystem_mcp = FilesystemMCP(
        base_path=app.config.get('MCP_STORAGE_PATH', 'mcp_storage')
    )


@celery_app.task(bind=True, name='app.tasks.process_document_async')
def process_document_async(self, scan_id: int, image_data: str, 
                          document_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Asynchronously process a document with OCR
    
    Args:
        scan_id: Database ID of the scan record
        image_data: Base64 encoded image data
        document_type: Optional document type hint
    
    Returns:
        Processing result dictionary
    """
    try:
        # Update task state
        self.update_state(state='PROCESSING', meta={'stage': 'initialization'})
        
        # Get scan record
        scan = ScanHistory.query.get(scan_id)
        if not scan:
            raise ValueError(f"Scan record {scan_id} not found")
        
        # Update scan status
        scan.status = 'processing'
        scan.started_at = datetime.utcnow()
        db.session.commit()
        
        # Decode image
        self.update_state(state='PROCESSING', meta={'stage': 'decoding_image'})
        try:
            image_bytes = base64.b64decode(image_data)
        except Exception as e:
            raise ValueError(f"Failed to decode image: {str(e)}")
        
        # Quality analysis
        self.update_state(state='PROCESSING', meta={'stage': 'quality_analysis'})
        quality_result = quality_analyzer.analyze_image_quality(image_bytes)
        scan.quality_score = quality_result['overall_score']
        
        # Document classification
        self.update_state(state='PROCESSING', meta={'stage': 'classification'})
        if not document_type:
            classification_result = classifier.classify_document(image_bytes)
            document_type = classification_result['document_type']
            scan.confidence_score = classification_result['confidence']
        
        scan.document_type = document_type
        db.session.commit()
        
        # Process with appropriate processor
        self.update_state(state='PROCESSING', meta={'stage': 'ocr_processing'})
        processor = processor_registry.get_processor(document_type)
        
        if not processor:
            raise ValueError(f"No processor available for document type: {document_type}")
        
        # Perform OCR
        ocr_result = processor.process(image_bytes)
        
        # Validation
        self.update_state(state='PROCESSING', meta={'stage': 'validation'})
        validation_result = validator.validate_extracted_data(
            ocr_result['data'], 
            document_type
        )
        
        # Cache result
        cache_key = f"ocr_result:{scan_id}"
        cache_manager.set(cache_key, {
            'ocr_result': ocr_result,
            'quality': quality_result,
            'validation': validation_result
        }, ttl=3600)
        
        # Update scan record
        scan.extracted_data = json.dumps(ocr_result['data'])
        scan.validation_status = 'valid' if validation_result['is_valid'] else 'invalid'
        scan.validation_errors = json.dumps(validation_result.get('errors', []))
        scan.completed_at = datetime.utcnow()
        scan.status = 'completed'
        scan.processing_time = (scan.completed_at - scan.started_at).total_seconds()
        
        db.session.commit()
        
        # Store in MCP memory for future reference
        memory_mcp.store_memory(
            content={
                'document_type': document_type,
                'quality_score': quality_result['overall_score'],
                'validation_status': validation_result['is_valid']
            },
            context={'scan_id': scan_id, 'task_id': self.request.id},
            tags=['ocr_processing', document_type, f"scan_{scan_id}"],
            importance=0.7
        )
        
        return {
            'success': True,
            'scan_id': scan_id,
            'document_type': document_type,
            'extracted_data': ocr_result['data'],
            'quality_score': quality_result['overall_score'],
            'validation': validation_result,
            'processing_time': scan.processing_time
        }
        
    except SoftTimeLimitExceeded:
        logger.error(f"Task timeout for scan {scan_id}")
        if scan:
            scan.status = 'timeout'
            scan.error_message = "Processing timeout exceeded"
            db.session.commit()
        raise
        
    except Exception as e:
        logger.error(f"Error processing scan {scan_id}: {str(e)}")
        if scan:
            scan.status = 'failed'
            scan.error_message = str(e)
            scan.completed_at = datetime.utcnow()
            db.session.commit()
        raise


@celery_app.task(bind=True, name='app.tasks.batch_process_async')
def batch_process_async(self, job_id: int, image_data_list: List[str]) -> Dict[str, Any]:
    """
    Process multiple documents in batch
    
    Args:
        job_id: Batch job ID
        image_data_list: List of base64 encoded images
    
    Returns:
        Batch processing results
    """
    try:
        # Update job status
        job = BatchProcessingJob.query.get(job_id)
        if not job:
            raise ValueError(f"Batch job {job_id} not found")
        
        job.status = 'processing'
        job.started_at = datetime.utcnow()
        db.session.commit()
        
        # Create individual scan records
        scan_ids = []
        for idx, image_data in enumerate(image_data_list):
            scan = ScanHistory(
                user_id=job.user_id,
                filename=f"batch_{job_id}_doc_{idx + 1}",
                status='pending',
                batch_job_id=job_id
            )
            db.session.add(scan)
            db.session.flush()
            scan_ids.append(scan.id)
        
        db.session.commit()
        
        # Create subtasks for parallel processing
        job_group = group(
            process_document_async.s(scan_id, image_data)
            for scan_id, image_data in zip(scan_ids, image_data_list)
        )
        
        # Execute subtasks
        result = job_group.apply_async()
        
        # Wait for completion
        results = result.get(timeout=300)  # 5 minute timeout
        
        # Update job status
        successful = sum(1 for r in results if r.get('success', False))
        failed = len(results) - successful
        
        job.completed_at = datetime.utcnow()
        job.successful_count = successful
        job.failed_count = failed
        job.status = 'completed'
        job.processing_time = (job.completed_at - job.started_at).total_seconds()
        
        db.session.commit()
        
        return {
            'success': True,
            'job_id': job_id,
            'total_documents': len(image_data_list),
            'successful': successful,
            'failed': failed,
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Batch processing error for job {job_id}: {str(e)}")
        if job:
            job.status = 'failed'
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.session.commit()
        raise


@celery_app.task(name='app.tasks.generate_analytics_async')
def generate_analytics_async(user_id: Optional[int] = None, 
                           days: int = 30) -> Dict[str, Any]:
    """
    Generate analytics report asynchronously
    
    Args:
        user_id: Optional user ID for user-specific analytics
        days: Number of days to include in report
    
    Returns:
        Analytics report data
    """
    try:
        from .analytics_dashboard import AnalyticsDashboard
        dashboard = AnalyticsDashboard()
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Generate comprehensive analytics
        analytics_data = {
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'processing_stats': dashboard.get_processing_stats(start_date, end_date, user_id),
            'document_distribution': dashboard.get_document_distribution(start_date, end_date, user_id),
            'quality_metrics': dashboard.get_quality_metrics(start_date, end_date, user_id),
            'performance_trends': dashboard.get_performance_trends(start_date, end_date, user_id),
            'error_analysis': dashboard.get_error_analysis(start_date, end_date, user_id),
            'user_activity': dashboard.get_user_activity(start_date, end_date) if not user_id else None
        }
        
        # Store report
        report_filename = f"analytics_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        filesystem_mcp.write_file(
            f"reports/{report_filename}",
            json.dumps(analytics_data, indent=2),
            metadata={'user_id': user_id, 'days': days}
        )
        
        # Cache report
        cache_key = f"analytics_report:{user_id or 'global'}:{days}"
        cache_manager.set(cache_key, analytics_data, ttl=3600)
        
        return {
            'success': True,
            'report_file': report_filename,
            'data': analytics_data
        }
        
    except Exception as e:
        logger.error(f"Analytics generation error: {str(e)}")
        raise


@celery_app.task(name='app.tasks.cleanup_old_files_async')
def cleanup_old_files_async(days_to_keep: int = 30) -> Dict[str, Any]:
    """
    Clean up old files and database records
    
    Args:
        days_to_keep: Number of days to retain files
    
    Returns:
        Cleanup summary
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # Clean up database records
        old_scans = ScanHistory.query.filter(
            ScanHistory.created_at < cutoff_date
        ).all()
        
        deleted_scans = len(old_scans)
        for scan in old_scans:
            db.session.delete(scan)
        
        # Clean up batch jobs
        old_jobs = BatchProcessingJob.query.filter(
            BatchProcessingJob.created_at < cutoff_date
        ).all()
        
        deleted_jobs = len(old_jobs)
        for job in old_jobs:
            db.session.delete(job)
        
        db.session.commit()
        
        # Clean up filesystem
        files = filesystem_mcp.list_directory("", recursive=True)
        deleted_files = 0
        
        for file_info in files:
            if file_info.created < cutoff_date:
                if filesystem_mcp.delete_file(file_info.path):
                    deleted_files += 1
        
        # Clear old cache entries
        cache_manager.clear_expired()
        
        return {
            'success': True,
            'deleted_scans': deleted_scans,
            'deleted_jobs': deleted_jobs,
            'deleted_files': deleted_files,
            'cutoff_date': cutoff_date.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Cleanup error: {str(e)}")
        raise


@celery_app.task(bind=True, name='app.tasks.process_with_mcp_thinking')
def process_with_mcp_thinking(self, document_id: int, requirements: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process document using MCP Sequential Thinking for complex workflows
    
    Args:
        document_id: Document ID to process
        requirements: Processing requirements and context
    
    Returns:
        Processing results with thinking trace
    """
    try:
        # Create thinking context
        session_id = sequential_thinking_mcp.create_context(
            goal=f"Process document {document_id} with requirements",
            metadata={'document_id': document_id, 'requirements': requirements}
        )
        
        # Add analysis step
        sequential_thinking_mcp.add_step(session_id, ThoughtStep(
            step_id="analyze_doc",
            stage=ThinkingStage.ANALYSIS,
            description="Analyze document and requirements",
            input_data={
                'document_id': document_id,
                'requirements': requirements
            }
        ))
        
        # Add planning step
        sequential_thinking_mcp.add_step(session_id, ThoughtStep(
            step_id="plan_processing",
            stage=ThinkingStage.PLANNING,
            description="Plan processing approach",
            input_data={},
            dependencies=["analyze_doc"]
        ))
        
        # Process steps
        thinking_trace = []
        while True:
            step = sequential_thinking_mcp.process_next_step(session_id)
            if not step:
                break
            
            thinking_trace.append({
                'step': step.step_id,
                'stage': step.stage.value,
                'status': step.status,
                'output': step.output_data
            })
            
            # Update task progress
            self.update_state(
                state='PROCESSING',
                meta={
                    'thinking_stage': step.stage.value,
                    'current_step': step.step_id
                }
            )
        
        # Get final thinking trace
        final_trace = sequential_thinking_mcp.export_thinking_trace(session_id)
        
        return {
            'success': True,
            'session_id': session_id,
            'thinking_trace': final_trace,
            'result': thinking_trace[-1]['output'] if thinking_trace else None
        }
        
    except Exception as e:
        logger.error(f"MCP thinking error: {str(e)}")
        raise


# Periodic tasks
@celery_app.task(name='app.tasks.periodic_cleanup')
def periodic_cleanup():
    """Periodic cleanup task (run daily)"""
    return cleanup_old_files_async.delay(days_to_keep=30)


@celery_app.task(name='app.tasks.periodic_analytics')
def periodic_analytics():
    """Generate daily analytics reports"""
    return generate_analytics_async.delay(days=1)


# Task monitoring
@celery_app.task(name='app.tasks.monitor_task_health')
def monitor_task_health() -> Dict[str, Any]:
    """Monitor health of task queues and workers"""
    from celery import current_app
    
    inspect = current_app.control.inspect()
    
    stats = {
        'active_tasks': len(inspect.active() or {}),
        'scheduled_tasks': len(inspect.scheduled() or {}),
        'reserved_tasks': len(inspect.reserved() or {}),
        'workers': list((inspect.active_queues() or {}).keys()),
        'timestamp': datetime.utcnow().isoformat()
    }
    
    # Store in cache for monitoring
    cache_manager.set('celery_health', stats, ttl=60)
    
    return stats