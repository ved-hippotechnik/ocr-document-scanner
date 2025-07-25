#!/usr/bin/env python3
"""
Advanced Analytics & Business Intelligence Dashboard
Provides comprehensive analytics, performance monitoring, and business insights
"""

import sqlite3
import json
import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import statistics
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict, Counter
import pandas as pd

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ProcessingMetrics:
    """Processing performance metrics"""
    total_documents: int
    successful_extractions: int
    failed_extractions: int
    average_processing_time: float
    average_confidence: float
    success_rate: float
    documents_by_type: Dict[str, int]
    processing_times: List[float]
    confidence_scores: List[float]
    error_types: Dict[str, int]

@dataclass
class QualityMetrics:
    """Document quality metrics"""
    average_quality_score: float
    quality_distribution: Dict[str, int]
    low_quality_count: int
    high_quality_count: int
    quality_trends: List[float]

@dataclass
class UsageMetrics:
    """System usage metrics"""
    total_sessions: int
    active_users: int
    peak_usage_time: str
    usage_by_hour: Dict[int, int]
    usage_by_day: Dict[str, int]
    average_session_duration: float

@dataclass
class BusinessInsights:
    """Business intelligence insights"""
    document_type_trends: Dict[str, List[int]]
    processing_efficiency: float
    cost_analysis: Dict[str, float]
    user_satisfaction: float
    recommendations: List[str]

class AnalyticsDatabase:
    """Database for storing analytics data"""
    
    def __init__(self, db_path: str = "analytics.db"):
        self.db_path = Path(db_path)
        self.init_database()
    
    def init_database(self):
        """Initialize the analytics database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Processing logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processing_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                session_id TEXT,
                document_type TEXT,
                processing_time REAL,
                confidence_score REAL,
                quality_score REAL,
                success BOOLEAN,
                error_message TEXT,
                file_size INTEGER,
                image_width INTEGER,
                image_height INTEGER,
                extracted_fields TEXT,
                user_agent TEXT,
                ip_address TEXT
            )
        ''')
        
        # Quality metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quality_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                session_id TEXT,
                sharpness REAL,
                brightness REAL,
                contrast REAL,
                noise_level REAL,
                overall_quality REAL
            )
        ''')
        
        # Usage sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usage_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE,
                start_time DATETIME,
                end_time DATETIME,
                duration REAL,
                documents_processed INTEGER,
                user_agent TEXT,
                ip_address TEXT
            )
        ''')
        
        # Performance metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                metric_name TEXT,
                metric_value REAL,
                metadata TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"Analytics database initialized at {self.db_path}")
    
    def log_processing_event(self, event_data: Dict[str, Any]):
        """Log a processing event"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO processing_logs 
            (session_id, document_type, processing_time, confidence_score, 
             quality_score, success, error_message, file_size, image_width, 
             image_height, extracted_fields, user_agent, ip_address)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            event_data.get('session_id'),
            event_data.get('document_type'),
            event_data.get('processing_time'),
            event_data.get('confidence_score'),
            event_data.get('quality_score'),
            event_data.get('success'),
            event_data.get('error_message'),
            event_data.get('file_size'),
            event_data.get('image_width'),
            event_data.get('image_height'),
            json.dumps(event_data.get('extracted_fields', {})),
            event_data.get('user_agent'),
            event_data.get('ip_address')
        ))
        
        conn.commit()
        conn.close()
    
    def log_quality_metrics(self, metrics_data: Dict[str, Any]):
        """Log quality metrics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO quality_metrics 
            (session_id, sharpness, brightness, contrast, noise_level, overall_quality)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            metrics_data.get('session_id'),
            metrics_data.get('sharpness'),
            metrics_data.get('brightness'),
            metrics_data.get('contrast'),
            metrics_data.get('noise_level'),
            metrics_data.get('overall_quality')
        ))
        
        conn.commit()
        conn.close()
    
    def log_usage_session(self, session_data: Dict[str, Any]):
        """Log usage session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO usage_sessions 
            (session_id, start_time, end_time, duration, documents_processed, 
             user_agent, ip_address)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_data.get('session_id'),
            session_data.get('start_time'),
            session_data.get('end_time'),
            session_data.get('duration'),
            session_data.get('documents_processed'),
            session_data.get('user_agent'),
            session_data.get('ip_address')
        ))
        
        conn.commit()
        conn.close()
    
    def get_processing_data(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get processing data for the last N days"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM processing_logs 
            WHERE timestamp >= datetime('now', '-{} days')
            ORDER BY timestamp DESC
        '''.format(days))
        
        columns = [desc[0] for desc in cursor.description]
        data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return data
    
    def get_quality_data(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get quality data for the last N days"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM quality_metrics 
            WHERE timestamp >= datetime('now', '-{} days')
            ORDER BY timestamp DESC
        '''.format(days))
        
        columns = [desc[0] for desc in cursor.description]
        data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return data
    
    def get_usage_data(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get usage data for the last N days"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM usage_sessions 
            WHERE start_time >= datetime('now', '-{} days')
            ORDER BY start_time DESC
        '''.format(days))
        
        columns = [desc[0] for desc in cursor.description]
        data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return data

class AnalyticsProcessor:
    """Process and analyze data to generate insights"""
    
    def __init__(self, database: AnalyticsDatabase):
        self.database = database
        
    def calculate_processing_metrics(self, days: int = 30) -> ProcessingMetrics:
        """Calculate processing performance metrics"""
        data = self.database.get_processing_data(days)
        
        if not data:
            return ProcessingMetrics(
                total_documents=0,
                successful_extractions=0,
                failed_extractions=0,
                average_processing_time=0.0,
                average_confidence=0.0,
                success_rate=0.0,
                documents_by_type={},
                processing_times=[],
                confidence_scores=[],
                error_types={}
            )
        
        total_documents = len(data)
        successful_extractions = sum(1 for d in data if d['success'])
        failed_extractions = total_documents - successful_extractions
        
        processing_times = [d['processing_time'] for d in data if d['processing_time']]
        confidence_scores = [d['confidence_score'] for d in data if d['confidence_score']]
        
        average_processing_time = statistics.mean(processing_times) if processing_times else 0.0
        average_confidence = statistics.mean(confidence_scores) if confidence_scores else 0.0
        success_rate = (successful_extractions / total_documents * 100) if total_documents > 0 else 0.0
        
        documents_by_type = Counter(d['document_type'] for d in data if d['document_type'])
        error_types = Counter(d['error_message'] for d in data if d['error_message'])
        
        return ProcessingMetrics(
            total_documents=total_documents,
            successful_extractions=successful_extractions,
            failed_extractions=failed_extractions,
            average_processing_time=average_processing_time,
            average_confidence=average_confidence,
            success_rate=success_rate,
            documents_by_type=dict(documents_by_type),
            processing_times=processing_times,
            confidence_scores=confidence_scores,
            error_types=dict(error_types)
        )
    
    def calculate_quality_metrics(self, days: int = 30) -> QualityMetrics:
        """Calculate quality metrics"""
        data = self.database.get_quality_data(days)
        
        if not data:
            return QualityMetrics(
                average_quality_score=0.0,
                quality_distribution={},
                low_quality_count=0,
                high_quality_count=0,
                quality_trends=[]
            )
        
        quality_scores = [d['overall_quality'] for d in data if d['overall_quality']]
        average_quality_score = statistics.mean(quality_scores) if quality_scores else 0.0
        
        # Quality distribution
        quality_distribution = {
            'Poor (0-0.3)': sum(1 for q in quality_scores if 0 <= q < 0.3),
            'Fair (0.3-0.6)': sum(1 for q in quality_scores if 0.3 <= q < 0.6),
            'Good (0.6-0.8)': sum(1 for q in quality_scores if 0.6 <= q < 0.8),
            'Excellent (0.8-1.0)': sum(1 for q in quality_scores if 0.8 <= q <= 1.0)
        }
        
        low_quality_count = sum(1 for q in quality_scores if q < 0.5)
        high_quality_count = sum(1 for q in quality_scores if q >= 0.8)
        
        return QualityMetrics(
            average_quality_score=average_quality_score,
            quality_distribution=quality_distribution,
            low_quality_count=low_quality_count,
            high_quality_count=high_quality_count,
            quality_trends=quality_scores[-50:] if len(quality_scores) > 50 else quality_scores
        )
    
    def calculate_usage_metrics(self, days: int = 30) -> UsageMetrics:
        """Calculate usage metrics"""
        data = self.database.get_usage_data(days)
        
        if not data:
            return UsageMetrics(
                total_sessions=0,
                active_users=0,
                peak_usage_time="N/A",
                usage_by_hour={},
                usage_by_day={},
                average_session_duration=0.0
            )
        
        total_sessions = len(data)
        active_users = len({d['ip_address'] for d in data if d['ip_address']})
        
        # Calculate usage by hour
        usage_by_hour = defaultdict(int)
        for d in data:
            if d['start_time']:
                try:
                    dt = datetime.fromisoformat(d['start_time'])
                    usage_by_hour[dt.hour] += 1
                except (ValueError, TypeError):
                    pass
        
        # Peak usage time
        peak_hour = max(usage_by_hour.items(), key=lambda x: x[1])[0] if usage_by_hour else 0
        peak_usage_time = f"{peak_hour:02d}:00"
        
        # Usage by day
        usage_by_day = defaultdict(int)
        for d in data:
            if d['start_time']:
                try:
                    dt = datetime.fromisoformat(d['start_time'])
                    usage_by_day[dt.strftime('%A')] += 1
                except (ValueError, TypeError):
                    pass
        
        # Average session duration
        durations = [d['duration'] for d in data if d['duration']]
        average_session_duration = statistics.mean(durations) if durations else 0.0
        
        return UsageMetrics(
            total_sessions=total_sessions,
            active_users=active_users,
            peak_usage_time=peak_usage_time,
            usage_by_hour=dict(usage_by_hour),
            usage_by_day=dict(usage_by_day),
            average_session_duration=average_session_duration
        )
    
    def generate_business_insights(self, days: int = 30) -> BusinessInsights:
        """Generate business intelligence insights"""
        processing_metrics = self.calculate_processing_metrics(days)
        quality_metrics = self.calculate_quality_metrics(days)
        
        # Document type trends (simplified)
        document_type_trends = {}
        for doc_type, count in processing_metrics.documents_by_type.items():
            document_type_trends[doc_type] = [count]  # In real implementation, this would be historical data
        
        # Processing efficiency
        processing_efficiency = processing_metrics.success_rate / 100
        
        # Cost analysis (simplified)
        cost_per_document = 0.05  # Example cost
        total_cost = processing_metrics.total_documents * cost_per_document
        cost_analysis = {
            'total_cost': total_cost,
            'cost_per_document': cost_per_document,
            'cost_per_success': total_cost / processing_metrics.successful_extractions if processing_metrics.successful_extractions > 0 else 0
        }
        
        # User satisfaction (based on quality and success rate)
        user_satisfaction = (quality_metrics.average_quality_score + processing_efficiency) / 2
        
        # Generate recommendations
        recommendations = []
        
        if processing_metrics.success_rate < 80:
            recommendations.append("Improve OCR accuracy - success rate below 80%")
        
        if quality_metrics.average_quality_score < 0.6:
            recommendations.append("Implement image quality guidelines for users")
        
        if processing_metrics.average_processing_time > 10:
            recommendations.append("Optimize processing pipeline - average time too high")
        
        if quality_metrics.low_quality_count > quality_metrics.high_quality_count:
            recommendations.append("Focus on image enhancement algorithms")
        
        if not recommendations:
            recommendations.append("System performance is optimal")
        
        return BusinessInsights(
            document_type_trends=document_type_trends,
            processing_efficiency=processing_efficiency,
            cost_analysis=cost_analysis,
            user_satisfaction=user_satisfaction,
            recommendations=recommendations
        )

class VisualizationGenerator:
    """Generate visualizations for analytics dashboard"""
    
    def __init__(self, output_dir: str = "analytics_charts"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Set style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
    
    def generate_processing_charts(self, metrics: ProcessingMetrics) -> List[str]:
        """Generate processing performance charts"""
        charts = []
        
        # 1. Document types pie chart
        if metrics.documents_by_type:
            plt.figure(figsize=(10, 8))
            plt.pie(metrics.documents_by_type.values(), 
                   labels=list(metrics.documents_by_type.keys()), 
                   autopct='%1.1f%%',
                   startangle=90)
            plt.title('Document Types Distribution')
            chart_path = self.output_dir / 'document_types.png'
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            charts.append(str(chart_path))
        
        # 2. Processing times histogram
        if metrics.processing_times:
            plt.figure(figsize=(12, 6))
            plt.hist(metrics.processing_times, bins=30, alpha=0.7, edgecolor='black')
            plt.title('Processing Time Distribution')
            plt.xlabel('Processing Time (seconds)')
            plt.ylabel('Frequency')
            plt.axvline(metrics.average_processing_time, color='red', linestyle='--', 
                       label=f'Average: {metrics.average_processing_time:.2f}s')
            plt.legend()
            chart_path = self.output_dir / 'processing_times.png'
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            charts.append(str(chart_path))
        
        # 3. Success rate gauge (simplified as bar chart)
        plt.figure(figsize=(8, 6))
        categories = ['Success', 'Failure']
        values = [metrics.successful_extractions, metrics.failed_extractions]
        colors = ['green', 'red']
        plt.bar(categories, values, color=colors, alpha=0.7)
        plt.title(f'Success Rate: {metrics.success_rate:.1f}%')
        plt.ylabel('Number of Documents')
        for i, v in enumerate(values):
            plt.text(i, v + max(values) * 0.01, str(v), ha='center', va='bottom')
        chart_path = self.output_dir / 'success_rate.png'
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        charts.append(str(chart_path))
        
        return charts
    
    def generate_quality_charts(self, metrics: QualityMetrics) -> List[str]:
        """Generate quality analysis charts"""
        charts = []
        
        # 1. Quality distribution
        if metrics.quality_distribution:
            plt.figure(figsize=(10, 6))
            categories = list(metrics.quality_distribution.keys())
            values = list(metrics.quality_distribution.values())
            bars = plt.bar(categories, values, alpha=0.7)
            plt.title('Quality Score Distribution')
            plt.ylabel('Number of Documents')
            plt.xticks(rotation=45)
            
            # Add value labels on bars
            for bar, value in zip(bars, values):
                plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(values) * 0.01,
                        str(value), ha='center', va='bottom')
            
            chart_path = self.output_dir / 'quality_distribution.png'
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            charts.append(str(chart_path))
        
        # 2. Quality trends
        if metrics.quality_trends:
            plt.figure(figsize=(12, 6))
            plt.plot(metrics.quality_trends, marker='o', markersize=4, alpha=0.7)
            plt.title('Quality Score Trends')
            plt.xlabel('Document Number')
            plt.ylabel('Quality Score')
            plt.axhline(metrics.average_quality_score, color='red', linestyle='--',
                       label=f'Average: {metrics.average_quality_score:.3f}')
            plt.legend()
            plt.grid(True, alpha=0.3)
            chart_path = self.output_dir / 'quality_trends.png'
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            charts.append(str(chart_path))
        
        return charts
    
    def generate_usage_charts(self, metrics: UsageMetrics) -> List[str]:
        """Generate usage analysis charts"""
        charts = []
        
        # 1. Usage by hour
        if metrics.usage_by_hour:
            plt.figure(figsize=(12, 6))
            hours = list(range(24))
            usage_counts = [metrics.usage_by_hour.get(h, 0) for h in hours]
            plt.bar(hours, usage_counts, alpha=0.7)
            plt.title('Usage by Hour of Day')
            plt.xlabel('Hour of Day')
            plt.ylabel('Number of Sessions')
            plt.xticks(hours)
            chart_path = self.output_dir / 'usage_by_hour.png'
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            charts.append(str(chart_path))
        
        # 2. Usage by day
        if metrics.usage_by_day:
            plt.figure(figsize=(10, 6))
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            usage_counts = [metrics.usage_by_day.get(day, 0) for day in days]
            plt.bar(days, usage_counts, alpha=0.7)
            plt.title('Usage by Day of Week')
            plt.xlabel('Day of Week')
            plt.ylabel('Number of Sessions')
            plt.xticks(rotation=45)
            chart_path = self.output_dir / 'usage_by_day.png'
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            charts.append(str(chart_path))
        
        return charts

class AnalyticsDashboard:
    """Main analytics dashboard system"""
    
    def __init__(self, db_path: str = "analytics.db"):
        self.database = AnalyticsDatabase(db_path)
        self.processor = AnalyticsProcessor(self.database)
        self.visualizer = VisualizationGenerator()
        
    def log_processing_event(self, event_data: Dict[str, Any]):
        """Log a processing event"""
        self.database.log_processing_event(event_data)
    
    def log_quality_metrics(self, metrics_data: Dict[str, Any]):
        """Log quality metrics"""
        self.database.log_quality_metrics(metrics_data)
    
    def log_usage_session(self, session_data: Dict[str, Any]):
        """Log usage session"""
        self.database.log_usage_session(session_data)
    
    def generate_analytics_report(self, days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive analytics report"""
        logger.info(f"Generating analytics report for last {days} days...")
        
        # Calculate metrics
        processing_metrics = self.processor.calculate_processing_metrics(days)
        quality_metrics = self.processor.calculate_quality_metrics(days)
        usage_metrics = self.processor.calculate_usage_metrics(days)
        business_insights = self.processor.generate_business_insights(days)
        
        # Generate visualizations
        processing_charts = self.visualizer.generate_processing_charts(processing_metrics)
        quality_charts = self.visualizer.generate_quality_charts(quality_metrics)
        usage_charts = self.visualizer.generate_usage_charts(usage_metrics)
        
        # Compile report
        report = {
            'report_generated': datetime.now().isoformat(),
            'analysis_period_days': days,
            'processing_metrics': asdict(processing_metrics),
            'quality_metrics': asdict(quality_metrics),
            'usage_metrics': asdict(usage_metrics),
            'business_insights': asdict(business_insights),
            'charts': {
                'processing': processing_charts,
                'quality': quality_charts,
                'usage': usage_charts
            }
        }
        
        # Save report
        report_path = Path(f"analytics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Analytics report saved to {report_path}")
        return report
    
    def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get real-time metrics for dashboard"""
        return {
            'processing_metrics': asdict(self.processor.calculate_processing_metrics(1)),
            'quality_metrics': asdict(self.processor.calculate_quality_metrics(1)),
            'usage_metrics': asdict(self.processor.calculate_usage_metrics(1)),
            'timestamp': datetime.now().isoformat()
        }
    
    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get dashboard summary"""
        processing_metrics = self.processor.calculate_processing_metrics(30)
        quality_metrics = self.processor.calculate_quality_metrics(30)
        usage_metrics = self.processor.calculate_usage_metrics(30)
        
        return {
            'total_documents': processing_metrics.total_documents,
            'success_rate': processing_metrics.success_rate,
            'average_processing_time': processing_metrics.average_processing_time,
            'average_quality_score': quality_metrics.average_quality_score,
            'total_sessions': usage_metrics.total_sessions,
            'active_users': usage_metrics.active_users,
            'peak_usage_time': usage_metrics.peak_usage_time
        }

# Usage example and testing
if __name__ == "__main__":
    print("📊 ANALYTICS DASHBOARD - INITIALIZATION")
    print("=" * 60)
    
    # Initialize dashboard
    dashboard = AnalyticsDashboard()
    
    # Generate sample data for testing
    print("\n🎯 GENERATING SAMPLE DATA...")
    import random
    
    # Sample processing events
    document_types = ['Aadhaar Card', 'PAN Card', 'Passport', 'Driving License', 'Voter ID']
    
    for i in range(100):
        dashboard.log_processing_event({
            'session_id': f'session_{i // 10}',
            'document_type': random.choice(document_types),
            'processing_time': random.uniform(1, 15),
            'confidence_score': random.uniform(0.3, 0.95),
            'quality_score': random.uniform(0.2, 0.9),
            'success': random.choice([True, True, True, False]),  # 75% success rate
            'error_message': None if random.random() > 0.25 else 'Processing error',
            'file_size': random.randint(100000, 2000000),
            'image_width': random.randint(800, 2400),
            'image_height': random.randint(600, 1800),
            'extracted_fields': {'name': 'Sample Name', 'number': '123456789'},
            'user_agent': 'Mozilla/5.0 Test',
            'ip_address': f'192.168.1.{random.randint(1, 254)}'
        })
    
    # Sample quality metrics
    for i in range(100):
        dashboard.log_quality_metrics({
            'session_id': f'session_{i // 10}',
            'sharpness': random.uniform(0.1, 0.9),
            'brightness': random.uniform(0.2, 0.8),
            'contrast': random.uniform(0.3, 0.9),
            'noise_level': random.uniform(0.1, 0.7),
            'overall_quality': random.uniform(0.2, 0.9)
        })
    
    # Sample usage sessions
    for i in range(20):
        dashboard.log_usage_session({
            'session_id': f'session_{i}',
            'start_time': datetime.now().isoformat(),
            'end_time': (datetime.now() + timedelta(minutes=random.randint(5, 60))).isoformat(),
            'duration': random.uniform(300, 3600),
            'documents_processed': random.randint(1, 10),
            'user_agent': 'Mozilla/5.0 Test',
            'ip_address': f'192.168.1.{random.randint(1, 254)}'
        })
    
    print("   ✅ Sample data generated")
    
    # Generate analytics report
    print("\n📈 GENERATING ANALYTICS REPORT...")
    report = dashboard.generate_analytics_report(30)
    
    # Display summary
    print("\n📋 DASHBOARD SUMMARY:")
    summary = dashboard.get_dashboard_summary()
    print(f"   📄 Total Documents: {summary['total_documents']}")
    print(f"   ✅ Success Rate: {summary['success_rate']:.1f}%")
    print(f"   ⏱️  Average Processing Time: {summary['average_processing_time']:.2f}s")
    print(f"   🎯 Average Quality Score: {summary['average_quality_score']:.3f}")
    print(f"   👥 Total Sessions: {summary['total_sessions']}")
    print(f"   🌐 Active Users: {summary['active_users']}")
    print(f"   📊 Peak Usage Time: {summary['peak_usage_time']}")
    
    # Business insights
    print("\n💡 BUSINESS INSIGHTS:")
    insights = report['business_insights']
    print(f"   📊 Processing Efficiency: {insights['processing_efficiency']:.1%}")
    print(f"   💰 Total Cost: ${insights['cost_analysis']['total_cost']:.2f}")
    print(f"   😊 User Satisfaction: {insights['user_satisfaction']:.1%}")
    print("   📈 Recommendations:")
    for rec in insights['recommendations']:
        print(f"      • {rec}")
    
    print("\n✅ ANALYTICS DASHBOARD READY!")
    print("   • Comprehensive performance monitoring")
    print("   • Quality assessment and trending")
    print("   • Usage analytics and insights")
    print("   • Business intelligence reporting")
    print("   • Automated visualization generation")
    print("   • Real-time metrics and dashboards")
