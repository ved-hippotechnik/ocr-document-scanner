#!/usr/bin/env python3
"""
Production-ready Flask application for Enhanced OCR Document Scanner
Integrates all enhancement phases for production deployment
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string, send_file, redirect, url_for
from flask_cors import CORS
import tempfile
import uuid
import cv2
import numpy as np
from PIL import Image
import io
import base64

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our enhanced system components
try:
    from enhanced_ocr_complete import EnhancedOCRSystem
    from ml_document_classifier import MLDocumentClassifier
    from security_validator import DocumentSecurityValidator
    from analytics_dashboard import AnalyticsDashboard
    ENHANCED_SYSTEM_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Enhanced system not available: {e}")
    ENHANCED_SYSTEM_AVAILABLE = False

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ocr_scanner.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'ocr-scanner-secret-key-production')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()

# Enable CORS for all routes
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Initialize enhanced OCR system if available
enhanced_ocr = None
if ENHANCED_SYSTEM_AVAILABLE:
    try:
        enhanced_ocr = EnhancedOCRSystem()
        logger.info("Enhanced OCR System initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize enhanced OCR system: {e}")
        enhanced_ocr = None

# Basic OCR fallback system
class BasicOCRSystem:
    """Basic OCR system for fallback when enhanced system is unavailable"""
    
    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.performance_metrics = {
            'total_processed': 0,
            'successful_extractions': 0,
            'failed_extractions': 0
        }
    
    def process_document_complete(self, file_data):
        """Basic document processing"""
        try:
            # Read image
            image_bytes = file_data.read()
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to OpenCV format
            opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Basic OCR
            import pytesseract
            text = pytesseract.image_to_string(opencv_image)
            
            # Basic classification
            classification = self.classify_document_basic(text)
            
            result = {
                'success': True,
                'session_id': self.session_id,
                'classification': {'predicted_class': classification, 'confidence': 0.7},
                'ocr': {'text': text, 'confidence': 0.7, 'extracted_fields': {}},
                'security': {'authenticity_score': 0.5, 'risk_level': 'MEDIUM'},
                'quality': {'overall_quality': 0.6, 'quality_grade': 'Good'},
                'processing_time': 1.0
            }
            
            self.performance_metrics['total_processed'] += 1
            self.performance_metrics['successful_extractions'] += 1
            
            return result
            
        except Exception as e:
            logger.error(f"Basic OCR processing error: {e}")
            self.performance_metrics['failed_extractions'] += 1
            return {
                'success': False,
                'error': str(e),
                'session_id': self.session_id
            }
    
    def classify_document_basic(self, text):
        """Basic document classification"""
        text_lower = text.lower()
        
        if 'aadhaar' in text_lower or 'आधार' in text_lower:
            return 'Aadhaar Card'
        elif 'pan' in text_lower or 'permanent account number' in text_lower:
            return 'PAN Card'
        elif 'passport' in text_lower:
            return 'Passport'
        elif 'driving' in text_lower or 'license' in text_lower:
            return 'Driving License'
        else:
            return 'Unknown Document'
    
    def get_dashboard_summary(self):
        """Basic dashboard summary"""
        return {
            'total_documents': self.performance_metrics['total_processed'],
            'success_rate': (self.performance_metrics['successful_extractions'] / 
                           max(self.performance_metrics['total_processed'], 1)) * 100,
            'average_processing_time': 1.0,
            'system_status': 'Basic OCR Mode'
        }

# Initialize OCR system (enhanced or basic)
ocr_system = enhanced_ocr if enhanced_ocr else BasicOCRSystem()

# Web interface HTML template
MAIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Enhanced OCR Document Scanner</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            min-height: 100vh; 
            color: #333; 
        }
        .container { 
            max-width: 1200px; 
            margin: 0 auto; 
            padding: 20px; 
        }
        .header { 
            text-align: center; 
            color: white; 
            margin-bottom: 30px; 
        }
        .header h1 { 
            font-size: 3rem; 
            margin-bottom: 10px; 
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3); 
        }
        .header p { 
            font-size: 1.2rem; 
            opacity: 0.9; 
        }
        .main-card { 
            background: white; 
            border-radius: 15px; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.2); 
            padding: 40px; 
            margin-bottom: 30px; 
        }
        .upload-area { 
            border: 3px dashed #ddd; 
            border-radius: 10px; 
            padding: 60px 20px; 
            text-align: center; 
            cursor: pointer; 
            transition: all 0.3s ease; 
            margin-bottom: 20px; 
        }
        .upload-area:hover { 
            border-color: #667eea; 
            background: #f8f9ff; 
        }
        .upload-area.dragover { 
            border-color: #667eea; 
            background: #f0f4ff; 
        }
        .upload-icon { 
            font-size: 4rem; 
            color: #667eea; 
            margin-bottom: 20px; 
        }
        .upload-text { 
            font-size: 1.3rem; 
            color: #666; 
            margin-bottom: 10px; 
        }
        .upload-subtext { 
            color: #999; 
            font-size: 0.9rem; 
        }
        .btn { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; 
            border: none; 
            padding: 12px 30px; 
            border-radius: 25px; 
            font-size: 1rem; 
            cursor: pointer; 
            transition: all 0.3s ease; 
            margin: 10px 5px; 
        }
        .btn:hover { 
            transform: translateY(-2px); 
            box-shadow: 0 5px 15px rgba(0,0,0,0.2); 
        }
        .status-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
            gap: 20px; 
            margin-bottom: 30px; 
        }
        .status-card { 
            background: white; 
            padding: 20px; 
            border-radius: 10px; 
            box-shadow: 0 5px 15px rgba(0,0,0,0.1); 
            text-align: center; 
        }
        .status-icon { 
            font-size: 2.5rem; 
            margin-bottom: 10px; 
        }
        .status-value { 
            font-size: 2rem; 
            font-weight: bold; 
            color: #667eea; 
            margin-bottom: 5px; 
        }
        .status-label { 
            color: #666; 
            font-size: 0.9rem; 
        }
        .results { 
            background: white; 
            border-radius: 10px; 
            padding: 20px; 
            margin-top: 20px; 
            box-shadow: 0 5px 15px rgba(0,0,0,0.1); 
            display: none; 
        }
        .progress-bar { 
            width: 100%; 
            height: 6px; 
            background: #e0e0e0; 
            border-radius: 3px; 
            overflow: hidden; 
            margin: 20px 0; 
        }
        .progress-fill { 
            height: 100%; 
            background: linear-gradient(90deg, #667eea, #764ba2); 
            border-radius: 3px; 
            transition: width 0.3s ease; 
            width: 0%; 
        }
        .result-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
            gap: 20px; 
            margin-top: 20px; 
        }
        .result-card { 
            background: #f8f9fa; 
            padding: 20px; 
            border-radius: 8px; 
            border-left: 4px solid #667eea; 
        }
        .result-title { 
            font-size: 1.1rem; 
            font-weight: bold; 
            color: #333; 
            margin-bottom: 10px; 
        }
        .result-item { 
            display: flex; 
            justify-content: space-between; 
            margin-bottom: 8px; 
            padding: 5px 0; 
            border-bottom: 1px solid #eee; 
        }
        .result-item:last-child { 
            border-bottom: none; 
        }
        .badge { 
            padding: 4px 8px; 
            border-radius: 12px; 
            font-size: 0.8rem; 
            font-weight: bold; 
        }
        .badge-success { 
            background: #d4edda; 
            color: #155724; 
        }
        .badge-warning { 
            background: #fff3cd; 
            color: #856404; 
        }
        .badge-danger { 
            background: #f8d7da; 
            color: #721c24; 
        }
        .footer { 
            text-align: center; 
            color: white; 
            margin-top: 40px; 
            padding: 20px; 
            opacity: 0.8; 
        }
        @media (max-width: 768px) {
            .header h1 { font-size: 2rem; }
            .main-card { padding: 20px; }
            .upload-area { padding: 40px 15px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Enhanced OCR Document Scanner</h1>
            <p>Advanced ML Classification • Security Validation • Real-time Processing • Analytics</p>
        </div>
        
        <div class="status-grid">
            <div class="status-card">
                <div class="status-icon">📊</div>
                <div class="status-value" id="totalDocs">0</div>
                <div class="status-label">Documents Processed</div>
            </div>
            <div class="status-card">
                <div class="status-icon">✅</div>
                <div class="status-value" id="successRate">0%</div>
                <div class="status-label">Success Rate</div>
            </div>
            <div class="status-card">
                <div class="status-icon">⚡</div>
                <div class="status-value" id="avgTime">0.0s</div>
                <div class="status-label">Avg Processing Time</div>
            </div>
            <div class="status-card">
                <div class="status-icon">🔒</div>
                <div class="status-value" id="systemStatus">Ready</div>
                <div class="status-label">System Status</div>
            </div>
        </div>
        
        <div class="main-card">
            <div class="upload-area" id="uploadArea">
                <div class="upload-icon">📤</div>
                <div class="upload-text">Drop your document here or click to browse</div>
                <div class="upload-subtext">Supports JPG, PNG, PDF • Max 16MB • All document types</div>
            </div>
            
            <input type="file" id="fileInput" accept="image/*,.pdf" style="display: none;">
            
            <div style="text-align: center;">
                <button class="btn" onclick="document.getElementById('fileInput').click()">
                    📁 Select Document
                </button>
                <button class="btn" onclick="loadMetrics()">
                    📊 Refresh Stats
                </button>
                <button class="btn" onclick="window.open('/api/analytics/dashboard')">
                    📈 View Analytics
                </button>
            </div>
            
            <div id="results" class="results">
                <h3>🔍 Processing Results</h3>
                <div class="progress-bar">
                    <div class="progress-fill" id="progressFill"></div>
                </div>
                <div id="resultsContent"></div>
            </div>
        </div>
        
        <div class="footer">
            <p>Enhanced OCR Document Scanner v2.0 • Built with Python, Flask, OpenCV, TensorFlow</p>
            <p>© 2025 Advanced Document Processing System</p>
        </div>
    </div>
    
    <script>
        // Load initial metrics
        loadMetrics();
        
        // File input handler
        document.getElementById('fileInput').addEventListener('change', handleFileSelect);
        
        // Drag and drop handlers
        const uploadArea = document.getElementById('uploadArea');
        uploadArea.addEventListener('dragover', handleDragOver);
        uploadArea.addEventListener('dragleave', handleDragLeave);
        uploadArea.addEventListener('drop', handleDrop);
        uploadArea.addEventListener('click', () => document.getElementById('fileInput').click());
        
        function handleDragOver(e) {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        }
        
        function handleDragLeave(e) {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
        }
        
        function handleDrop(e) {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                processFile(files[0]);
            }
        }
        
        function handleFileSelect(e) {
            const file = e.target.files[0];
            if (file) {
                processFile(file);
            }
        }
        
        function processFile(file) {
            const formData = new FormData();
            formData.append('file', file);
            
            const results = document.getElementById('results');
            const progressFill = document.getElementById('progressFill');
            const resultsContent = document.getElementById('resultsContent');
            
            results.style.display = 'block';
            resultsContent.innerHTML = '<p>Processing document...</p>';
            
            // Simulate progress
            let progress = 0;
            const progressInterval = setInterval(() => {
                progress += 10;
                progressFill.style.width = progress + '%';
                if (progress >= 90) clearInterval(progressInterval);
            }, 200);
            
            fetch('/api/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                clearInterval(progressInterval);
                progressFill.style.width = '100%';
                setTimeout(() => {
                    displayResults(data);
                    loadMetrics();
                }, 500);
            })
            .catch(error => {
                clearInterval(progressInterval);
                resultsContent.innerHTML = '<p style="color: red;">Error: ' + error.message + '</p>';
            });
        }
        
        function displayResults(data) {
            const resultsContent = document.getElementById('resultsContent');
            
            if (data.success) {
                const classification = data.classification || {};
                const security = data.security || {};
                const ocr = data.ocr || {};
                const quality = data.quality || {};
                
                resultsContent.innerHTML = `
                    <div class="result-grid">
                        <div class="result-card">
                            <div class="result-title">🤖 ML Classification</div>
                            <div class="result-item">
                                <span>Document Type:</span>
                                <span><strong>${classification.predicted_class || 'Unknown'}</strong></span>
                            </div>
                            <div class="result-item">
                                <span>Confidence:</span>
                                <span>${Math.round((classification.confidence || 0) * 100)}%</span>
                            </div>
                        </div>
                        
                        <div class="result-card">
                            <div class="result-title">🔒 Security Validation</div>
                            <div class="result-item">
                                <span>Risk Level:</span>
                                <span class="badge ${getRiskBadgeClass(security.risk_level || 'MEDIUM')}">${security.risk_level || 'MEDIUM'}</span>
                            </div>
                            <div class="result-item">
                                <span>Authenticity:</span>
                                <span>${Math.round((security.authenticity_score || 0) * 100)}%</span>
                            </div>
                        </div>
                        
                        <div class="result-card">
                            <div class="result-title">📝 OCR Extraction</div>
                            <div class="result-item">
                                <span>Text Confidence:</span>
                                <span>${Math.round((ocr.confidence || 0) * 100)}%</span>
                            </div>
                            <div class="result-item">
                                <span>Fields Extracted:</span>
                                <span>${Object.keys(ocr.extracted_fields || {}).length}</span>
                            </div>
                        </div>
                        
                        <div class="result-card">
                            <div class="result-title">🎯 Quality Assessment</div>
                            <div class="result-item">
                                <span>Quality Grade:</span>
                                <span class="badge badge-success">${quality.quality_grade || 'Good'}</span>
                            </div>
                            <div class="result-item">
                                <span>Overall Score:</span>
                                <span>${Math.round((quality.overall_quality || 0) * 100)}%</span>
                            </div>
                        </div>
                    </div>
                    
                    <div style="margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px;">
                        <strong>⏱️ Processing Time:</strong> ${data.processing_time?.toFixed(2) || 0}s
                        <br><strong>📊 Status:</strong> <span class="badge badge-success">Success</span>
                    </div>
                `;
            } else {
                resultsContent.innerHTML = `
                    <div style="color: red; text-align: center; padding: 20px;">
                        <h3>❌ Processing Failed</h3>
                        <p>${data.error || 'Unknown error occurred'}</p>
                    </div>
                `;
            }
        }
        
        function getRiskBadgeClass(risk) {
            switch(risk) {
                case 'LOW': return 'badge-success';
                case 'MEDIUM': return 'badge-warning';
                case 'HIGH': 
                case 'CRITICAL': return 'badge-danger';
                default: return 'badge-warning';
            }
        }
        
        function loadMetrics() {
            fetch('/api/dashboard/summary')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('totalDocs').textContent = data.total_documents || 0;
                    document.getElementById('successRate').textContent = (data.success_rate || 0).toFixed(1) + '%';
                    document.getElementById('avgTime').textContent = (data.average_processing_time || 0).toFixed(1) + 's';
                    document.getElementById('systemStatus').textContent = data.system_status || 'Ready';
                })
                .catch(error => console.error('Error loading metrics:', error));
        }
        
        // Refresh metrics every 30 seconds
        setInterval(loadMetrics, 30000);
    </script>
</body>
</html>
"""

# API Routes
@app.route('/')
def index():
    """Main dashboard page"""
    return render_template_string(MAIN_TEMPLATE)

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0',
        'enhanced_system': ENHANCED_SYSTEM_AVAILABLE
    })

@app.route('/api/upload', methods=['POST'])
def upload_document():
    """Upload and process document"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded', 'success': False}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected', 'success': False}), 400
        
        # Process the document
        result = ocr_system.process_document_complete(file)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/dashboard/summary')
def get_dashboard_summary():
    """Get dashboard summary"""
    try:
        if hasattr(ocr_system, 'get_dashboard_summary'):
            summary = ocr_system.get_dashboard_summary()
        else:
            summary = {
                'total_documents': 0,
                'success_rate': 0,
                'average_processing_time': 0,
                'system_status': 'Basic Mode'
            }
        
        return jsonify(summary)
        
    except Exception as e:
        logger.error(f"Dashboard summary error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/dashboard')
def get_analytics_dashboard():
    """Get analytics dashboard data"""
    try:
        if enhanced_ocr and hasattr(enhanced_ocr, 'analytics_dashboard'):
            summary = enhanced_ocr.analytics_dashboard.get_dashboard_summary()
            real_time_metrics = enhanced_ocr.analytics_dashboard.get_real_time_metrics()
            
            return jsonify({
                'summary': summary,
                'real_time_metrics': real_time_metrics,
                'performance_metrics': enhanced_ocr.performance_metrics
            })
        else:
            return jsonify({
                'summary': {'message': 'Analytics not available in basic mode'},
                'real_time_metrics': {},
                'performance_metrics': {}
            })
        
    except Exception as e:
        logger.error(f"Analytics error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/report')
def generate_analytics_report():
    """Generate comprehensive analytics report"""
    try:
        if enhanced_ocr and hasattr(enhanced_ocr, 'analytics_dashboard'):
            days = request.args.get('days', 30, type=int)
            report = enhanced_ocr.analytics_dashboard.generate_analytics_report(days)
            return jsonify(report)
        else:
            return jsonify({'error': 'Analytics not available in basic mode'}), 503
        
    except Exception as e:
        logger.error(f"Report generation error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/status')
def get_system_status():
    """Get system status"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'enhanced_system': ENHANCED_SYSTEM_AVAILABLE,
        'components': {
            'ml_classifier': 'ready' if ENHANCED_SYSTEM_AVAILABLE else 'basic',
            'security_validator': 'ready' if ENHANCED_SYSTEM_AVAILABLE else 'basic',
            'analytics_dashboard': 'ready' if ENHANCED_SYSTEM_AVAILABLE else 'basic',
            'realtime_server': 'ready' if ENHANCED_SYSTEM_AVAILABLE else 'inactive'
        },
        'session_id': getattr(ocr_system, 'session_id', 'unknown')
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(413)
def too_large(error):
    return jsonify({'error': 'File too large. Maximum size is 16MB'}), 413

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    logger.info(f"Starting Enhanced OCR Document Scanner on port {port}")
    logger.info(f"Enhanced system available: {ENHANCED_SYSTEM_AVAILABLE}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
