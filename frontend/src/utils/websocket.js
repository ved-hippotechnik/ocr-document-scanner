import { io } from 'socket.io-client';
import { WS_URL } from '../config';

let socket = null;
let _connectionStatus = 'disconnected'; // disconnected | connecting | connected | failed

/**
 * Get or create a shared SocketIO connection with timeout and heartbeat.
 */
export function getSocket() {
  if (!socket) {
    socket = io(WS_URL, {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionAttempts: 10,
      reconnectionDelay: 2000,
      timeout: 10000, // Q3 — connection timeout
      autoConnect: false,
    });

    // Track connection state
    socket.on('connect', () => {
      _connectionStatus = 'connected';
    });

    socket.on('disconnect', () => {
      _connectionStatus = 'disconnected';
    });

    // Q1 — track connection errors
    socket.on('connect_error', (err) => {
      _connectionStatus = 'connecting';
      console.error('[WebSocket] Connection error:', err.message);
    });

    // Q1 — all reconnection attempts exhausted
    socket.io.on('reconnect_failed', () => {
      _connectionStatus = 'failed';
      console.error('[WebSocket] All reconnection attempts exhausted');
      // Dispatch custom event for App.js to show persistent toast
      window.dispatchEvent(new CustomEvent('websocket-failed'));
    });

    socket.io.on('reconnect', (attempt) => {
      _connectionStatus = 'connected';
      console.info(`[WebSocket] Reconnected after ${attempt} attempts`);
    });

    // Q1 — heartbeat to detect zombie connections (25s ping)
    let heartbeatInterval = null;
    socket.on('connect', () => {
      if (heartbeatInterval) clearInterval(heartbeatInterval);
      heartbeatInterval = setInterval(() => {
        if (socket && socket.connected) {
          socket.emit('ping_heartbeat');
        }
      }, 25000);
    });

    socket.on('disconnect', () => {
      if (heartbeatInterval) {
        clearInterval(heartbeatInterval);
        heartbeatInterval = null;
      }
    });
  }
  return socket;
}

/**
 * Get the current WebSocket connection status.
 * @returns {'disconnected' | 'connecting' | 'connected' | 'failed'}
 */
export function getConnectionStatus() {
  return _connectionStatus;
}

/**
 * Connect to WebSocket server and join a session room.
 * Returns a cleanup function.
 */
export function connectSession(sessionId, handlers = {}) {
  const sock = getSocket();

  if (!sock.connected) {
    _connectionStatus = 'connecting';
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
    _connectionStatus = 'disconnected';
  }
}
