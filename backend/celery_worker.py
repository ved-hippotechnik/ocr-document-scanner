#!/usr/bin/env python
"""
Celery worker entry point

Run with:
    celery -A celery_worker.celery worker --loglevel=info
    
Or for specific queues:
    celery -A celery_worker.celery worker -Q ocr_processing,default --loglevel=info
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app import create_app
from app.celery_app import celery_app

# Create Flask app to ensure proper context
app, _ = create_app()

# Get the celery instance
celery = app.celery

if __name__ == '__main__':
    celery.start()