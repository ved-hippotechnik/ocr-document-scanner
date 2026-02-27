"""
App factory helpers — extracted from __init__.py to reduce complexity.
"""
import os
import logging

logger = logging.getLogger(__name__)


def load_config(app, flask_env):
    """Load and validate all configuration from environment variables."""
    secret_key = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')

    if flask_env == 'production':
        if secret_key == 'dev-key-change-in-production':
            raise ValueError("Production deployment requires a secure SECRET_KEY environment variable")
        if len(secret_key) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long in production")

    app.config['SECRET_KEY'] = secret_key
    app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))
    app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', 'uploads')

    # JWT
    jwt_secret = os.environ.get('JWT_SECRET_KEY', app.config['SECRET_KEY'])
    if flask_env == 'production' and jwt_secret == secret_key:
        raise ValueError("Production deployment requires a separate JWT_SECRET_KEY environment variable")
    app.config['JWT_SECRET_KEY'] = jwt_secret
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', 86400))
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = int(os.environ.get('JWT_REFRESH_TOKEN_EXPIRES', 2592000))

    # MCP
    app.config['MCP_STORAGE_PATH'] = os.environ.get('MCP_STORAGE_PATH', 'mcp_storage')
    app.config['MCP_MAX_MEMORY_SIZE'] = int(os.environ.get('MCP_MAX_MEMORY_SIZE', 10000))
    app.config['MCP_MEMORY_PERSISTENCE_PATH'] = os.environ.get('MCP_MEMORY_PERSISTENCE_PATH', 'mcp_storage/memory.pkl')

    # Rate limiting
    app.config['RATE_LIMIT_ENABLED'] = os.environ.get('RATE_LIMIT_ENABLED', 'true').lower() == 'true'
    app.config['RATE_LIMIT_STORAGE_URL'] = os.environ.get('RATE_LIMIT_STORAGE_URL', 'memory://')
    app.config['RATE_LIMIT_REQUESTS'] = int(os.environ.get('RATE_LIMIT_REQUESTS', 100))
    app.config['RATE_LIMIT_WINDOW'] = int(os.environ.get('RATE_LIMIT_WINDOW', 60))

    # Database
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_size': int(os.environ.get('DATABASE_POOL_SIZE', 20)),
            'pool_timeout': int(os.environ.get('DATABASE_POOL_TIMEOUT', 30)),
            'pool_recycle': int(os.environ.get('DATABASE_POOL_RECYCLE', 3600)),
            'max_overflow': int(os.environ.get('DATABASE_MAX_OVERFLOW', 40)),
            'pool_pre_ping': True,
            'echo_pool': flask_env == 'development',
        }
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
            'SQLALCHEMY_DATABASE_URI', 'sqlite:///ocr_scanner.db'
        )
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_timeout': 20, 'pool_recycle': -1, 'pool_pre_ping': True,
        }

    # OCR
    app.config['OCR_TIMEOUT'] = int(os.environ.get('OCR_TIMEOUT', 60))
    app.config['OCR_DPI'] = int(os.environ.get('OCR_DPI', 300))
    app.config['OCR_LANGUAGES'] = os.environ.get('OCR_LANGUAGES', 'eng,ara,hin').split(',')


def init_optional_services(app):
    """Initialize optional services that can fail without blocking startup."""

    # ML Document Classifier
    try:
        from .ml_document_classifier import MLDocumentClassifier
        app.ml_classifier = MLDocumentClassifier()
        app.logger.info("ML Document Classifier initialized")
    except Exception as e:
        app.logger.error(f"Failed to initialize ML Classifier: {e}")
        app.ml_classifier = None

    # Claude Vision Service
    if os.environ.get('ANTHROPIC_API_KEY'):
        try:
            from .ai.vision_service import ClaudeVisionService
            app.vision_service = ClaudeVisionService(
                api_key=os.environ['ANTHROPIC_API_KEY'],
                model=os.environ.get('VISION_MODEL', 'claude-sonnet-4-20250514')
            )
            app.logger.info("Claude Vision Service initialized")
        except Exception as e:
            app.logger.error(f"Failed to initialize Vision Service: {e}")
            app.vision_service = None
    else:
        app.vision_service = None

    # Security Validator
    try:
        from .security_validator import DocumentSecurityValidator
        app.security_validator = DocumentSecurityValidator()
    except Exception as e:
        app.logger.error(f"Failed to initialize Security Validator: {e}")
        app.security_validator = None

    # Performance Optimizer
    try:
        from .performance_optimizer import PerformanceOptimizer
        app.performance_optimizer = PerformanceOptimizer()
    except Exception as e:
        app.logger.error(f"Failed to initialize Performance Optimizer: {e}")
        app.performance_optimizer = None

    # Duplicate Detector
    try:
        from .duplicate_detector import DuplicateDetector
        app.duplicate_detector = DuplicateDetector()
    except Exception as e:
        app.logger.warning(f"Duplicate Detector init failed: {e}")
        app.duplicate_detector = None


def init_logging(app):
    """Configure logging for non-debug, non-test environments."""
    if app.debug or app.testing:
        return

    log_level = getattr(logging, os.environ.get('LOG_LEVEL', 'INFO').upper())
    log_file = os.environ.get('LOG_FILE', 'app.log')

    if not os.path.exists('logs'):
        os.mkdir('logs')

    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler(f'logs/{log_file}', maxBytes=1048576, backupCount=10)

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


def register_all_blueprints(app):
    """Register all API blueprints."""
    # Consolidated v3 + auth + legacy proxies
    from .api import register_api_blueprints
    register_api_blueprints(app)

    # MCP module
    try:
        from .mcp.routes import mcp_bp, init_mcp_servers
        init_mcp_servers(app)
        app.register_blueprint(mcp_bp)
        app.logger.info("MCP servers initialized and blueprint registered")
    except Exception as e:
        app.logger.warning(f"Could not initialize MCP servers: {e}")

    # AI routes (kept as separate module — used by v3/classify internally)
    from .ai import ai_bp
    app.register_blueprint(ai_bp)

    # Client metrics
    try:
        from .client_metrics_routes import client_metrics_bp
        app.register_blueprint(client_metrics_bp)
    except ImportError:
        pass


def register_middleware(app):
    """Register request/response middleware."""
    import uuid
    import time as _time
    from datetime import datetime, timezone
    from flask import g, request
    from .database import db as _db, ApiUsageLog as _ApiUsageLog

    @app.before_request
    def assign_request_id():
        g.request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))

    @app.after_request
    def add_request_id_header(response):
        request_id = getattr(g, 'request_id', None)
        if request_id:
            response.headers['X-Request-ID'] = request_id
        return response

    @app.before_request
    def _track_api_start_time():
        request._api_start_time = _time.time()

    @app.after_request
    def _track_api_usage(response):
        api_key_obj = getattr(request, 'current_api_key', None)
        if api_key_obj is None:
            return response

        try:
            elapsed_ms = (_time.time() - getattr(request, '_api_start_time', _time.time())) * 1000
            today = datetime.now(timezone.utc).date()
            endpoint = request.path

            row = _ApiUsageLog.query.filter_by(
                api_key_id=api_key_obj.id, date=today, endpoint=endpoint
            ).first()
            if row is None:
                row = _ApiUsageLog(api_key_id=api_key_obj.id, date=today, endpoint=endpoint)
                _db.session.add(row)

            row.request_count = (row.request_count or 0) + 1
            row.total_latency_ms = (row.total_latency_ms or 0) + elapsed_ms
            if response.status_code >= 400:
                row.error_count = (row.error_count or 0) + 1
            _db.session.commit()
        except Exception:
            _db.session.rollback()

        return response
