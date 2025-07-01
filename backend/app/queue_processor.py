"""
Advanced queue-based batch processing system for OCR documents
Implements Redis-based task queue with worker processes
"""

import redis
import json
import uuid
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from .processors.registry import ProcessorRegistry
from .quality import QualityAssessment
from .classification import DocumentClassifier
import base64
from PIL import Image
import io

logger = logging.getLogger(__name__)

class TaskQueue:
    """Redis-based task queue for document processing"""
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or os.environ.get('REDIS_URL', 'redis://localhost:6379')
        try:
            self.redis_client = redis.from_url(self.redis_url)
            self.redis_client.ping()
        except (redis.ConnectionError, redis.TimeoutError):
            logger.warning("Redis not available, using in-memory queue")
            self.redis_client = None
            self._memory_queue = {}
            self._memory_results = {}
    
    def enqueue_task(self, task_data: Dict[str, Any]) -> str:
        """Add a task to the processing queue"""
        task_id = str(uuid.uuid4())
        task = {
            'id': task_id,
            'data': task_data,
            'status': 'queued',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        if self.redis_client:
            self.redis_client.lpush('document_queue', json.dumps(task))
            self.redis_client.setex(f'task:{task_id}', 3600, json.dumps(task))
        else:
            self._memory_queue[task_id] = task
        
        return task_id
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status and results"""
        if self.redis_client:
            task_data = self.redis_client.get(f'task:{task_id}')
            if task_data:
                return json.loads(task_data)
        else:
            return self._memory_queue.get(task_id) or self._memory_results.get(task_id)
        
        return None
    
    def update_task_status(self, task_id: str, status: str, result: Dict[str, Any] = None):
        """Update task status and results"""
        task = self.get_task_status(task_id)
        if not task:
            return
        
        task['status'] = status
        task['updated_at'] = datetime.utcnow().isoformat()
        
        if result:
            task['result'] = result
        
        if self.redis_client:
            self.redis_client.setex(f'task:{task_id}', 3600, json.dumps(task))
        else:
            if status in ['completed', 'failed']:
                self._memory_results[task_id] = task
                self._memory_queue.pop(task_id, None)
            else:
                self._memory_queue[task_id] = task
    
    def get_next_task(self) -> Optional[Dict[str, Any]]:
        """Get next task from queue"""
        if self.redis_client:
            task_data = self.redis_client.brpop('document_queue', timeout=1)
            if task_data:
                return json.loads(task_data[1])
        else:
            if self._memory_queue:
                task_id, task = next(iter(self._memory_queue.items()))
                return task
        
        return None

class BatchProcessor:
    """Batch document processing with quality control and validation"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.queue = TaskQueue()
        self.processor_registry = ProcessorRegistry()
        self.quality_assessor = QualityAssessment()
        self.classifier = DocumentClassifier()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self._running = False
    
    def submit_batch(self, documents: List[Dict[str, Any]], 
                    options: Dict[str, Any] = None) -> str:
        """Submit a batch of documents for processing"""
        batch_id = str(uuid.uuid4())
        task_data = {
            'type': 'batch',
            'batch_id': batch_id,
            'documents': documents,
            'options': options or {},
            'total_documents': len(documents)
        }
        
        task_id = self.queue.enqueue_task(task_data)
        logger.info(f"Submitted batch {batch_id} with {len(documents)} documents (task {task_id})")
        
        return task_id
    
    def submit_single(self, image_data: str, document_type: str = None,
                     options: Dict[str, Any] = None) -> str:
        """Submit a single document for processing"""
        task_data = {
            'type': 'single',
            'image_data': image_data,
            'document_type': document_type,
            'options': options or {}
        }
        
        task_id = self.queue.enqueue_task(task_data)
        logger.info(f"Submitted single document for processing (task {task_id})")
        
        return task_id
    
    def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single task"""
        task_id = task['id']
        task_data = task['data']
        
        try:
            self.queue.update_task_status(task_id, 'processing')
            
            if task_data['type'] == 'batch':
                result = self._process_batch(task_data)
            elif task_data['type'] == 'single':
                result = self._process_single_document(task_data)
            else:
                raise ValueError(f"Unknown task type: {task_data['type']}")
            
            self.queue.update_task_status(task_id, 'completed', result)
            return result
        
        except Exception as e:
            error_result = {
                'error': str(e),
                'error_type': type(e).__name__
            }
            self.queue.update_task_status(task_id, 'failed', error_result)
            logger.error(f"Task {task_id} failed: {e}")
            raise
    
    def _process_batch(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a batch of documents"""
        documents = task_data['documents']
        options = task_data['options']
        batch_id = task_data['batch_id']
        
        results = []
        successful = 0
        failed = 0
        
        # Process documents concurrently
        with ThreadPoolExecutor(max_workers=min(self.max_workers, len(documents))) as executor:
            future_to_doc = {
                executor.submit(self._process_document, doc, options): i 
                for i, doc in enumerate(documents)
            }
            
            for future in as_completed(future_to_doc):
                doc_index = future_to_doc[future]
                try:
                    result = future.result()
                    result['document_index'] = doc_index
                    results.append(result)
                    successful += 1
                except Exception as e:
                    error_result = {
                        'document_index': doc_index,
                        'error': str(e),
                        'error_type': type(e).__name__
                    }
                    results.append(error_result)
                    failed += 1
        
        # Sort results by document index
        results.sort(key=lambda x: x['document_index'])
        
        return {
            'batch_id': batch_id,
            'total_documents': len(documents),
            'successful': successful,
            'failed': failed,
            'results': results,
            'processing_time': time.time()
        }
    
    def _process_single_document(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single document"""
        document = {
            'image_data': task_data['image_data'],
            'document_type': task_data.get('document_type')
        }
        
        return self._process_document(document, task_data['options'])
    
    def _process_document(self, document: Dict[str, Any], 
                         options: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single document with quality assessment and classification"""
        start_time = time.time()
        
        # Decode image
        image_data = base64.b64decode(document['image_data'])
        image = Image.open(io.BytesIO(image_data))
        
        # Quality assessment
        quality_result = self.quality_assessor.assess_quality(image)
        
        # Skip processing if quality is too low (configurable threshold)
        min_quality = options.get('min_quality_score', 0.3)
        if quality_result['overall_score'] < min_quality:
            return {
                'status': 'skipped',
                'reason': 'low_quality',
                'quality_assessment': quality_result,
                'processing_time': time.time() - start_time
            }
        
        # Document classification if type not specified
        document_type = document.get('document_type')
        if not document_type:
            classification_result = self.classifier.classify_document(image)
            document_type = classification_result['predicted_type']
        else:
            classification_result = None
        
        # Get processor
        processor = self.processor_registry.get_processor(document_type)
        if not processor:
            return {
                'status': 'failed',
                'error': f'No processor available for document type: {document_type}',
                'quality_assessment': quality_result,
                'classification': classification_result,
                'processing_time': time.time() - start_time
            }
        
        # Process document
        try:
            extraction_result = processor.process(image)
            
            return {
                'status': 'success',
                'document_type': document_type,
                'extraction_result': extraction_result,
                'quality_assessment': quality_result,
                'classification': classification_result,
                'processing_time': time.time() - start_time,
                'confidence': extraction_result.get('confidence', 0.0)
            }
        
        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e),
                'error_type': type(e).__name__,
                'document_type': document_type,
                'quality_assessment': quality_result,
                'classification': classification_result,
                'processing_time': time.time() - start_time
            }
    
    def start_worker(self):
        """Start background worker process"""
        self._running = True
        logger.info("Starting batch processor worker")
        
        while self._running:
            try:
                task = self.queue.get_next_task()
                if task:
                    self.process_task(task)
                else:
                    time.sleep(1)  # No tasks available, wait
            
            except KeyboardInterrupt:
                logger.info("Worker interrupted")
                break
            except Exception as e:
                logger.error(f"Worker error: {e}")
                time.sleep(5)  # Wait before retrying
        
        logger.info("Batch processor worker stopped")
    
    def stop_worker(self):
        """Stop background worker process"""
        self._running = False
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get queue status and statistics"""
        if self.redis_client:
            queue_length = self.redis_client.llen('document_queue')
        else:
            queue_length = len(self._memory_queue)
        
        return {
            'queue_length': queue_length,
            'max_workers': self.max_workers,
            'worker_running': self._running
        }

# Global batch processor instance
batch_processor = BatchProcessor()
