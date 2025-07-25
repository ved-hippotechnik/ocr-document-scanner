"""
Batch Processing System for OCR Document Scanner
Handles large-scale document processing with queue management and progress tracking
"""

import uuid
import time
import logging
from typing import List, Dict, Optional, Callable
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import json
import asyncio
from enum import Enum

from ..database import db
from ..models.analytics import BatchProcessingJob
# from ..websocket import notify_processing_progress, notify_user

# Temporary stub functions for websocket notifications
def notify_processing_progress(*args, **kwargs):
    pass

def notify_user(*args, **kwargs):
    pass
from ..ai.document_classifier import DocumentClassifier
from ..processors import processor_registry
from ..cache import cache_manager

logger = logging.getLogger(__name__)

class BatchStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class BatchJobManager:
    """
    Manages batch processing jobs with queue management and progress tracking
    """
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.active_jobs: Dict[str, 'BatchJob'] = {}
        self.job_lock = Lock()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.ai_classifier = DocumentClassifier()
        
        # Performance metrics
        self.total_jobs = 0
        self.successful_jobs = 0
        self.failed_jobs = 0
        
        logger.info(f"Batch Job Manager initialized with {max_workers} workers")
    
    def create_job(self, user_id: int, documents: List[Dict], 
                   job_config: Optional[Dict] = None) -> str:
        """
        Create a new batch processing job
        
        Args:
            user_id: ID of the user creating the job
            documents: List of document data with 'id' and 'image' fields
            job_config: Optional configuration for the job
            
        Returns:
            Job ID for tracking
        """
        job_id = str(uuid.uuid4())
        
        # Create database record
        try:
            job_record = BatchProcessingJob(
                job_id=job_id,
                user_id=user_id,
                total_documents=len(documents),
                status=BatchStatus.PENDING.value
            )
            db.session.add(job_record)
            db.session.commit()
            
            # Create job object
            job = BatchJob(
                job_id=job_id,
                user_id=user_id,
                documents=documents,
                config=job_config or {},
                db_record=job_record
            )
            
            with self.job_lock:
                self.active_jobs[job_id] = job
                self.total_jobs += 1
            
            logger.info(f"Created batch job {job_id} with {len(documents)} documents")
            
            return job_id
            
        except Exception as e:
            logger.error(f"Error creating batch job: {e}")
            if 'job_record' in locals():
                db.session.rollback()
            raise
    
    def submit_job(self, job_id: str) -> bool:
        """
        Submit a job for processing
        
        Args:
            job_id: ID of the job to submit
            
        Returns:
            True if job was submitted successfully
        """
        with self.job_lock:
            if job_id not in self.active_jobs:
                logger.error(f"Job {job_id} not found")
                return False
            
            job = self.active_jobs[job_id]
            
            if job.status != BatchStatus.PENDING:
                logger.error(f"Job {job_id} is not in pending state")
                return False
            
            # Submit to executor
            future = self.executor.submit(self._process_job, job)
            job.future = future
            
            logger.info(f"Submitted job {job_id} for processing")
            return True
    
    def _process_job(self, job: 'BatchJob'):
        """
        Process a batch job
        
        Args:
            job: BatchJob instance to process
        """
        try:
            job.start_processing()
            
            # Update database status
            job.db_record.status = BatchStatus.PROCESSING.value
            db.session.commit()
            
            # Process documents
            for i, document in enumerate(job.documents):
                try:
                    # Check if job was cancelled
                    if job.status == BatchStatus.CANCELLED:
                        logger.info(f"Job {job.job_id} was cancelled")
                        break
                    
                    # Process single document
                    result = self._process_single_document(document, job)
                    
                    # Update job progress
                    job.add_result(document['id'], result)
                    progress = int(((i + 1) / len(job.documents)) * 100)
                    job.update_progress(progress)
                    
                    # Notify progress
                    notify_processing_progress(
                        job.job_id,
                        progress,
                        f"Processing document {i + 1}/{len(job.documents)}"
                    )
                    
                    # Update database
                    job.db_record.processed_documents = i + 1
                    if result.get('success', False):
                        job.db_record.successful_extractions += 1
                    db.session.commit()
                    
                except Exception as e:
                    logger.error(f"Error processing document {document.get('id', 'unknown')}: {e}")
                    job.add_result(document['id'], {
                        'success': False,
                        'error': str(e),
                        'document_id': document['id']
                    })
            
            # Complete job
            job.complete()
            
            # Update database
            job.db_record.status = BatchStatus.COMPLETED.value
            job.db_record.completed_at = datetime.utcnow()
            db.session.commit()
            
            # Send completion notification
            notify_user(job.user_id, {
                'type': 'batch_complete',
                'job_id': job.job_id,
                'total_processed': len(job.documents),
                'successful': job.db_record.successful_extractions,
                'failed': job.db_record.processed_documents - job.db_record.successful_extractions
            })
            
            with self.job_lock:
                self.successful_jobs += 1
            
            logger.info(f"Batch job {job.job_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Error processing batch job {job.job_id}: {e}")
            
            # Mark job as failed
            job.fail(str(e))
            
            # Update database
            job.db_record.status = BatchStatus.FAILED.value
            job.db_record.completed_at = datetime.utcnow()
            db.session.commit()
            
            # Send failure notification
            notify_user(job.user_id, {
                'type': 'batch_failed',
                'job_id': job.job_id,
                'error': str(e)
            })
            
            with self.job_lock:
                self.failed_jobs += 1
    
    def _process_single_document(self, document: Dict, job: 'BatchJob') -> Dict:
        """
        Process a single document
        
        Args:
            document: Document data with 'id' and 'image' fields
            job: Parent batch job
            
        Returns:
            Processing result dictionary
        """
        try:
            import base64
            import hashlib
            
            # Decode image
            image_data = base64.b64decode(document['image'])
            image_hash = hashlib.sha256(image_data).hexdigest()
            
            # Check cache first
            cache_key = f"batch_process:{image_hash}"
            cached_result = cache_manager.get(cache_key)
            
            if cached_result:
                logger.info(f"Using cached result for document {document['id']}")
                return {**cached_result, 'cached': True}
            
            # AI Classification
            classification_result = self.ai_classifier.classify_document(image_data)
            
            if 'error' in classification_result:
                return {
                    'success': False,
                    'error': 'Classification failed',
                    'document_id': document['id'],
                    'details': classification_result
                }
            
            # Select processor
            document_type = classification_result['document_type']
            processor = processor_registry.get_processor(document_type)
            
            if processor is None:
                processor = processor_registry.get_best_processor(image_data)
            
            # OCR Processing
            ocr_result = processor.process(image_data)
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(ocr_result, classification_result)
            
            # Prepare result
            result = {
                'success': True,
                'document_id': document['id'],
                'image_hash': image_hash,
                'classification': classification_result,
                'ocr_result': ocr_result,
                'quality_score': quality_score,
                'processor_used': processor.__class__.__name__,
                'timestamp': datetime.now().isoformat(),
                'cached': False
            }
            
            # Cache result
            cache_manager.set(cache_key, result, ttl=3600)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing document {document.get('id', 'unknown')}: {e}")
            return {
                'success': False,
                'error': str(e),
                'document_id': document['id']
            }
    
    def _calculate_quality_score(self, ocr_result: Dict, classification_result: Dict) -> float:
        """Calculate quality score for processing result"""
        try:
            quality_factors = []
            
            # Classification confidence
            classification_confidence = classification_result.get('confidence', 0)
            quality_factors.append(classification_confidence)
            
            # OCR confidence
            ocr_confidence = ocr_result.get('confidence', 0)
            quality_factors.append(ocr_confidence / 100 if ocr_confidence > 1 else ocr_confidence)
            
            # Data completeness
            extracted_data = ocr_result.get('extracted_data', {})
            if extracted_data:
                completeness = len([v for v in extracted_data.values() if v and str(v).strip()]) / len(extracted_data)
                quality_factors.append(completeness)
            
            return sum(quality_factors) / len(quality_factors) if quality_factors else 0.0
            
        except Exception:
            return 0.0
    
    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """
        Get status of a batch job
        
        Args:
            job_id: ID of the job
            
        Returns:
            Job status dictionary or None if not found
        """
        with self.job_lock:
            if job_id not in self.active_jobs:
                # Check database for historical jobs
                try:
                    job_record = BatchProcessingJob.query.filter_by(job_id=job_id).first()
                    if job_record:
                        return job_record.to_dict()
                except Exception as e:
                    logger.error(f"Error querying job {job_id}: {e}")
                return None
            
            job = self.active_jobs[job_id]
            return {
                'job_id': job.job_id,
                'status': job.status.value,
                'progress': job.progress,
                'total_documents': len(job.documents),
                'processed_documents': len(job.results),
                'successful_extractions': len([r for r in job.results.values() if r.get('success', False)]),
                'created_at': job.created_at.isoformat(),
                'started_at': job.started_at.isoformat() if job.started_at else None,
                'completed_at': job.completed_at.isoformat() if job.completed_at else None,
                'error': job.error
            }
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a batch job
        
        Args:
            job_id: ID of the job to cancel
            
        Returns:
            True if job was cancelled successfully
        """
        with self.job_lock:
            if job_id not in self.active_jobs:
                return False
            
            job = self.active_jobs[job_id]
            
            if job.status in [BatchStatus.COMPLETED, BatchStatus.FAILED]:
                logger.warning(f"Cannot cancel job {job_id} - already finished")
                return False
            
            job.cancel()
            
            # Update database
            job.db_record.status = BatchStatus.CANCELLED.value
            job.db_record.completed_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Cancelled batch job {job_id}")
            return True
    
    def get_job_results(self, job_id: str) -> Optional[Dict]:
        """
        Get results of a completed batch job
        
        Args:
            job_id: ID of the job
            
        Returns:
            Job results dictionary or None if not found
        """
        with self.job_lock:
            if job_id not in self.active_jobs:
                return None
            
            job = self.active_jobs[job_id]
            
            if job.status != BatchStatus.COMPLETED:
                return None
            
            return {
                'job_id': job.job_id,
                'status': job.status.value,
                'total_documents': len(job.documents),
                'processed_documents': len(job.results),
                'successful_extractions': len([r for r in job.results.values() if r.get('success', False)]),
                'results': list(job.results.values()),
                'processing_time': (job.completed_at - job.started_at).total_seconds() if job.completed_at and job.started_at else None
            }
    
    def cleanup_completed_jobs(self, max_age_hours: int = 24):
        """
        Clean up completed jobs older than specified age
        
        Args:
            max_age_hours: Maximum age in hours before cleanup
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        with self.job_lock:
            jobs_to_remove = []
            
            for job_id, job in self.active_jobs.items():
                if (job.status in [BatchStatus.COMPLETED, BatchStatus.FAILED, BatchStatus.CANCELLED] and
                    job.completed_at and job.completed_at < cutoff_time):
                    jobs_to_remove.append(job_id)
            
            for job_id in jobs_to_remove:
                del self.active_jobs[job_id]
                logger.info(f"Cleaned up old job {job_id}")
    
    def get_manager_stats(self) -> Dict:
        """Get batch manager performance statistics"""
        with self.job_lock:
            active_count = len([j for j in self.active_jobs.values() if j.status == BatchStatus.PROCESSING])
            pending_count = len([j for j in self.active_jobs.values() if j.status == BatchStatus.PENDING])
            
            return {
                'total_jobs': self.total_jobs,
                'successful_jobs': self.successful_jobs,
                'failed_jobs': self.failed_jobs,
                'active_jobs': active_count,
                'pending_jobs': pending_count,
                'success_rate': self.successful_jobs / self.total_jobs if self.total_jobs > 0 else 0.0,
                'max_workers': self.max_workers
            }

class BatchJob:
    """
    Represents a single batch processing job
    """
    
    def __init__(self, job_id: str, user_id: int, documents: List[Dict], 
                 config: Dict, db_record: BatchProcessingJob):
        self.job_id = job_id
        self.user_id = user_id
        self.documents = documents
        self.config = config
        self.db_record = db_record
        
        self.status = BatchStatus.PENDING
        self.progress = 0
        self.results: Dict[str, Dict] = {}
        self.error = None
        self.future = None
        
        self.created_at = datetime.utcnow()
        self.started_at = None
        self.completed_at = None
    
    def start_processing(self):
        """Mark job as started"""
        self.status = BatchStatus.PROCESSING
        self.started_at = datetime.utcnow()
        logger.info(f"Started processing job {self.job_id}")
    
    def update_progress(self, progress: int):
        """Update job progress"""
        self.progress = progress
    
    def add_result(self, document_id: str, result: Dict):
        """Add processing result for a document"""
        self.results[document_id] = result
    
    def complete(self):
        """Mark job as completed"""
        self.status = BatchStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.progress = 100
        logger.info(f"Completed job {self.job_id}")
    
    def fail(self, error: str):
        """Mark job as failed"""
        self.status = BatchStatus.FAILED
        self.error = error
        self.completed_at = datetime.utcnow()
        logger.error(f"Failed job {self.job_id}: {error}")
    
    def cancel(self):
        """Cancel the job"""
        self.status = BatchStatus.CANCELLED
        self.completed_at = datetime.utcnow()
        logger.info(f"Cancelled job {self.job_id}")

# Global batch manager instance
batch_manager = BatchJobManager()