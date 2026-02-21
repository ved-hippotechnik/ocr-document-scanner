#!/usr/bin/env python3
"""
Complete Enhanced OCR Document Scanner Integration
Combines all enhancement phases into a unified system
"""

import os
import sys
import json
import time
import logging
import io
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import asyncio
import uuid

# Import all our enhancement modules
from ml_document_classifier import MLDocumentClassifier
from security_validator import DocumentSecurityValidator
from realtime_processor import WebSocketOCRServer
from analytics_dashboard import AnalyticsDashboard

# Additional imports for integration
import cv2
import numpy as np
from PIL import Image
import pytesseract
import requests
from flask import Flask, request, jsonify, render_template_string, send_file
from flask_cors import CORS
import threading
import signal
import socket
import webbrowser

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedOCRSystem:
    """
    Complete enhanced OCR system with all improvements:
    - ML-powered document classification
    - Security validation and fraud detection
    - Real-time processing capabilities
    - Analytics dashboard and business intelligence
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the enhanced OCR system"""
        self.config = config or {}
        self.session_id = str(uuid.uuid4())
        
        # Initialize components
        self.ml_classifier = MLDocumentClassifier()
        self.security_validator = DocumentSecurityValidator()
        self.analytics_dashboard = AnalyticsDashboard()
        self.realtime_server = None
        
        # Performance tracking
        self.performance_metrics = {
            'total_processed': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            'total_processing_time': 0.0,
            'ml_predictions': 0,
            'security_validations': 0,
            'fraud_detections': 0
        }
        
        # Flask app for web interface
        self.app = Flask(__name__)
        CORS(self.app)
        self.setup_routes()
        
        logger.info("Enhanced OCR System initialized successfully")
    
    def setup_routes(self):
        """Setup Flask routes for web interface"""
        
        @self.app.route('/')
        def index():
            """Main dashboard page"""
            return render_template_string(DASHBOARD_HTML)
        
        @self.app.route('/api/upload', methods=['POST'])
        def upload_document():
            """Upload and process document"""
            try:
                if 'file' not in request.files:
                    return jsonify({'error': 'No file uploaded'}), 400
                
                file = request.files['file']
                if file.filename == '':
                    return jsonify({'error': 'No file selected'}), 400
                
                # Process the document
                result = self.process_document_complete(file)
                
                return jsonify(result)
                
            except Exception as e:
                logger.error(f"Upload error: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/analytics/dashboard')
        def get_analytics_dashboard():
            """Get analytics dashboard data"""
            try:
                summary = self.analytics_dashboard.get_dashboard_summary()
                real_time_metrics = self.analytics_dashboard.get_real_time_metrics()
                
                return jsonify({
                    'summary': summary,
                    'real_time_metrics': real_time_metrics,
                    'performance_metrics': self.performance_metrics
                })
                
            except Exception as e:
                logger.error(f"Analytics error: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/analytics/report')
        def generate_analytics_report():
            """Generate comprehensive analytics report"""
            try:
                days = request.args.get('days', 30, type=int)
                report = self.analytics_dashboard.generate_analytics_report(days)
                
                return jsonify(report)
                
            except Exception as e:
                logger.error(f"Report generation error: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/performance/metrics')
        def get_performance_metrics():
            """Get current performance metrics"""
            return jsonify(self.performance_metrics)
        
        @self.app.route('/api/status')
        def get_system_status():
            """Get system status"""
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'components': {
                    'ml_classifier': 'ready',
                    'security_validator': 'ready',
                    'analytics_dashboard': 'ready',
                    'realtime_server': 'ready' if self.realtime_server else 'inactive'
                },
                'session_id': self.session_id
            })
    
    def process_document_complete(self, file_data) -> Dict[str, Any]:
        """
        Complete document processing pipeline with all enhancements
        """
        start_time = time.time()
        result = {
            'success': False,
            'session_id': self.session_id,
            'processing_time': 0.0,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Read image
            if hasattr(file_data, 'read'):
                image_data = file_data.read()
            else:
                image_data = file_data
            
            # Convert to PIL Image
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to OpenCV format
            opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Phase 1: ML Classification
            logger.info("Phase 1: ML Document Classification")
            classification_result = self.ml_classifier.classify_document(opencv_image, "")
            self.performance_metrics['ml_predictions'] += 1
            
            result['classification'] = classification_result
            
            # Phase 2: Security Validation
            logger.info("Phase 2: Security Validation")
            security_result = self.security_validator.validate_document_security(opencv_image, "")
            self.performance_metrics['security_validations'] += 1
            
            # Check for fraud - using simplified approach
            if hasattr(security_result, 'authenticity_score') and security_result.authenticity_score < 0.3:
                self.performance_metrics['fraud_detections'] += 1
            
            result['security'] = security_result.__dict__ if hasattr(security_result, '__dict__') else security_result
            
            # Phase 3: Enhanced OCR Extraction
            logger.info("Phase 3: Enhanced OCR Extraction")
            predicted_class = getattr(classification_result, 'predicted_class', 'Unknown')
            ocr_result = self.perform_enhanced_ocr(opencv_image, predicted_class)
            
            result['ocr'] = ocr_result
            
            # Phase 4: Quality Assessment
            logger.info("Phase 4: Quality Assessment")
            quality_result = self.assess_document_quality(opencv_image)
            
            result['quality'] = quality_result
            
            # Final processing
            processing_time = time.time() - start_time
            result['processing_time'] = processing_time
            result['success'] = True
            
            # Update performance metrics
            self.performance_metrics['total_processed'] += 1
            self.performance_metrics['successful_extractions'] += 1
            self.performance_metrics['total_processing_time'] += processing_time
            
            # Log to analytics
            self.log_processing_event(result, file_data)
            
            logger.info(f"Document processed successfully in {processing_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Processing error: {str(e)}")
            result['error'] = str(e)
            result['processing_time'] = time.time() - start_time
            
            # Update failure metrics
            self.performance_metrics['failed_extractions'] += 1
            
            # Log error to analytics
            self.log_processing_event(result, file_data)
        
        return result
    
    def perform_enhanced_ocr(self, image: np.ndarray, document_type: str) -> Dict[str, Any]:
        """Enhanced OCR with document-specific processing"""
        try:
            # Basic OCR
            text = pytesseract.image_to_string(image)
            
            # Document-specific field extraction
            extracted_fields = self.extract_document_fields(text, document_type)
            
            # Confidence scoring
            confidence = self.calculate_ocr_confidence(image, text)
            
            return {
                'text': text,
                'extracted_fields': extracted_fields,
                'confidence': confidence,
                'document_type': document_type
            }
            
        except Exception as e:
            logger.error(f"OCR error: {str(e)}")
            return {
                'text': '',
                'extracted_fields': {},
                'confidence': 0.0,
                'error': str(e)
            }
    
    def extract_document_fields(self, text: str, document_type: str) -> Dict[str, Any]:
        """Extract specific fields based on document type"""
        import re
        fields = {}
        
        if document_type == 'Aadhaar Card':
            # Extract Aadhaar number (12 digits)
            aadhaar_pattern = r'\b\d{4}\s*\d{4}\s*\d{4}\b'
            match = re.search(aadhaar_pattern, text)
            if match:
                fields['aadhaar_number'] = match.group().replace(' ', '')
            
            # Extract name (simple heuristic)
            lines = text.split('\n')
            for line in lines:
                if len(line.strip()) > 5 and any(char.isalpha() for char in line):
                    fields['name'] = line.strip()
                    break
        
        elif document_type == 'PAN Card':
            # Extract PAN number
            pan_pattern = r'\b[A-Z]{5}\d{4}[A-Z]\b'
            match = re.search(pan_pattern, text)
            if match:
                fields['pan_number'] = match.group()
        
        elif document_type == 'Passport':
            # Extract passport number
            passport_pattern = r'\b[A-Z]\d{7}\b'
            match = re.search(passport_pattern, text)
            if match:
                fields['passport_number'] = match.group()
        
        return fields
    
    def calculate_ocr_confidence(self, image: np.ndarray, text: str) -> float:
        """Calculate OCR confidence score"""
        try:
            # Simple confidence calculation based on text quality
            if not text or len(text.strip()) < 5:
                return 0.0
            
            # Factor in image quality
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Normalize sharpness to 0-1 range
            sharpness_score = min(sharpness / 1000.0, 1.0)
            
            # Factor in text characteristics
            text_score = min(len(text.strip()) / 100.0, 1.0)
            
            # Combine factors
            confidence = (sharpness_score + text_score) / 2.0
            
            return min(confidence, 1.0)
            
        except Exception as e:
            logger.error(f"Confidence calculation error: {str(e)}")
            return 0.5  # Default confidence
    
    def assess_document_quality(self, image: np.ndarray) -> Dict[str, Any]:
        """Assess document image quality"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Sharpness (Laplacian variance)
            sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Brightness
            brightness = cv2.mean(gray)[0]
            
            # Contrast
            contrast = cv2.meanStdDev(gray)[1][0][0]
            
            # Normalize scores
            sharpness_score = min(sharpness / 1000.0, 1.0)
            brightness_score = 1.0 - abs(brightness - 127.5) / 127.5
            contrast_score = min(contrast / 64.0, 1.0)
            
            # Overall quality
            overall_quality = (sharpness_score + brightness_score + contrast_score) / 3.0
            
            return {
                'sharpness': sharpness_score,
                'brightness': brightness_score,
                'contrast': contrast_score,
                'overall_quality': overall_quality,
                'quality_grade': self.get_quality_grade(overall_quality)
            }
            
        except Exception as e:
            logger.error(f"Quality assessment error: {str(e)}")
            return {
                'sharpness': 0.0,
                'brightness': 0.0,
                'contrast': 0.0,
                'overall_quality': 0.0,
                'quality_grade': 'Poor'
            }
    
    def get_quality_grade(self, score: float) -> str:
        """Get quality grade from score"""
        if score >= 0.8:
            return 'Excellent'
        elif score >= 0.6:
            return 'Good'
        elif score >= 0.4:
            return 'Fair'
        else:
            return 'Poor'
    
    def log_processing_event(self, result: Dict[str, Any], file_data):
        """Log processing event to analytics"""
        try:
            event_data = {
                'session_id': self.session_id,
                'document_type': result.get('classification', {}).get('predicted_class', 'Unknown'),
                'processing_time': result.get('processing_time', 0.0),
                'confidence_score': result.get('ocr', {}).get('confidence', 0.0),
                'quality_score': result.get('quality', {}).get('overall_quality', 0.0),
                'success': result.get('success', False),
                'error_message': result.get('error'),
                'file_size': len(file_data.read()) if hasattr(file_data, 'read') else 0,
                'image_width': 0,  # Would need to calculate from image
                'image_height': 0,  # Would need to calculate from image
                'extracted_fields': result.get('ocr', {}).get('extracted_fields', {}),
                'user_agent': 'Enhanced OCR System',
                'ip_address': '127.0.0.1'
            }
            
            self.analytics_dashboard.log_processing_event(event_data)
            
            # Log quality metrics
            if 'quality' in result:
                quality_data = {
                    'session_id': self.session_id,
                    'sharpness': result['quality'].get('sharpness', 0.0),
                    'brightness': result['quality'].get('brightness', 0.0),
                    'contrast': result['quality'].get('contrast', 0.0),
                    'noise_level': 0.0,  # Would need to calculate
                    'overall_quality': result['quality'].get('overall_quality', 0.0)
                }
                
                self.analytics_dashboard.log_quality_metrics(quality_data)
                
        except Exception as e:
            logger.error(f"Analytics logging error: {str(e)}")
    
    def start_realtime_server(self, port: int = 8765):
        """Start the real-time WebSocket server"""
        try:
            self.realtime_server = WebSocketOCRServer(port=port)
            
            # Start server in a separate thread
            def run_server():
                if self.realtime_server and hasattr(self.realtime_server, 'start_server'):
                    asyncio.run(self.realtime_server.start_server())
                else:
                    logger.warning("Real-time server start_server method not available")
            
            server_thread = threading.Thread(target=run_server, daemon=True)
            server_thread.start()
            
            logger.info(f"Real-time server started on port {port}")
            
        except Exception as e:
            logger.error(f"Real-time server error: {str(e)}")
    
    def run_web_interface(self, host: str = '0.0.0.0', port: int = 5000, debug: bool = False):
        """Run the web interface"""
        try:
            # Start real-time server
            self.start_realtime_server(8765)
            
            # Check if port is available
            if not self.is_port_available(port):
                logger.warning(f"Port {port} is busy, trying {port + 1}")
                port += 1
            
            # Open browser
            if not debug:
                def open_browser():
                    time.sleep(1)
                    webbrowser.open(f'http://localhost:{port}')
                
                browser_thread = threading.Thread(target=open_browser, daemon=True)
                browser_thread.start()
            
            logger.info(f"Starting Enhanced OCR System web interface on http://{host}:{port}")
            
            # Run Flask app
            self.app.run(host=host, port=port, debug=debug, use_reloader=False)
            
        except Exception as e:
            logger.error(f"Web interface error: {str(e)}")
    
    def is_port_available(self, port: int) -> bool:
        """Check if port is available"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                return s.connect_ex(('localhost', port)) != 0
        except Exception:
            return False
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive system report"""
        try:
            analytics_report = self.analytics_dashboard.generate_analytics_report(30)
            
            report = {
                'system_info': {
                    'version': '1.0.0',
                    'session_id': self.session_id,
                    'timestamp': datetime.now().isoformat(),
                    'components': {
                        'ml_classifier': 'active',
                        'security_validator': 'active',
                        'analytics_dashboard': 'active',
                        'realtime_server': 'active' if self.realtime_server else 'inactive'
                    }
                },
                'performance_metrics': self.performance_metrics,
                'analytics_report': analytics_report,
                'recommendations': self.get_system_recommendations()
            }
            
            # Save report
            report_path = Path(f"enhanced_ocr_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"Comprehensive report saved to {report_path}")
            return report
            
        except Exception as e:
            logger.error(f"Report generation error: {str(e)}")
            return {'error': str(e)}
    
    def get_system_recommendations(self) -> List[str]:
        """Get system improvement recommendations"""
        recommendations = []
        
        # Performance-based recommendations
        if self.performance_metrics['total_processed'] > 0:
            success_rate = (self.performance_metrics['successful_extractions'] / 
                          self.performance_metrics['total_processed']) * 100
            
            if success_rate < 80:
                recommendations.append("Consider improving image preprocessing algorithms")
            
            avg_processing_time = (self.performance_metrics['total_processing_time'] / 
                                 self.performance_metrics['total_processed'])
            
            if avg_processing_time > 10:
                recommendations.append("Optimize processing pipeline for better performance")
        
        # Component-specific recommendations
        if self.performance_metrics['fraud_detections'] > 0:
            recommendations.append("Review security protocols due to fraud detections")
        
        if not recommendations:
            recommendations.append("System is performing optimally")
        
        return recommendations

# HTML template for the web interface
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Enhanced OCR Document Scanner</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
        .header h1 { margin: 0; font-size: 2.5em; }
        .header p { margin: 5px 0 0 0; opacity: 0.9; }
        .dashboard { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
        .card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .card h3 { margin-top: 0; color: #333; }
        .upload-area { border: 2px dashed #ccc; padding: 40px; text-align: center; border-radius: 10px; margin-bottom: 20px; cursor: pointer; }
        .upload-area:hover { border-color: #667eea; background-color: #f9f9f9; }
        .button { background: #667eea; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
        .button:hover { background: #5a67d8; }
        .results { background: white; padding: 20px; border-radius: 10px; margin-top: 20px; }
        .progress { width: 100%; height: 20px; background: #e0e0e0; border-radius: 10px; overflow: hidden; margin: 10px 0; }
        .progress-bar { height: 100%; background: #4caf50; transition: width 0.3s ease; }
        .metric { text-align: center; padding: 10px; }
        .metric-value { font-size: 2em; font-weight: bold; color: #667eea; }
        .metric-label { color: #666; }
        .status-indicator { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 5px; }
        .status-active { background-color: #4caf50; }
        .status-inactive { background-color: #f44336; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Enhanced OCR Document Scanner</h1>
            <p>Advanced ML Classification • Security Validation • Real-time Processing • Analytics Dashboard</p>
        </div>
        
        <div class="dashboard">
            <div class="card">
                <h3>📊 System Status</h3>
                <div id="systemStatus">
                    <div><span class="status-indicator status-active"></span>ML Classifier: Ready</div>
                    <div><span class="status-indicator status-active"></span>Security Validator: Ready</div>
                    <div><span class="status-indicator status-active"></span>Analytics Dashboard: Ready</div>
                    <div><span class="status-indicator status-active"></span>Real-time Server: Active</div>
                </div>
            </div>
            
            <div class="card">
                <h3>📈 Performance Metrics</h3>
                <div class="metric">
                    <div class="metric-value" id="totalProcessed">0</div>
                    <div class="metric-label">Documents Processed</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="successRate">0%</div>
                    <div class="metric-label">Success Rate</div>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h3>📤 Upload Document</h3>
            <div class="upload-area" onclick="document.getElementById('fileInput').click()">
                <p>Click to upload or drag and drop your document</p>
                <p style="color: #666;">Supported formats: JPG, PNG, PDF</p>
            </div>
            <input type="file" id="fileInput" accept="image/*,.pdf" style="display: none;" onchange="uploadFile(this)">
            <button class="button" onclick="document.getElementById('fileInput').click()">Select File</button>
        </div>
        
        <div id="results" class="results" style="display: none;">
            <h3>🔍 Processing Results</h3>
            <div id="resultsContent"></div>
        </div>
    </div>
    
    <script>
        // Load system metrics
        function loadMetrics() {
            fetch('/api/performance/metrics')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('totalProcessed').textContent = data.total_processed;
                    const successRate = data.total_processed > 0 ? 
                        Math.round((data.successful_extractions / data.total_processed) * 100) : 0;
                    document.getElementById('successRate').textContent = successRate + '%';
                });
        }
        
        // Upload file
        function uploadFile(input) {
            const file = input.files[0];
            if (!file) return;
            
            const formData = new FormData();
            formData.append('file', file);
            
            document.getElementById('results').style.display = 'block';
            document.getElementById('resultsContent').innerHTML = '<div class="progress"><div class="progress-bar" style="width: 0%"></div></div><p>Processing document...</p>';
            
            // Simulate progress
            let progress = 0;
            const progressInterval = setInterval(() => {
                progress += 10;
                document.querySelector('.progress-bar').style.width = progress + '%';
                if (progress >= 90) clearInterval(progressInterval);
            }, 200);
            
            fetch('/api/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                clearInterval(progressInterval);
                document.querySelector('.progress-bar').style.width = '100%';
                
                setTimeout(() => {
                    displayResults(data);
                    loadMetrics();
                }, 500);
            })
            .catch(error => {
                clearInterval(progressInterval);
                document.getElementById('resultsContent').innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
            });
        }
        
        // Display results
        function displayResults(data) {
            const resultsHtml = `
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                    <div>
                        <h4>🤖 ML Classification</h4>
                        <p><strong>Document Type:</strong> ${data.classification?.predicted_class || 'Unknown'}</p>
                        <p><strong>Confidence:</strong> ${Math.round((data.classification?.confidence || 0) * 100)}%</p>
                    </div>
                    <div>
                        <h4>🔒 Security Validation</h4>
                        <p><strong>Risk Level:</strong> <span style="color: ${data.security?.risk_level === 'LOW' ? 'green' : data.security?.risk_level === 'MEDIUM' ? 'orange' : 'red'};">${data.security?.risk_level || 'Unknown'}</span></p>
                        <p><strong>Authenticity Score:</strong> ${Math.round((data.security?.authenticity_score || 0) * 100)}%</p>
                    </div>
                    <div>
                        <h4>📝 OCR Extraction</h4>
                        <p><strong>Confidence:</strong> ${Math.round((data.ocr?.confidence || 0) * 100)}%</p>
                        <p><strong>Fields Extracted:</strong> ${Object.keys(data.ocr?.extracted_fields || {}).length}</p>
                    </div>
                    <div>
                        <h4>🎯 Quality Assessment</h4>
                        <p><strong>Quality Grade:</strong> ${data.quality?.quality_grade || 'Unknown'}</p>
                        <p><strong>Overall Score:</strong> ${Math.round((data.quality?.overall_quality || 0) * 100)}%</p>
                    </div>
                </div>
                <div style="margin-top: 20px;">
                    <h4>⏱️ Processing Details</h4>
                    <p><strong>Processing Time:</strong> ${data.processing_time?.toFixed(2) || 0}s</p>
                    <p><strong>Status:</strong> <span style="color: ${data.success ? 'green' : 'red'};">${data.success ? 'Success' : 'Failed'}</span></p>
                </div>
            `;
            
            document.getElementById('resultsContent').innerHTML = resultsHtml;
        }
        
        // Load initial metrics
        loadMetrics();
        
        // Refresh metrics every 30 seconds
        setInterval(loadMetrics, 30000);
    </script>
</body>
</html>
"""

# Main execution
if __name__ == "__main__":
    print("🚀 ENHANCED OCR DOCUMENT SCANNER - COMPLETE INTEGRATION")
    print("=" * 80)
    
    # Initialize the enhanced system
    enhanced_ocr = EnhancedOCRSystem()
    
    print("\n✅ SYSTEM COMPONENTS INITIALIZED:")
    print("   🤖 ML Document Classifier - Ready")
    print("   🔒 Security Validator - Ready")
    print("   📊 Analytics Dashboard - Ready")
    print("   ⚡ Real-time Processor - Ready")
    
    print("\n🌐 STARTING WEB INTERFACE...")
    print("   📱 Dashboard: http://localhost:5000")
    print("   🔗 WebSocket: ws://localhost:8765")
    print("   📊 Analytics: http://localhost:5000/api/analytics/dashboard")
    
    try:
        # Start the enhanced OCR system
        enhanced_ocr.run_web_interface(debug=False)
        
    except KeyboardInterrupt:
        print("\n\n🛑 SHUTTING DOWN...")
        print("   ✅ Enhanced OCR System stopped")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        sys.exit(1)
