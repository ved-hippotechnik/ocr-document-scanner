"""
Database models and configuration for OCR Document Scanner
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime, timedelta, timezone
from werkzeug.security import generate_password_hash, check_password_hash
import hashlib
import hmac
import json
import os
import secrets

db = SQLAlchemy()
migrate = Migrate()

class User(db.Model):
    """Model for storing user information"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100), default='')
    last_name = db.Column(db.String(100), default='')
    organization = db.Column(db.String(200), default='')
    role = db.Column(db.String(20), default='user')  # 'user', 'admin', 'api_only'
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def set_password(self, password):
        """Hash and set user password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify password against stored hash"""
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        """Check if user has admin role"""
        return self.role == 'admin'

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'organization': self.organization,
            'role': self.role,
            'is_active': self.is_active,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class LoginAttempt(db.Model):
    """Model for tracking login attempts"""
    __tablename__ = 'login_attempts'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, index=True)
    ip_address = db.Column(db.String(45), nullable=False)
    user_agent = db.Column(db.String(500))
    success = db.Column(db.Boolean, nullable=False)
    attempted_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    # Relationships
    user = db.relationship('User', backref='login_attempts')

    @staticmethod
    def is_account_locked(email, max_attempts=5, lockout_minutes=15):
        """Check if account is locked due to too many failed attempts"""
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=lockout_minutes)
        failed_count = LoginAttempt.query.filter(
            LoginAttempt.email == email,
            LoginAttempt.success == False,
            LoginAttempt.attempted_at >= cutoff
        ).count()
        return failed_count >= max_attempts

    @staticmethod
    def get_failed_attempts(email, minutes=15):
        """Get count of failed attempts in the last N minutes"""
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        return LoginAttempt.query.filter(
            LoginAttempt.email == email,
            LoginAttempt.success == False,
            LoginAttempt.attempted_at >= cutoff
        ).count()

class ScanHistory(db.Model):
    """Model for storing scan history and results"""
    __tablename__ = 'scan_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    session_id = db.Column(db.String(255), nullable=False, index=True)
    document_type = db.Column(db.String(100), nullable=False, index=True)
    document_subtype = db.Column(db.String(100))

    __table_args__ = (
        db.Index('ix_scan_history_doctype_created', 'document_type', 'created_at'),
    )
    confidence_score = db.Column(db.Float)
    quality_score = db.Column(db.Float)
    processing_time = db.Column(db.Float)
    file_size = db.Column(db.Integer)
    file_format = db.Column(db.String(10))
    filename = db.Column(db.String(255))
    extracted_data = db.Column(db.Text)  # JSON string
    error_message = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    status = db.Column(db.String(50), default='pending')  # pending, processing, completed, failed, cancelled
    task_id = db.Column(db.String(255), index=True)  # Celery task ID
    batch_job_id = db.Column(db.Integer, db.ForeignKey('batch_processing_jobs.id'))
    validation_status = db.Column(db.String(50))  # valid, invalid, partial
    validation_errors = db.Column(db.Text)  # JSON string
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user = db.relationship('User', backref='scans')
    batch_job = db.relationship('BatchProcessingJob', backref='scans')
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'document_type': self.document_type,
            'document_subtype': self.document_subtype,
            'confidence_score': self.confidence_score,
            'quality_score': self.quality_score,
            'processing_time': self.processing_time,
            'file_size': self.file_size,
            'file_format': self.file_format,
            'filename': self.filename,
            'extracted_data': json.loads(self.extracted_data) if self.extracted_data else None,
            'error_message': self.error_message,
            'status': self.status,
            'task_id': self.task_id,
            'batch_job_id': self.batch_job_id,
            'validation_status': self.validation_status,
            'validation_errors': json.loads(self.validation_errors) if self.validation_errors else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class DocumentTypeStats(db.Model):
    """Model for storing document type statistics"""
    __tablename__ = 'document_type_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    document_type = db.Column(db.String(100), nullable=False, unique=True)
    total_scans = db.Column(db.Integer, default=0)
    successful_scans = db.Column(db.Integer, default=0)
    failed_scans = db.Column(db.Integer, default=0)
    average_confidence = db.Column(db.Float, default=0.0)
    average_quality = db.Column(db.Float, default=0.0)
    average_processing_time = db.Column(db.Float, default=0.0)
    last_scan_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'document_type': self.document_type,
            'total_scans': self.total_scans,
            'successful_scans': self.successful_scans,
            'failed_scans': self.failed_scans,
            'success_rate': (self.successful_scans / self.total_scans * 100) if self.total_scans > 0 else 0,
            'average_confidence': self.average_confidence,
            'average_quality': self.average_quality,
            'average_processing_time': self.average_processing_time,
            'last_scan_at': self.last_scan_at.isoformat() if self.last_scan_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class BatchProcessingJob(db.Model):
    """Model for batch processing jobs"""
    __tablename__ = 'batch_processing_jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    job_name = db.Column(db.String(255))
    total_documents = db.Column(db.Integer, nullable=False)
    processed_documents = db.Column(db.Integer, default=0)
    successful_count = db.Column(db.Integer, default=0)
    failed_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(50), default='queued')  # queued, processing, completed, failed, cancelled
    task_id = db.Column(db.String(255), index=True)  # Celery task ID
    priority = db.Column(db.Integer, default=0)  # Higher number = higher priority
    processing_time = db.Column(db.Float)
    error_message = db.Column(db.Text)
    job_metadata = db.Column(db.Text)  # JSON string for additional data
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user = db.relationship('User', backref='batch_jobs')
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'job_name': self.job_name,
            'total_documents': self.total_documents,
            'processed_documents': self.processed_documents,
            'successful_count': self.successful_count,
            'failed_count': self.failed_count,
            'status': self.status,
            'task_id': self.task_id,
            'priority': self.priority,
            'processing_time': self.processing_time,
            'error_message': self.error_message,
            'metadata': json.loads(self.job_metadata) if self.job_metadata else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class SystemMetrics(db.Model):
    """Model for storing system performance metrics"""
    __tablename__ = 'system_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    metric_name = db.Column(db.String(100), nullable=False, index=True)
    metric_value = db.Column(db.Float, nullable=False)
    metric_type = db.Column(db.String(50), nullable=False)  # counter, gauge, histogram
    labels = db.Column(db.Text)  # JSON string for metric labels
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'metric_name': self.metric_name,
            'metric_value': self.metric_value,
            'metric_type': self.metric_type,
            'labels': json.loads(self.labels) if self.labels else None,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

class ApiKey(db.Model):
    """API key for external service authentication"""
    __tablename__ = 'api_keys'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    key_prefix = db.Column(db.String(16), nullable=False)
    key_hash = db.Column(db.String(64), nullable=False, unique=True)
    name = db.Column(db.String(100), nullable=False)
    scopes = db.Column(db.Text, default='["scan"]')  # JSON list
    rate_limit = db.Column(db.Integer, default=60)  # requests per minute
    is_active = db.Column(db.Boolean, default=True)
    last_used_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', backref='api_keys')

    @staticmethod
    def _hash_key(raw_key: str) -> str:
        return hashlib.sha256(raw_key.encode()).hexdigest()

    @classmethod
    def generate(cls, user_id: int, name: str, scopes=None, rate_limit: int = 60,
                 expires_at=None):
        """Create a new API key. Returns (raw_key, ApiKey instance).

        The raw key is shown to the user exactly once and never stored.
        """
        raw_key = f"ocr_live_{secrets.token_urlsafe(32)}"
        key_prefix = raw_key[:16]
        key_hash = cls._hash_key(raw_key)

        api_key = cls(
            user_id=user_id,
            key_prefix=key_prefix,
            key_hash=key_hash,
            name=name,
            scopes=json.dumps(scopes or ['scan']),
            rate_limit=rate_limit,
            expires_at=expires_at,
        )
        return raw_key, api_key

    @classmethod
    def verify(cls, raw_key: str):
        """Look up an API key by its raw value. Returns the ApiKey or None."""
        key_hash = cls._hash_key(raw_key)
        api_key = cls.query.filter_by(key_hash=key_hash, is_active=True).first()
        if api_key is None:
            return None
        if api_key.expires_at and api_key.expires_at < datetime.now(timezone.utc):
            return None
        api_key.last_used_at = datetime.now(timezone.utc)
        db.session.commit()
        return api_key

    def get_scopes(self):
        return json.loads(self.scopes) if self.scopes else []

    def has_scope(self, scope: str) -> bool:
        return scope in self.get_scopes()

    def to_dict(self, show_prefix=True):
        return {
            'id': self.id,
            'name': self.name,
            'key_prefix': f"{self.key_prefix}..." if show_prefix else None,
            'scopes': self.get_scopes(),
            'rate_limit': self.rate_limit,
            'is_active': self.is_active,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class WebhookConfig(db.Model):
    """Webhook configuration for async event delivery"""
    __tablename__ = 'webhook_configs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    url = db.Column(db.String(2048), nullable=False)
    secret = db.Column(db.String(64), nullable=False)
    events = db.Column(db.Text, default='["scan.complete"]')  # JSON list
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', backref='webhook_configs')
    deliveries = db.relationship('WebhookDelivery', backref='webhook_config',
                                 lazy='dynamic', cascade='all, delete-orphan')

    @classmethod
    def create(cls, user_id: int, url: str, events=None):
        """Create a new webhook config with auto-generated HMAC secret."""
        return cls(
            user_id=user_id,
            url=url,
            secret=secrets.token_hex(32),
            events=json.dumps(events or ['scan.complete']),
        )

    def get_events(self):
        return json.loads(self.events) if self.events else []

    def sign_payload(self, payload_bytes: bytes) -> str:
        """Compute HMAC-SHA256 signature for a payload."""
        return hmac.new(self.secret.encode(), payload_bytes, hashlib.sha256).hexdigest()

    def to_dict(self, include_secret=False):
        result = {
            'id': self.id,
            'url': self.url,
            'events': self.get_events(),
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_secret:
            result['secret'] = self.secret
        return result


class WebhookDelivery(db.Model):
    """Individual webhook delivery attempt and its result"""
    __tablename__ = 'webhook_deliveries'

    id = db.Column(db.Integer, primary_key=True)
    webhook_config_id = db.Column(db.Integer, db.ForeignKey('webhook_configs.id'),
                                  nullable=False, index=True)
    event_type = db.Column(db.String(50), nullable=False)
    payload = db.Column(db.Text, nullable=False)  # JSON
    response_status = db.Column(db.Integer)
    response_body = db.Column(db.Text)
    attempts = db.Column(db.Integer, default=0)
    max_attempts = db.Column(db.Integer, default=3)
    next_retry_at = db.Column(db.DateTime)
    delivered_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.Index('ix_webhook_delivery_config_created', 'webhook_config_id', 'created_at'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'webhook_config_id': self.webhook_config_id,
            'event_type': self.event_type,
            'payload': json.loads(self.payload) if self.payload else None,
            'response_status': self.response_status,
            'attempts': self.attempts,
            'max_attempts': self.max_attempts,
            'next_retry_at': self.next_retry_at.isoformat() if self.next_retry_at else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class ApiUsageLog(db.Model):
    """Aggregated daily API usage per key per endpoint"""
    __tablename__ = 'api_usage_logs'

    id = db.Column(db.Integer, primary_key=True)
    api_key_id = db.Column(db.Integer, db.ForeignKey('api_keys.id'), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False)
    endpoint = db.Column(db.String(200), nullable=False)
    request_count = db.Column(db.Integer, default=0)
    error_count = db.Column(db.Integer, default=0)
    total_latency_ms = db.Column(db.Float, default=0.0)

    __table_args__ = (
        db.Index('ix_api_usage_key_date', 'api_key_id', 'date'),
        db.UniqueConstraint('api_key_id', 'date', 'endpoint', name='uq_usage_key_date_endpoint'),
    )

    api_key = db.relationship('ApiKey', backref='usage_logs')

    def to_dict(self):
        return {
            'id': self.id,
            'api_key_id': self.api_key_id,
            'date': self.date.isoformat() if self.date else None,
            'endpoint': self.endpoint,
            'request_count': self.request_count,
            'error_count': self.error_count,
            'avg_latency_ms': round(self.total_latency_ms / self.request_count, 2)
                if self.request_count > 0 else 0,
        }


def _fix_login_attempts_schema(app):
    """Fix login_attempts table if it has wrong column names (username instead of email)"""
    from sqlalchemy import inspect, text
    inspector = inspect(db.engine)

    if 'login_attempts' not in inspector.get_table_names():
        return  # Table doesn't exist yet, create_all will handle it

    columns = {col['name'] for col in inspector.get_columns('login_attempts')}
    if 'username' in columns and 'email' not in columns:
        app.logger.warning("Fixing login_attempts schema: renaming 'username' to 'email'")
        try:
            # SQLite doesn't support ALTER COLUMN RENAME, so recreate the table
            with db.engine.begin() as conn:
                conn.execute(text("ALTER TABLE login_attempts RENAME TO login_attempts_old"))
            db.create_all()
            with db.engine.begin() as conn:
                conn.execute(text("""
                    INSERT INTO login_attempts (id, email, ip_address, user_agent, success, attempted_at, user_id)
                    SELECT id, username, ip_address, user_agent, success, attempted_at, user_id
                    FROM login_attempts_old
                """))
                conn.execute(text("DROP TABLE login_attempts_old"))
            app.logger.info("login_attempts schema fixed successfully")
        except Exception as e:
            app.logger.error(f"Failed to fix login_attempts schema: {e}")
            db.session.rollback()


def init_db(app):
    """Initialize database with Flask app.

    In production, uses Alembic migrations (flask db upgrade).
    In development, falls back to db.create_all() for convenience.
    """
    import os

    db.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        flask_env = os.environ.get('FLASK_ENV', 'development')

        if flask_env == 'production':
            try:
                from flask_migrate import upgrade
                upgrade(directory='migrations')
                app.logger.info("Database migrations applied successfully")
            except Exception as e:
                app.logger.error(f"Migration failed: {e}")
                raise
        else:
            _fix_login_attempts_schema(app)
            db.create_all()
        
        # Initialize document type stats for known processors
        known_types = [
            'emirates_id', 'aadhaar', 'driving_license', 
            'passport', 'us_drivers_license', 'us_green_card'
        ]
        
        for doc_type in known_types:
            existing = DocumentTypeStats.query.filter_by(document_type=doc_type).first()
            if not existing:
                stats = DocumentTypeStats(document_type=doc_type)
                db.session.add(stats)
        
        try:
            db.session.commit()
        except Exception as e:
            app.logger.error(f"Error initializing database: {str(e)}")
            db.session.rollback()

def log_scan_result(session_id, document_type, result_data, processing_time, 
                   file_info=None, error_message=None, request_info=None):
    """Log a scan result to the database"""
    try:
        scan_record = ScanHistory(
            session_id=session_id,
            document_type=document_type,
            document_subtype=result_data.get('document_subtype') if result_data else None,
            confidence_score=result_data.get('confidence_score') if result_data else None,
            quality_score=result_data.get('quality_score') if result_data else None,
            processing_time=processing_time,
            file_size=file_info.get('size') if file_info else None,
            file_format=file_info.get('format') if file_info else None,
            extracted_data=json.dumps(result_data) if result_data else None,
            error_message=error_message,
            ip_address=request_info.get('ip') if request_info else None,
            user_agent=request_info.get('user_agent') if request_info else None
        )
        
        db.session.add(scan_record)
        
        # Update document type stats
        stats = DocumentTypeStats.query.filter_by(document_type=document_type).first()
        if not stats:
            stats = DocumentTypeStats(document_type=document_type)
            db.session.add(stats)
        
        stats.total_scans += 1
        stats.last_scan_at = datetime.now(timezone.utc)
        
        if error_message:
            stats.failed_scans += 1
        else:
            stats.successful_scans += 1
            
            # Update averages
            if result_data:
                confidence = result_data.get('confidence_score', 0)
                quality = result_data.get('quality_score', 0)
                
                # Simple moving average calculation
                total_successful = stats.successful_scans
                stats.average_confidence = (
                    (stats.average_confidence * (total_successful - 1) + confidence) / total_successful
                )
                stats.average_quality = (
                    (stats.average_quality * (total_successful - 1) + quality) / total_successful
                )
                stats.average_processing_time = (
                    (stats.average_processing_time * (total_successful - 1) + processing_time) / total_successful
                )
        
        db.session.commit()
        return scan_record.id
        
    except Exception as e:
        db.session.rollback()
        raise e

def get_analytics_data(days=30):
    """Get analytics data for the dashboard"""
    from sqlalchemy import func
    from datetime import datetime, timedelta
    
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    # Get scan statistics
    total_scans = ScanHistory.query.filter(
        ScanHistory.created_at >= start_date
    ).count()
    
    successful_scans = ScanHistory.query.filter(
        ScanHistory.created_at >= start_date,
        ScanHistory.error_message.is_(None)
    ).count()
    
    # Get document type distribution
    doc_type_stats = db.session.query(
        ScanHistory.document_type,
        func.count(ScanHistory.id).label('count')
    ).filter(
        ScanHistory.created_at >= start_date
    ).group_by(ScanHistory.document_type).all()
    
    # Get daily scan counts
    daily_stats = db.session.query(
        func.date(ScanHistory.created_at).label('date'),
        func.count(ScanHistory.id).label('count')
    ).filter(
        ScanHistory.created_at >= start_date
    ).group_by(func.date(ScanHistory.created_at)).all()
    
    # Get performance metrics
    avg_processing_time = db.session.query(
        func.avg(ScanHistory.processing_time)
    ).filter(
        ScanHistory.created_at >= start_date,
        ScanHistory.error_message.is_(None)
    ).scalar() or 0
    
    avg_confidence = db.session.query(
        func.avg(ScanHistory.confidence_score)
    ).filter(
        ScanHistory.created_at >= start_date,
        ScanHistory.confidence_score.isnot(None)
    ).scalar() or 0
    
    return {
        'period': {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'days': days
        },
        'summary': {
            'total_scans': total_scans,
            'successful_scans': successful_scans,
            'failed_scans': total_scans - successful_scans,
            'success_rate': (successful_scans / total_scans * 100) if total_scans > 0 else 0,
            'average_processing_time': round(avg_processing_time, 2),
            'average_confidence': round(avg_confidence, 2)
        },
        'document_types': [
            {'type': stat[0], 'count': stat[1]} 
            for stat in doc_type_stats
        ],
        'daily_scans': [
            {'date': stat[0].isoformat(), 'count': stat[1]} 
            for stat in daily_stats
        ]
    }
