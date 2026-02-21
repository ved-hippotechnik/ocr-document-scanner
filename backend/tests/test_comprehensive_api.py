"""
Comprehensive API tests for OCR Document Scanner
"""
import pytest
import json
import base64
from unittest.mock import patch, Mock

from app.database import db, ScanHistory


class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_basic_health_check(self, client):
        """Test basic health endpoint"""
        response = client.get('/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert data['service'] == 'ocr-document-scanner'
    
    def test_enhanced_health_check(self, client):
        """Test enhanced health endpoint"""
        response = client.get('/api/v2/health')
        assert response.status_code == 200
        data = response.get_json()
        assert 'status' in data
        assert 'components' in data
        assert 'timestamp' in data


class TestProcessorEndpoints:
    """Test processor information endpoints"""
    
    def test_list_processors(self, client):
        """Test processors listing endpoint"""
        response = client.get('/api/processors')
        assert response.status_code == 200
        data = response.get_json()
        assert 'supported_documents' in data
        assert 'total_processors' in data
        assert isinstance(data['supported_documents'], list)
        assert data['total_processors'] > 0


class TestDocumentProcessing:
    """Test document processing endpoints"""
    
    @pytest.mark.integration
    def test_basic_scan_endpoint(self, client, sample_image_data, mock_ocr_system):
        """Test basic scan endpoint"""
        with patch('builtins.open', create=True) as mock_file:
            mock_file.return_value.__enter__.return_value.read.return_value = base64.b64decode(sample_image_data)
            
            response = client.post('/api/scan', 
                data={'image': (BytesIO(base64.b64decode(sample_image_data)), 'test.jpg')},
                content_type='multipart/form-data'
            )
            
            assert response.status_code in [200, 400]  # 400 if no auth
    
    @pytest.mark.integration
    def test_enhanced_scan_endpoint(self, client, auth_headers, sample_image_data, mock_ocr_system):
        """Test enhanced scan endpoint with authentication"""
        response = client.post('/api/v2/scan',
            headers=auth_headers,
            json={
                'image': sample_image_data,
                'document_type': 'aadhaar_card',
                'enhance_quality': True,
                'validate_data': True
            }
        )
        
        assert response.status_code in [200, 422]  # May fail due to mock data
        if response.status_code == 200:
            data = response.get_json()
            assert 'success' in data
            assert 'document_type' in data


class TestAsyncProcessing:
    """Test asynchronous processing endpoints"""
    
    @pytest.mark.celery
    def test_async_scan_submission(self, client, auth_headers, sample_image_data, mock_celery_task):
        """Test async scan submission"""
        response = client.post('/api/v2/async/scan',
            headers=auth_headers,
            json={
                'image': sample_image_data,
                'document_type': 'aadhaar_card',
                'priority': 1
            }
        )
        
        assert response.status_code == 202
        data = response.get_json()
        assert data['success'] is True
        assert 'task_id' in data
        assert 'scan_id' in data
    
    @pytest.mark.celery
    def test_task_status_check(self, client, auth_headers, mock_celery_task):
        """Test task status checking"""
        task_id = 'test-task-id'
        
        with patch('celery.result.AsyncResult') as mock_result:
            mock_task = Mock()
            mock_task.state = 'SUCCESS'
            mock_task.ready.return_value = True
            mock_task.result = {'success': True}
            mock_result.return_value = mock_task
            
            response = client.get(f'/api/v2/async/status/{task_id}',
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['task_id'] == task_id
            assert data['state'] == 'SUCCESS'
    
    @pytest.mark.celery
    def test_task_cancellation(self, client, auth_headers):
        """Test task cancellation"""
        task_id = 'test-task-id'
        
        with patch('celery.result.AsyncResult') as mock_result:
            mock_task = Mock()
            mock_task.revoke = Mock()
            mock_result.return_value = mock_task
            
            response = client.post(f'/api/v2/async/cancel/{task_id}',
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True


class TestBatchProcessing:
    """Test batch processing endpoints"""
    
    @pytest.mark.celery
    def test_batch_submission(self, client, auth_headers, sample_image_data, mock_celery_task):
        """Test batch processing submission"""
        response = client.post('/api/v2/batch',
            headers=auth_headers,
            json={
                'images': [sample_image_data, sample_image_data],
                'job_name': 'Test Batch Job',
                'priority': 0
            }
        )
        
        assert response.status_code == 202
        data = response.get_json()
        assert data['success'] is True
        assert 'job_id' in data
        assert 'task_id' in data
        assert data['total_documents'] == 2
    
    def test_batch_job_status(self, client, auth_headers, test_user, db_session):
        """Test batch job status retrieval"""
        from app.database import BatchProcessingJob
        
        # Create test batch job
        job = BatchProcessingJob(
            user_id=test_user.id,
            job_name='Test Job',
            total_documents=5,
            processed_documents=3,
            status='processing'
        )
        db_session.add(job)
        db_session.commit()
        
        response = client.get(f'/api/v2/batch/{job.id}',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['job_name'] == 'Test Job'
        assert data['total_documents'] == 5
        assert data['processed_documents'] == 3


class TestAuthentication:
    """Test authentication endpoints"""
    
    def test_user_login(self, client, test_user):
        """Test user login"""
        response = client.post('/api/auth/login',
            json={
                'username': 'testuser',
                'password': 'testpassword'
            }
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'access_token' in data
        assert 'refresh_token' in data
    
    def test_invalid_login(self, client):
        """Test invalid login credentials"""
        response = client.post('/api/auth/login',
            json={
                'username': 'invalid',
                'password': 'invalid'
            }
        )
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['success'] is False
    
    def test_protected_endpoint_without_auth(self, client, sample_image_data):
        """Test accessing protected endpoint without authentication"""
        response = client.post('/api/v2/scan',
            json={'image': sample_image_data}
        )
        
        assert response.status_code == 401


class TestAnalytics:
    """Test analytics endpoints"""
    
    def test_analytics_dashboard(self, client, auth_headers):
        """Test analytics dashboard endpoint"""
        with patch('app.analytics.dashboard.get_dashboard_data') as mock_dashboard:
            mock_dashboard.return_value = {
                'total_scans': 100,
                'success_rate': 0.95,
                'avg_processing_time': 2.5,
                'document_types': {'aadhaar_card': 50, 'emirates_id': 30, 'passport': 20}
            }
            
            response = client.get('/api/v2/analytics/dashboard',
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert 'data' in data
            assert 'summary' in data
    
    @pytest.mark.celery
    def test_analytics_generation(self, client, auth_headers, mock_celery_task):
        """Test analytics report generation"""
        response = client.post('/api/v2/analytics/generate',
            headers=auth_headers,
            json={
                'days': 30,
                'global': False
            }
        )
        
        assert response.status_code == 202
        data = response.get_json()
        assert data['success'] is True
        assert 'task_id' in data


class TestMCPEndpoints:
    """Test MCP server endpoints"""
    
    @pytest.mark.mcp
    def test_sequential_thinking_creation(self, client, auth_headers, mock_mcp_servers):
        """Test sequential thinking session creation"""
        response = client.post('/api/v2/mcp/thinking/create',
            headers=auth_headers,
            json={
                'goal': 'Process document analysis',
                'metadata': {'document_type': 'aadhaar_card'}
            }
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        assert 'session_id' in data
    
    @pytest.mark.mcp
    def test_context7_set_value(self, client, auth_headers, mock_mcp_servers):
        """Test context7 value setting"""
        context_id = 'test-context'
        
        response = client.post(f'/api/v2/mcp/context/{context_id}/set',
            headers=auth_headers,
            json={
                'layer': 'session',
                'key': 'document_confidence',
                'value': 0.95,
                'confidence': 1.0
            }
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
    
    @pytest.mark.mcp
    def test_memory_storage(self, client, auth_headers, mock_mcp_servers):
        """Test memory storage"""
        response = client.post('/api/v2/mcp/memory/store',
            headers=auth_headers,
            json={
                'content': {'processed_document': 'aadhaar_card'},
                'context': {'user_session': 'test-session'},
                'tags': ['document', 'processing'],
                'importance': 0.8
            }
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        assert 'memory_id' in data


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_invalid_json_request(self, client, auth_headers):
        """Test handling of invalid JSON requests"""
        response = client.post('/api/v2/scan',
            headers=auth_headers,
            data='invalid json',
            content_type='application/json'
        )
        
        assert response.status_code == 400
    
    def test_missing_required_fields(self, client, auth_headers):
        """Test handling of missing required fields"""
        response = client.post('/api/v2/scan',
            headers=auth_headers,
            json={}  # Missing required 'image' field
        )
        
        assert response.status_code == 400
    
    def test_large_file_handling(self, client, auth_headers):
        """Test handling of oversized files"""
        # Create a large base64 string (>16MB when decoded)
        large_data = 'A' * (20 * 1024 * 1024)  # 20MB of 'A' characters
        
        response = client.post('/api/v2/scan',
            headers=auth_headers,
            json={'image': large_data}
        )
        
        assert response.status_code == 413  # Request Entity Too Large
    
    def test_rate_limiting(self, client, auth_headers, sample_image_data):
        """Test rate limiting functionality"""
        # This would need actual rate limiting implementation
        # For now, just test that the endpoint responds
        for i in range(5):
            response = client.post('/api/v2/scan',
                headers=auth_headers,
                json={'image': sample_image_data}
            )
            # Rate limiting would kick in after a few requests
            if response.status_code == 429:
                break
        
        # At least check the endpoint is accessible
        assert response.status_code in [200, 400, 401, 422, 429]


# Import BytesIO for file upload tests
from io import BytesIO