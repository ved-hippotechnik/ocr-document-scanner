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
