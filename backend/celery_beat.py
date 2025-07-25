#!/usr/bin/env python
"""
Celery beat scheduler entry point for periodic tasks

Run with:
    celery -A celery_beat.celery beat --loglevel=info
"""

import os
import sys
from pathlib import Path
from celery.schedules import crontab

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app import create_app
from app.celery_app import celery_app

# Create Flask app to ensure proper context
app, _ = create_app()

# Get the celery instance
celery = app.celery

# Configure periodic tasks
celery.conf.beat_schedule = {
    'daily-cleanup': {
        'task': 'app.tasks.periodic_cleanup',
        'schedule': crontab(hour=2, minute=0),  # Run at 2 AM daily
        'options': {'queue': 'maintenance'}
    },
    'hourly-analytics': {
        'task': 'app.tasks.periodic_analytics',
        'schedule': crontab(minute=0),  # Run every hour
        'options': {'queue': 'analytics'}
    },
    'health-check': {
        'task': 'app.tasks.monitor_task_health',
        'schedule': 60.0,  # Every minute
        'options': {'queue': 'default'}
    },
}

if __name__ == '__main__':
    celery.start()