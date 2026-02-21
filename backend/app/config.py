"""
Secure configuration management for OCR Document Scanner
"""
import os
import secrets
from typing import Optional, Dict, Any
from pathlib import Path
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)


class Config:
    """Base configuration with secure defaults"""
    
    # Load environment variables
    def __init__(self):
        self.load_environment()
        self.validate_configuration()
    
    def load_environment(self):
        """Load environment variables from .env file"""
        env_file = os.getenv('ENV_FILE', '.env')
        if os.path.exists(env_file):
            load_dotenv(env_file)
    
    def get_secret(self, key: str, default: Optional[str] = None) -> str:
        """Get secret from environment with fallback"""
        value = os.getenv(key, default)
        if value and value.startswith('${') and value.endswith('}'):
            # Placeholder detected - generate secure random value
            logger.warning(f"Placeholder detected for {key}, generating secure random value")
            value = secrets.token_urlsafe(32)
        return value
    
    # Flask Configuration
    FLASK_ENV = os.getenv('FLASK_ENV', 'production')
    DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
    TESTING = os.getenv('TESTING', 'false').lower() == 'true'
    
    # Security Keys - Generate if not provided
    SECRET_KEY = os.getenv('SECRET_KEY') or secrets.token_urlsafe(64)
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY') or secrets.token_urlsafe(64)
    
    # JWT Configuration
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', '3600'))
    JWT_REFRESH_TOKEN_EXPIRES = int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', '86400'))
    JWT_ALGORITHM = 'HS256'
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///ocr_scanner.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': int(os.getenv('DATABASE_POOL_SIZE', '20')),
        'pool_timeout': int(os.getenv('DATABASE_POOL_TIMEOUT', '30')),
        'pool_recycle': int(os.getenv('DATABASE_POOL_RECYCLE', '3600')),
        'max_overflow': int(os.getenv('DATABASE_MAX_OVERFLOW', '40')),
        'pool_pre_ping': True,  # Verify connections before using
    }
    
    # Redis Configuration
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')
    REDIS_MAX_CONNECTIONS = int(os.getenv('REDIS_MAX_CONNECTIONS', '50'))
    REDIS_CONNECTION_TIMEOUT = int(os.getenv('REDIS_CONNECTION_TIMEOUT', '5'))
    
    # CORS Configuration
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')
    CORS_ALLOW_HEADERS = ['Content-Type', 'Authorization']
    CORS_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
    CORS_CREDENTIALS = True
    
    # File Upload Configuration
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', '16777216'))  # 16MB
    MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', '16777216'))
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    ALLOWED_EXTENSIONS = set(os.getenv('ALLOWED_EXTENSIONS', 'jpg,jpeg,png,pdf,tiff,bmp').split(','))
    
    # Virus Scanning
    ENABLE_VIRUS_SCAN = os.getenv('ENABLE_VIRUS_SCAN', 'false').lower() == 'true'
    CLAMAV_SOCKET = os.getenv('CLAMAV_SOCKET', '/var/run/clamav/clamd.ctl')
    
    # Rate Limiting
    RATE_LIMIT_ENABLED = os.getenv('RATE_LIMIT_ENABLED', 'true').lower() == 'true'
    RATE_LIMIT_STORAGE_URL = os.getenv('RATE_LIMIT_STORAGE_URL', REDIS_URL)
    RATE_LIMIT_REQUESTS = int(os.getenv('RATE_LIMIT_REQUESTS', '100'))
    RATE_LIMIT_WINDOW = int(os.getenv('RATE_LIMIT_WINDOW', '3600'))
    
    # Security Headers
    SECURITY_HEADERS_ENABLED = os.getenv('SECURITY_HEADERS_ENABLED', 'true').lower() == 'true'
    CONTENT_SECURITY_POLICY = os.getenv(
        'CONTENT_SECURITY_POLICY',
        "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';"
    )
    
    # SSL/HTTPS Configuration
    FORCE_HTTPS = os.getenv('FORCE_HTTPS', 'false').lower() == 'true'
    SSL_CERT_PATH = os.getenv('SSL_CERT_PATH')
    SSL_KEY_PATH = os.getenv('SSL_KEY_PATH')
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'true').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = os.getenv('SESSION_COOKIE_HTTPONLY', 'true').lower() == 'true'
    SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/app.log')
    LOG_MAX_BYTES = int(os.getenv('LOG_MAX_BYTES', '10485760'))  # 10MB
    LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', '5'))
    SENTRY_DSN = os.getenv('SENTRY_DSN')
    
    # OCR Configuration
    OCR_TIMEOUT = int(os.getenv('OCR_TIMEOUT', '60'))
    OCR_DPI = int(os.getenv('OCR_DPI', '300'))
    OCR_LANGUAGES = os.getenv('OCR_LANGUAGES', 'eng,ara,hin').split(',')
    TESSERACT_CMD = os.getenv('TESSERACT_CMD', '/usr/bin/tesseract')
    
    # Celery Configuration
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', REDIS_URL)
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', REDIS_URL)
    CELERY_TASK_TIME_LIMIT = int(os.getenv('CELERY_TASK_TIME_LIMIT', '300'))
    CELERY_TASK_SOFT_TIME_LIMIT = int(os.getenv('CELERY_TASK_SOFT_TIME_LIMIT', '240'))
    
    # Monitoring
    PROMETHEUS_ENABLED = os.getenv('PROMETHEUS_ENABLED', 'true').lower() == 'true'
    PROMETHEUS_PORT = int(os.getenv('PROMETHEUS_PORT', '9090'))
    METRICS_ENABLED = os.getenv('METRICS_ENABLED', 'true').lower() == 'true'
    
    def validate_configuration(self):
        """Validate critical configuration settings"""
        errors = []
        
        # Check if we're in production
        if self.FLASK_ENV == 'production':
            # Ensure debug is off
            if self.DEBUG:
                errors.append("DEBUG must be False in production")
            
            # Check for default secrets
            if 'your-super-secret-key' in self.SECRET_KEY:
                errors.append("SECRET_KEY must be changed from default")
            
            if 'your-jwt-secret-key' in self.JWT_SECRET_KEY:
                errors.append("JWT_SECRET_KEY must be changed from default")
            
            # Check database
            if 'sqlite' in self.SQLALCHEMY_DATABASE_URI:
                logger.warning("SQLite detected in production - consider using PostgreSQL")
            
            # Check CORS
            if '*' in self.CORS_ORIGINS or 'localhost' in str(self.CORS_ORIGINS):
                logger.warning("CORS origins contain development values")
            
            # Check SSL
            if not self.FORCE_HTTPS:
                logger.warning("HTTPS is not enforced in production")
            
            # Check required environment variables
            required_vars = os.getenv('REQUIRED_ENV_VARS', '').split(',')
            for var in required_vars:
                if var and not os.getenv(var):
                    errors.append(f"Required environment variable {var} is not set")
        
        if errors:
            for error in errors:
                logger.error(f"Configuration Error: {error}")
            if self.FLASK_ENV == 'production':
                raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")
    
    @classmethod
    def get_config(cls, env: Optional[str] = None) -> 'Config':
        """Factory method to get configuration based on environment"""
        env = env or os.getenv('FLASK_ENV', 'production')
        
        if env == 'development':
            return DevelopmentConfig()
        elif env == 'testing':
            return TestingConfig()
        else:
            return ProductionConfig()


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    FLASK_ENV = 'development'
    SQLALCHEMY_DATABASE_URI = os.getenv('DEV_DATABASE_URL', 'sqlite:///dev_ocr_scanner.db')
    CORS_ORIGINS = ['http://localhost:3000', 'http://localhost:3001']
    FORCE_HTTPS = False
    SESSION_COOKIE_SECURE = False
    RATE_LIMIT_ENABLED = False


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    FLASK_ENV = 'testing'
    SQLALCHEMY_DATABASE_URI = os.getenv('TEST_DATABASE_URL', 'sqlite:///test_ocr_scanner.db')
    JWT_ACCESS_TOKEN_EXPIRES = 60
    RATE_LIMIT_ENABLED = False


class ProductionConfig(Config):
    """Production configuration with strict security"""
    DEBUG = False
    FLASK_ENV = 'production'
    FORCE_HTTPS = True
    SESSION_COOKIE_SECURE = True
    RATE_LIMIT_ENABLED = True
    ENABLE_VIRUS_SCAN = True
    SECURITY_HEADERS_ENABLED = True
    
    def __init__(self):
        super().__init__()
        # Additional production validation
        self.validate_production_config()
    
    def validate_production_config(self):
        """Additional production-specific validation"""
        if not self.SENTRY_DSN:
            logger.warning("Sentry DSN not configured for error tracking")
        
        if 'sqlite' in self.SQLALCHEMY_DATABASE_URI:
            logger.error("SQLite should not be used in production")
        
        if not os.path.exists(self.SSL_CERT_PATH or ''):
            logger.warning("SSL certificate not found")


# Export the configuration
config = Config.get_config()