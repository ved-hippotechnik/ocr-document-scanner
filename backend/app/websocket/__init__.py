"""
WebSocket initialization and configuration
"""
from flask_socketio import SocketIO, emit, join_room, leave_room
import logging

logger = logging.getLogger(__name__)

# Global socketio instance
socketio = None

def init_websocket(app):
    """Initialize WebSocket with Flask app"""
    global socketio
    
    # Get configuration
    cors_origins = app.config.get('CORS_ORIGINS', '*')
    
    # Initialize SocketIO
    socketio = SocketIO(
        app,
        cors_allowed_origins=cors_origins,
        logger=app.config.get('DEBUG', False),
        engineio_logger=False,
        async_mode='threading',
        ping_timeout=60,
        ping_interval=25
    )
    
    # Register event handlers
    register_handlers(socketio)
    
    logger.info("WebSocket initialized")
    return socketio

def register_handlers(socketio):
    """Register WebSocket event handlers"""
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        logger.info(f"Client connected")
        emit('connected', {'message': 'Connected to OCR Scanner WebSocket'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        logger.info(f"Client disconnected")
    
    @socketio.on('join')
    def handle_join(data):
        """Handle room join"""
        room = data.get('room')
        if room:
            join_room(room)
            emit('joined', {'room': room, 'message': f'Joined room {room}'})
            logger.info(f"Client joined room: {room}")
    
    @socketio.on('leave')
    def handle_leave(data):
        """Handle room leave"""
        room = data.get('room')
        if room:
            leave_room(room)
            emit('left', {'room': room, 'message': f'Left room {room}'})
            logger.info(f"Client left room: {room}")
    
    @socketio.on('scan_progress')
    def handle_scan_progress(data):
        """Handle scan progress updates"""
        room = data.get('room')
        progress = data.get('progress', 0)
        message = data.get('message', '')
        
        if room:
            emit('progress_update', {
                'progress': progress,
                'message': message
            }, room=room)
    
    @socketio.on('ping')
    def handle_ping():
        """Handle ping for connection keep-alive"""
        emit('pong', {'timestamp': datetime.utcnow().isoformat()})

def emit_progress(room, progress, message):
    """Emit progress update to a specific room"""
    if socketio:
        socketio.emit('progress_update', {
            'progress': progress,
            'message': message
        }, room=room)

def emit_result(room, result):
    """Emit scan result to a specific room"""
    if socketio:
        socketio.emit('scan_complete', {
            'result': result
        }, room=room)

def emit_error(room, error):
    """Emit error to a specific room"""
    if socketio:
        socketio.emit('scan_error', {
            'error': error
        }, room=room)


def notify_processing_start(session_id, document_type=None):
    """Notify client that processing has started"""
    try:
        emit_progress(session_id, 0, f"Starting processing{' for ' + document_type if document_type else ''}")
    except Exception as e:
        logger.warning(f"WebSocket notify_processing_start failed: {e}")


def notify_processing_progress(session_id, progress, message=''):
    """Notify client of processing progress"""
    try:
        emit_progress(session_id, progress, message)
    except Exception as e:
        logger.warning(f"WebSocket notify_processing_progress failed: {e}")


def notify_processing_complete(session_id, result):
    """Notify client that processing is complete"""
    try:
        emit_result(session_id, result)
    except Exception as e:
        logger.warning(f"WebSocket notify_processing_complete failed: {e}")


def notify_processing_error(session_id, error):
    """Notify client of processing error"""
    try:
        emit_error(session_id, error)
    except Exception as e:
        logger.warning(f"WebSocket notify_processing_error failed: {e}")


# Import datetime for timestamp
from datetime import datetime

# Export functions
__all__ = [
    'init_websocket', 'socketio',
    'emit_progress', 'emit_result', 'emit_error',
    'notify_processing_start', 'notify_processing_progress',
    'notify_processing_complete', 'notify_processing_error',
]