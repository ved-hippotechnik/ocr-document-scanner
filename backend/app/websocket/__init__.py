"""
WebSocket implementation for real-time updates
"""
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
from flask import request
import logging
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Global SocketIO instance
socketio = SocketIO()

# Store active connections
active_connections = {}
user_rooms = {}  # user_id -> set of room_ids


def init_websocket(app):
    """Initialize WebSocket with Flask app"""
    socketio.init_app(
        app,
        cors_allowed_origins="*",
        async_mode='threading',
        logger=True,
        engineio_logger=True
    )
    
    # Register event handlers
    register_event_handlers()
    
    logger.info("✅ WebSocket initialized successfully")
    return socketio


def register_event_handlers():
    """Register WebSocket event handlers"""
    
    @socketio.on('connect')
    def handle_connect(auth):
        """Handle client connection"""
        try:
            client_id = request.sid
            user_id = None
            
            # Extract user info from auth token if provided
            if auth and isinstance(auth, dict) and 'token' in auth:
                user_id = authenticate_websocket_token(auth['token'])
            
            # Store connection info
            active_connections[client_id] = {
                'user_id': user_id,
                'connected_at': datetime.now(timezone.utc).isoformat(),
                'rooms': set()
            }
            
            logger.info(f"WebSocket client connected: {client_id} (user: {user_id})")
            
            # Send connection confirmation
            emit('connected', {
                'status': 'connected',
                'client_id': client_id,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
            
            # Send current statistics
            emit('stats_update', get_current_stats())
            
        except Exception as e:
            logger.error(f"Error handling WebSocket connection: {e}")
            disconnect()
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        try:
            client_id = request.sid
            
            if client_id in active_connections:
                user_id = active_connections[client_id]['user_id']
                rooms = active_connections[client_id]['rooms']
                
                # Leave all rooms
                for room in rooms:
                    leave_room(room)
                
                # Remove from user rooms mapping
                if user_id and user_id in user_rooms:
                    user_rooms[user_id].discard(client_id)
                    if not user_rooms[user_id]:
                        del user_rooms[user_id]
                
                # Remove connection
                del active_connections[client_id]
                
                logger.info(f"WebSocket client disconnected: {client_id} (user: {user_id})")
            
        except Exception as e:
            logger.error(f"Error handling WebSocket disconnection: {e}")
    
    @socketio.on('join_room')
    def handle_join_room(data):
        """Handle client joining a room"""
        try:
            client_id = request.sid
            room_id = data.get('room_id')
            
            if not room_id:
                emit('error', {'message': 'Room ID is required'})
                return
            
            # Validate room access
            if not can_access_room(client_id, room_id):
                emit('error', {'message': 'Access denied to room'})
                return
            
            # Join room
            join_room(room_id)
            
            # Update connection info
            if client_id in active_connections:
                active_connections[client_id]['rooms'].add(room_id)
                
                # Update user rooms mapping
                user_id = active_connections[client_id]['user_id']
                if user_id:
                    if user_id not in user_rooms:
                        user_rooms[user_id] = set()
                    user_rooms[user_id].add(room_id)
            
            logger.info(f"Client {client_id} joined room {room_id}")
            
            emit('room_joined', {
                'room_id': room_id,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error handling room join: {e}")
            emit('error', {'message': 'Failed to join room'})
    
    @socketio.on('leave_room')
    def handle_leave_room(data):
        """Handle client leaving a room"""
        try:
            client_id = request.sid
            room_id = data.get('room_id')
            
            if not room_id:
                emit('error', {'message': 'Room ID is required'})
                return
            
            # Leave room
            leave_room(room_id)
            
            # Update connection info
            if client_id in active_connections:
                active_connections[client_id]['rooms'].discard(room_id)
                
                # Update user rooms mapping
                user_id = active_connections[client_id]['user_id']
                if user_id and user_id in user_rooms:
                    user_rooms[user_id].discard(room_id)
            
            logger.info(f"Client {client_id} left room {room_id}")
            
            emit('room_left', {
                'room_id': room_id,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error handling room leave: {e}")
            emit('error', {'message': 'Failed to leave room'})
    
    @socketio.on('subscribe_notifications')
    def handle_subscribe_notifications(data):
        """Handle notification subscription"""
        try:
            client_id = request.sid
            notification_types = data.get('types', [])
            
            if client_id not in active_connections:
                emit('error', {'message': 'Client not found'})
                return
            
            # Store subscription preferences
            active_connections[client_id]['subscriptions'] = notification_types
            
            logger.info(f"Client {client_id} subscribed to notifications: {notification_types}")
            
            emit('subscription_updated', {
                'types': notification_types,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error handling notification subscription: {e}")
            emit('error', {'message': 'Failed to update subscription'})


def authenticate_websocket_token(token: str) -> Optional[str]:
    """Authenticate WebSocket token and return user ID"""
    try:
        from ..auth.jwt_utils import jwt_manager
        
        payload = jwt_manager.decode_token(token)
        if 'error' in payload:
            return None
        
        return payload.get('user_id')
    
    except Exception as e:
        logger.error(f"WebSocket token authentication error: {e}")
        return None


def can_access_room(client_id: str, room_id: str) -> bool:
    """Check if client can access a room"""
    try:
        # Basic room access control
        # For now, allow access to general rooms
        general_rooms = ['general', 'processing', 'notifications']
        
        if room_id in general_rooms:
            return True
        
        # For user-specific rooms, check if client is authenticated
        if room_id.startswith('user_'):
            if client_id in active_connections:
                user_id = active_connections[client_id]['user_id']
                expected_room = f'user_{user_id}'
                return room_id == expected_room
        
        return False
    
    except Exception as e:
        logger.error(f"Error checking room access: {e}")
        return False


def get_current_stats() -> Dict[str, Any]:
    """Get current application statistics"""
    try:
        from ..cache import cache
        
        stats = {
            'active_connections': len(active_connections),
            'cache_stats': cache.get_stats() if cache.is_available() else None,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        return stats
    
    except Exception as e:
        logger.error(f"Error getting current stats: {e}")
        return {'error': 'Failed to get stats'}


# WebSocket notification functions
def notify_processing_start(session_id: str, document_type: str = None):
    """Notify clients that processing has started"""
    try:
        message = {
            'type': 'processing_start',
            'session_id': session_id,
            'document_type': document_type,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        socketio.emit('processing_update', message, room='processing')
        logger.info(f"Sent processing start notification for session {session_id}")
        
    except Exception as e:
        logger.error(f"Error sending processing start notification: {e}")


def notify_processing_progress(session_id: str, progress: int, stage: str):
    """Notify clients of processing progress"""
    try:
        message = {
            'type': 'processing_progress',
            'session_id': session_id,
            'progress': progress,
            'stage': stage,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        socketio.emit('processing_update', message, room='processing')
        logger.info(f"Sent processing progress notification: {progress}% ({stage})")
        
    except Exception as e:
        logger.error(f"Error sending processing progress notification: {e}")


def notify_processing_complete(session_id: str, result: Dict[str, Any]):
    """Notify clients that processing is complete"""
    try:
        message = {
            'type': 'processing_complete',
            'session_id': session_id,
            'result': result,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        socketio.emit('processing_update', message, room='processing')
        logger.info(f"Sent processing complete notification for session {session_id}")
        
    except Exception as e:
        logger.error(f"Error sending processing complete notification: {e}")


def notify_processing_error(session_id: str, error: str):
    """Notify clients of processing error"""
    try:
        message = {
            'type': 'processing_error',
            'session_id': session_id,
            'error': error,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        socketio.emit('processing_update', message, room='processing')
        logger.error(f"Sent processing error notification for session {session_id}: {error}")
        
    except Exception as e:
        logger.error(f"Error sending processing error notification: {e}")


def notify_stats_update(stats: Dict[str, Any]):
    """Notify clients of statistics update"""
    try:
        message = {
            'type': 'stats_update',
            'stats': stats,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        socketio.emit('stats_update', message, room='general')
        logger.info("Sent stats update notification")
        
    except Exception as e:
        logger.error(f"Error sending stats update notification: {e}")


def notify_user(user_id: str, message: Dict[str, Any]):
    """Send notification to specific user"""
    try:
        room_id = f'user_{user_id}'
        
        notification = {
            'type': 'user_notification',
            'user_id': user_id,
            'message': message,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        socketio.emit('user_notification', notification, room=room_id)
        logger.info(f"Sent user notification to {user_id}")
        
    except Exception as e:
        logger.error(f"Error sending user notification: {e}")


def broadcast_system_message(message: str, message_type: str = 'info'):
    """Broadcast system message to all connected clients"""
    try:
        notification = {
            'type': 'system_message',
            'message': message,
            'message_type': message_type,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        socketio.emit('system_message', notification)
        logger.info(f"Broadcast system message: {message}")
        
    except Exception as e:
        logger.error(f"Error broadcasting system message: {e}")


def get_connection_stats():
    """Get WebSocket connection statistics"""
    try:
        stats = {
            'total_connections': len(active_connections),
            'authenticated_connections': len([
                conn for conn in active_connections.values() 
                if conn['user_id'] is not None
            ]),
            'active_rooms': len(set().union(*[
                conn['rooms'] for conn in active_connections.values()
            ])) if active_connections else 0,
            'users_online': len(user_rooms)
        }
        
        return stats
    
    except Exception as e:
        logger.error(f"Error getting connection stats: {e}")
        return {'error': 'Failed to get connection stats'}


# Export main functions
__all__ = [
    'socketio',
    'init_websocket',
    'notify_processing_start',
    'notify_processing_progress',
    'notify_processing_complete',
    'notify_processing_error',
    'notify_stats_update',
    'notify_user',
    'broadcast_system_message',
    'get_connection_stats'
]