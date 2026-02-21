#!/usr/bin/env python3
"""
PostgreSQL Migration Script for OCR Document Scanner

This script helps migrate from SQLite to PostgreSQL for production deployment.
It includes database setup, data migration, and validation.

Usage:
    python migrate_to_postgresql.py --setup
    python migrate_to_postgresql.py --migrate
    python migrate_to_postgresql.py --validate
"""

import os
import sys
import sqlite3
import argparse
import subprocess
from datetime import datetime
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_dir))

def setup_postgresql_database():
    """Set up PostgreSQL database and user."""
    print("Setting up PostgreSQL database...")
    
    # Get PostgreSQL connection details from environment
    db_name = os.getenv('POSTGRES_DB', 'ocr_scanner_prod')
    db_user = os.getenv('POSTGRES_USER', 'ocr_app_user')
    db_password = os.getenv('POSTGRES_PASSWORD', 'secure_password_here')
    db_host = os.getenv('POSTGRES_HOST', 'localhost')
    db_port = os.getenv('POSTGRES_PORT', '5432')
    
    # PostgreSQL setup commands
    setup_commands = [
        f"CREATE DATABASE {db_name};",
        f"CREATE USER {db_user} WITH ENCRYPTED PASSWORD '{db_password}';",
        f"GRANT ALL PRIVILEGES ON DATABASE {db_name} TO {db_user};",
        f"ALTER USER {db_user} CREATEDB;"
    ]
    
    print(f"Database: {db_name}")
    print(f"User: {db_user}")
    print(f"Host: {db_host}:{db_port}")
    print("\nPostgreSQL setup commands:")
    print("Run these commands as PostgreSQL superuser:")
    print("-" * 50)
    
    for cmd in setup_commands:
        print(f"psql -h {db_host} -p {db_port} -U postgres -c \"{cmd}\"")
    
    print("-" * 50)
    print(f"\nAlternatively, connect to PostgreSQL and run:")
    for cmd in setup_commands:
        print(f"  {cmd}")

def create_production_database_config():
    """Create database configuration for production."""
    config_content = """
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
        \"\"\"Validate database connection.\"\"\"
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
"""
    
    config_file = backend_dir / 'app' / 'database_config.py'
    with open(config_file, 'w') as f:
        f.write(config_content)
    
    print(f"Created database configuration: {config_file}")

def migrate_sqlite_to_postgresql():
    """Migrate data from SQLite to PostgreSQL."""
    print("Starting data migration from SQLite to PostgreSQL...")
    
    # Check if SQLite database exists
    sqlite_path = backend_dir / 'instance' / 'ocr_scanner.db'
    if not sqlite_path.exists():
        print(f"SQLite database not found at {sqlite_path}")
        return False
    
    try:
        # Import Flask app and database
        os.environ['DATABASE_URL'] = os.getenv('DATABASE_URL', 'postgresql://...')
        
        from app import create_app
        from app.database import db
        
        # Create Flask app with PostgreSQL config
        app, _ = create_app()
        
        with app.app_context():
            # Create all tables in PostgreSQL
            print("Creating tables in PostgreSQL...")
            db.create_all()
            
            # Connect to SQLite database
            sqlite_conn = sqlite3.connect(sqlite_path)
            sqlite_conn.row_factory = sqlite3.Row
            
            # Get list of tables from SQLite
            cursor = sqlite_conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = [row[0] for row in cursor.fetchall()]
            
            print(f"Found {len(tables)} tables to migrate: {tables}")
            
            # Migrate each table
            for table_name in tables:
                if table_name.startswith('sqlite_'):
                    continue
                    
                print(f"Migrating table: {table_name}")
                
                # Get data from SQLite
                sqlite_cursor = sqlite_conn.execute(f"SELECT * FROM {table_name}")
                rows = sqlite_cursor.fetchall()
                
                if not rows:
                    print(f"  No data in {table_name}")
                    continue
                
                # Get column names
                column_names = [description[0] for description in sqlite_cursor.description]
                
                # Insert data into PostgreSQL
                placeholders = ', '.join(['%s'] * len(column_names))
                columns_str = ', '.join(column_names)
                
                insert_query = f"""
                    INSERT INTO {table_name} ({columns_str})
                    VALUES ({placeholders})
                    ON CONFLICT DO NOTHING
                """
                
                # Convert rows to list of tuples
                data_to_insert = [tuple(row) for row in rows]
                
                # Execute batch insert
                db.session.execute(insert_query, data_to_insert)
                db.session.commit()
                
                print(f"  Migrated {len(data_to_insert)} rows")
            
            sqlite_conn.close()
            print("Migration completed successfully!")
            return True
            
    except Exception as e:
        print(f"Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def validate_postgresql_setup():
    """Validate PostgreSQL setup and data integrity."""
    print("Validating PostgreSQL setup...")
    
    try:
        from app import create_app
        from app.database import db, ScanHistory
        
        # Create Flask app
        app, _ = create_app()
        
        with app.app_context():
            # Test database connection
            db.session.execute("SELECT 1")
            print("✅ Database connection successful")
            
            # Check if tables exist
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            print(f"✅ Found {len(tables)} tables: {tables}")
            
            # Check sample data
            scan_count = ScanHistory.query.count()
            print(f"✅ ScanHistory table has {scan_count} records")
            
            # Test database operations
            test_scan = ScanHistory(
                filename='migration_test.jpg',
                document_type='test',
                confidence_score=0.99,
                processing_time=1.0,
                extracted_text='Migration test',
                status='completed'
            )
            
            db.session.add(test_scan)
            db.session.commit()
            db.session.delete(test_scan)
            db.session.commit()
            
            print("✅ Database operations test successful")
            print("✅ PostgreSQL validation completed successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Validation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    parser = argparse.ArgumentParser(
        description='PostgreSQL Migration Tool for OCR Document Scanner'
    )
    parser.add_argument(
        '--setup', action='store_true',
        help='Show PostgreSQL database setup commands'
    )
    parser.add_argument(
        '--migrate', action='store_true',
        help='Migrate data from SQLite to PostgreSQL'
    )
    parser.add_argument(
        '--validate', action='store_true',
        help='Validate PostgreSQL setup'
    )
    parser.add_argument(
        '--config', action='store_true',
        help='Create production database configuration'
    )
    
    args = parser.parse_args()
    
    if not any([args.setup, args.migrate, args.validate, args.config]):
        parser.print_help()
        return
    
    print("=" * 80)
    print("POSTGRESQL MIGRATION TOOL")
    print("=" * 80)
    print(f"Migration started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    if args.setup:
        setup_postgresql_database()
    
    if args.config:
        create_production_database_config()
    
    if args.migrate:
        success = migrate_sqlite_to_postgresql()
        if not success:
            sys.exit(1)
    
    if args.validate:
        success = validate_postgresql_setup()
        if not success:
            sys.exit(1)
    
    print("\n" + "=" * 80)
    print("MIGRATION COMPLETED")
    print("=" * 80)

if __name__ == "__main__":
    main()