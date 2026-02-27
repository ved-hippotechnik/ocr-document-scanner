from flask import Flask
from flask_cors import CORS
import os
from dotenv import load_dotenv
from .celery_app import make_celery

# Load .env file before app creation
load_dotenv()

# Swagger / OpenAPI documentation (Flasgger)
try:
    from flasgger import Swagger
    from .swagger import SWAGGER_TEMPLATE, SWAGGER_CONFIG
    _FLASGGER_AVAILABLE = True
except ImportError:
    _FLASGGER_AVAILABLE = False

# Module-level socketio reference (set by _init_core_services)
socketio = None


def create_app():
    app = Flask(__name__)
    flask_env = os.environ.get('FLASK_ENV', 'development')

    from .extensions import (
        load_config, init_optional_services, init_logging,
        register_all_blueprints, register_middleware,
    )

    # ── Configuration ─────────────────────────────────────────────────────
    load_config(app, flask_env)

    cors_origins = os.environ.get('CORS_ORIGINS', '*')
    if cors_origins != '*':
        cors_origins = cors_origins.split(',')
    CORS(app, origins=cors_origins,
         expose_headers=['X-Request-ID', 'X-Error-ID', 'X-Request-Duration', 'Retry-After'])
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # ── Core services (must succeed) ──────────────────────────────────────
    _init_core_services(app, flask_env)

    # ── Optional services & logging ───────────────────────────────────────
    init_optional_services(app)
    init_logging(app)

    # ── Monitoring, processors, cache ─────────────────────────────────────
    try:
        from .monitoring import setup_metrics
        setup_metrics(app)
    except Exception as e:
        app.logger.warning(f"Monitoring setup failed (non-critical): {e}")

    from .processors import registry  # noqa: F401 — triggers processor init

    from .cache import init_cache
    app.cache = init_cache(app)

    # ── Blueprints & middleware ────────────────────────────────────────────
    register_all_blueprints(app)
    register_middleware(app)

    # ── Swagger UI ────────────────────────────────────────────────────────
    if _FLASGGER_AVAILABLE:
        try:
            Swagger(app, template=SWAGGER_TEMPLATE, config=SWAGGER_CONFIG)
            app.logger.info("Swagger UI available at /api/docs")
        except Exception as e:
            app.logger.warning(f"Flasgger initialization failed (non-critical): {e}")

    # ── Health probes ─────────────────────────────────────────────────────
    _register_health_routes(app)

    return app, socketio


def _init_core_services(app, flask_env):
    """Initialize services that must succeed for the app to be usable."""
    global socketio

    # Database
    from .database import init_db, db
    init_db(app)
    try:
        from sqlalchemy import text
        with app.app_context():
            db.session.execute(text('SELECT 1'))
            db.session.rollback()
        app.logger.info("Database connectivity verified at startup")
    except Exception as db_err:
        app.logger.error("DATABASE UNREACHABLE AT STARTUP: %s", db_err)
        if flask_env == 'production':
            raise RuntimeError(f"Cannot start: database unreachable — {db_err}") from db_err

    # JWT
    from .auth import jwt_manager
    jwt_manager.init_app(app)

    # Rate limiter
    from .rate_limiter import init_rate_limiter
    app.limiter = init_rate_limiter(app)

    # Security middleware
    from .security.middleware import setup_security_middleware
    setup_security_middleware(app)

    # Celery
    app.celery = make_celery(app)

    # WebSocket
    if os.environ.get('ENABLE_WEBSOCKET', 'true').lower() == 'true':
        try:
            from .websocket import init_websocket
            socketio = init_websocket(app)
        except Exception as e:
            app.logger.warning(f"WebSocket initialization failed: {e}")
            socketio = None
    else:
        socketio = None


def _register_health_routes(app):
    """Register liveness and readiness probes."""

    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'service': 'ocr-document-scanner'}, 200

    @app.route('/health/ready')
    def readiness_check():
        from .health import aggregate_health
        overall, details = aggregate_health(app)
        status_code = 200 if overall != 'unhealthy' else 503
        return {
            'status': overall,
            'service': 'ocr-document-scanner',
            'checks': details,
        }, status_code
