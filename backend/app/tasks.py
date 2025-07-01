"""
Celery configuration and background tasks for OCR Document Scanner
"""
from celery import Celery
import os
import logging
from datetime import datetime, timezone
import json

# Celery configuration
def make_celery(app):
    """Create and configure Celery instance"""
    celery = Celery(
        app.import_name,
        backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
        broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    )
    
    # Update configuration from Flask app
    celery.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        result_expires=3600,  # Results expire after 1 hour
        task_soft_time_limit=300,  # 5 minutes soft limit
        task_time_limit=600,  # 10 minutes hard limit
        worker_prefetch_multiplier=1,
        task_acks_late=True,
        worker_disable_rate_limits=False,
        task_compression='gzip',
        result_compression='gzip'
    )
    
    # Configure task routes
    celery.conf.task_routes = {
        'app.tasks.process_document_async': {'queue': 'document_processing'},
        'app.tasks.process_batch_documents': {'queue': 'batch_processing'},
        'app.tasks.cleanup_old_files': {'queue': 'maintenance'},
        'app.tasks.generate_analytics_report': {'queue': 'analytics'}
    }
    
    class ContextTask(celery.Task):
        """Make celery tasks work with Flask app context"""
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery

# Initialize Celery (to be called from app factory)
celery = None

def init_celery(app):
    """Initialize Celery with Flask app"""
    global celery
    celery = make_celery(app)
    return celery

# Create a dummy Celery instance for task decoration
# This will be replaced by the real instance in init_celery
celery = Celery('dummy')

# Background Tasks
@celery.task(bind=True, name='app.tasks.process_document_async')
def process_document_async(self, image_data, document_type=None, options=None):
    """
    Process document asynchronously
    
    Args:
        image_data: Base64 encoded image data
        document_type: Optional document type hint
        options: Processing options
    
    Returns:
        dict: Processing result with job information
    """
    try:
        from .processors import processor_registry
        from .classification import document_classifier
        from .quality import quality_analyzer
        from .database import log_scan_result
        import base64
        import cv2
        import numpy as np
        from PIL import Image
        import io
        import time
        import uuid
        
        start_time = time.time()
        task_id = self.request.id
        
        # Update task status
        self.update_state(
            state='PROCESSING',
            meta={'status': 'Decoding image data', 'progress': 10}
        )
        
        # Decode image
        try:
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            image_array = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        except Exception as e:
            raise Exception(f"Failed to decode image: {str(e)}")
        
        # Update progress
        self.update_state(
            state='PROCESSING',
            meta={'status': 'Analyzing image quality', 'progress': 25}
        )
        
        # Quality analysis
        quality_result = quality_analyzer.analyze_quality(image_array)
        
        # Update progress
        self.update_state(
            state='PROCESSING',
            meta={'status': 'Classifying document type', 'progress': 40}
        )
        
        # Document classification
        classification_result = document_classifier.classify_document(image_array)
        
        # Update progress
        self.update_state(
            state='PROCESSING',
            meta={'status': 'Processing document', 'progress': 60}
        )
        
        # Document processing
        result = {}
        processor_used = None
        
        if classification_result['document_type'] != 'unknown':
            processor = processor_registry.get_processor(classification_result['document_type'])
            if processor:
                processing_result = processor.process_document(image_array)
                result.update(processing_result)
                processor_used = processor.__class__.__name__
        elif document_type:
            processor = processor_registry.get_processor(document_type)
            if processor:
                processing_result = processor.process_document(image_array)
                result.update(processing_result)
                processor_used = processor.__class__.__name__
        
        # Update progress
        self.update_state(
            state='PROCESSING',
            meta={'status': 'Finalizing results', 'progress': 80}
        )
        
        # Combine results
        processing_time = time.time() - start_time
        final_result = {
            'task_id': task_id,
            'document_type': result.get('document_type', classification_result['document_type']),
            'confidence': result.get('confidence', classification_result['confidence']),
            'extracted_data': result.get('extracted_data', {}),
            'quality_assessment': quality_result,
            'classification_result': classification_result,
            'processor_used': processor_used,
            'processing_time': round(processing_time, 3),
            'status': 'completed',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Log to database
        try:
            session_id = options.get('session_id', str(uuid.uuid4())) if options else str(uuid.uuid4())
            log_scan_result(
                session_id=session_id,
                document_type=final_result['document_type'],
                result_data=final_result,
                processing_time=processing_time,
                file_info={'size': len(image_data), 'format': 'base64'},
                request_info={'ip': 'async_task', 'user_agent': 'Celery Worker'}
            )
        except Exception as e:
            logging.error(f"Failed to log async task result: {str(e)}")
        
        # Update progress to completed
        self.update_state(
            state='SUCCESS',
            meta={'status': 'Completed successfully', 'progress': 100, 'result': final_result}
        )
        
        return final_result
        
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Async document processing failed: {error_msg}")
        
        self.update_state(
            state='FAILURE',
            meta={
                'status': 'Failed',
                'error': error_msg,
                'progress': 0,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        )
        
        raise Exception(error_msg)

@celery.task(bind=True, name='app.tasks.process_batch_documents')
def process_batch_documents(self, batch_data):
    """
    Process multiple documents in batch
    
    Args:
        batch_data: List of document data with image_data and metadata
    
    Returns:
        dict: Batch processing results
    """
    try:
        batch_id = self.request.id
        total_documents = len(batch_data)
        results = []
        errors = []
        
        self.update_state(
            state='PROCESSING',
            meta={
                'status': f'Processing batch of {total_documents} documents',
                'progress': 0,
                'completed': 0,
                'total': total_documents
            }
        )
        
        for i, doc_data in enumerate(batch_data):
            try:
                # Process individual document
                doc_result = process_document_async.apply_async(
                    args=[doc_data['image_data'], doc_data.get('document_type'), doc_data.get('options')]
                ).get(timeout=300)  # 5 minute timeout per document
                
                results.append({
                    'index': i,
                    'filename': doc_data.get('filename', f'document_{i}'),
                    'result': doc_result,
                    'status': 'success'
                })
                
            except Exception as e:
                error_info = {
                    'index': i,
                    'filename': doc_data.get('filename', f'document_{i}'),
                    'error': str(e),
                    'status': 'error'
                }
                errors.append(error_info)
                results.append(error_info)
            
            # Update progress
            progress = int((i + 1) / total_documents * 100)
            self.update_state(
                state='PROCESSING',
                meta={
                    'status': f'Processed {i + 1}/{total_documents} documents',
                    'progress': progress,
                    'completed': i + 1,
                    'total': total_documents,
                    'errors': len(errors)
                }
            )
        
        # Final result
        batch_result = {
            'batch_id': batch_id,
            'total_documents': total_documents,
            'successful': total_documents - len(errors),
            'failed': len(errors),
            'results': results,
            'errors': errors,
            'status': 'completed',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        self.update_state(
            state='SUCCESS',
            meta={
                'status': 'Batch processing completed',
                'progress': 100,
                'result': batch_result
            }
        )
        
        return batch_result
        
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Batch processing failed: {error_msg}")
        
        self.update_state(
            state='FAILURE',
            meta={
                'status': 'Batch processing failed',
                'error': error_msg,
                'progress': 0,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        )
        
        raise Exception(error_msg)

@celery.task(name='app.tasks.cleanup_old_files')
def cleanup_old_files():
    """Clean up old uploaded files and temp data"""
    try:
        import os
        import shutil
        from datetime import timedelta
        
        upload_dir = os.getenv('UPLOAD_FOLDER', '/app/uploads')
        max_age_days = int(os.getenv('FILE_CLEANUP_DAYS', 7))
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=max_age_days)
        
        cleaned_count = 0
        total_size_freed = 0
        
        if os.path.exists(upload_dir):
            for filename in os.listdir(upload_dir):
                file_path = os.path.join(upload_dir, filename)
                if os.path.isfile(file_path):
                    file_mtime = datetime.fromtimestamp(
                        os.path.getmtime(file_path), 
                        tz=timezone.utc
                    )
                    
                    if file_mtime < cutoff_time:
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        cleaned_count += 1
                        total_size_freed += file_size
        
        # Clean up old database records
        from .database import ScanHistory, db
        old_records = ScanHistory.query.filter(
            ScanHistory.created_at < cutoff_time
        ).count()
        
        if old_records > 0:
            ScanHistory.query.filter(
                ScanHistory.created_at < cutoff_time
            ).delete()
            db.session.commit()
        
        result = {
            'files_cleaned': cleaned_count,
            'space_freed_mb': round(total_size_freed / (1024 * 1024), 2),
            'old_records_removed': old_records,
            'cleanup_date': datetime.now(timezone.utc).isoformat()
        }
        
        logging.info(f"Cleanup completed: {result}")
        return result
        
    except Exception as e:
        error_msg = f"Cleanup task failed: {str(e)}"
        logging.error(error_msg)
        raise Exception(error_msg)

@celery.task(name='app.tasks.generate_analytics_report')
def generate_analytics_report(days=30):
    """Generate analytics report for the specified period"""
    try:
        from .database import get_analytics_data
        
        report_data = get_analytics_data(days)
        
        # Add additional computed metrics
        summary = report_data['summary']
        
        # Calculate trends (simplified)
        report_data['insights'] = {
            'performance_grade': 'A' if summary['success_rate'] > 90 else 'B' if summary['success_rate'] > 80 else 'C',
            'avg_processing_speed': 'Fast' if summary['average_processing_time'] < 2 else 'Medium' if summary['average_processing_time'] < 5 else 'Slow',
            'confidence_level': 'High' if summary['average_confidence'] > 0.8 else 'Medium' if summary['average_confidence'] > 0.6 else 'Low',
            'most_processed_type': max(report_data['document_types'], key=lambda x: x['count'])['type'] if report_data['document_types'] else 'None'
        }
        
        report_data['report_generated'] = datetime.now(timezone.utc).isoformat()
        
        logging.info(f"Analytics report generated for {days} days")
        return report_data
        
    except Exception as e:
        error_msg = f"Analytics report generation failed: {str(e)}"
        logging.error(error_msg)
        raise Exception(error_msg)

# Periodic tasks setup
from celery.schedules import crontab

# Configure periodic tasks
celery.conf.beat_schedule = {
    'cleanup-old-files': {
        'task': 'app.tasks.cleanup_old_files',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    'generate-daily-analytics': {
        'task': 'app.tasks.generate_analytics_report',
        'schedule': crontab(hour=1, minute=0),  # Daily at 1 AM
        'args': (1,)  # Generate daily report
    },
}

celery.conf.timezone = 'UTC'
