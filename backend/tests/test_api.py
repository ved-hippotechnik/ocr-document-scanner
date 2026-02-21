"""
Tests for API endpoints
"""
import unittest
import json
import base64
import io
from PIL import Image
from unittest.mock import patch, MagicMock

# Add the backend directory to the path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app
from app.database import db
from app.database import User
from app.auth.jwt_utils import jwt_manager


class TestAPIEndpoints(unittest.TestCase):
    """Test cases for API endpoints"""
    
    def setUp(self):
        """Set up test environment"""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['SECRET_KEY'] = 'test-secret-key'
        self.app.config['JWT_SECRET_KEY'] = 'test-jwt-secret'
        
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
            
            # Create test user
            self.test_user = User(
                email='test@example.com',
                username='testuser',
                first_name='Test',
                last_name='User',
                role=UserRole.USER
            )
            self.test_user.set_password('TestPass123!')
            
            db.session.add(self.test_user)
            db.session.commit()
            
            # Generate tokens for testing
            self.test_tokens = jwt_manager.generate_tokens(self.test_user)
            self.auth_headers = {'Authorization': f'Bearer {self.test_tokens["access_token"]}'}
    
    def tearDown(self):
        """Clean up test environment"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
    
    def create_test_image(self, width=200, height=200):
        """Create a test image for testing"""
        image = Image.new('RGB', (width, height), color='white')
        # Add some text to make it look like a document
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(image)
        draw.text((10, 10), "Test Document", fill='black')
        draw.text((10, 50), "Name: John Doe", fill='black')
        draw.text((10, 90), "ID: 123456789", fill='black')
        
        # Convert to base64
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        img_data = buffer.getvalue()
        
        return base64.b64encode(img_data).decode('utf-8')
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
    
    def test_enhanced_health_check(self):
        """Test enhanced health check endpoint"""
        response = self.client.get('/api/v2/health')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('status', data)
        self.assertIn('components', data)
    
    def test_processors_endpoint(self):
        """Test processors list endpoint"""
        response = self.client.get('/api/processors')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('supported_documents', data)
        self.assertIn('total_processors', data)
    
    @patch('app.routes_enhanced.document_classifier')
    @patch('app.routes_enhanced.quality_analyzer')
    @patch('app.routes_enhanced.processor_registry')
    def test_enhanced_scan_endpoint(self, mock_registry, mock_quality, mock_classifier):
        """Test enhanced scan endpoint with authentication"""
        # Mock dependencies
        mock_quality.analyze_quality.return_value = {
            'quality_score': 0.85,
            'issues': []
        }
        
        mock_classifier.classify_document.return_value = {
            'document_type': 'passport',
            'confidence': 0.9,
            'country': 'US'
        }
        
        mock_processor = MagicMock()
        mock_processor.process_document.return_value = {
            'document_type': 'passport',
            'confidence': 0.9,
            'extracted_info': {'name': 'John Doe', 'passport_number': '123456789'}
        }
        mock_processor.__class__.__name__ = 'PassportProcessor'
        
        mock_registry.get_processor_by_country_and_type.return_value = mock_processor
        
        # Create test data
        test_image = self.create_test_image()
        
        # Test without authentication (should fail)
        response = self.client.post('/api/v2/scan', json={
            'image': f'data:image/png;base64,{test_image}'
        })
        self.assertEqual(response.status_code, 401)
        
        # Test with authentication
        response = self.client.post('/api/v2/scan', 
                                    headers=self.auth_headers,
                                    json={
                                        'image': f'data:image/png;base64,{test_image}',
                                        'document_type': 'passport'
                                    })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('document_type', data)
        self.assertIn('confidence', data)
        self.assertIn('processing_time', data)
    
    def test_enhanced_scan_invalid_image(self):
        """Test enhanced scan with invalid image"""
        response = self.client.post('/api/v2/scan', 
                                    headers=self.auth_headers,
                                    json={
                                        'image': 'invalid_base64_data'
                                    })
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('error', data)
    
    def test_enhanced_scan_empty_request(self):
        """Test enhanced scan with empty request"""
        response = self.client.post('/api/v2/scan', 
                                    headers=self.auth_headers,
                                    json={})
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('error', data)
    
    @patch('app.routes_enhanced.document_classifier')
    def test_classify_endpoint(self, mock_classifier):
        """Test document classification endpoint"""
        mock_classifier.classify_document.return_value = {
            'document_type': 'driving_license',
            'confidence': 0.85,
            'country': 'US'
        }
        
        test_image = self.create_test_image()
        
        response = self.client.post('/api/v2/classify', 
                                    headers=self.auth_headers,
                                    json={
                                        'image': f'data:image/png;base64,{test_image}'
                                    })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['document_type'], 'driving_license')
        self.assertEqual(data['confidence'], 0.85)
    
    @patch('app.routes_enhanced.quality_analyzer')
    def test_quality_check_endpoint(self, mock_quality):
        """Test quality check endpoint"""
        mock_quality.analyze_quality.return_value = {
            'quality_score': 0.75,
            'issues': [
                {
                    'type': 'low_resolution',
                    'severity': 'medium',
                    'description': 'Image resolution could be higher'
                }
            ],
            'recommendations': [
                'Take photo in better lighting',
                'Hold camera steady'
            ]
        }
        
        test_image = self.create_test_image()
        
        response = self.client.post('/api/v2/quality', 
                                    headers=self.auth_headers,
                                    json={
                                        'image': f'data:image/png;base64,{test_image}'
                                    })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['quality_score'], 0.75)
        self.assertIn('issues', data)
        self.assertIn('recommendations', data)
    
    def test_stats_endpoint(self):
        """Test statistics endpoint"""
        response = self.client.get('/api/v2/stats')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('stats', data)
        self.assertIn('performance', data['stats'])
        self.assertIn('system', data['stats'])
        self.assertIn('cache', data['stats'])
    
    def test_cache_stats_endpoint(self):
        """Test cache statistics endpoint"""
        response = self.client.get('/api/v2/cache/stats', headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('cache', data)
    
    def test_cache_clear_endpoint_non_admin(self):
        """Test cache clear endpoint with non-admin user"""
        response = self.client.post('/api/v2/cache/clear', headers=self.auth_headers)
        self.assertEqual(response.status_code, 403)
    
    def test_cache_warm_endpoint_non_admin(self):
        """Test cache warm endpoint with non-admin user"""
        response = self.client.post('/api/v2/cache/warm', headers=self.auth_headers)
        self.assertEqual(response.status_code, 403)
    
    def test_invalid_content_type(self):
        """Test API with invalid content type"""
        response = self.client.post('/api/v2/scan', 
                                    headers={**self.auth_headers, 'Content-Type': 'text/plain'},
                                    data='invalid data')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('Content-Type must be application/json', data['error']['message'])
    
    def test_rate_limiting(self):
        """Test rate limiting"""
        # Make multiple requests quickly
        test_image = self.create_test_image()
        
        # First request should work
        response = self.client.post('/api/v2/classify', 
                                    headers=self.auth_headers,
                                    json={
                                        'image': f'data:image/png;base64,{test_image}'
                                    })
        
        self.assertEqual(response.status_code, 200)
        
        # Check rate limit headers
        self.assertIn('X-RateLimit-Limit', response.headers)
        self.assertIn('X-RateLimit-Remaining', response.headers)
    
    def test_cors_headers(self):
        """Test CORS headers"""
        response = self.client.get('/api/v2/health')
        
        # Check for CORS headers (these are set by Flask-CORS)
        self.assertIn('Access-Control-Allow-Origin', response.headers)
    
    def test_security_headers(self):
        """Test security headers"""
        response = self.client.get('/api/v2/health')
        
        # Check for security headers
        self.assertIn('X-Content-Type-Options', response.headers)
        self.assertIn('X-Frame-Options', response.headers)
        self.assertIn('X-XSS-Protection', response.headers)
    
    def test_large_image_handling(self):
        """Test handling of large images"""
        # Create a large image (but still within limits)
        large_image = self.create_test_image(width=1000, height=1000)
        
        response = self.client.post('/api/v2/quality', 
                                    headers=self.auth_headers,
                                    json={
                                        'image': f'data:image/png;base64,{large_image}'
                                    })
        
        # Should handle large images gracefully
        self.assertIn(response.status_code, [200, 400, 413])  # Success, validation error, or too large
    
    def test_malformed_json(self):
        """Test malformed JSON handling"""
        response = self.client.post('/api/v2/scan', 
                                    headers={**self.auth_headers, 'Content-Type': 'application/json'},
                                    data='{"invalid": json}')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('error', data)
    
    def test_missing_required_fields(self):
        """Test missing required fields"""
        response = self.client.post('/api/v2/scan', 
                                    headers=self.auth_headers,
                                    json={
                                        'document_type': 'passport'
                                        # Missing 'image' field
                                    })
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('image', data['error']['message'])
    
    def test_invalid_options(self):
        """Test invalid processing options"""
        test_image = self.create_test_image()
        
        response = self.client.post('/api/v2/scan', 
                                    headers=self.auth_headers,
                                    json={
                                        'image': f'data:image/png;base64,{test_image}',
                                        'options': {
                                            'invalid_option': True,
                                            'confidence_threshold': 1.5  # Invalid value
                                        }
                                    })
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('error', data)


class TestAsyncEndpoints(unittest.TestCase):
    """Test cases for async endpoints"""
    
    def setUp(self):
        """Set up test environment"""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['SECRET_KEY'] = 'test-secret-key'
        self.app.config['JWT_SECRET_KEY'] = 'test-jwt-secret'
        
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
            
            # Create test user
            self.test_user = User(
                email='test@example.com',
                username='testuser',
                role=UserRole.USER
            )
            self.test_user.set_password('TestPass123!')
            
            db.session.add(self.test_user)
            db.session.commit()
            
            # Generate tokens for testing
            self.test_tokens = jwt_manager.generate_tokens(self.test_user)
            self.auth_headers = {'Authorization': f'Bearer {self.test_tokens["access_token"]}'}
    
    def tearDown(self):
        """Clean up test environment"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
    
    @patch('app.routes_enhanced.process_document_async')
    def test_async_scan_endpoint(self, mock_async_task):
        """Test async scan endpoint"""
        # Mock Celery task
        mock_task = MagicMock()
        mock_task.id = 'task_123'
        mock_async_task.delay.return_value = mock_task
        
        test_image = base64.b64encode(b'fake_image_data').decode('utf-8')
        
        response = self.client.post('/async/scan', 
                                    headers=self.auth_headers,
                                    json={
                                        'image': f'data:image/png;base64,{test_image}',
                                        'document_type': 'passport'
                                    })
        
        self.assertEqual(response.status_code, 202)
        data = json.loads(response.data)
        self.assertEqual(data['task_id'], 'task_123')
        self.assertEqual(data['status'], 'accepted')
    
    @patch('app.routes_enhanced.process_batch_documents')
    def test_async_batch_scan_endpoint(self, mock_batch_task):
        """Test async batch scan endpoint"""
        # Mock Celery task
        mock_task = MagicMock()
        mock_task.id = 'batch_task_123'
        mock_batch_task.delay.return_value = mock_task
        
        test_image = base64.b64encode(b'fake_image_data').decode('utf-8')
        
        response = self.client.post('/async/batch', 
                                    headers=self.auth_headers,
                                    json={
                                        'documents': [
                                            {'image': f'data:image/png;base64,{test_image}'},
                                            {'image': f'data:image/png;base64,{test_image}'}
                                        ]
                                    })
        
        self.assertEqual(response.status_code, 202)
        data = json.loads(response.data)
        self.assertEqual(data['batch_id'], 'batch_task_123')
        self.assertEqual(data['total_documents'], 2)
    
    def test_async_batch_too_large(self):
        """Test async batch with too many documents"""
        test_image = base64.b64encode(b'fake_image_data').decode('utf-8')
        
        # Create more than 50 documents
        documents = [{'image': f'data:image/png;base64,{test_image}'} for _ in range(51)]
        
        response = self.client.post('/async/batch', 
                                    headers=self.auth_headers,
                                    json={'documents': documents})
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('Batch size cannot exceed 50', data['error'])
    
    @patch('app.routes_enhanced.celery')
    def test_task_status_endpoint(self, mock_celery):
        """Test task status endpoint"""
        # Mock Celery AsyncResult
        mock_result = MagicMock()
        mock_result.state = 'SUCCESS'
        mock_result.result = {'document_type': 'passport', 'confidence': 0.9}
        mock_celery.AsyncResult.return_value = mock_result
        
        response = self.client.get('/async/status/task_123')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['task_id'], 'task_123')
        self.assertEqual(data['state'], 'SUCCESS')
        self.assertIn('result', data)
    
    @patch('app.routes_enhanced.celery')
    def test_cancel_task_endpoint(self, mock_celery):
        """Test cancel task endpoint"""
        response = self.client.post('/async/cancel/task_123')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['task_id'], 'task_123')
        self.assertEqual(data['status'], 'cancelled')
        
        # Verify revoke was called
        mock_celery.control.revoke.assert_called_once_with('task_123', terminate=True)


if __name__ == '__main__':
    unittest.main()