import signal
import sys
import logging
from app import create_app

logger = logging.getLogger(__name__)

app, socketio = create_app()


def graceful_shutdown(signum, frame):
    """Handle SIGTERM/SIGINT for graceful shutdown."""
    sig_name = signal.Signals(signum).name
    logger.info(f"Received {sig_name} — shutting down gracefully")

    # Close database connections
    try:
        from app.database import db
        with app.app_context():
            db.session.remove()
            db.engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.warning(f"Error closing database connections: {e}")

    sys.exit(0)


signal.signal(signal.SIGTERM, graceful_shutdown)
signal.signal(signal.SIGINT, graceful_shutdown)

if __name__ == '__main__':
    if socketio:
        socketio.run(app, debug=True, host='0.0.0.0', port=5001, allow_unsafe_werkzeug=True)
    else:
        app.run(debug=True, host='0.0.0.0', port=5001)
