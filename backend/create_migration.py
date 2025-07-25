#!/usr/bin/env python
"""
Create database migration for async processing support
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app import create_app
from app.database import db
from flask_migrate import init, migrate, upgrade

# Create Flask app
app, _ = create_app()

with app.app_context():
    # Initialize migrations if not already done
    migrations_dir = Path('migrations')
    if not migrations_dir.exists():
        init()
        print("Initialized migrations directory")
    
    # Create migration
    migrate(message='Add async processing support with Celery task IDs and batch jobs')
    print("Created migration for async processing support")
    
    # Apply migration
    upgrade()
    print("Applied migration successfully")
    
    print("\nDatabase schema updated with:")
    print("- Added task_id to scan_history table")
    print("- Added batch_job_id to scan_history table") 
    print("- Added status fields for async processing")
    print("- Created batch_processing_jobs table")
    print("- Added validation fields to scan_history")