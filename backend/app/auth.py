"""
Advanced authentication and API key management system
Supports multiple authentication methods and rate limiting
"""

import jwt
import hashlib
import secrets
import time
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple
from functools import wraps
from flask import request, jsonify, current_app
import sqlite3
import os
import bcrypt
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class UserRole(Enum):
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"

class AuthType(Enum):
    API_KEY = "api_key"
    JWT = "jwt"
    BASIC = "basic"

@dataclass
class User:
    id: int
    username: str
    email: str
    role: UserRole
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True

@dataclass
class APIKey:
    id: int
    key_id: str
    key_hash: str
    user_id: int
    name: str
    permissions: List[str]
    rate_limit: int
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    is_active: bool = True

class AuthManager:
    """Advanced authentication and authorization manager"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or os.environ.get('AUTH_DB_PATH', 'auth.db')
        self.secret_key = os.environ.get('JWT_SECRET_KEY', 'change-this-in-production')
        self.token_expiry = int(os.environ.get('JWT_EXPIRY_HOURS', 24))
        self.rate_limit_window = int(os.environ.get('RATE_LIMIT_WINDOW', 3600))  # 1 hour
        self._init_db()
    
    def _init_db(self):
        """Initialize the authentication database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'user',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS api_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key_id TEXT UNIQUE NOT NULL,
                    key_hash TEXT NOT NULL,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    permissions TEXT NOT NULL,
                    rate_limit INTEGER DEFAULT 100,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    last_used TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS rate_limits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key_id TEXT NOT NULL,
                    window_start TIMESTAMP NOT NULL,
                    request_count INTEGER DEFAULT 0,
                    UNIQUE(key_id, window_start)
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    key_id TEXT,
                    action TEXT NOT NULL,
                    resource TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    success BOOLEAN DEFAULT TRUE,
                    details TEXT
                )
            ''')
    
    def create_user(self, username: str, email: str, password: str, 
                   role: UserRole = UserRole.USER) -> User:
        """Create a new user"""
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                INSERT INTO users (username, email, password_hash, role)
                VALUES (?, ?, ?, ?)
            ''', (username, email, password_hash, role.value))
            
            user_id = cursor.lastrowid
            
            # Log user creation
            self._log_action(user_id, 'user_created', f'user:{user_id}')
            
            return self.get_user_by_id(user_id)
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username/password"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT id, username, email, password_hash, role, created_at, last_login, is_active
                FROM users WHERE username = ? AND is_active = TRUE
            ''', (username,))
            
            user_data = cursor.fetchone()
            if not user_data:
                return None
            
            # Verify password
            if not bcrypt.checkpw(password.encode('utf-8'), user_data[3]):
                self._log_action(user_data[0], 'login_failed', 'authentication')
                return None
            
            # Update last login
            conn.execute('''
                UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?
            ''', (user_data[0],))
            
            self._log_action(user_data[0], 'login_success', 'authentication')
            
            return User(
                id=user_data[0],
                username=user_data[1],
                email=user_data[2],
                role=UserRole(user_data[4]),
                created_at=datetime.fromisoformat(user_data[5]),
                last_login=datetime.fromisoformat(user_data[6]) if user_data[6] else None,
                is_active=bool(user_data[7])
            )
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT id, username, email, role, created_at, last_login, is_active
                FROM users WHERE id = ?
            ''', (user_id,))
            
            user_data = cursor.fetchone()
            if not user_data:
                return None
            
            return User(
                id=user_data[0],
                username=user_data[1],
                email=user_data[2],
                role=UserRole(user_data[3]),
                created_at=datetime.fromisoformat(user_data[4]),
                last_login=datetime.fromisoformat(user_data[5]) if user_data[5] else None,
                is_active=bool(user_data[6])
            )
    
    def create_api_key(self, user_id: int, name: str, permissions: List[str],
                      rate_limit: int = 100, expires_days: int = None) -> Tuple[str, APIKey]:
        """Create a new API key"""
        # Generate key
        key_id = f"ocr_{secrets.token_urlsafe(16)}"
        key_secret = secrets.token_urlsafe(32)
        full_key = f"{key_id}.{key_secret}"
        
        # Hash the secret part
        key_hash = hashlib.sha256(key_secret.encode()).hexdigest()
        
        expires_at = None
        if expires_days:
            expires_at = datetime.now(timezone.utc) + timedelta(days=expires_days)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                INSERT INTO api_keys (key_id, key_hash, user_id, name, permissions, rate_limit, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (key_id, key_hash, user_id, name, ','.join(permissions), rate_limit, expires_at))
            
            api_key_id = cursor.lastrowid
            
            # Log API key creation
            self._log_action(user_id, 'api_key_created', f'api_key:{key_id}')
            
            api_key = APIKey(
                id=api_key_id,
                key_id=key_id,
                key_hash=key_hash,
                user_id=user_id,
                name=name,
                permissions=permissions,
                rate_limit=rate_limit,
                created_at=datetime.now(timezone.utc),
                expires_at=expires_at
            )
            
            return full_key, api_key
    
    def validate_api_key(self, api_key: str) -> Optional[Tuple[User, APIKey]]:
        """Validate API key and return user and key info"""
        try:
            key_id, key_secret = api_key.split('.', 1)
        except ValueError:
            return None
        
        key_hash = hashlib.sha256(key_secret.encode()).hexdigest()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT ak.id, ak.key_id, ak.key_hash, ak.user_id, ak.name, ak.permissions,
                       ak.rate_limit, ak.created_at, ak.expires_at, ak.last_used, ak.is_active,
                       u.id, u.username, u.email, u.role, u.created_at, u.last_login, u.is_active
                FROM api_keys ak
                JOIN users u ON ak.user_id = u.id
                WHERE ak.key_id = ? AND ak.key_hash = ? AND ak.is_active = TRUE AND u.is_active = TRUE
            ''', (key_id, key_hash))
            
            result = cursor.fetchone()
            if not result:
                return None
            
            # Check expiry
            if result[8] and datetime.fromisoformat(result[8]) < datetime.now(timezone.utc):
                return None
            
            # Update last used
            conn.execute('''
                UPDATE api_keys SET last_used = CURRENT_TIMESTAMP WHERE id = ?
            ''', (result[0],))
            
            # Create objects
            api_key_obj = APIKey(
                id=result[0],
                key_id=result[1],
                key_hash=result[2],
                user_id=result[3],
                name=result[4],
                permissions=result[5].split(',') if result[5] else [],
                rate_limit=result[6],
                created_at=datetime.fromisoformat(result[7]),
                expires_at=datetime.fromisoformat(result[8]) if result[8] else None,
                last_used=datetime.fromisoformat(result[9]) if result[9] else None,
                is_active=bool(result[10])
            )
            
            user_obj = User(
                id=result[11],
                username=result[12],
                email=result[13],
                role=UserRole(result[14]),
                created_at=datetime.fromisoformat(result[15]),
                last_login=datetime.fromisoformat(result[16]) if result[16] else None,
                is_active=bool(result[17])
            )
            
            return user_obj, api_key_obj
    
    def check_rate_limit(self, key_id: str, rate_limit: int) -> bool:
        """Check if API key is within rate limit"""
        window_start = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT request_count FROM rate_limits
                WHERE key_id = ? AND window_start = ?
            ''', (key_id, window_start))
            
            result = cursor.fetchone()
            current_count = result[0] if result else 0
            
            if current_count >= rate_limit:
                return False
            
            # Increment counter
            conn.execute('''
                INSERT OR REPLACE INTO rate_limits (key_id, window_start, request_count)
                VALUES (?, ?, ?)
            ''', (key_id, window_start, current_count + 1))
            
            return True
    
    def generate_jwt_token(self, user: User) -> str:
        """Generate JWT token for user"""
        payload = {
            'user_id': user.id,
            'username': user.username,
            'role': user.role.value,
            'exp': datetime.now(timezone.utc) + timedelta(hours=self.token_expiry),
            'iat': datetime.now(timezone.utc)
        }
        
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def validate_jwt_token(self, token: str) -> Optional[User]:
        """Validate JWT token and return user"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return self.get_user_by_id(payload['user_id'])
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def _log_action(self, user_id: int = None, action: str = None, resource: str = None,
                   key_id: str = None, success: bool = True, details: str = None):
        """Log authentication action"""
        ip_address = request.remote_addr if request else None
        user_agent = request.headers.get('User-Agent') if request else None
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO audit_log (user_id, key_id, action, resource, ip_address, user_agent, success, details)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, key_id, action, resource, ip_address, user_agent, success, details))
    
    def get_audit_log(self, user_id: int = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get audit log entries"""
        with sqlite3.connect(self.db_path) as conn:
            if user_id:
                cursor = conn.execute('''
                    SELECT * FROM audit_log WHERE user_id = ?
                    ORDER BY timestamp DESC LIMIT ?
                ''', (user_id, limit))
            else:
                cursor = conn.execute('''
                    SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT ?
                ''', (limit,))
            
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

# Global auth manager instance
auth_manager = AuthManager()

def require_auth(permissions: List[str] = None, auth_types: List[AuthType] = None):
    """Decorator to require authentication"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            auth_types_list = auth_types or [AuthType.API_KEY, AuthType.JWT]
            
            user, api_key_obj = _authenticate_request(auth_types_list)
            
            if not user:
                return jsonify({'error': 'Authentication required'}), 401
            
            # Check API key rate limits and permissions
            if api_key_obj:
                if not auth_manager.check_rate_limit(api_key_obj.key_id, api_key_obj.rate_limit):
                    return jsonify({'error': 'Rate limit exceeded'}), 429
                
                if permissions and not _check_permissions(permissions, api_key_obj.permissions):
                    return jsonify({'error': 'Insufficient permissions'}), 403
            
            # Add user context to request
            request.current_user = user
            request.current_api_key = api_key_obj
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def _authenticate_request(auth_types_list: List[AuthType]) -> Tuple[Optional[User], Optional[APIKey]]:
    """Helper function to authenticate request using various methods"""
    # Try API Key authentication
    if AuthType.API_KEY in auth_types_list:
        user, api_key = _try_api_key_auth()
        if user:
            return user, api_key
    
    # Try JWT authentication
    if AuthType.JWT in auth_types_list:
        user = _try_jwt_auth()
        if user:
            return user, None
    
    # Try Basic authentication
    if AuthType.BASIC in auth_types_list:
        user = _try_basic_auth()
        if user:
            return user, None
    
    return None, None

def _try_api_key_auth() -> Tuple[Optional[User], Optional[APIKey]]:
    """Try API key authentication"""
    api_key = request.headers.get('X-API-Key')
    if api_key:
        result = auth_manager.validate_api_key(api_key)
        if result:
            return result
    return None, None

def _try_jwt_auth() -> Optional[User]:
    """Try JWT authentication"""
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        return auth_manager.validate_jwt_token(token)
    return None

def _try_basic_auth() -> Optional[User]:
    """Try Basic authentication"""
    auth = request.authorization
    if auth:
        return auth_manager.authenticate_user(auth.username, auth.password)
    return None

def _check_permissions(required_permissions: List[str], user_permissions: List[str]) -> bool:
    """Check if user has required permissions"""
    return any(perm in user_permissions for perm in required_permissions)

def require_role(role: UserRole):
    """Decorator to require specific role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(request, 'current_user') or not request.current_user:
                return jsonify({'error': 'Authentication required'}), 401
            
            if request.current_user.role != role and request.current_user.role != UserRole.ADMIN:
                return jsonify({'error': 'Insufficient privileges'}), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator
