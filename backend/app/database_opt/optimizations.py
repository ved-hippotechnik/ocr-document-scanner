"""
Database optimizations and performance improvements
"""
import logging
from sqlalchemy import Index, text
from sqlalchemy.ext.declarative import declarative_base
from flask import current_app

from ..database import db

logger = logging.getLogger(__name__)


class DatabaseOptimizer:
    """Database optimization and performance tuning"""
    
    def __init__(self):
        self.optimizations_applied = False
    
    def apply_optimizations(self):
        """Apply all database optimizations"""
        try:
            logger.info("Applying database optimizations...")
            
            # Create indexes
            self._create_indexes()
            
            # Configure database settings
            self._configure_database_settings()
            
            # Analyze tables for query optimization
            self._analyze_tables()
            
            # Set up database maintenance
            self._setup_maintenance()
            
            self.optimizations_applied = True
            logger.info("✅ Database optimizations applied successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to apply database optimizations: {e}")
            raise
    
    def _create_indexes(self):
        """Create database indexes for performance"""
        indexes_to_create = [
            # ScanHistory indexes
            {
                'table': 'scan_history',
                'name': 'idx_scan_history_user_id',
                'columns': ['user_id']
            },
            {
                'table': 'scan_history',
                'name': 'idx_scan_history_created_at',
                'columns': ['created_at']
            },
            {
                'table': 'scan_history',
                'name': 'idx_scan_history_document_type',
                'columns': ['document_type']
            },
            {
                'table': 'scan_history',
                'name': 'idx_scan_history_status',
                'columns': ['status']
            },
            {
                'table': 'scan_history',
                'name': 'idx_scan_history_task_id',
                'columns': ['task_id']
            },
            {
                'table': 'scan_history',
                'name': 'idx_scan_history_user_created',
                'columns': ['user_id', 'created_at']
            },
            {
                'table': 'scan_history',
                'name': 'idx_scan_history_type_status',
                'columns': ['document_type', 'status']
            },
            
            # User indexes
            {
                'table': 'users',
                'name': 'idx_users_username',
                'columns': ['username'],
                'unique': True
            },
            {
                'table': 'users',
                'name': 'idx_users_email',
                'columns': ['email'],
                'unique': True
            },
            {
                'table': 'users',
                'name': 'idx_users_created_at',
                'columns': ['created_at']
            },
            {
                'table': 'users',
                'name': 'idx_users_is_active',
                'columns': ['is_active']
            },
            
            # UserSession indexes
            {
                'table': 'user_sessions',
                'name': 'idx_user_sessions_user_id',
                'columns': ['user_id']
            },
            {
                'table': 'user_sessions',
                'name': 'idx_user_sessions_session_token',
                'columns': ['session_token'],
                'unique': True
            },
            {
                'table': 'user_sessions',
                'name': 'idx_user_sessions_expires_at',
                'columns': ['expires_at']
            },
            {
                'table': 'user_sessions',
                'name': 'idx_user_sessions_is_active',
                'columns': ['is_active']
            },
            
            # DocumentTypeStats indexes
            {
                'table': 'document_type_stats',
                'name': 'idx_doc_stats_doc_type',
                'columns': ['document_type']
            },
            {
                'table': 'document_type_stats',
                'name': 'idx_doc_stats_last_updated',
                'columns': ['last_updated']
            },
            
            # BatchProcessingJob indexes
            {
                'table': 'batch_processing_jobs',
                'name': 'idx_batch_jobs_user_id',
                'columns': ['user_id']
            },
            {
                'table': 'batch_processing_jobs',
                'name': 'idx_batch_jobs_status',
                'columns': ['status']
            },
            {
                'table': 'batch_processing_jobs',
                'name': 'idx_batch_jobs_created_at',
                'columns': ['created_at']
            },
            {
                'table': 'batch_processing_jobs',
                'name': 'idx_batch_jobs_task_id',
                'columns': ['task_id']
            },
            {
                'table': 'batch_processing_jobs',
                'name': 'idx_batch_jobs_user_status',
                'columns': ['user_id', 'status']
            },
            
            # LoginAttempts indexes
            {
                'table': 'login_attempts',
                'name': 'idx_login_attempts_user_id',
                'columns': ['user_id']
            },
            {
                'table': 'login_attempts',
                'name': 'idx_login_attempts_ip_address',
                'columns': ['ip_address']
            },
            {
                'table': 'login_attempts',
                'name': 'idx_login_attempts_attempted_at',
                'columns': ['attempted_at']
            },
            {
                'table': 'login_attempts',
                'name': 'idx_login_attempts_success',
                'columns': ['success']
            },
            {
                'table': 'login_attempts',
                'name': 'idx_login_attempts_ip_time',
                'columns': ['ip_address', 'attempted_at']
            }
        ]
        
        # Create indexes
        for index_info in indexes_to_create:
            try:
                self._create_index(index_info)
            except Exception as e:
                logger.warning(f"Failed to create index {index_info['name']}: {e}")
    
    def _create_index(self, index_info):
        """Create a single index"""
        table_name = index_info['table']
        index_name = index_info['name']
        columns = index_info['columns']
        unique = index_info.get('unique', False)
        
        # Check if index already exists
        if self._index_exists(index_name):
            logger.debug(f"Index {index_name} already exists, skipping")
            return
        
        # Build CREATE INDEX statement
        unique_clause = "UNIQUE " if unique else ""
        columns_clause = ", ".join(columns)
        
        sql = f"""
        CREATE {unique_clause}INDEX IF NOT EXISTS {index_name} 
        ON {table_name} ({columns_clause})
        """
        
        try:
            db.session.execute(text(sql))
            db.session.commit()
            logger.info(f"Created index: {index_name}")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create index {index_name}: {e}")
            raise
    
    def _index_exists(self, index_name):
        """Check if index exists"""
        try:
            # SQLite specific query
            if 'sqlite' in str(db.engine.url):
                result = db.session.execute(text(
                    "SELECT name FROM sqlite_master WHERE type='index' AND name=:index_name"
                ), {'index_name': index_name})
                return result.fetchone() is not None
            
            # PostgreSQL specific query
            elif 'postgresql' in str(db.engine.url):
                result = db.session.execute(text(
                    "SELECT indexname FROM pg_indexes WHERE indexname=:index_name"
                ), {'index_name': index_name})
                return result.fetchone() is not None
            
            # MySQL specific query
            elif 'mysql' in str(db.engine.url):
                result = db.session.execute(text(
                    "SELECT INDEX_NAME FROM information_schema.STATISTICS WHERE INDEX_NAME=:index_name"
                ), {'index_name': index_name})
                return result.fetchone() is not None
            
            return False
            
        except Exception as e:
            logger.warning(f"Could not check if index {index_name} exists: {e}")
            return False
    
    def _configure_database_settings(self):
        """Configure database-specific performance settings"""
        try:
            # SQLite optimizations
            if 'sqlite' in str(db.engine.url):
                optimizations = [
                    "PRAGMA journal_mode = WAL",
                    "PRAGMA synchronous = NORMAL",
                    "PRAGMA cache_size = 10000",
                    "PRAGMA temp_store = MEMORY",
                    "PRAGMA mmap_size = 268435456",  # 256MB
                    "PRAGMA optimize"
                ]
                
                for pragma in optimizations:
                    try:
                        db.session.execute(text(pragma))
                        logger.debug(f"Applied SQLite optimization: {pragma}")
                    except Exception as e:
                        logger.warning(f"Failed to apply SQLite optimization '{pragma}': {e}")
                
                db.session.commit()
                logger.info("Applied SQLite performance optimizations")
            
            # PostgreSQL optimizations
            elif 'postgresql' in str(db.engine.url):
                # Set session-level optimizations
                optimizations = [
                    "SET work_mem = '16MB'",
                    "SET maintenance_work_mem = '64MB'",
                    "SET random_page_cost = 1.1",
                    "SET effective_cache_size = '512MB'"
                ]
                
                for setting in optimizations:
                    try:
                        db.session.execute(text(setting))
                        logger.debug(f"Applied PostgreSQL optimization: {setting}")
                    except Exception as e:
                        logger.warning(f"Failed to apply PostgreSQL optimization '{setting}': {e}")
                
                logger.info("Applied PostgreSQL performance optimizations")
            
        except Exception as e:
            logger.error(f"Failed to configure database settings: {e}")
    
    def _analyze_tables(self):
        """Analyze tables for query optimizer statistics"""
        try:
            tables = ['scan_history', 'users', 'user_sessions', 'document_type_stats', 
                     'batch_processing_jobs', 'login_attempts']
            
            for table in tables:
                try:
                    if 'sqlite' in str(db.engine.url):
                        db.session.execute(text(f"ANALYZE {table}"))
                    elif 'postgresql' in str(db.engine.url):
                        db.session.execute(text(f"ANALYZE {table}"))
                    elif 'mysql' in str(db.engine.url):
                        db.session.execute(text(f"ANALYZE TABLE {table}"))
                    
                    logger.debug(f"Analyzed table: {table}")
                except Exception as e:
                    logger.warning(f"Failed to analyze table {table}: {e}")
            
            db.session.commit()
            logger.info("Analyzed tables for query optimization")
            
        except Exception as e:
            logger.error(f"Failed to analyze tables: {e}")
    
    def _setup_maintenance(self):
        """Set up database maintenance procedures"""
        try:
            # Schedule regular maintenance tasks
            self._schedule_maintenance_tasks()
            
            # Set up automatic statistics updates
            self._setup_auto_stats_update()
            
            logger.info("Database maintenance procedures set up")
            
        except Exception as e:
            logger.error(f"Failed to set up database maintenance: {e}")
    
    def _schedule_maintenance_tasks(self):
        """Schedule regular maintenance tasks"""
        # This would integrate with Celery for periodic tasks
        logger.info("Maintenance tasks scheduling placeholder - integrate with Celery")
    
    def _setup_auto_stats_update(self):
        """Set up automatic statistics updates"""
        # This would set up triggers or scheduled tasks for statistics updates
        logger.info("Auto statistics update setup placeholder")
    
    def get_performance_metrics(self):
        """Get database performance metrics"""
        try:
            metrics = {}
            
            # Table sizes
            metrics['table_sizes'] = self._get_table_sizes()
            
            # Index usage statistics
            metrics['index_usage'] = self._get_index_usage()
            
            # Query performance
            metrics['query_stats'] = self._get_query_stats()
            
            # Connection pool stats
            metrics['connection_pool'] = self._get_connection_pool_stats()
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return {'error': str(e)}
    
    def _get_table_sizes(self):
        """Get table size information"""
        try:
            sizes = {}
            
            if 'sqlite' in str(db.engine.url):
                result = db.session.execute(text("""
                    SELECT name, 
                           (SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=m.name) as row_count
                    FROM sqlite_master m WHERE type='table'
                """))
                
                for row in result:
                    table_name = row[0]
                    if not table_name.startswith('sqlite_'):
                        # Get actual row count
                        count_result = db.session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                        row_count = count_result.scalar()
                        sizes[table_name] = {'rows': row_count}
            
            elif 'postgresql' in str(db.engine.url):
                result = db.session.execute(text("""
                    SELECT schemaname, tablename, 
                           pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                           pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                    FROM pg_tables WHERE schemaname = 'public'
                """))
                
                for row in result:
                    table_name = row[1]
                    sizes[table_name] = {
                        'size_pretty': row[2],
                        'size_bytes': row[3]
                    }
            
            return sizes
            
        except Exception as e:
            logger.error(f"Failed to get table sizes: {e}")
            return {}
    
    def _get_index_usage(self):
        """Get index usage statistics"""
        try:
            usage = {}
            
            if 'postgresql' in str(db.engine.url):
                result = db.session.execute(text("""
                    SELECT schemaname, tablename, indexname, 
                           idx_tup_read, idx_tup_fetch
                    FROM pg_stat_user_indexes
                """))
                
                for row in result:
                    index_name = row[2]
                    usage[index_name] = {
                        'table': row[1],
                        'tuples_read': row[3],
                        'tuples_fetched': row[4]
                    }
            
            return usage
            
        except Exception as e:
            logger.error(f"Failed to get index usage: {e}")
            return {}
    
    def _get_query_stats(self):
        """Get query performance statistics"""
        try:
            # This would require pg_stat_statements extension for PostgreSQL
            # For now, return basic connection info
            return {
                'active_connections': self._get_active_connections(),
                'database_size': self._get_database_size()
            }
            
        except Exception as e:
            logger.error(f"Failed to get query stats: {e}")
            return {}
    
    def _get_connection_pool_stats(self):
        """Get connection pool statistics"""
        try:
            pool = db.engine.pool
            return {
                'pool_size': pool.size(),
                'checked_in': pool.checkedin(),
                'checked_out': pool.checkedout(),
                'overflow': pool.overflow(),
                'invalid': pool.invalid()
            }
            
        except Exception as e:
            logger.error(f"Failed to get connection pool stats: {e}")
            return {}
    
    def _get_active_connections(self):
        """Get number of active database connections"""
        try:
            if 'postgresql' in str(db.engine.url):
                result = db.session.execute(text(
                    "SELECT count(*) FROM pg_stat_activity WHERE state = 'active'"
                ))
                return result.scalar()
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get active connections: {e}")
            return None
    
    def _get_database_size(self):
        """Get database size"""
        try:
            if 'postgresql' in str(db.engine.url):
                result = db.session.execute(text(
                    "SELECT pg_size_pretty(pg_database_size(current_database()))"
                ))
                return result.scalar()
            
            elif 'sqlite' in str(db.engine.url):
                import os
                db_path = str(db.engine.url).replace('sqlite:///', '')
                if os.path.exists(db_path):
                    size = os.path.getsize(db_path)
                    return f"{size / (1024*1024):.2f} MB"
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get database size: {e}")
            return None
    
    def optimize_queries(self):
        """Run query optimization procedures"""
        try:
            logger.info("Running query optimization procedures...")
            
            # Vacuum and analyze for PostgreSQL
            if 'postgresql' in str(db.engine.url):
                # Note: VACUUM cannot be run inside a transaction
                db.session.commit()  # Commit any pending transaction
                
                # Use autocommit mode for VACUUM
                connection = db.engine.connect()
                connection.execute(text("VACUUM ANALYZE"))
                connection.close()
                
                logger.info("Ran VACUUM ANALYZE on PostgreSQL")
            
            # SQLite optimizations
            elif 'sqlite' in str(db.engine.url):
                db.session.execute(text("VACUUM"))
                db.session.execute(text("PRAGMA optimize"))
                db.session.commit()
                
                logger.info("Ran VACUUM and PRAGMA optimize on SQLite")
            
            logger.info("Query optimization procedures completed")
            
        except Exception as e:
            logger.error(f"Failed to optimize queries: {e}")


# Global database optimizer instance
database_optimizer = DatabaseOptimizer()


def setup_database_optimizations(app):
    """Set up database optimizations for the Flask app"""
    with app.app_context():
        try:
            database_optimizer.apply_optimizations()
            app.database_optimizer = database_optimizer
            logger.info("Database optimizations initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database optimizations: {e}")


def get_database_performance_metrics():
    """Get current database performance metrics"""
    return database_optimizer.get_performance_metrics()


def run_database_maintenance():
    """Run database maintenance procedures"""
    try:
        database_optimizer.optimize_queries()
        logger.info("Database maintenance completed")
    except Exception as e:
        logger.error(f"Database maintenance failed: {e}")
        raise