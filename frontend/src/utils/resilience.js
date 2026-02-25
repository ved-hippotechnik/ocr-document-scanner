/**
 * Frontend resilience utilities.
 *
 * Provides hooks and helpers that answer the 7 production questions
 * for React components:
 *
 *   Q1 (services down)  — useCircuitBreaker, useApiHealthCheck
 *   Q2 (1000 req/s)     — useProcessingGuard, useRequestDedup
 *   Q3 (slow network)   — withTimeout
 *   Q5 (aggressive retry)— useProcessingGuard, useRequestDedup
 *   Q6 (3AM debugging)  — generateErrorId
 */

import { useRef, useCallback, useState, useEffect } from 'react';

// ---------------------------------------------------------------------------
// generateErrorId — trackable error references (Q6)
// ---------------------------------------------------------------------------

let _errorCounter = 0;

/**
 * Generate a unique, human-readable error ID.
 * Format: ERR-<timestamp_base36>-<counter>
 */
export function generateErrorId() {
  _errorCounter += 1;
  const ts = Date.now().toString(36).toUpperCase();
  const seq = _errorCounter.toString(36).toUpperCase().padStart(3, '0');
  return `ERR-${ts}-${seq}`;
}

// ---------------------------------------------------------------------------
// useProcessingGuard — synchronous double-click prevention (Q2, Q5)
// ---------------------------------------------------------------------------

/**
 * Returns a `guard(asyncFn)` wrapper that prevents concurrent executions.
 *
 * Unlike state-based `isProcessing` checks, this uses a ref so the guard
 * is synchronous and immune to React's async state batching — a second
 * click within the same event loop tick is blocked immediately.
 *
 * Usage:
 *   const { guard, isProcessing } = useProcessingGuard();
 *   const handleClick = guard(async () => { ... });
 */
export function useProcessingGuard() {
  const processingRef = useRef(false);
  const [isProcessing, setIsProcessing] = useState(false);

  const guard = useCallback(
    (asyncFn) =>
      async (...args) => {
        if (processingRef.current) return undefined;
        processingRef.current = true;
        setIsProcessing(true);
        try {
          return await asyncFn(...args);
        } finally {
          processingRef.current = false;
          setIsProcessing(false);
        }
      },
    []
  );

  return { guard, isProcessing };
}

// ---------------------------------------------------------------------------
// useRequestDedup — deduplicate in-flight requests (Q2, Q5)
// ---------------------------------------------------------------------------

/**
 * Returns a `dedup(key, promiseFn)` helper.
 *
 * If a request with the same key is already in-flight, the existing promise
 * is returned instead of starting a new one.
 *
 * Usage:
 *   const dedup = useRequestDedup();
 *   const result = await dedup(`${file.name}-${file.size}`, () => fetch(...));
 */
export function useRequestDedup() {
  const inflightRef = useRef(new Map());

  const dedup = useCallback((key, promiseFn) => {
    const inflight = inflightRef.current;
    if (inflight.has(key)) {
      return inflight.get(key);
    }

    const promise = promiseFn().finally(() => {
      inflight.delete(key);
    });

    inflight.set(key, promise);
    return promise;
  }, []);

  return dedup;
}

// ---------------------------------------------------------------------------
// useCircuitBreaker — stop sending requests after repeated failures (Q1)
// ---------------------------------------------------------------------------

const CB_CLOSED = 'closed';
const CB_OPEN = 'open';
const CB_HALF_OPEN = 'half_open';

/**
 * Circuit breaker hook for API calls.
 *
 * Opens after `failureThreshold` consecutive failures. While open, all
 * calls are rejected immediately. After `resetTimeoutMs`, the breaker
 * moves to half-open and allows one trial request.
 *
 * Returns:
 *   { state, call, reset }
 *   - state: 'closed' | 'open' | 'half_open'
 *   - call(promiseFn): wraps a promise through the breaker
 *   - reset(): manually close the breaker
 */
export function useCircuitBreaker({
  failureThreshold = 5,
  resetTimeoutMs = 30000,
} = {}) {
  const [state, setState] = useState(CB_CLOSED);
  const failCountRef = useRef(0);
  const timerRef = useRef(null);

  const openBreaker = useCallback(() => {
    setState(CB_OPEN);
    // Schedule half-open transition
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => {
      setState(CB_HALF_OPEN);
    }, resetTimeoutMs);
  }, [resetTimeoutMs]);

  const reset = useCallback(() => {
    failCountRef.current = 0;
    setState(CB_CLOSED);
    if (timerRef.current) clearTimeout(timerRef.current);
  }, []);

  const call = useCallback(
    async (promiseFn) => {
      if (state === CB_OPEN) {
        throw new Error('Circuit breaker is open — API appears unreachable');
      }

      try {
        const result = await promiseFn();
        // Success → close the breaker
        if (state === CB_HALF_OPEN) {
          reset();
        } else {
          failCountRef.current = 0;
        }
        return result;
      } catch (err) {
        failCountRef.current += 1;
        if (failCountRef.current >= failureThreshold || state === CB_HALF_OPEN) {
          openBreaker();
        }
        throw err;
      }
    },
    [state, failureThreshold, openBreaker, reset]
  );

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  return { state, call, reset };
}

// ---------------------------------------------------------------------------
// withTimeout — hard timeout + intermediate warning (Q3)
// ---------------------------------------------------------------------------

/**
 * Wrap a promise with a hard timeout and optional intermediate warning.
 *
 * @param {Promise} promise - The promise to wrap
 * @param {number} timeoutMs - Hard timeout in milliseconds
 * @param {number} [warningMs] - Show warning after this many ms (optional)
 * @param {Function} [onWarning] - Callback when warning threshold is reached
 * @returns {Promise} Resolves/rejects with the original promise, or rejects on timeout
 */
export function withTimeout(promise, timeoutMs, warningMs, onWarning) {
  return new Promise((resolve, reject) => {
    let settled = false;
    let warningTimer = null;

    const timeoutTimer = setTimeout(() => {
      if (!settled) {
        settled = true;
        if (warningTimer) clearTimeout(warningTimer);
        reject(new Error(`Request timed out after ${Math.round(timeoutMs / 1000)}s`));
      }
    }, timeoutMs);

    if (warningMs && onWarning) {
      warningTimer = setTimeout(() => {
        if (!settled) {
          onWarning();
        }
      }, warningMs);
    }

    promise.then(
      (value) => {
        if (!settled) {
          settled = true;
          clearTimeout(timeoutTimer);
          if (warningTimer) clearTimeout(warningTimer);
          resolve(value);
        }
      },
      (err) => {
        if (!settled) {
          settled = true;
          clearTimeout(timeoutTimer);
          if (warningTimer) clearTimeout(warningTimer);
          reject(err);
        }
      }
    );
  });
}

// ---------------------------------------------------------------------------
// useApiHealthCheck — tri-state health check (Q1, Q4)
// ---------------------------------------------------------------------------

/**
 * Periodically pings a health endpoint and returns a tri-state status.
 *
 * States:
 *   'healthy'  — API responded with 2xx
 *   'api_down' — API did not respond or returned error, but browser is online
 *   'offline'  — Browser reports navigator.onLine === false
 *
 * @param {string} url - Health check URL (e.g., '/api/v3/health')
 * @param {number} intervalMs - Polling interval (default 30s)
 */
export function useApiHealthCheck(url = '/api/v3/health', intervalMs = 30000) {
  const [status, setStatus] = useState('healthy');

  useEffect(() => {
    let mounted = true;

    const check = async () => {
      if (!navigator.onLine) {
        if (mounted) setStatus('offline');
        return;
      }

      try {
        const res = await fetch(url, {
          method: 'GET',
          cache: 'no-store',
          signal: AbortSignal.timeout?.(5000),
        });
        if (mounted) {
          setStatus(res.ok ? 'healthy' : 'api_down');
        }
      } catch {
        if (mounted) setStatus('api_down');
      }
    };

    check();
    const id = setInterval(check, intervalMs);

    const handleOnline = () => check();
    const handleOffline = () => { if (mounted) setStatus('offline'); };
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      mounted = false;
      clearInterval(id);
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [url, intervalMs]);

  return status;
}
