"""
Celery application configuration for async task processing
"""

import os
from celery import Celery
from flask import Flask
from typing import Any

def make_celery(app: Flask) -> Celery:
    """Create and configure Celery instance with Flask app context"""
    
    # Get broker URL from environment or use default
    broker_url = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    result_backend = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    
    celery = Celery(
        app.import_name,
        broker=broker_url,
        backend=result_backend,
        include=['app.tasks']  # Include task modules
    )
    
    # Update configuration
    celery.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        result_expires=3600,  # Results expire after 1 hour
        task_track_started=True,
        task_time_limit=300,  # 5 minutes hard limit
        task_soft_time_limit=240,  # 4 minutes soft limit
        task_acks_late=True,
        worker_prefetch_multiplier=1,
        worker_max_tasks_per_child=100,  # Restart worker after 100 tasks
    )
    
    # Configure task routes
    celery.conf.task_routes = {
        'app.tasks.process_document_async': {'queue': 'ocr_processing'},
        'app.tasks.batch_process_async': {'queue': 'batch_processing'},
        'app.tasks.generate_analytics_async': {'queue': 'analytics'},
        'app.tasks.cleanup_old_files_async': {'queue': 'maintenance'},
    }
    
    # Configure queues
    celery.conf.task_default_queue = 'default'
    celery.conf.task_queues = {
        'default': {
            'exchange': 'default',
            'exchange_type': 'direct',
            'routing_key': 'default',
        },
        'ocr_processing': {
            'exchange': 'ocr',
            'exchange_type': 'direct',
            'routing_key': 'ocr.process',
        },
        'batch_processing': {
            'exchange': 'batch',
            'exchange_type': 'direct',
            'routing_key': 'batch.process',
        },
        'analytics': {
            'exchange': 'analytics',
            'exchange_type': 'direct',
            'routing_key': 'analytics.generate',
        },
        'maintenance': {
            'exchange': 'maintenance',
            'exchange_type': 'direct',
            'routing_key': 'maintenance.cleanup',
        },
    }
    
    class ContextTask(celery.Task):
        """Custom task class to ensure Flask app context"""
        abstract = True
        
        def __call__(self, *args: Any, **kwargs: Any) -> Any:
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery

# Global celery instance (will be initialized in app factory)
celery_app = None