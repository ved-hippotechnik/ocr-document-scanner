"""
Pytest configuration and fixtures for OCR Document Scanner tests
"""
import pytest
import tempfile
import os
from typing import Generator
from unittest.mock import Mock, patch

from app import create_app
from app.database import db, User, ScanHistory
from app.auth.jwt_utils import generate_tokens


@pytest.fixture(scope='session')
def app():
    """Create application for testing"""
    # Create temporary database
    db_fd, db_path = tempfile.mkstemp()
    
    # Test configuration
    test_config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SECRET_KEY': 'test-secret-key',
        'JWT_SECRET_KEY': 'test-jwt-secret',
        'WTF_CSRF_ENABLED': False,
        'CELERY_TASK_ALWAYS_EAGER': True,  # Execute tasks synchronously in tests
        'CELERY_TASK_EAGER_PROPAGATES': True,
        'MCP_STORAGE_PATH': tempfile.mkdtemp(),
        'UPLOAD_FOLDER': tempfile.mkdtemp()
    }
    
    app, socketio = create_app()
    
    # Override config for testing
    for key, value in test_config.items():
        app.config[key] = value
    
    with app.app_context():
        db.create_all()
        yield app
        
    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create test runner"""
    return app.test_cli_runner()


@pytest.fixture
def auth_headers(app):
    """Create authentication headers for testing"""
    with app.app_context():
        # Create test user
        user = User(
            username='testuser',
            email='test@example.com',
            is_active=True
        )
        user.set_password('testpassword')
        db.session.add(user)
        db.session.commit()
        
        # Generate tokens
        tokens = generate_tokens(user)
        
        return {
            'Authorization': f'Bearer {tokens["access_token"]}',
            'Content-Type': 'application/json'
        }


@pytest.fixture
def mock_ocr_system():
    """Mock OCR system for testing"""
    with patch('app.enhanced_ocr_complete.EnhancedOCRSystem') as mock:
        mock_instance = Mock()
        mock_instance.process_document.return_value = {
            'success': True,
            'document_type': 'aadhaar_card',
            'confidence': 0.95,
            'extracted_data': {
                'name': 'Test User',
                'aadhaar_number': '1234-5678-9012',
                'dob': '01/01/1990'
            },
            'quality_metrics': {
                'overall_score': 0.85,
                'brightness': 0.8,
                'contrast': 0.9,
                'sharpness': 0.8
            }
        }
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_celery_task():
    """Mock Celery tasks for testing"""
    with patch('app.tasks.process_document_async') as mock_task:
        mock_result = Mock()
        mock_result.id = 'test-task-id'
        mock_result.state = 'SUCCESS'
        mock_result.result = {'success': True, 'message': 'Test completed'}
        mock_task.apply_async.return_value = mock_result
        yield mock_task


@pytest.fixture
def sample_image_data():
    """Sample base64 image data for testing"""
    # Simple 1x1 pixel PNG in base64
    return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAGA+4nQUgAAAABJRU5ErkJggg=="


@pytest.fixture
def mock_mcp_servers(app):
    """Mock MCP servers for testing"""
    with app.app_context():
        with patch('app.mcp.routes.sequential_thinking_mcp') as mock_st, \
             patch('app.mcp.routes.memory_mcp') as mock_mem, \
             patch('app.mcp.routes.context7_mcp') as mock_ctx, \
             patch('app.mcp.routes.filesystem_mcp') as mock_fs:
            
            # Setup mock returns
            mock_st.create_context.return_value = 'test-session-id'
            mock_mem.store_memory.return_value = 'test-memory-id'
            mock_ctx.set_context.return_value = True
            mock_fs.write_file.return_value = True
            
            yield {
                'sequential_thinking': mock_st,
                'memory': mock_mem,
                'context7': mock_ctx,
                'filesystem': mock_fs
            }


@pytest.fixture
def db_session(app):
    """Database session for testing"""
    with app.app_context():
        yield db.session
        db.session.rollback()


@pytest.fixture
def test_user(db_session):
    """Create test user"""
    user = User(
        username='testuser',
        email='test@example.com',
        is_active=True
    )
    user.set_password('testpassword')
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def test_scan_history(db_session, test_user):
    """Create test scan history"""
    scan = ScanHistory(
        user_id=test_user.id,
        filename='test_document.jpg',
        document_type='aadhaar_card',
        confidence=0.95,
        processing_time=2.5,
        status='completed',
        extracted_data={
            'name': 'Test User',
            'aadhaar_number': '1234-5678-9012'
        }
    )
    db_session.add(scan)
    db_session.commit()
    return scan


# Test data fixtures
@pytest.fixture
def aadhaar_test_data():
    """Sample Aadhaar card test data"""
    return {
        'name': 'RAJESH KUMAR',
        'aadhaar_number': '1234 5678 9012',
        'dob': '01/01/1990',
        'gender': 'MALE',
        'father_name': 'RAM KUMAR',
        'address': '123 Test Street, Test City, Test State - 123456'
    }


@pytest.fixture
def emirates_id_test_data():
    """Sample Emirates ID test data"""
    return {
        'name': 'MOHAMMED AHMED',
        'id_number': '784-1990-1234567-8',
        'nationality': 'ARE',
        'dob': '01/01/1990',
        'expiry_date': '01/01/2030'
    }


@pytest.fixture
def passport_test_data():
    """Sample passport test data"""
    return {
        'name': 'PRIYA SHARMA',
        'passport_number': 'A1234567',
        'nationality': 'IND',
        'dob': '15/06/1985',
        'issue_date': '10/01/2020',
        'expiry_date': '09/01/2030',
        'place_of_birth': 'DELHI'
    }


# Environment setup fixtures
@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment variables"""
    test_env = {
        'FLASK_ENV': 'testing',
        'TESTING': 'True',
        'OCR_TIMEOUT': '30',
        'LOG_LEVEL': 'DEBUG'
    }
    
    original_env = {}
    for key, value in test_env.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value
    
    yield
    
    # Restore original environment
    for key, value in original_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


# Performance testing fixtures
@pytest.fixture
def performance_tracker():
    """Track performance metrics during tests"""
    import time
    
    class PerformanceTracker:
        def __init__(self):
            self.metrics = {}
        
        def start_timer(self, name: str):
            self.metrics[name] = {'start': time.time()}
        
        def end_timer(self, name: str):
            if name in self.metrics:
                self.metrics[name]['duration'] = time.time() - self.metrics[name]['start']
        
        def get_duration(self, name: str) -> float:
            return self.metrics.get(name, {}).get('duration', 0)
    
    return PerformanceTracker()