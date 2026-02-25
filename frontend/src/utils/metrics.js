/**
 * Client-side metrics collection and batched reporting.
 *
 * Collects API call timings, errors, user actions, and performance data,
 * then flushes to the backend via POST /api/v3/client-metrics.
 *
 * Uses navigator.sendBeacon for reliable delivery on page unload.
 *
 *   Q6 (3AM debugging) — trackError with full context
 *   Q7 (metrics)        — trackApiCall, trackUserAction, initMetrics
 */

const FLUSH_INTERVAL_MS = 30000; // 30 seconds
const MAX_BUFFER_SIZE = 200;
const METRICS_ENDPOINT = '/api/v3/client-metrics';

let _buffer = [];
let _flushTimer = null;
let _initialized = false;

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Track an API call with timing and success status.
 */
export function trackApiCall(endpoint, durationMs, success, meta = {}) {
  _push({
    type: 'api_call',
    endpoint,
    durationMs,
    success: Boolean(success),
    ...meta,
  });
}

/**
 * Track a client-side error with full context for debugging.
 */
export function trackError(errorId, component, message, context = {}) {
  _push({
    type: 'error',
    errorId,
    component,
    message: String(message).slice(0, 500),
    action: context.action || 'unknown',
    online: navigator.onLine,
    url: window.location.pathname,
    ...context,
  });
}

/**
 * Track a user action (retries, navigation, feature usage).
 */
export function trackUserAction(action, meta = {}) {
  _push({
    type: 'user_action',
    action,
    ...meta,
  });
}

/**
 * Track a performance measurement (component mount time, render time, etc.).
 */
export function trackPerformance(component, metric, valueMs) {
  _push({
    type: 'performance',
    component,
    metric,
    valueMs,
  });
}

/**
 * Force an immediate flush of the metrics buffer.
 * Call this on critical errors so data isn't lost.
 */
export function flushMetrics() {
  _flush();
}

/**
 * Initialize metrics collection.
 * Sets up periodic flush and page lifecycle handlers.
 * Safe to call multiple times — only initializes once.
 */
export function initMetrics() {
  if (_initialized) return;
  _initialized = true;

  // Periodic flush
  _flushTimer = setInterval(_flush, FLUSH_INTERVAL_MS);

  // Flush on page hide / unload (uses sendBeacon for reliability)
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') {
      _flushBeacon();
    }
  });

  window.addEventListener('beforeunload', _flushBeacon);
}

/**
 * Stop metrics collection and flush remaining data.
 */
export function stopMetrics() {
  if (_flushTimer) {
    clearInterval(_flushTimer);
    _flushTimer = null;
  }
  _flush();
  _initialized = false;
}

// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------

function _push(metric) {
  metric.clientTimestamp = Date.now();
  _buffer.push(metric);

  // Auto-flush if buffer is getting large
  if (_buffer.length >= MAX_BUFFER_SIZE) {
    _flush();
  }
}

function _flush() {
  if (_buffer.length === 0) return;

  const metrics = _buffer.splice(0);
  const payload = JSON.stringify({
    metrics,
    clientTimestamp: Date.now(),
  });

  // Use fetch for normal flushes (we can retry on failure)
  fetch(METRICS_ENDPOINT, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: payload,
    keepalive: true,
  }).catch(() => {
    // If fetch fails, put metrics back for next flush (up to limit)
    if (_buffer.length < MAX_BUFFER_SIZE) {
      _buffer.unshift(...metrics.slice(0, MAX_BUFFER_SIZE - _buffer.length));
    }
  });
}

function _flushBeacon() {
  if (_buffer.length === 0) return;

  const metrics = _buffer.splice(0);
  const payload = JSON.stringify({
    metrics,
    clientTimestamp: Date.now(),
  });

  // sendBeacon is reliable during page unload
  if (navigator.sendBeacon) {
    const blob = new Blob([payload], { type: 'application/json' });
    navigator.sendBeacon(METRICS_ENDPOINT, blob);
  }
}
