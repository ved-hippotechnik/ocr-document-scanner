"""
Batch processing module for OCR Document Scanner
Provides scalable batch processing capabilities with queue management
"""

from .processor import batch_manager, BatchJobManager, BatchJob, BatchStatus
from .routes import batch_bp

__all__ = ['batch_manager', 'BatchJobManager', 'BatchJob', 'BatchStatus', 'batch_bp']