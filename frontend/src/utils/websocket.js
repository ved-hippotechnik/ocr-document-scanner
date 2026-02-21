import { io } from 'socket.io-client';
import { WS_URL } from '../config';

let socket = null;

/**
 * Get or create a shared SocketIO connection.
 */
export function getSocket() {
  if (!socket) {
    socket = io(WS_URL, {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionAttempts: 10,
      reconnectionDelay: 2000,
      autoConnect: false,
    });
  }
  return socket;
}

/**
 * Connect to WebSocket server and join a session room.
 * Returns an object with helper methods and a cleanup function.
 */
export function connectSession(sessionId, handlers = {}) {
  const sock = getSocket();

  if (!sock.connected) {
    sock.connect();
  }

  // Join session room once connected
  const onConnect = () => {
    sock.emit('join', { session_id: sessionId });
  };

  if (sock.connected) {
    onConnect();
  } else {
    sock.on('connect', onConnect);
  }

  // Register event handlers
  if (handlers.onProgress) {
    sock.on('progress_update', handlers.onProgress);
  }
  if (handlers.onComplete) {
    sock.on('scan_complete', handlers.onComplete);
  }
  if (handlers.onError) {
    sock.on('scan_error', handlers.onError);
  }
  if (handlers.onStart) {
    sock.on('processing_started', handlers.onStart);
  }

  // Return cleanup function
  return () => {
    sock.off('connect', onConnect);
    if (handlers.onProgress) sock.off('progress_update', handlers.onProgress);
    if (handlers.onComplete) sock.off('scan_complete', handlers.onComplete);
    if (handlers.onError) sock.off('scan_error', handlers.onError);
    if (handlers.onStart) sock.off('processing_started', handlers.onStart);
    sock.emit('leave', { session_id: sessionId });
  };
}

/**
 * Disconnect the socket entirely.
 */
export function disconnectSocket() {
  if (socket) {
    socket.disconnect();
    socket = null;
  }
}
