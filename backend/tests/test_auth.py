"""
Comprehensive tests for authentication system
"""
import unittest
import json
import jwt
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

# Add the backend directory to the path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app
from app.database import db
from app.database import User, LoginAttempt
from app.auth.jwt_utils import jwt_manager


class TestAuth(unittest.TestCase):
    """Test cases for authentication system"""
    
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
            
            # Create admin user
            self.admin_user = User(
                email='admin@example.com',
                username='adminuser',
                first_name='Admin',
                last_name='User',
                role=UserRole.ADMIN
            )
            self.admin_user.set_password('AdminPass123!')
            
            db.session.add(self.test_user)
            db.session.add(self.admin_user)
            db.session.commit()
            
            # Generate tokens for testing
            self.test_tokens = jwt_manager.generate_tokens(self.test_user)
            self.admin_tokens = jwt_manager.generate_tokens(self.admin_user)
    
    def tearDown(self):
        """Clean up test environment"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_user_registration(self):
        """Test user registration"""
        # Test successful registration
        response = self.client.post('/api/auth/register', json={
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password': 'NewPass123!',
            'first_name': 'New',
            'last_name': 'User'
        })
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('access_token', data)
        self.assertIn('user', data)
        
        # Test duplicate email
        response = self.client.post('/api/auth/register', json={
            'email': 'newuser@example.com',
            'username': 'anotheruser',
            'password': 'NewPass123!'
        })
        
        self.assertEqual(response.status_code, 409)
    
    def test_user_login(self):
        """Test user login"""
        # Test successful login
        response = self.client.post('/api/auth/login', json={
            'email': 'test@example.com',
            'password': 'TestPass123!'
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('access_token', data)
        self.assertIn('refresh_token', data)
        
        # Test invalid credentials
        response = self.client.post('/api/auth/login', json={
            'email': 'test@example.com',
            'password': 'wrongpassword'
        })
        
        self.assertEqual(response.status_code, 401)
    
    def test_token_refresh(self):
        """Test token refresh"""
        response = self.client.post('/api/auth/refresh', json={
            'refresh_token': self.test_tokens['refresh_token']
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('access_token', data)
    
    def test_protected_route_access(self):
        """Test accessing protected routes"""
        # Test without token
        response = self.client.get('/api/auth/profile')
        self.assertEqual(response.status_code, 401)
        
        # Test with valid token
        headers = {'Authorization': f'Bearer {self.test_tokens["access_token"]}'}
        response = self.client.get('/api/auth/profile', headers=headers)
        self.assertEqual(response.status_code, 200)
    
    def test_admin_access(self):
        """Test admin-only routes"""
        # Test non-admin access
        headers = {'Authorization': f'Bearer {self.test_tokens["access_token"]}'}
        response = self.client.get('/api/auth/admin/users', headers=headers)
        self.assertEqual(response.status_code, 403)
        
        # Test admin access
        admin_headers = {'Authorization': f'Bearer {self.admin_tokens["access_token"]}'}
        response = self.client.get('/api/auth/admin/users', headers=admin_headers)
        self.assertEqual(response.status_code, 200)
    
    def test_api_key_creation(self):
        """Test API key creation and usage"""
        headers = {'Authorization': f'Bearer {self.test_tokens["access_token"]}'}
        
        # Create API key
        response = self.client.post('/api/auth/api-keys', 
                                    headers=headers,
                                    json={'name': 'Test API Key'})
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('api_key', data)
        api_key = data['api_key']['key']
        
        # Test API key usage
        api_headers = {'X-API-Key': api_key}
        response = self.client.get('/api/auth/profile', headers=api_headers)
        self.assertEqual(response.status_code, 200)
    
    def test_password_validation(self):
        """Test password validation"""
        # Test weak password
        response = self.client.post('/api/auth/register', json={
            'email': 'weak@example.com',
            'username': 'weakuser',
            'password': '123'
        })
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('Password must be at least 8 characters', data['error']['message'])
    
    def test_rate_limiting(self):
        """Test rate limiting for login attempts"""
        # Simulate multiple failed login attempts
        for i in range(6):
            response = self.client.post('/api/auth/login', json={
                'email': 'test@example.com',
                'password': 'wrongpassword'
            })
        
        # Should be rate limited now
        response = self.client.post('/api/auth/login', json={
            'email': 'test@example.com',
            'password': 'TestPass123!'
        })
        
        self.assertEqual(response.status_code, 423)  # Account locked
    
    def test_password_reset(self):
        """Test password reset functionality"""
        # Request password reset
        response = self.client.post('/api/auth/forgot-password', json={
            'email': 'test@example.com'
        })
        
        self.assertEqual(response.status_code, 200)
        
        # In a real test, you would extract the token from email
        # For now, we'll create a token manually
        with self.app.app_context():
            reset = PasswordReset(
                user_id=self.test_user.id,
                token='test-reset-token',
                expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
            )
            db.session.add(reset)
            db.session.commit()
            
            # Reset password
            response = self.client.post('/api/auth/reset-password', json={
                'token': 'test-reset-token',
                'new_password': 'NewTestPass123!'
            })
            
            self.assertEqual(response.status_code, 200)
    
    def test_user_profile_update(self):
        """Test user profile update"""
        headers = {'Authorization': f'Bearer {self.test_tokens["access_token"]}'}
        
        response = self.client.put('/api/auth/profile', 
                                   headers=headers,
                                   json={
                                       'first_name': 'Updated',
                                       'last_name': 'Name',
                                       'organization': 'Test Org'
                                   })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['user']['first_name'], 'Updated')
    
    def test_change_password(self):
        """Test password change"""
        headers = {'Authorization': f'Bearer {self.test_tokens["access_token"]}'}
        
        response = self.client.post('/api/auth/change-password', 
                                    headers=headers,
                                    json={
                                        'current_password': 'TestPass123!',
                                        'new_password': 'NewTestPass123!'
                                    })
        
        self.assertEqual(response.status_code, 200)
        
        # Test login with new password
        response = self.client.post('/api/auth/login', json={
            'email': 'test@example.com',
            'password': 'NewTestPass123!'
        })
        
        self.assertEqual(response.status_code, 200)
    
    def test_jwt_token_validation(self):
        """Test JWT token validation"""
        # Test valid token
        payload = jwt_manager.decode_token(self.test_tokens['access_token'])
        self.assertNotIn('error', payload)
        self.assertEqual(payload['user_id'], str(self.test_user.id))
        
        # Test expired token
        expired_payload = {
            'user_id': str(self.test_user.id),
            'exp': datetime.now(timezone.utc) - timedelta(hours=1)
        }
        expired_token = jwt.encode(expired_payload, self.app.config['JWT_SECRET_KEY'], algorithm='HS256')
        
        payload = jwt_manager.decode_token(expired_token)
        self.assertIn('error', payload)
        self.assertEqual(payload['error'], 'Token has expired')
    
    def test_user_deactivation(self):
        """Test user deactivation"""
        admin_headers = {'Authorization': f'Bearer {self.admin_tokens["access_token"]}'}
        
        # Deactivate user
        response = self.client.post(f'/api/auth/admin/users/{self.test_user.id}/deactivate', 
                                    headers=admin_headers)
        
        self.assertEqual(response.status_code, 200)
        
        # Test that deactivated user cannot login
        response = self.client.post('/api/auth/login', json={
            'email': 'test@example.com',
            'password': 'TestPass123!'
        })
        
        self.assertEqual(response.status_code, 401)


if __name__ == '__main__':
    unittest.main()