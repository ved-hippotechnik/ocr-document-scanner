from flask import Flask
from flask_cors import CORS
import os
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
from .celery_app import make_celery

# Load .env file before app creation
load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # Configuration with production security enforcement
    secret_key = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    flask_env = os.environ.get('FLASK_ENV', 'development')
    
    # Enforce secure secrets in production
    if flask_env == 'production':
        if secret_key == 'dev-key-change-in-production':
            raise ValueError("Production deployment requires a secure SECRET_KEY environment variable")
        if len(secret_key) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long in production")
    
    app.config['SECRET_KEY'] = secret_key
    app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', 'uploads')
    
    # JWT Configuration with enhanced security
    jwt_secret = os.environ.get('JWT_SECRET_KEY', app.config['SECRET_KEY'])
    if flask_env == 'production' and jwt_secret == secret_key:
        raise ValueError("Production deployment requires a separate JWT_SECRET_KEY environment variable")
    
    app.config['JWT_SECRET_KEY'] = jwt_secret
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', 86400))  # 24 hours
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = int(os.environ.get('JWT_REFRESH_TOKEN_EXPIRES', 2592000))  # 30 days
    
    # MCP Configuration
    app.config['MCP_STORAGE_PATH'] = os.environ.get('MCP_STORAGE_PATH', 'mcp_storage')
    app.config['MCP_MAX_MEMORY_SIZE'] = int(os.environ.get('MCP_MAX_MEMORY_SIZE', 10000))
    app.config['MCP_MEMORY_PERSISTENCE_PATH'] = os.environ.get('MCP_MEMORY_PERSISTENCE_PATH', 'mcp_storage/memory.pkl')
    
    # Rate Limiting Configuration
    app.config['RATE_LIMIT_ENABLED'] = os.environ.get('RATE_LIMIT_ENABLED', 'true').lower() == 'true'
    app.config['RATE_LIMIT_STORAGE_URL'] = os.environ.get('RATE_LIMIT_STORAGE_URL', 'memory://')
    app.config['RATE_LIMIT_REQUESTS'] = int(os.environ.get('RATE_LIMIT_REQUESTS', 100))
    app.config['RATE_LIMIT_WINDOW'] = int(os.environ.get('RATE_LIMIT_WINDOW', 60))
    
    # Database configuration with connection pooling
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        # Handle DATABASE_URL from various cloud providers
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
        
        # Connection pooling configuration
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_size': int(os.environ.get('DATABASE_POOL_SIZE', 20)),
            'pool_timeout': int(os.environ.get('DATABASE_POOL_TIMEOUT', 30)),
            'pool_recycle': int(os.environ.get('DATABASE_POOL_RECYCLE', 3600)),
            'max_overflow': int(os.environ.get('DATABASE_MAX_OVERFLOW', 40)),
            'pool_pre_ping': True,  # Verify connections before using
            'echo_pool': flask_env == 'development',  # Log pool checkouts in dev
        }
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
    
    # Initialize JWT manager
    from .auth import jwt_manager
    jwt_manager.init_app(app)
    
    # Initialize Rate Limiter
    from .rate_limiter import init_rate_limiter
    limiter = init_rate_limiter(app)
    app.limiter = limiter  # Make limiter accessible to blueprints
    app.logger.info("✅ Rate limiter initialized")
    
    # Initialize Security Middleware
    from .security.middleware import setup_security_middleware
    setup_security_middleware(app)
    app.logger.info("✅ Security middleware initialized")
    
    # Initialize Celery for async tasks
    celery = make_celery(app)
    app.celery = celery
    app.logger.info("✅ Celery initialized for async processing")
    
    # Initialize WebSocket
    if os.environ.get('ENABLE_WEBSOCKET', 'true').lower() == 'true':
        try:
            from .websocket import init_websocket
            socketio = init_websocket(app)
            app.logger.info("✅ WebSocket initialized")
        except Exception as e:
            app.logger.warning(f"WebSocket initialization failed: {e}")
            socketio = None
    else:
        socketio = None
    
    # Initialize ML Document Classifier
    try:
        from .ml_document_classifier import MLDocumentClassifier
        app.ml_classifier = MLDocumentClassifier()
        app.logger.info("✅ ML Document Classifier initialized")
    except Exception as e:
        app.logger.error(f"❌ Failed to initialize ML Classifier: {e}")
        app.ml_classifier = None
    
    # Initialize Claude Vision Service
    if os.environ.get('ANTHROPIC_API_KEY'):
        try:
            from .ai.vision_service import ClaudeVisionService
            app.vision_service = ClaudeVisionService(
                api_key=os.environ['ANTHROPIC_API_KEY'],
                model=os.environ.get('VISION_MODEL', 'claude-sonnet-4-20250514')
            )
            app.logger.info("✅ Claude Vision Service initialized")
        except Exception as e:
            app.logger.error(f"❌ Failed to initialize Vision Service: {e}")
            app.vision_service = None
    else:
        app.vision_service = None
        app.logger.info("ℹ️ Claude Vision Service disabled (no ANTHROPIC_API_KEY)")

    # Initialize Security Validator
    try:
        from .security_validator import DocumentSecurityValidator
        app.security_validator = DocumentSecurityValidator()
        app.logger.info("✅ Security Validator initialized")
    except Exception as e:
        app.logger.error(f"❌ Failed to initialize Security Validator: {e}")
        app.security_validator = None
    
    # Initialize Analytics Dashboard
    try:
        from .analytics_dashboard import AnalyticsDashboard
        app.analytics_dashboard = AnalyticsDashboard()
        app.logger.info("✅ Analytics Dashboard initialized")
    except Exception as e:
        app.logger.error(f"❌ Failed to initialize Analytics Dashboard: {e}")
        app.analytics_dashboard = None
    
    # Initialize Performance Optimizer
    try:
        from .performance_optimizer import PerformanceOptimizer
        app.performance_optimizer = PerformanceOptimizer()
        app.logger.info("✅ Performance Optimizer initialized")
    except Exception as e:
        app.logger.error(f"❌ Failed to initialize Performance Optimizer: {e}")
        app.performance_optimizer = None

    # Initialize Duplicate Detector
    try:
        from .duplicate_detector import DuplicateDetector
        app.duplicate_detector = DuplicateDetector()
        if app.duplicate_detector.available:
            app.logger.info("✅ Duplicate Detector initialized")
        else:
            app.logger.info("ℹ️ Duplicate Detector disabled (imagehash not installed)")
    except Exception as e:
        app.logger.warning(f"Duplicate Detector init failed: {e}")
        app.duplicate_detector = None

    # Logging Configuration
    if not app.debug and not app.testing:
        log_level = getattr(logging, os.environ.get('LOG_LEVEL', 'INFO').upper())
        log_file = os.environ.get('LOG_FILE', 'app.log')

        if not os.path.exists('logs'):
            os.mkdir('logs')

        file_handler = RotatingFileHandler(f'logs/{log_file}', maxBytes=1048576, backupCount=10)

        # Use structured JSON logging if pythonjsonlogger is available
        try:
            from pythonjsonlogger import jsonlogger
            formatter = jsonlogger.JsonFormatter(
                '%(asctime)s %(levelname)s %(name)s %(message)s %(pathname)s %(lineno)d',
                rename_fields={'asctime': 'timestamp', 'levelname': 'level'}
            )
        except ImportError:
            formatter = logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            )

        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(log_level)
        app.logger.info('OCR Document Scanner startup')
    
    # Initialize monitoring
    try:
        from .monitoring import setup_metrics
        setup_metrics(app)
        app.logger.info("✅ Monitoring metrics initialized")
    except Exception as e:
        app.logger.warning(f"Monitoring setup failed (non-critical): {e}")
    
    # Initialize document processors
    from .processors import registry  # This will initialize all processors
    
    # Initialize cache
    from .cache import init_cache
    cache = init_cache(app)
    app.cache = cache
    app.logger.info("✅ Cache system initialized")
    
    # Register blueprints
    from .routes import main as main_blueprint
    from .routes_enhanced import enhanced as enhanced_blueprint
    from .auth import auth_bp
    from .analytics import analytics_bp
    from .ai import ai_bp
    from .batch import batch_bp
    
    # Register improved routes with better error handling
    try:
        from .routes_improved import improved
        app.register_blueprint(improved)
        app.logger.info("✅ Improved routes v3 registered")
    except ImportError as e:
        app.logger.warning(f"Could not import improved routes: {e}")
    
    # Register async routes for long-running operations
    try:
        from .routes_async import async_bp
        app.register_blueprint(async_bp)
        app.logger.info("✅ Async routes registered")
    except ImportError as e:
        app.logger.warning(f"Could not import async routes: {e}")
    
    app.register_blueprint(main_blueprint)
    app.register_blueprint(enhanced_blueprint)
    app.register_blueprint(auth_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(batch_bp)
    
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
    
    return app, socketio
