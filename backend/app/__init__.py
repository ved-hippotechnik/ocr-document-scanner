from flask import Flask
from flask_cors import CORS
import os
import logging
from logging.handlers import RotatingFileHandler

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', 'uploads')
    
    # Database configuration
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        # Handle DATABASE_URL from various cloud providers
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        # Fallback to SQLite for development
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
            'SQLALCHEMY_DATABASE_URI', 
            'sqlite:///ocr_scanner.db'
        )
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_timeout': 20,
        'pool_recycle': -1,
        'pool_pre_ping': True
    }
    
    # OCR Configuration
    app.config['OCR_TIMEOUT'] = int(os.environ.get('OCR_TIMEOUT', 60))
    app.config['OCR_DPI'] = int(os.environ.get('OCR_DPI', 300))
    app.config['OCR_LANGUAGES'] = os.environ.get('OCR_LANGUAGES', 'eng,ara,hin').split(',')
    
    # CORS Configuration
    cors_origins = os.environ.get('CORS_ORIGINS', '*')
    if cors_origins != '*':
        cors_origins = cors_origins.split(',')
    CORS(app, origins=cors_origins)
    
    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize database
    from .database import init_db
    init_db(app)
    
    # Logging Configuration
    if not app.debug and not app.testing:
        log_level = getattr(logging, os.environ.get('LOG_LEVEL', 'INFO').upper())
        log_file = os.environ.get('LOG_FILE', 'app.log')
        
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = RotatingFileHandler(f'logs/{log_file}', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(log_level)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(log_level)
        app.logger.info('OCR Document Scanner startup')
    
    # Initialize monitoring
    from .monitoring import setup_metrics
    setup_metrics(app)
    
    # Initialize document processors
    from .processors import registry  # This will initialize all processors
    
    # Register blueprints
    from .routes import main as main_blueprint
    from .routes_enhanced import enhanced as enhanced_blueprint
    
    app.register_blueprint(main_blueprint)
    app.register_blueprint(enhanced_blueprint)
    
    # Root endpoint - API Documentation
    @app.route('/')
    def api_documentation():
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>OCR Document Scanner API</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }
                .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
                h2 { color: #34495e; margin-top: 30px; }
                .endpoint { background: #ecf0f1; padding: 15px; margin: 10px 0; border-radius: 5px; }
                .method { font-weight: bold; color: #e74c3c; }
                .url { font-family: monospace; background: #2c3e50; color: white; padding: 5px 10px; border-radius: 3px; }
                .status { color: #27ae60; font-weight: bold; }
                .feature { background: #e8f6f3; padding: 10px; margin: 5px 0; border-left: 4px solid #1abc9c; }
                .test-section { background: #fef9e7; padding: 15px; border-radius: 5px; border-left: 4px solid #f39c12; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 OCR Document Scanner API</h1>
                <p><strong>Status:</strong> <span class="status">✅ OPERATIONAL</span></p>
                <p><strong>Version:</strong> 2.0.0</p>
                <p><strong>Base URL:</strong> <code>http://localhost:5002</code></p>
                
                <h2>📋 Available Document Types</h2>
                <div class="feature">🇦🇪 Emirates ID Card (UAE)</div>
                <div class="feature">🇮🇳 Aadhaar Card (India)</div>
                <div class="feature">🇮🇳 Driving License (India)</div>
                <div class="feature">🇮🇳 Passport (India)</div>
                <div class="feature">🇺🇸 US Driver's License</div>
                
                <h2>🔗 API Endpoints</h2>
                
                <div class="endpoint">
                    <div><span class="method">GET</span> <span class="url">/health</span></div>
                    <p>Check service health status</p>
                </div>
                
                <div class="endpoint">
                    <div><span class="method">GET</span> <span class="url">/api/processors</span></div>
                    <p>Get list of available document processors</p>
                </div>
                
                <div class="endpoint">
                    <div><span class="method">POST</span> <span class="url">/api/scan</span></div>
                    <p>Upload and process a document image</p>
                    <p><strong>Parameters:</strong> <code>image</code> (multipart file upload)</p>
                </div>
                
                <div class="endpoint">
                    <div><span class="method">GET</span> <span class="url">/api/stats</span></div>
                    <p>Get processing statistics</p>
                </div>
                
                <div class="endpoint">
                    <div><span class="method">GET</span> <span class="url">/api/v2/health</span></div>
                    <p>Enhanced health check with component status</p>
                </div>
                
                <div class="endpoint">
                    <div><span class="method">POST</span> <span class="url">/api/v2/scan</span></div>
                    <p>Enhanced document processing with quality assessment</p>
                    <p><strong>Content-Type:</strong> application/json</p>
                    <p><strong>Body:</strong> <code>{"image": "base64_encoded_image", "document_type": "optional_hint"}</code></p>
                </div>
                
                <h2>🧪 Quick Test</h2>
                <div class="test-section">
                    <p><strong>Test the API:</strong></p>
                    <p>1. Health Check: <a href="/health" target="_blank">GET /health</a></p>
                    <p>2. Processors: <a href="/api/processors" target="_blank">GET /api/processors</a></p>
                    <p>3. Statistics: <a href="/api/stats" target="_blank">GET /api/stats</a></p>
                    <p>4. Enhanced Health: <a href="/api/v2/health" target="_blank">GET /api/v2/health</a></p>
                </div>
                
                <h2>📄 Example Upload</h2>
                <div class="test-section">
                    <p><strong>Using curl:</strong></p>
                    <code>curl -X POST -F "image=@your_document.jpg" http://localhost:5002/api/scan</code>
                </div>
                
                <p style="text-align: center; margin-top: 30px; color: #7f8c8d;">
                    OCR Document Scanner - Ready for Document Processing 🎉
                </p>
            </div>
        </body>
        </html>
        ''', 200
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'service': 'ocr-document-scanner'}, 200
    
    # Processors info endpoint
    @app.route('/api/processors')
    def list_processors():
        from .processors import processor_registry
        return {
            'supported_documents': processor_registry.list_supported_documents(),
            'total_processors': len(processor_registry.processors)
        }
    
    return app
