
# PostgreSQL Database Configuration
# Add this to your production app configuration

import os
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

class ProductionDatabaseConfig:
    # PostgreSQL connection parameters
    POSTGRES_USER = os.getenv('POSTGRES_USER', 'ocr_app_user')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
    POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
    POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
    POSTGRES_DB = os.getenv('POSTGRES_DB', 'ocr_scanner_prod')
    
    # Build database URL
    if all([POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_DB]):
        SQLALCHEMY_DATABASE_URI = (
            f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@"
            f"{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
        )
    else:
        SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    
    # Database engine configuration for production
    SQLALCHEMY_ENGINE_OPTIONS = {
        'poolclass': QueuePool,
        'pool_size': int(os.getenv('DATABASE_POOL_SIZE', 10)),
        'max_overflow': int(os.getenv('DATABASE_MAX_OVERFLOW', 20)),
        'pool_timeout': int(os.getenv('DATABASE_POOL_TIMEOUT', 30)),
        'pool_recycle': int(os.getenv('DATABASE_POOL_RECYCLE', 3600)),
        'pool_pre_ping': True,
        'echo': False,  # Disable SQL query logging in production
    }
    
    # Additional production settings
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = False
    
    @classmethod
    def validate_connection(cls):
        """Validate database connection."""
        try:
            engine = create_engine(
                cls.SQLALCHEMY_DATABASE_URI,
                **cls.SQLALCHEMY_ENGINE_OPTIONS
            )
            with engine.connect() as conn:
                conn.execute("SELECT 1")
            return True, "Database connection successful"
        except Exception as e:
            return False, f"Database connection failed: {str(e)}"

# Usage in your Flask app:
# from .database_config import ProductionDatabaseConfig
# app.config.from_object(ProductionDatabaseConfig)
