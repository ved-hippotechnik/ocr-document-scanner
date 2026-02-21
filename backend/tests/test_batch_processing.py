"""
Tests for batch processing system
"""

import unittest
import json
import base64
import time
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import sys
import os

# Add the parent directory to sys.path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.batch.processor import BatchJobManager, BatchJob, BatchStatus
from app.database import BatchProcessingJob

class TestBatchJobManager(unittest.TestCase):
    """Test cases for BatchJobManager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.manager = BatchJobManager(max_workers=2)
        self.test_documents = [
            {
                'id': 'doc1',
                'image': base64.b64encode(b'test_image_data_1').decode('utf-8')
            },
            {
                'id': 'doc2',
                'image': base64.b64encode(b'test_image_data_2').decode('utf-8')
            }
        ]
    
    def tearDown(self):
        """Clean up after tests"""
        # Clean up any active jobs
        self.manager.active_jobs.clear()
    
    @patch('app.batch.processor.db')
    def test_create_job(self, mock_db):
        """Test job creation"""
        # Mock database operations
        mock_db.session.add = MagicMock()
        mock_db.session.commit = MagicMock()
        
        # Create job
        job_id = self.manager.create_job(
            user_id=1,
            documents=self.test_documents
        )
        
        # Verify job was created
        self.assertIsNotNone(job_id)
        self.assertIn(job_id, self.manager.active_jobs)
        
        job = self.manager.active_jobs[job_id]
        self.assertEqual(job.user_id, 1)
        self.assertEqual(len(job.documents), 2)
        self.assertEqual(job.status, BatchStatus.PENDING)
    
    @patch('app.batch.processor.db')
    def test_submit_job(self, mock_db):
        """Test job submission"""
        # Mock database operations
        mock_db.session.add = MagicMock()
        mock_db.session.commit = MagicMock()
        
        # Create and submit job
        job_id = self.manager.create_job(
            user_id=1,
            documents=self.test_documents
        )
        
        success = self.manager.submit_job(job_id)
        
        # Verify job was submitted
        self.assertTrue(success)
        
        job = self.manager.active_jobs[job_id]
        self.assertIsNotNone(job.future)
    
    def test_submit_nonexistent_job(self):
        """Test submitting a job that doesn't exist"""
        success = self.manager.submit_job('nonexistent_job')
        self.assertFalse(success)
    
    @patch('app.batch.processor.db')
    def test_get_job_status(self, mock_db):
        """Test getting job status"""
        # Mock database operations
        mock_db.session.add = MagicMock()
        mock_db.session.commit = MagicMock()
        
        # Create job
        job_id = self.manager.create_job(
            user_id=1,
            documents=self.test_documents
        )
        
        # Get status
        status = self.manager.get_job_status(job_id)
        
        # Verify status
        self.assertIsNotNone(status)
        self.assertEqual(status['job_id'], job_id)
        self.assertEqual(status['status'], BatchStatus.PENDING.value)
        self.assertEqual(status['total_documents'], 2)
    
    def test_get_nonexistent_job_status(self):
        """Test getting status of non-existent job"""
        status = self.manager.get_job_status('nonexistent_job')
        self.assertIsNone(status)
    
    @patch('app.batch.processor.db')
    def test_cancel_job(self, mock_db):
        """Test job cancellation"""
        # Mock database operations
        mock_db.session.add = MagicMock()
        mock_db.session.commit = MagicMock()
        
        # Create job
        job_id = self.manager.create_job(
            user_id=1,
            documents=self.test_documents
        )
        
        # Cancel job
        success = self.manager.cancel_job(job_id)
        
        # Verify cancellation
        self.assertTrue(success)
        
        job = self.manager.active_jobs[job_id]
        self.assertEqual(job.status, BatchStatus.CANCELLED)
    
    def test_cancel_nonexistent_job(self):
        """Test cancelling a job that doesn't exist"""
        success = self.manager.cancel_job('nonexistent_job')
        self.assertFalse(success)
    
    @patch('app.batch.processor.db')
    def test_cleanup_completed_jobs(self, mock_db):
        """Test cleanup of old completed jobs"""
        # Mock database operations
        mock_db.session.add = MagicMock()
        mock_db.session.commit = MagicMock()
        
        # Create and complete an old job
        job_id = self.manager.create_job(
            user_id=1,
            documents=self.test_documents
        )
        
        job = self.manager.active_jobs[job_id]
        job.status = BatchStatus.COMPLETED
        job.completed_at = datetime.utcnow() - timedelta(hours=25)  # 25 hours ago
        
        # Clean up jobs older than 24 hours
        self.manager.cleanup_completed_jobs(max_age_hours=24)
        
        # Verify job was cleaned up
        self.assertNotIn(job_id, self.manager.active_jobs)
    
    def test_get_manager_stats(self):
        """Test getting manager statistics"""
        stats = self.manager.get_manager_stats()
        
        # Verify stats structure
        self.assertIsInstance(stats, dict)
        self.assertIn('total_jobs', stats)
        self.assertIn('successful_jobs', stats)
        self.assertIn('failed_jobs', stats)
        self.assertIn('active_jobs', stats)
        self.assertIn('pending_jobs', stats)
        self.assertIn('success_rate', stats)
        self.assertIn('max_workers', stats)
    
    @patch('app.batch.processor.DocumentClassifier')
    @patch('app.batch.processor.processor_registry')
    @patch('app.batch.processor.cache_manager')
    def test_process_single_document(self, mock_cache, mock_registry, mock_classifier):
        """Test processing a single document"""
        # Mock dependencies
        mock_classifier.return_value.classify_document.return_value = {
            'document_type': 'aadhaar',
            'confidence': 0.95
        }
        
        mock_processor = MagicMock()
        mock_processor.process.return_value = {
            'extracted_data': {'name': 'Test User'},
            'confidence': 85
        }
        mock_registry.get_processor.return_value = mock_processor
        
        mock_cache.get.return_value = None
        mock_cache.set = MagicMock()
        
        # Create job
        job = BatchJob(
            job_id='test_job',
            user_id=1,
            documents=self.test_documents,
            config={},
            db_record=MagicMock()
        )
        
        # Process single document
        result = self.manager._process_single_document(self.test_documents[0], job)
        
        # Verify result
        self.assertIsInstance(result, dict)
        self.assertIn('success', result)
        self.assertIn('document_id', result)
        self.assertIn('classification', result)
        self.assertIn('ocr_result', result)
    
    def test_calculate_quality_score(self):
        """Test quality score calculation"""
        ocr_result = {
            'extracted_data': {'name': 'Test User', 'id': '123456'},
            'confidence': 85
        }
        
        classification_result = {
            'confidence': 0.95
        }
        
        quality_score = self.manager._calculate_quality_score(ocr_result, classification_result)
        
        # Verify quality score
        self.assertIsInstance(quality_score, float)
        self.assertGreaterEqual(quality_score, 0.0)
        self.assertLessEqual(quality_score, 1.0)

class TestBatchJob(unittest.TestCase):
    """Test cases for BatchJob"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_db_record = MagicMock()
        self.job = BatchJob(
            job_id='test_job',
            user_id=1,
            documents=[{'id': 'doc1', 'image': 'test_image'}],
            config={},
            db_record=self.mock_db_record
        )
    
    def test_job_initialization(self):
        """Test job initialization"""
        self.assertEqual(self.job.job_id, 'test_job')
        self.assertEqual(self.job.user_id, 1)
        self.assertEqual(len(self.job.documents), 1)
        self.assertEqual(self.job.status, BatchStatus.PENDING)
        self.assertEqual(self.job.progress, 0)
        self.assertEqual(len(self.job.results), 0)
    
    def test_start_processing(self):
        """Test starting job processing"""
        self.job.start_processing()
        
        self.assertEqual(self.job.status, BatchStatus.PROCESSING)
        self.assertIsNotNone(self.job.started_at)
    
    def test_update_progress(self):
        """Test updating job progress"""
        self.job.update_progress(50)
        self.assertEqual(self.job.progress, 50)
    
    def test_add_result(self):
        """Test adding processing result"""
        result = {'success': True, 'data': 'test_result'}
        self.job.add_result('doc1', result)
        
        self.assertIn('doc1', self.job.results)
        self.assertEqual(self.job.results['doc1'], result)
    
    def test_complete_job(self):
        """Test completing job"""
        self.job.complete()
        
        self.assertEqual(self.job.status, BatchStatus.COMPLETED)
        self.assertEqual(self.job.progress, 100)
        self.assertIsNotNone(self.job.completed_at)
    
    def test_fail_job(self):
        """Test failing job"""
        error_msg = "Test error message"
        self.job.fail(error_msg)
        
        self.assertEqual(self.job.status, BatchStatus.FAILED)
        self.assertEqual(self.job.error, error_msg)
        self.assertIsNotNone(self.job.completed_at)
    
    def test_cancel_job(self):
        """Test cancelling job"""
        self.job.cancel()
        
        self.assertEqual(self.job.status, BatchStatus.CANCELLED)
        self.assertIsNotNone(self.job.completed_at)

class TestBatchRoutes(unittest.TestCase):
    """Test cases for batch processing routes"""
    
    def setUp(self):
        """Set up test fixtures"""
        # This would require setting up a test Flask app
        pass
    
    def test_route_setup(self):
        """Test that routes are properly set up"""
        from app.batch.routes import batch_bp
        
        self.assertIsNotNone(batch_bp)
        self.assertEqual(batch_bp.name, 'batch')
        self.assertEqual(batch_bp.url_prefix, '/api/batch')
    
    def test_batch_status_enum(self):
        """Test BatchStatus enum values"""
        self.assertEqual(BatchStatus.PENDING.value, "pending")
        self.assertEqual(BatchStatus.PROCESSING.value, "processing")
        self.assertEqual(BatchStatus.COMPLETED.value, "completed")
        self.assertEqual(BatchStatus.FAILED.value, "failed")
        self.assertEqual(BatchStatus.CANCELLED.value, "cancelled")

class TestBatchIntegration(unittest.TestCase):
    """Integration tests for batch processing"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.manager = BatchJobManager(max_workers=1)
    
    def tearDown(self):
        """Clean up after integration tests"""
        self.manager.active_jobs.clear()
    
    @patch('app.batch.processor.db')
    @patch('app.batch.processor.DocumentClassifier')
    @patch('app.batch.processor.processor_registry')
    @patch('app.batch.processor.cache_manager')
    def test_full_batch_workflow(self, mock_cache, mock_registry, mock_classifier, mock_db):
        """Test complete batch processing workflow"""
        # Mock database operations
        mock_db.session.add = MagicMock()
        mock_db.session.commit = MagicMock()
        
        # Mock AI classifier
        mock_classifier.return_value.classify_document.return_value = {
            'document_type': 'aadhaar',
            'confidence': 0.95
        }
        
        # Mock processor
        mock_processor = MagicMock()
        mock_processor.process.return_value = {
            'extracted_data': {'name': 'Test User'},
            'confidence': 85
        }
        mock_registry.get_processor.return_value = mock_processor
        
        # Mock cache
        mock_cache.get.return_value = None
        mock_cache.set = MagicMock()
        
        # Create and submit job
        job_id = self.manager.create_job(
            user_id=1,
            documents=[{
                'id': 'doc1',
                'image': base64.b64encode(b'test_image_data').decode('utf-8')
            }]
        )
        
        success = self.manager.submit_job(job_id)
        self.assertTrue(success)
        
        # Wait for processing to complete
        job = self.manager.active_jobs[job_id]
        if job.future:
            job.future.result(timeout=10)  # Wait up to 10 seconds
        
        # Verify job completion
        status = self.manager.get_job_status(job_id)
        self.assertEqual(status['status'], BatchStatus.COMPLETED.value)
        self.assertEqual(status['processed_documents'], 1)
        
        # Verify results
        results = self.manager.get_job_results(job_id)
        self.assertIsNotNone(results)
        self.assertEqual(len(results['results']), 1)

if __name__ == '__main__':
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(unittest.makeSuite(TestBatchJobManager))
    suite.addTest(unittest.makeSuite(TestBatchJob))
    suite.addTest(unittest.makeSuite(TestBatchRoutes))
    suite.addTest(unittest.makeSuite(TestBatchIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)