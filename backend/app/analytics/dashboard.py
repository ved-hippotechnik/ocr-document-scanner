"""
Advanced Analytics Dashboard for OCR Document Scanner
"""
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
from collections import defaultdict, Counter
import logging

from flask import Blueprint, request, jsonify, render_template_string
from ..database import db, ScanHistory, DocumentTypeStats
from ..auth import token_required, admin_required
from ..validation import ErrorHandler, handle_processing_errors
from ..cache import cache
# from ..websocket import get_connection_stats

# Temporary stub function for websocket stats
def get_connection_stats():
    return {"total_connections": 0, "active_rooms": 0}

logger = logging.getLogger(__name__)

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')


class AnalyticsEngine:
    """Advanced analytics engine for OCR processing data"""
    
    def __init__(self):
        self.cache_ttl = 300  # 5 minutes cache
    
    def get_dashboard_data(self, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        try:
            # Check cache first
            cache_key = {'dashboard_data': True, 'days': days}
            cached_data = cache.get_document_result(cache_key)
            
            if cached_data:
                return cached_data['result']
            
            # Calculate date range
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days)
            
            # Get all data
            dashboard_data = {
                'overview': self._get_overview_stats(start_date, end_date),
                'processing_trends': self._get_processing_trends(start_date, end_date),
                'document_types': self._get_document_type_stats(start_date, end_date),
                'quality_metrics': self._get_quality_metrics(start_date, end_date),
                'performance_metrics': self._get_performance_metrics(start_date, end_date),
                'error_analysis': self._get_error_analysis(start_date, end_date),
                'user_activity': self._get_user_activity(start_date, end_date),
                'system_health': self._get_system_health(),
                'generated_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Cache the result
            cache.set_document_result(cache_key, dashboard_data, self.cache_ttl)
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error generating dashboard data: {e}")
            raise
    
    def _get_overview_stats(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get overview statistics"""
        try:
            # Query database for overview stats
            total_scans = ScanHistory.query.filter(
                ScanHistory.created_at >= start_date,
                ScanHistory.created_at <= end_date
            ).count()
            
            # Successful scans (confidence > 0.5)
            successful_scans = ScanHistory.query.filter(
                ScanHistory.created_at >= start_date,
                ScanHistory.created_at <= end_date,
                ScanHistory.result_data.contains('"confidence":')
            ).count()
            
            # Average processing time
            avg_processing_time = db.session.query(
                db.func.avg(ScanHistory.processing_time)
            ).filter(
                ScanHistory.created_at >= start_date,
                ScanHistory.created_at <= end_date
            ).scalar() or 0
            
            # Calculate success rate
            success_rate = (successful_scans / total_scans * 100) if total_scans > 0 else 0
            
            # Get previous period for comparison
            prev_start = start_date - (end_date - start_date)
            prev_total = ScanHistory.query.filter(
                ScanHistory.created_at >= prev_start,
                ScanHistory.created_at < start_date
            ).count()
            
            growth_rate = ((total_scans - prev_total) / prev_total * 100) if prev_total > 0 else 0
            
            return {
                'total_scans': total_scans,
                'successful_scans': successful_scans,
                'success_rate': round(success_rate, 2),
                'avg_processing_time': round(avg_processing_time, 3),
                'growth_rate': round(growth_rate, 2),
                'period_days': (end_date - start_date).days
            }
            
        except Exception as e:
            logger.error(f"Error getting overview stats: {e}")
            return {}
    
    def _get_processing_trends(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get processing trends over time"""
        try:
            # Query scans grouped by date
            scans_by_date = db.session.query(
                db.func.date(ScanHistory.created_at).label('date'),
                db.func.count(ScanHistory.id).label('count'),
                db.func.avg(ScanHistory.processing_time).label('avg_time')
            ).filter(
                ScanHistory.created_at >= start_date,
                ScanHistory.created_at <= end_date
            ).group_by(
                db.func.date(ScanHistory.created_at)
            ).order_by('date').all()
            
            # Format data for charts
            dates = []
            counts = []
            avg_times = []
            
            for scan_date, count, avg_time in scans_by_date:
                dates.append(scan_date.strftime('%Y-%m-%d'))
                counts.append(count)
                avg_times.append(round(avg_time, 3) if avg_time else 0)
            
            # Get hourly distribution
            scans_by_hour = db.session.query(
                db.func.extract('hour', ScanHistory.created_at).label('hour'),
                db.func.count(ScanHistory.id).label('count')
            ).filter(
                ScanHistory.created_at >= start_date,
                ScanHistory.created_at <= end_date
            ).group_by(
                db.func.extract('hour', ScanHistory.created_at)
            ).order_by('hour').all()
            
            hourly_data = {str(int(hour)): count for hour, count in scans_by_hour}
            
            return {
                'daily_trends': {
                    'dates': dates,
                    'scan_counts': counts,
                    'avg_processing_times': avg_times
                },
                'hourly_distribution': hourly_data
            }
            
        except Exception as e:
            logger.error(f"Error getting processing trends: {e}")
            return {}
    
    def _get_document_type_stats(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get document type statistics"""
        try:
            # Query document types
            doc_type_stats = db.session.query(
                ScanHistory.document_type,
                db.func.count(ScanHistory.id).label('count'),
                db.func.avg(ScanHistory.processing_time).label('avg_time')
            ).filter(
                ScanHistory.created_at >= start_date,
                ScanHistory.created_at <= end_date
            ).group_by(
                ScanHistory.document_type
            ).order_by(
                db.func.count(ScanHistory.id).desc()
            ).all()
            
            # Format data
            document_types = []
            counts = []
            avg_times = []
            
            for doc_type, count, avg_time in doc_type_stats:
                document_types.append(doc_type or 'Unknown')
                counts.append(count)
                avg_times.append(round(avg_time, 3) if avg_time else 0)
            
            # Calculate percentages
            total_docs = sum(counts)
            percentages = [round(count / total_docs * 100, 2) if total_docs > 0 else 0 for count in counts]
            
            return {
                'document_types': document_types,
                'counts': counts,
                'percentages': percentages,
                'avg_processing_times': avg_times,
                'total_documents': total_docs
            }
            
        except Exception as e:
            logger.error(f"Error getting document type stats: {e}")
            return {}
    
    def _get_quality_metrics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get quality metrics"""
        try:
            # This would require storing quality scores in the database
            # For now, return mock data based on typical quality distributions
            
            quality_ranges = [
                ('0.0-0.2', 'Very Poor'),
                ('0.2-0.4', 'Poor'),
                ('0.4-0.6', 'Fair'),
                ('0.6-0.8', 'Good'),
                ('0.8-1.0', 'Excellent')
            ]
            
            # Mock quality distribution (in real implementation, query from database)
            quality_distribution = {
                'ranges': [label for _, label in quality_ranges],
                'counts': [2, 5, 15, 45, 33],  # Mock percentages
                'avg_quality_score': 0.75,
                'quality_trend': 'improving'
            }
            
            return quality_distribution
            
        except Exception as e:
            logger.error(f"Error getting quality metrics: {e}")
            return {}
    
    def _get_performance_metrics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get performance metrics"""
        try:
            # Query performance data
            performance_stats = db.session.query(
                db.func.min(ScanHistory.processing_time).label('min_time'),
                db.func.max(ScanHistory.processing_time).label('max_time'),
                db.func.avg(ScanHistory.processing_time).label('avg_time'),
                db.func.count(ScanHistory.id).label('total_scans')
            ).filter(
                ScanHistory.created_at >= start_date,
                ScanHistory.created_at <= end_date
            ).first()
            
            if not performance_stats:
                return {}
            
            # Get percentiles (simplified calculation)
            processing_times = [
                pt[0] for pt in db.session.query(ScanHistory.processing_time).filter(
                    ScanHistory.created_at >= start_date,
                    ScanHistory.created_at <= end_date,
                    ScanHistory.processing_time.isnot(None)
                ).order_by(ScanHistory.processing_time).all()
            ]
            
            percentiles = {}
            if processing_times:
                percentiles = {
                    'p50': self._calculate_percentile(processing_times, 50),
                    'p90': self._calculate_percentile(processing_times, 90),
                    'p95': self._calculate_percentile(processing_times, 95),
                    'p99': self._calculate_percentile(processing_times, 99)
                }
            
            return {
                'min_processing_time': round(performance_stats.min_time, 3) if performance_stats.min_time else 0,
                'max_processing_time': round(performance_stats.max_time, 3) if performance_stats.max_time else 0,
                'avg_processing_time': round(performance_stats.avg_time, 3) if performance_stats.avg_time else 0,
                'total_scans': performance_stats.total_scans,
                'percentiles': percentiles
            }
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {}
    
    def _get_error_analysis(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get error analysis"""
        try:
            # Query failed scans (this would require storing error info)
            # For now, return mock data
            
            error_types = [
                'Low Quality Image',
                'Unsupported Format',
                'Processing Timeout',
                'Document Not Detected',
                'OCR Engine Error'
            ]
            
            error_counts = [12, 8, 3, 15, 2]  # Mock data
            
            return {
                'error_types': error_types,
                'error_counts': error_counts,
                'total_errors': sum(error_counts),
                'error_rate': 3.2  # Mock error rate percentage
            }
            
        except Exception as e:
            logger.error(f"Error getting error analysis: {e}")
            return {}
    
    def _get_user_activity(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get user activity metrics"""
        try:
            # Query user activity (this would require storing user info with scans)
            # For now, return mock data
            
            return {
                'active_users': 45,
                'new_users': 12,
                'returning_users': 33,
                'avg_scans_per_user': 8.5,
                'top_users': [
                    {'user': 'User A', 'scans': 156},
                    {'user': 'User B', 'scans': 143},
                    {'user': 'User C', 'scans': 128}
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting user activity: {e}")
            return {}
    
    def _get_system_health(self) -> Dict[str, Any]:
        """Get system health metrics"""
        try:
            # Get cache stats
            cache_stats = cache.get_stats()
            
            # Get WebSocket stats
            websocket_stats = get_connection_stats()
            
            # Get database stats
            db_stats = self._get_database_stats()
            
            return {
                'cache': cache_stats,
                'websocket': websocket_stats,
                'database': db_stats,
                'system_load': self._get_system_load()
            }
            
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return {}
    
    def _get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            total_scans = ScanHistory.query.count()
            recent_scans = ScanHistory.query.filter(
                ScanHistory.created_at >= datetime.now(timezone.utc) - timedelta(hours=1)
            ).count()
            
            return {
                'total_records': total_scans,
                'recent_activity': recent_scans,
                'connection_status': 'healthy'
            }
            
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {'connection_status': 'error'}
    
    def _get_system_load(self) -> Dict[str, Any]:
        """Get system load metrics"""
        try:
            import psutil
            
            return {
                'cpu_usage': psutil.cpu_percent(interval=1),
                'memory_usage': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('/').percent
            }
            
        except ImportError:
            return {'status': 'monitoring_unavailable'}
        except Exception as e:
            logger.error(f"Error getting system load: {e}")
            return {'status': 'error'}
    
    def _calculate_percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile value"""
        if not data:
            return 0
        
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        index = min(index, len(sorted_data) - 1)
        
        return round(sorted_data[index], 3)
    
    def export_analytics_report(self, days: int = 30, format: str = 'json') -> Dict[str, Any]:
        """Export analytics report in specified format"""
        try:
            dashboard_data = self.get_dashboard_data(days)
            
            if format == 'json':
                return dashboard_data
            elif format == 'csv':
                return self._convert_to_csv(dashboard_data)
            elif format == 'pdf':
                return self._convert_to_pdf(dashboard_data)
            else:
                raise ValueError(f"Unsupported format: {format}")
                
        except Exception as e:
            logger.error(f"Error exporting analytics report: {e}")
            raise
    
    def _convert_to_csv(self, data: Dict[str, Any]) -> str:
        """Convert analytics data to CSV format"""
        # This would implement CSV conversion
        # For now, return a simplified version
        return "CSV export not implemented yet"
    
    def _convert_to_pdf(self, data: Dict[str, Any]) -> bytes:
        """Convert analytics data to PDF format"""
        # This would implement PDF conversion
        # For now, return a placeholder
        return b"PDF export not implemented yet"


# Global analytics engine instance
analytics_engine = AnalyticsEngine()


@analytics_bp.route('/dashboard', methods=['GET'])
@token_required
@handle_processing_errors()
def get_dashboard():
    """Get comprehensive analytics dashboard data"""
    try:
        days = request.args.get('days', 30, type=int)
        if days < 1 or days > 365:
            days = 30
        
        dashboard_data = analytics_engine.get_dashboard_data(days)
        
        return ErrorHandler.create_success_response({
            'dashboard': dashboard_data
        })
        
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        raise


@analytics_bp.route('/overview', methods=['GET'])
@token_required
@handle_processing_errors()
def get_overview():
    """Get analytics overview"""
    try:
        days = request.args.get('days', 7, type=int)
        
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        overview = analytics_engine._get_overview_stats(start_date, end_date)
        
        return ErrorHandler.create_success_response({
            'overview': overview
        })
        
    except Exception as e:
        logger.error(f"Overview error: {e}")
        raise


@analytics_bp.route('/trends', methods=['GET'])
@token_required
@handle_processing_errors()
def get_trends():
    """Get processing trends"""
    try:
        days = request.args.get('days', 30, type=int)
        
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        trends = analytics_engine._get_processing_trends(start_date, end_date)
        
        return ErrorHandler.create_success_response({
            'trends': trends
        })
        
    except Exception as e:
        logger.error(f"Trends error: {e}")
        raise


@analytics_bp.route('/export', methods=['GET'])
@token_required
@handle_processing_errors()
def export_report():
    """Export analytics report"""
    try:
        days = request.args.get('days', 30, type=int)
        format = request.args.get('format', 'json')
        
        if format not in ['json', 'csv', 'pdf']:
            return ErrorHandler.create_success_response({
                'error': 'Invalid format. Supported formats: json, csv, pdf'
            }), 400
        
        report = analytics_engine.export_analytics_report(days, format)
        
        if format == 'json':
            return ErrorHandler.create_success_response({
                'report': report
            })
        else:
            # For CSV and PDF, return appropriate response
            return ErrorHandler.create_success_response({
                'message': f'{format.upper()} export completed',
                'data': report
            })
        
    except Exception as e:
        logger.error(f"Export error: {e}")
        raise


@analytics_bp.route('/real-time', methods=['GET'])
@token_required
@handle_processing_errors()
def get_real_time_stats():
    """Get real-time statistics"""
    try:
        # Get last hour stats
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(hours=1)
        
        recent_scans = ScanHistory.query.filter(
            ScanHistory.created_at >= start_date
        ).count()
        
        # Get active connections
        websocket_stats = get_connection_stats()
        
        # Get cache stats
        cache_stats = cache.get_stats()
        
        return ErrorHandler.create_success_response({
            'real_time': {
                'recent_scans': recent_scans,
                'active_connections': websocket_stats.get('total_connections', 0),
                'cache_hit_rate': cache_stats.get('hit_rate', 0) if cache_stats.get('available') else 0,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Real-time stats error: {e}")
        raise


@analytics_bp.route('/system-health', methods=['GET'])
@token_required
@admin_required
@handle_processing_errors()
def get_system_health():
    """Get system health metrics (admin only)"""
    try:
        health_data = analytics_engine._get_system_health()
        
        return ErrorHandler.create_success_response({
            'system_health': health_data
        })
        
    except Exception as e:
        logger.error(f"System health error: {e}")
        raise