"""
Database models and configuration for OCR Document Scanner
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime, timezone
import json

db = SQLAlchemy()
migrate = Migrate()

class ScanHistory(db.Model):
    """Model for storing scan history and results"""
    __tablename__ = 'scan_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    session_id = db.Column(db.String(255), nullable=False, index=True)
    document_type = db.Column(db.String(100), nullable=False)
    document_subtype = db.Column(db.String(100))
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
    metadata = db.Column(db.Text)  # JSON string for additional data
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
            'metadata': json.loads(self.metadata) if self.metadata else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class SystemMetrics(db.Model):
    """Model for storing system performance metrics"""
    __tablename__ = 'system_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    metric_name = db.Column(db.String(100), nullable=False)
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

def init_db(app):
    """Initialize database with Flask app"""
    db.init_app(app)
    migrate.init_app(app, db)
    
    with app.app_context():
        # Create tables if they don't exist
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
